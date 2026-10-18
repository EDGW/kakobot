"""Unified dispatch; outer readonly gate, authorization, error and reply policies."""

import logging
from contextlib import nullcontext

from ..domain.commands import CATALOG, LEGACY, resolve
from ..domain.deadlines import DeadlineConfirmation
from ..domain.errors import BusinessError, ModelError
from ..domain.security import SecretViolation
from ..infrastructure.messaging.onebot import ReadonlyViolation, deadline_context
from ..presentation.names import NameDirectory

logger = logging.getLogger("astrbot")


class Dispatcher:
    def __init__(
        self,
        roles,
        readonly,
        guard,
        authorizer,
        role_service,
        deadlines,
        summaries,
        analysis,
        costs,
        announcements,
        super_roles,
        super_deadlines,
        requests,
        help_service,
        release_service,
    ):
        self.roles, self.readonly, self.guard, self.authorizer = (
            roles,
            readonly,
            guard,
            authorizer,
        )
        self.role_service, self.deadlines, self.summaries, self.analysis = (
            role_service,
            deadlines,
            summaries,
            analysis,
        )
        self.costs = costs
        self.help_service = help_service
        self.release_service = release_service
        self.announcements = announcements
        self.super_roles, self.super_deadlines, self.requests = (
            super_roles,
            super_deadlines,
            requests,
        )

    def should_handle(self, ctx):
        if ctx.actor == ctx.bot or (ctx.group and not ctx.mentioned_bot):
            return False
        command = ctx.command
        if command:
            return command[0] in {spec.name for spec in CATALOG} | {
                name for name, _ in LEGACY
            }
        return not ctx.text.lstrip().startswith("/") and self.analysis.enabled(ctx)

    async def handle(self, ctx, gateway):
        if not self.should_handle(ctx):
            return
        command = ctx.command
        is_ddl = (
            command is None
            or command[0] == "/ddl"
            or (command[0] == "/super" and command[1].split()[:1] == ["ddl"])
        )
        with deadline_context() if is_ddl else nullcontext():
            try:
                if ctx.group in self.readonly.readonly_groups:
                    if not is_ddl:
                        await self.guard.check(
                            gateway.bot, ctx.group, ctx.bot, "命令入口"
                        )
                    return
                names = NameDirectory(gateway, self.guard)

                async def on_submitted():
                    await self.reply(ctx, gateway, "已提交模型，正在处理，请稍候。")

                if command is None:
                    reply = await self.analysis.handle(
                        ctx, gateway, names, on_submitted
                    )
                else:
                    if command[0] == "/super" and "super" not in self.roles.effective(
                        ctx.actor
                    ):
                        raise BusinessError(
                            "此命令在当前位置不可用，或你没有所需的身份组。"
                        )
                    spec, args = resolve(*command)
                    if spec is None:
                        raise BusinessError("未知子命令，请使用 /help 查看语法。")
                    if spec.input_policy == "TEXT" and any(
                        part.get("type") != "text" for part in ctx.segments
                    ):
                        raise BusinessError("此命令只接受文字参数。")
                    action = await self.authorizer.authorize(spec, ctx, args, gateway)
                    reply = await self.execute(action, gateway, names, on_submitted)
                if reply:
                    show_view = False
                    for message in reply if isinstance(reply, list) else [reply]:
                        if isinstance(message, DeadlineConfirmation):
                            show_view |= message.refresh_view
                            message = message.text
                        if message:
                            await self.reply(ctx, gateway, message)
                    if show_view:
                        await self.updated_view(ctx, gateway, names)
            except ReadonlyViolation:
                return
            except SecretViolation as exc:
                await self.guard.report_error(gateway.bot, ctx.bot, "密钥拦截", exc)
            except BusinessError as exc:
                await self.safe_reply(ctx, gateway, str(exc))
            except Exception as exc:
                logger.error(
                    "KakoBot %s failed (%s)",
                    command[0] if command else "autoanalysis",
                    type(exc).__name__,
                )
                await self.guard.report_error(
                    gateway.bot,
                    ctx.bot,
                    f"{command[0] if command else 'autoanalysis'}；用户 {ctx.actor}；来源 {ctx.group or '私聊'}",
                    exc,
                    exc.diagnostic if isinstance(exc, ModelError) else "",
                )
                await self.safe_reply(
                    ctx, gateway, "操作失败，请联系 Super 查看详细错误。"
                )

    async def execute(self, action, gateway, names, on_submitted=None):
        handler = action.spec.handler
        if handler == "roles":
            return await self.role_service.handle(action, names)
        if handler == "super_roles":
            return await self.super_roles.handle(action, names)
        if handler == "super_deadlines":
            return await self.super_deadlines.handle(action, gateway, names)
        if handler == "requests":
            return await self.requests.handle(action, gateway, names)
        if handler in {"help", "super_help"}:
            return await self.help_service.handle(action, gateway)
        if handler in {"version", "changelog"}:
            return await self.release_service.handle(action, gateway)
        if handler == "deadlines":
            return await self.deadlines.handle(action, gateway, names, on_submitted)
        if handler == "summary":
            return await self.summaries.handle(action, gateway, names, on_submitted)
        if handler == "cost":
            return await self.costs.handle(action, names)
        if handler in {"announce", "announce_reject"}:
            return await self.announcements.handle(action, gateway)
        if handler == "readonly":
            parts = action.arguments.split()
            sub = action.spec.subcommand.split()[-1]
            if sub == "list":
                if parts:
                    raise BusinessError("用法：/readonly list")
                return "Readonly 群：\n" + (
                    "\n".join(
                        [
                            await names.group(group)
                            for group in sorted(self.readonly.readonly_groups, key=int)
                        ]
                    )
                    or "（空）"
                )
            if len(parts) != 1:
                raise BusinessError("用法：" + action.spec.usage)
            from ..domain.context import qq_id

            group = qq_id(parts[0])
            before = sorted(self.readonly.readonly_groups, key=int)
            after = sorted(
                (self.readonly.readonly_groups | {group})
                if sub == "add"
                else (self.readonly.readonly_groups - {group}),
                key=int,
            )
            ticket = self.super_roles.audit.prepare(
                action.context, "readonly " + sub, before, after
            )
            try:
                self.readonly.set(group, sub == "add")
            except Exception:
                self.super_roles.audit.finish(ticket, "uncertain")
                raise
            self.super_roles.audit.finish(ticket)
            return "已更新 Readonly：" + await names.group(group)
        if handler == "send":
            await gateway.send(
                text=action.resources["text"], group=action.resources["group"]
            )
            return "已发送到群 " + await names.group(action.resources["group"])
        if handler == "hello":
            return "好牛魔呢"
        raise RuntimeError("命令未绑定处理器。")

    async def reply(self, ctx, gateway, text):
        self.guard.secrets.check(text)
        await gateway.send(
            text=text, group=ctx.group, user="" if ctx.group else ctx.actor
        )

    async def updated_view(self, ctx, gateway, names):
        try:
            await self.deadlines.send_view(ctx, gateway, names)
        except ReadonlyViolation:
            return
        except Exception as exc:
            await self.guard.report_error(
                gateway.bot, ctx.bot, "DDL 操作已完成；自动发送 view 图片", exc
            )
            await self.safe_reply(
                ctx,
                gateway,
                "DDL 操作已完成，但预览图片未能发送，可稍后使用 /ddl view。",
            )

    async def safe_reply(self, ctx, gateway, text):
        try:
            await self.reply(ctx, gateway, text)
        except (ReadonlyViolation, SecretViolation):
            pass
        except Exception as exc:
            await self.guard.report_error(gateway.bot, ctx.bot, "错误回复发送", exc)
