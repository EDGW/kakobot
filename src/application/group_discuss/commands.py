"""Scoped business commands; no shell, arbitrary dispatch or model access."""

import hashlib
from dataclasses import replace

from ...domain.commands import resolve
from ...domain.deadlines import DeadlineConfirmation
from ...domain.errors import BusinessError
from ...infrastructure.group_discuss.store import scope_key
from ...presentation.names import NameDirectory

ALLOWED = {
    ("/help", ""),
    ("/role", ""),
    ("/version", ""),
    ("/changelog", ""),
    *(("/ddl", sub) for sub in ("add-strict", "list", "view", "show", "remove")),
}


class CommandGateway:
    """Keep replies to command-produced images in the same discuss session."""

    def __init__(self, turn):
        self.turn = turn

    def __getattr__(self, name):
        return getattr(self.turn.gateway, name)

    def record(self, result):
        if isinstance(result, dict) and result.get("message_id") is not None:
            self.turn.service.store.map_message(
                self.turn.scope, result["message_id"], self.turn.session
            )
        return result

    async def send(self, **kwargs):
        return self.record(await self.turn.gateway.send(**kwargs))

    async def send_image(self, *args, **kwargs):
        return self.record(await self.turn.gateway.send_image(*args, **kwargs))


class BusinessCommands:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    async def execute(self, turn, command):
        actor = turn.service.store.command_actor(turn.scope, turn.session, turn.id)
        # Neither identity nor conversation scope is supplied by the model.
        if scope_key(turn.ctx) != turn.scope or actor != turn.ctx.actor:
            raise BusinessError("命令执行身份或群上下文不匹配。")
        ctx = replace(
            turn.ctx,
            actor=actor,
            text=command,
            segments=[{"type": "text", "data": {"text": command}}],
            mentioned_bot=True,
            text_only=True,
        )
        parsed = ctx.command
        spec, args = resolve(*parsed) if parsed else (None, "")
        if spec is None or (spec.name, spec.subcommand) not in ALLOWED:
            raise BusinessError(
                "仅支持 /help、/role、/version、/changelog，以及 /ddl "
                "add-strict/list/view/show/remove；其他命令未开放。"
            )
        dispatcher, gateway = self.dispatcher, CommandGateway(turn)
        # Discuss may not inherit DDL's readonly exemption.
        if ctx.group in dispatcher.readonly.readonly_groups:
            raise BusinessError("Readonly 群禁止 discuss 执行业务命令。")
        if ctx.group:
            await dispatcher.authorizer.require_member(actor, ctx.group, gateway)
        action = await dispatcher.authorizer.authorize(spec, ctx, args, gateway)
        await turn.check()
        turn.service.store.command_actor(turn.scope, turn.session, turn.id)
        with turn.service.store.db:
            turn.service.store.log(
                turn.scope,
                actor,
                "business command",
                f"{turn.session}: {spec.name} {spec.subcommand}",
            )
        reply = await dispatcher.execute(
            action, gateway, NameDirectory(gateway, dispatcher.guard)
        )
        messages = []
        for item in reply if isinstance(reply, list) else [reply]:
            if isinstance(item, DeadlineConfirmation):
                item = item.text
            if item:
                messages.append(str(item))
        return "\n".join(messages) or "命令执行完成，图片等内容已由原处理器发送。"


async def execute_commands(turn, commands):
    """Persist a claim before any await or side effect; uncertain work is never retried."""
    if (
        not isinstance(commands, list)
        or not 1 <= len(commands) <= 5
        or any(
            not isinstance(c, str) or not c.strip() or len(c) > 2000 for c in commands
        )
    ):
        raise BusinessError("每批须为 1～5 条命令，每条最多 2000 字符。")
    executor = turn.service.command_executor
    if executor is None:
        raise BusinessError("业务命令执行器未初始化。")
    store = turn.service.store
    results = []
    for index, command in enumerate(commands):
        try:
            await turn.check()
            if not turn.config["tools.execute_commands.enabled"]:
                raise BusinessError("业务命令工具已禁用。")
            actor = store.command_actor(turn.scope, turn.session, turn.id)
            if actor != turn.ctx.actor or scope_key(turn.ctx) != turn.scope:
                raise BusinessError("命令执行身份或群上下文不匹配。")
        except BusinessError as exc:
            results.extend(
                {"status": "blocked", "text": str(exc)} for _ in commands[index:]
            )
            break
        command = command.strip()
        turn.service.guard.secrets.check(command)
        fingerprint = hashlib.sha256(
            (command if turn.ctx.group else turn.id + "\0" + command).encode()
        ).hexdigest()
        try:
            previous = store.claim_command(
                turn.scope, turn.session, turn.id, fingerprint
            )
        except BusinessError as exc:
            results.append({"status": "blocked", "text": str(exc)})
            continue
        if previous is not None:
            results.append({**previous, "reused": True})
            continue
        try:
            text = await executor.execute(turn, command)
            turn.service.guard.secrets.check(text)
            result = {"status": "completed", "text": text}
        except BusinessError as exc:
            result = {"status": "rejected", "text": str(exc)}
            turn.service.guard.secrets.check(result)
        except Exception:
            # Side effects may have completed before a transport/storage failure.
            result = {
                "status": "uncertain",
                "text": "执行结果未确认，请人工核实；不会自动重复执行。",
            }
        store.finish_command(turn.scope, turn.session, actor, fingerprint, result)
        results.append(result)
    # Preserve every status when the shared tool layer crops large command output.
    budget = min(
        turn.service.policy["tool_result_max_bytes"],
        turn.config["context_max_bytes"] // 3,
    )
    per_result = max(0, (budget - 512) // len(results) - 192)
    for result in results:
        raw = result["text"].encode()
        if len(raw) > per_result:
            result["text"] = raw[:per_result].decode(errors="ignore") + " [详情已裁剪]"
    return results
