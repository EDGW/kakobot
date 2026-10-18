"""AstrBot lifecycle and QQ event adaptation; all business logic lives in services."""

import logging
import time
from pathlib import Path

from astrbot.api.event import filter
from astrbot.api.message_components import At, Plain
from astrbot.api.star import StarTools

from ..application.runtime import Runtime
from ..domain.context import CommandContext
from ..infrastructure.messaging.messages import (
    MAX_DEPTH,
    message_content,
    segments,
    visible_text,
)
from ..infrastructure.messaging.onebot import OneBotGateway

logger = logging.getLogger("astrbot")


def component(part, depth=1):
    if isinstance(part, Plain):
        return {"type": "text", "data": {"text": part.text}}
    if isinstance(part, At):
        return {"type": "at", "data": {"qq": str(part.qq)}}
    name = type(part).__name__.lower()
    if name in {"reply", "forward", "node", "nodes"} and depth > MAX_DEPTH:
        # Keep the boundary visible; the authorized expander rejects the whole
        # package before reading it. Unrelated messages still remain untouched.
        return {"type": "forward" if name == "nodes" else name, "data": {}}
    if name == "reply":
        data = {"id": str(part.id)}
        chain = getattr(part, "chain", None)
        if chain:
            data.update(
                message=[component(item, depth + 1) for item in chain],
                message_id=str(part.id),
                sender={
                    "user_id": str(getattr(part, "sender_id", "")),
                    "nickname": str(getattr(part, "sender_nickname", "")),
                },
                time=getattr(part, "time", None),
            )
        return {"type": "reply", "data": data}
    if name == "forward":
        return {"type": "forward", "data": {"id": str(part.id)}}
    if name == "nodes":
        return {
            "type": "forward",
            "data": {"content": [component(item, depth) for item in part.nodes]},
        }
    if name == "node":
        contents = getattr(part, "content", None)
        if contents is not None:
            return {
                "type": "node",
                "data": {
                    "user_id": str(getattr(part, "uin", "")),
                    "nickname": str(getattr(part, "name", "")),
                    "content": [component(item, depth + 1) for item in contents],
                    "time": getattr(part, "time", None),
                },
            }
    return {"type": name, "data": {}}


def incoming(event, platform):
    raw = getattr(event.message_obj, "raw_message", None)
    raw = raw if isinstance(raw, dict) else {}
    parts = (
        segments(raw["message"])
        if isinstance(raw.get("message"), (list, str))
        else [component(part) for part in event.get_messages()]
    )
    # AstrBot may have already fetched an ordinary quote. Reuse its full chain
    # instead of querying a temporary/inner message ID a second time.
    cached_quotes = {
        str(part.id): part
        for part in event.get_messages()
        if type(part).__name__.lower() == "reply" and getattr(part, "chain", None)
    }
    enriched = []
    for part in parts:
        data = part.get("data") or {}
        cached = cached_quotes.get(str(data.get("id")))
        if (
            part.get("type") == "reply"
            and cached
            and message_content(data) in (None, "", [])
        ):
            part = {**part, "data": {**data, **component(cached)["data"]}}
        enriched.append(part)
    parts = enriched
    bot = str(event.get_self_id())
    mentioned = any(
        part.get("type") == "at" and str(part.get("data", {}).get("qq")) == bot
        for part in parts
    )
    parts = [
        part
        for part in parts
        if not (part.get("type") == "at" and str(part.get("data", {}).get("qq")) == bot)
    ]
    return CommandContext(
        actor=str(event.get_sender_id()),
        bot=bot,
        platform=platform,
        group=str(event.get_group_id() or ""),
        message_id=str(
            raw.get("message_id") or getattr(event.message_obj, "message_id", "") or ""
        ),
        received_at=time.time(),
        text=visible_text(parts).strip(),
        segments=parts,
        mentioned_bot=mentioned,
        text_only=all(part.get("type") == "text" for part in parts),
    )


class InputFilter(filter.CustomFilter):
    """Run before default chat, while leaving unmatched events untouched."""

    def filter(self, event, cfg):
        return not event.get_group_id() or any(
            (isinstance(part, At) and str(part.qq) == str(event.get_self_id()))
            or type(part).__name__.lower() == "reply"
            for part in event.get_messages()
        )


class AstrBotAdapter:
    def __init__(self, context, config):
        self.context = context
        self.runtime = None
        self.routes = {}
        self.request_hooks = []
        self.config = config
        self.directory = Path(StarTools.get_data_dir("astrbot_plugin_kakobot"))

    async def initialize(self):
        config = self.config
        try:
            self.runtime = Runtime(
                self.directory, config, self.resolve_gateway, self.diagnostic_gateway
            )
        except Exception as exc:
            # No business or scheduler is exposed after a startup/migration failure.
            logger.error(
                "KakoBot 启动/迁移失败（%s），业务未启动。%s",
                type(exc).__name__,
                self._safe_startup_error(config, exc),
            )
            await self._report_startup(config, exc)
            raise
        self.install_guards()
        await self._load_routes()

    async def _report_startup(self, config, exc):
        from types import SimpleNamespace

        from ..infrastructure.messaging.onebot import OutboundGuard

        policy = SimpleNamespace(
            super_user=str(config.get("super_user", "000000000")),
            readonly_groups=frozenset(),
        )
        notifier = OutboundGuard(policy, config)
        for platform in self.platforms():
            try:
                await notifier.report_error(
                    platform.get_client(), "", "启动/迁移失败，业务未启动", exc
                )
                break
            except Exception:
                continue

    @staticmethod
    def _safe_startup_error(config, exc):
        from ..domain.security import SecretFilter

        return (
            "诊断包含受保护信息，已省略。"
            if SecretFilter(config).contains(str(exc))
            else str(exc)
        )

    @staticmethod
    def platform_id(platform):
        meta = platform.meta()
        return str(getattr(meta, "id", None) or meta.name)

    def platforms(self):
        return [
            item
            for item in self.context.platform_manager.get_insts()
            if item.meta().name == "aiocqhttp"
        ]

    def install_guards(self):
        if self.runtime:
            for platform in self.platforms():
                client = platform.get_client()
                self.runtime.guard.install(client)
                if not any(bot is client for bot, _ in self.request_hooks):
                    self.install_requests(platform, client)

    def install_requests(self, platform, client):
        platform_id = self.platform_id(platform)

        async def receive(raw):
            if not self.runtime or self.runtime.closing:
                return
            try:
                from ..domain.context import qq_id

                bot = qq_id(raw.get("self_id"))
                self.routes[(platform_id, bot)] = client
                await self.runtime.handle_request(
                    platform_id, raw, OneBotGateway(client, bot, platform_id)
                )
            except Exception as exc:
                logger.error("KakoBot 申请接入失败（%s）", type(exc).__name__)
                await self.runtime.guard.report_error(
                    client, str(raw.get("self_id") or ""), "申请接入", exc
                )

        client.subscribe("request", receive)
        self.request_hooks.append((client, receive))

    def resolve_gateway(self, platform_id, bot_id):
        matches = [
            platform
            for platform in self.platforms()
            if self.platform_id(platform) == platform_id
        ]
        if len(matches) != 1 or not bot_id:
            return None
        client = matches[0].get_client()
        # Confirm this bot account using a previously observed, authenticated event.
        if self.routes.get((platform_id, bot_id)) is not client:
            return None
        self.runtime.guard.install(client)
        return OneBotGateway(client, bot_id, platform_id)

    def diagnostic_gateway(self):
        for (platform_id, bot_id), client in self.routes.items():
            if any(item.get_client() is client for item in self.platforms()):
                return OneBotGateway(client, bot_id, platform_id)
        return None

    async def _load_routes(self):
        if not self.runtime or self.runtime.closing:
            return
        self.install_guards()
        for platform in self.platforms():
            try:
                result = await platform.get_client().call_action("get_login_info")
                bot = str(result["user_id"])
                self.routes[(self.platform_id(platform), bot)] = platform.get_client()
            except Exception as exc:
                logger.error("KakoBot 账号路由查询失败（%s）", type(exc).__name__)
                gateway = self.diagnostic_gateway()
                if gateway:
                    await self.runtime.guard.report_error(
                        gateway.bot, gateway.self_id, "启动账号路由查询", exc
                    )
                else:
                    await self.runtime.guard.report_error(
                        platform.get_client(), "", "启动账号路由查询", exc
                    )
        self.runtime.scheduler.start()
        self.runtime.upgrade_announcements.start()

    async def platforms_loaded(self):
        await self._load_routes()

    async def astrbot_loaded(self):
        await self._load_routes()

    async def handle_message(self, event):
        if not self.runtime or self.runtime.closing:
            return
        try:
            await self._handle_message(event)
        except Exception as exc:
            logger.error("KakoBot 消息接入失败（%s）", type(exc).__name__)
            try:
                await self.runtime.guard.report_error(
                    event.bot, str(event.get_self_id() or ""), "消息接入", exc
                )
            except Exception as report_exc:
                logger.error(
                    "KakoBot 接入错误通知失败（%s）", type(report_exc).__name__
                )

    async def _handle_message(self, event):
        raw = getattr(event.message_obj, "raw_message", None)
        if isinstance(raw, dict) and raw.get("post_type", "message") != "message":
            # Request events are handled by the raw OneBot hook, never as AI input.
            return
        self.runtime.guard.install(event.bot)
        matches = [
            platform
            for platform in self.platforms()
            if platform.get_client() is event.bot
        ]
        if len(matches) != 1:
            raise RuntimeError("收到消息但无法唯一确定平台，未处理。")
        platform_id = self.platform_id(matches[0])
        ctx = incoming(event, platform_id)
        self.routes[(platform_id, ctx.bot)] = event.bot
        if not self.runtime.candidate(ctx):
            self.runtime.observe(ctx)
            return
        if await self.runtime.handle(
            ctx, OneBotGateway(event.bot, ctx.bot, platform_id)
        ):
            event.stop_event()

    async def terminate(self):
        for client, handler in self.request_hooks:
            client.unsubscribe("request", handler)
        self.request_hooks.clear()
        if self.runtime:
            await self.runtime.close()
