"""Scoped business commands; no shell, other plugins or global AI credentials."""

import hashlib
import re
from dataclasses import replace

from ...domain.commands import resolve
from ...domain.deadlines import DeadlineConfirmation
from ...domain.errors import BusinessError
from ...infrastructure.group_discuss.store import scope_key
from ...infrastructure.messaging.messages import visible_text
from ...infrastructure.model import business_model
from ...presentation.names import NameDirectory
from .mentions import automation_command, automation_segments


class CommandGateway:
    """Keep replies to command-produced images in the same discuss session."""

    def __init__(self, turn):
        self.turn = turn
        self.card_texts = []

    async def discuss_prompt(self, text):
        from .harness import command_model_request

        result, _ = await command_model_request(
            self.turn, "回答用户的问题，不调用其他工具或递归开启会话。", text
        )
        return result

    def capture_card_text(self, text):
        self.turn.service.guard.secrets.check(text)
        self.card_texts.append(text)

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
    def __init__(self, dispatcher, *, group_discuss=None, personal_discuss=None):
        self.dispatcher = dispatcher
        self.group_discuss = group_discuss
        self.personal_discuss = personal_discuss

    async def execute(self, turn, command):
        actor = turn.service.store.command_actor(turn.scope, turn.session, turn.id)
        # Neither identity nor conversation scope is supplied by the model.
        if scope_key(turn.ctx) != turn.scope or actor != turn.ctx.actor:
            raise BusinessError("命令执行身份或群上下文不匹配。")
        # Only DDL creation consumes native mentions as recipient candidates.
        # Keep other commands' text and transport behavior unchanged.
        parsed_command = command.split(maxsplit=2)
        ddl_creation = (len(parsed_command) >= 2 and parsed_command[0].lower() == "/ddl"
                        and parsed_command[1].lower() in {"add", "add-strict"})
        parts = automation_segments(command) if ddl_creation else [
            {"type": "text", "data": {"text": automation_command(command)}}
        ]
        command = visible_text(parts).strip()
        ctx = replace(
            turn.ctx,
            actor=actor,
            text=command,
            segments=parts,
            mentioned_bot=True,
            text_only=all(part["type"] == "text" for part in parts),
        )
        parsed = ctx.command
        spec, args = resolve(*parsed) if parsed else (None, "")
        dispatcher, gateway = self.dispatcher, CommandGateway(turn)
        control = next(
            ((service, service.command(ctx))
             for service in (self.personal_discuss, self.group_discuss)
             if service is not None and service.command(ctx) is not None),
            None,
        )
        if spec is None and control is None:
            raise BusinessError("仅支持 KakoBot 已注册的业务命令；不支持系统或其他插件命令。")
        # Discuss may not inherit DDL's readonly exemption.
        if ctx.group in dispatcher.readonly.readonly_groups:
            raise BusinessError("Readonly 群禁止 discuss 执行业务命令。")
        if ctx.group:
            await dispatcher.authorizer.require_member(actor, ctx.group, gateway)
        action = None
        names = NameDirectory(gateway, dispatcher.guard)
        if control is None:
            action = await dispatcher.authorizer.authorize(spec, ctx, args, gateway)
        await turn.check()
        turn.service.store.command_actor(turn.scope, turn.session, turn.id)
        with turn.service.store.db:
            turn.service.store.log(
                turn.scope, actor, "business command",
                f"{turn.session}: {spec.name} {spec.subcommand}" if spec else f"{turn.session}: discuss command",
            )
        # Nested model requests use the same metering, limits and current scope key.
        from .harness import command_model_request

        async def request(*args, **kwargs):
            return await command_model_request(turn, *args, **kwargs)

        with business_model(request):
            if control is not None:
                service, (global_command, raw) = control
                if service is self.personal_discuss:
                    if global_command:
                        reply = await service.manage_personal(ctx, gateway, raw)
                    else:
                        reply = await service.user_command(ctx, gateway, raw)
                else:
                    reply = await service.manage(ctx, gateway, global_command, raw)
            else:
                reply = await dispatcher.execute(
                    action, gateway, names
                )
        messages = []
        refresh_view = False
        for item in reply if isinstance(reply, list) else [reply]:
            if isinstance(item, DeadlineConfirmation):
                refresh_view |= item.refresh_view
                item = item.text
            if item:
                messages.append(str(item))
        if refresh_view:
            await dispatcher.updated_view(ctx, gateway, names)
        return "\n".join([*gateway.card_texts, *messages]) or "命令执行完成，图片等内容已由原处理器发送。"


async def execute_commands(turn, commands):
    """Persist a claim before any await or side effect; uncertain work is never retried."""
    if (
        not isinstance(commands, list)
        or not commands
        or any(
            not isinstance(c, str) or not c.strip() or len(c) > 2000 for c in commands
        )
    ):
        raise BusinessError("每批至少一条命令，每条最多 2000 字符。")
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
            (turn.id + "\0" + command).encode()
        ).hexdigest()
        try:
            previous = store.claim_command(
                turn.scope, turn.session, turn.id, fingerprint,
                limit=None if turn.service.global_super(actor) else
                turn.config["tools.execute_commands.max_commands_per_request"],
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
    labels = {
        "completed": "成功", "rejected": "拒绝", "blocked": "未执行",
        "uncertain": "结果未确认",
    }
    lines = []
    for command, result in zip(commands, results, strict=True):
        # Newly supplied credentials may not have been registered yet.
        safe = re.sub(r"(?i)sk-[^\s\"']+", "[密钥已隐藏]", command)
        safe = re.sub(r"(?i)((?:api_?key|token|password)\s*(?:=|\s)\s*)\S+", r"\1[已隐藏]", safe)
        safe = turn.service.guard.secrets.redact(safe)
        label = "复用结果，未重复执行" if result.get("reused") else labels.get(result["status"], result["status"])
        lines.append(f"{label}：{safe}")
    await turn.service.send(
        turn.ctx, turn.gateway, "机器人业务命令执行记录：\n" + "\n".join(lines), turn.session
    )
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
