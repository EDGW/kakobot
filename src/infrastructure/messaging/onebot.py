"""Guard OneBot outbound traffic and expose the QQ operations used by KakoBot."""

import base64
import logging
import re
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from ...domain.context import qq_id
from ...domain.security import SecretFilter, SecretViolation
from ..storage.access.readonly import ReadonlyPolicy
from .output import format_text_output, needs_forward

logger = logging.getLogger("astrbot")
_DDL_SILENT = ContextVar("kakobot_ddl_silent", default=False)
_FORMAT_TEXT = ContextVar("kakobot_format_text", default=False)
SPARK_FACE_ID = "424"  # NapCat /续标识: native large animated "续火花" sticker.


def image_segment(data: bytes) -> dict:
    if not data.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
        raise ValueError("图片必须为 PNG 或 JPEG 格式。")
    return {
        "type": "image",
        "data": {"file": "base64://" + base64.b64encode(data).decode("ascii")},
    }


@contextmanager
def deadline_context():
    """DDL operations silently skip readonly; all other checks remain active."""
    token = _DDL_SILENT.set(True)
    try:
        yield
    finally:
        _DDL_SILENT.reset(token)


class ReadonlyViolation(PermissionError):
    """A group send was refused and a Super notification was attempted."""

    def __init__(self, group: str):
        super().__init__(f"群 {group} 为 Readonly 群，拒绝发送消息。")


def _action_name(action: str) -> str:
    return re.sub(r"_(?:async|rate_limited)$", "", action).lstrip("._")


def outbound_payload(action: str, params: dict) -> dict | None:
    """Select outgoing content; quick-operation context is inbound, not a reply."""
    name = _action_name(action)
    if name == "handle_quick_operation":
        operation = params.get("operation") or {}
        return operation if "reply" in operation else None
    if name.startswith(("send_", "upload_")):
        return params
    return None


def outbound_group(action: str, params: dict) -> str | None:
    """Resolve group destinations, including generic sends and quick replies."""
    name = _action_name(action)
    group = None
    if name == "handle_quick_operation":
        context = params.get("context") or {}
        operation = params.get("operation") or {}
        if context.get("message_type") == "group" and "reply" in operation:
            group = context.get("group_id")
    elif name == "send_msg" and params.get("message_type") == "private":
        return None
    elif name.startswith("send_") or name == "upload_group_file":
        group = params.get("group_id")
    if group is None:
        return None
    return qq_id(group)


@dataclass
class _Patch:
    api: Any
    original: Callable
    guarded: Callable


class OutboundGuard:
    """Enforce readonly and credential checks at the shared OneBot API entry."""

    def __init__(self, store: ReadonlyPolicy, config: Mapping | None = None):
        self.store = store
        self.secrets = SecretFilter(config if config is not None else {})
        self._patches: list[_Patch] = []

    def install(self, bot) -> None:
        # CQHttp.call_action, bot.api, dynamic send_* and sync API share this API.
        api = bot.api
        if any(patch.api is api for patch in self._patches):
            return
        original = api.call_action

        async def validate(action, params):
            group = outbound_group(action, params)
            if group in self.store.readonly_groups:
                if not _DDL_SILENT.get():
                    await self._notify(original, group, action, params.get("self_id"))
                raise ReadonlyViolation(group)
            payload = outbound_payload(action, params)
            if payload is not None:
                try:
                    self.secrets.check(payload)
                except SecretViolation as exc:
                    logger.warning("KakoBot: blocked QQ message containing an API key.")
                    await self._notify_super(
                        original,
                        "[KakoBot] 安全拦截：一条出站 QQ 消息包含受保护的 API Key，已拒绝发送。消息原文不记录、不转发。",
                        params.get("self_id"),
                    )
                    exc._kakobot_reported = True
                    raise

        async def guarded(action: str, **params):
            # Inspect the full original before splitting or moving it into nodes.
            await validate(action, params)
            outputs = (
                format_text_output(action, params)
                if _FORMAT_TEXT.get()
                else [(action, params)]
            )
            result = None
            for output_action, output_params in outputs:
                await validate(output_action, output_params)
                try:
                    result = await original(output_action, **output_params)
                except Exception as exc:
                    await self._report_error(
                        original, output_action, exc, output_params.get("self_id")
                    )
                    raise
            return result

        api.call_action = guarded
        self._patches.append(_Patch(api, original, guarded))

    async def check(self, bot, group: str, self_id: str, action: str) -> None:
        """Reject a known reply before spending time on a model request."""
        if group in self.store.readonly_groups:
            await self._notify(bot.call_action, group, action, self_id)
            raise ReadonlyViolation(group)

    async def _notify(self, call, group: str, action: str, self_id) -> None:
        await self._notify_super(
            call,
            f"[KakoBot] 已拦截向 Readonly 群 {group} 发送消息的请求，操作：{action}。",
            self_id,
        )

    async def report_error(
        self, bot, self_id: str, stage: str, error: Exception, detail: str = ""
    ) -> None:
        """Report command/model failures, bypassing recursive API error handling."""
        call = next(
            (patch.original for patch in self._patches if patch.api is bot.api),
            bot.call_action,
        )
        await self._report_error(call, stage, error, self_id, detail)

    async def _report_error(
        self, call, stage: str, error: Exception, self_id, detail: str = ""
    ) -> None:
        if getattr(error, "_kakobot_reported", False):
            return
        # Only explicitly supplied diagnostics may contain a model response body.
        text = f"[KakoBot] 运行错误\n阶段：{stage}\n错误类型：{type(error).__name__}"
        if detail or str(error):
            safe_detail = detail or str(error)
            if self.secrets.contains(safe_detail):
                public_error = str(error)
                safe_detail = (
                    public_error + "\n"
                    if not self.secrets.contains(public_error)
                    else ""
                ) + "详细诊断包含受保护信息，已省略。"
            text += "\n说明：" + safe_detail
        if self.secrets.contains(text):
            text = "[KakoBot] 运行错误，详细诊断包含受保护信息，已拒绝转发。"
        await self._notify_super(call, text, self_id)
        try:
            error._kakobot_reported = True
        except AttributeError:
            pass

    async def _notify_super(self, call, text: str, self_id) -> None:
        try:
            user = qq_id(self.store.super_user)
            params = {
                "user_id": int(user),
                "message": [
                    {
                        "type": "text",
                        "data": {"text": text},
                    }
                ],
            }
            if self_id:
                params["self_id"] = self_id
            # Check the whole text before splitting: keys may cross a boundary.
            self.secrets.check(params)
            if needs_forward(text) and not self_id:
                login = await call("get_login_info")
                params["self_id"] = qq_id(login["user_id"])
            for action, part in format_text_output(
                "send_private_msg", params, log=True
            ):
                # Internal notifications, complete nodes and headers are checked.
                self.secrets.check(part)
                await call(action, **part)
        except Exception as exc:
            # A notification failure cannot leak the message or recurse forever.
            logger.error(
                "KakoBot: Super notification failed (%s).",
                type(exc).__name__,
            )

    def uninstall(self) -> None:
        for patch in reversed(self._patches):
            if patch.api.call_action is patch.guarded:
                patch.api.call_action = patch.original
        self._patches.clear()


class OneBotGateway:
    """Route API calls through the guarded client and the triggering QQ account."""

    def __init__(self, bot, self_id: str, platform_id: str = "aiocqhttp"):
        self.bot = bot
        self.self_id = self_id
        self.platform_id = platform_id

    async def members(self, group: str) -> list[dict]:
        result = await self.bot.call_action(
            "get_group_member_list", group_id=int(qq_id(group)), self_id=self.self_id
        )
        if not isinstance(result, list) or any(
            not isinstance(item, dict) for item in result
        ):
            raise RuntimeError("群成员接口未返回有效列表。")
        return result

    async def remind(self, group: str, users: list[str], text: str):
        token = _FORMAT_TEXT.set(True)
        try:
            with deadline_context():
                await self.bot.call_action(
                    "send_group_msg",
                    group_id=int(qq_id(group)),
                    self_id=self.self_id,
                    message=[
                        {"type": "at", "data": {"qq": qq_id(user)}} for user in users
                    ]
                    + [{"type": "text", "data": {"text": "\n" + text}}],
                )
        finally:
            _FORMAT_TEXT.reset(token)

    async def remind_card(self, group: str, users: list[str], png: bytes):
        group_id = int(qq_id(group))
        if not 1 <= len(users) <= 20:
            raise ValueError("DDL 提醒须通知1～20名成员。")
        mentions = [{"type": "at", "data": {"qq": qq_id(user)}} for user in users]
        card = image_segment(png)
        with deadline_context():
            # Deliver the useful reminder first; a large animated face is sent
            # alone so QQ keeps its native sticker presentation.
            await self.bot.call_action(
                "send_group_msg",
                group_id=group_id,
                self_id=self.self_id,
                message=mentions + [card],
            )
            await self.bot.call_action(
                "send_group_msg",
                group_id=group_id,
                self_id=self.self_id,
                message=[{"type": "face", "data": {"id": SPARK_FACE_ID}}],
            )

    async def send(self, *, text: str, group: str = "", user: str = ""):
        if bool(group) == bool(user):
            raise ValueError("必须指定且只能指定一个群或私聊目标。")
        action = "send_group_msg" if group else "send_private_msg"
        destination = (
            {"group_id": int(qq_id(group))} if group else {"user_id": int(qq_id(user))}
        )
        # Array-format plain text prevents /send text being interpreted as CQ code.
        token = _FORMAT_TEXT.set(True)
        try:
            return await self.bot.call_action(
                action,
                **destination,
                self_id=self.self_id,
                message=[{"type": "text", "data": {"text": text}}],
            )
        finally:
            _FORMAT_TEXT.reset(token)

    async def history(self, group: str) -> list[dict]:
        result = await self.bot.call_action(
            "get_group_msg_history",
            group_id=int(qq_id(group)),
            count=100,
            message_id=0,
            reverse_order=True,
            self_id=self.self_id,
        )
        if not isinstance(result, dict) or not isinstance(result.get("messages"), list):
            raise RuntimeError("历史消息接口未返回有效的 messages 列表。")
        messages = result["messages"]
        if any(not isinstance(message, dict) for message in messages):
            raise RuntimeError("历史消息数据格式错误。")
        return sorted(messages, key=lambda message: float(message.get("time") or 0))[
            -100:
        ]

    async def send_link_forward(self, links, *, group="", user=""):
        if bool(group) == bool(user):
            raise ValueError("必须指定且只能指定一个群或私聊目标。")
        nodes = [
            {
                "type": "node",
                "data": {
                    "user_id": qq_id(self.self_id),
                    "nickname": "KakoBot · 回答链接",
                    "content": [
                        {
                            "type": "text",
                            "data": {
                                "text": label + "\n" + url if label != url else url
                            },
                        }
                    ],
                },
            }
            for label, url in links
        ]
        destination = (
            {"group_id": int(qq_id(group))} if group else {"user_id": int(qq_id(user))}
        )
        return await self.bot.call_action(
            "send_group_forward_msg" if group else "send_private_forward_msg",
            **destination,
            self_id=self.self_id,
            messages=nodes,
        )

    async def send_image(self, data: bytes, *, group: str = "", user: str = ""):
        if bool(group) == bool(user):
            raise ValueError("必须指定且只能指定一个群或私聊目标。")
        card = image_segment(data)
        destination = (
            {"group_id": int(qq_id(group))} if group else {"user_id": int(qq_id(user))}
        )
        # A native image segment bypasses only text-forward formatting; the
        # guarded client still validates the destination and full payload.
        return await self.bot.call_action(
            "send_group_msg" if group else "send_private_msg",
            **destination,
            self_id=self.self_id,
            message=[card],
        )

    async def message(self, identifier: str) -> dict:
        result = await self.bot.call_action(
            "get_msg", message_id=int(identifier), self_id=self.self_id
        )
        if not isinstance(result, dict):
            raise RuntimeError("引用消息接口未返回对象。")
        return result

    async def forward(self, identifier: str) -> list[dict]:
        result = await self.bot.call_action(
            "get_forward_msg", id=identifier, self_id=self.self_id
        )
        if isinstance(result, dict):
            candidates = [
                result.get(field) for field in ("messages", "message", "content")
            ]
            result = next(
                (value for value in candidates if value not in (None, "", [])),
                next((value for value in candidates if isinstance(value, list)), None),
            )
        if not isinstance(result, list) or any(
            not isinstance(item, dict) for item in result
        ):
            raise RuntimeError("合并转发接口未返回有效节点列表。")
        return result
