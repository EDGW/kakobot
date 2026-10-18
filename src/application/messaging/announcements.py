"""Explicit Super broadcasts to observed, eligible private conversations."""

import asyncio

from ...domain.errors import BusinessError
from ...domain.security import SecretViolation
from ...infrastructure.storage.broadcasts.updates import load_update
from ...presentation.announcements import format_announcement


class AnnouncementService:
    def __init__(self, roles, conversations, guard):
        self.roles = roles
        self.conversations = conversations
        self.guard = guard
        self.locks = {}

    async def handle(self, action, gateway):
        ctx, arguments = action.context, action.arguments.strip()
        if action.spec.handler == "announce_reject":
            if arguments.lower() not in {"on", "off"}:
                raise BusinessError("用法：/announce-reject on|off")
            rejected = arguments.lower() == "on"
            self.conversations.reject(ctx, rejected)
            return (
                "已拒收本机器人的所有广播，DDL 提醒不受影响；/announce-reject off 恢复接收。"
                if rejected
                else "已恢复接收本机器人的广播；需拥有 autoanalysis 身份组且有过私聊。"
            )
        if arguments:
            parts = arguments.split(maxsplit=1)
            if len(parts) != 2 or parts[0].lower() != "text" or not parts[1].strip():
                raise BusinessError("用法：" + action.spec.usage)
            content = parts[1].strip()
        else:
            content = load_update()
        text = format_announcement(content)
        self.guard.secrets.check(text)
        lock = self.locks.setdefault((ctx.platform, ctx.bot), asyncio.Lock())
        if lock.locked():
            raise BusinessError("当前机器人已有广播正在发送，请等待完成。")
        async with lock:
            candidates = [
                user
                for user in self.conversations.recipients(ctx.platform, ctx.bot)
                if user != ctx.bot and "autoanalysis" in self.roles.effective(user)
            ]
            if not candidates:
                return "没有可接收广播的私聊用户（须有私聊记录、autoanalysis 权限且未拒收）。"
            await gateway.send(
                text=f"开始广播，当前有{len(candidates)}位符合条件的私聊用户。",
                group=ctx.group,
                user="" if ctx.group else ctx.actor,
            )
            sent, skipped, failed = 0, 0, 0
            for user in candidates:
                if "super" not in self.roles.effective(ctx.actor):
                    raise BusinessError(
                        f"Super 权限已变更，广播已停止；已发送{sent}人，失败{failed}人。"
                    )
                if "autoanalysis" not in self.roles.effective(
                    user
                ) or not self.conversations.accepts(ctx.platform, ctx.bot, user):
                    skipped += 1
                    continue
                try:
                    await gateway.send(text=text, user=user)
                except SecretViolation:
                    raise
                except Exception as exc:
                    failed += 1
                    await self.guard.report_error(
                        gateway.bot, ctx.bot, f"广播；接收人 {user}", exc
                    )
                else:
                    sent += 1
                # Pace outbound QQ calls while allowing new opt-outs to be handled.
                await asyncio.sleep(0.5)
            return f"广播完成：已发送{sent}人，跳过{skipped}人，失败{failed}人。"
