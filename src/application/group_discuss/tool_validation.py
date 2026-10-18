"""Diagnose rejected tool arguments without logging commands or credentials."""

import json
import logging
import re

from pydantic import ValidationError
from pydantic_ai import ModelRetry
from pydantic_ai.capabilities import AbstractCapability

logger = logging.getLogger("astrbot")


class ToolValidationDiagnostics(AbstractCapability):
    async def on_tool_validate_error(self, ctx, *, call, tool_def, args, error):
        turn = ctx.deps
        if isinstance(error, ValidationError):
            # Never retain input/context: even a malformed JSON body can contain
            # credentials and arbitrary private command text.
            errors = [
                {"field": list(item["loc"]), "type": item["type"], "reason": item["msg"]}
                for item in error.errors(include_input=False, include_context=False, include_url=False)[:8]
            ]
        else:
            # Custom validators may embed user data in their message.
            errors = [{"type": "custom_validation", "reason": "参数未通过自定义校验。"}]
        detail = json.dumps({"tool": tool_def.name, "errors": errors}, ensure_ascii=False)
        detail = turn.service.guard.secrets.redact(detail)
        detail = re.sub(r"(?i)sk-[^\s\"'\\,}]+", "[密钥已隐藏]", detail)
        detail = detail[:2000]
        turn.validation_errors.append(detail)
        with turn.service.store.db:
            turn.service.store.log(turn.scope, turn.ctx.actor, "tool validation rejected", detail)
        logger.warning("KakoBot 工具参数校验失败：%s", detail)
        hint = (
            'execute_commands 参数须为 JSON 对象，commands 为非空字符串数组，例如 '
            '{"commands":["/ddl list"]}。仅修正错误调用，不重做已成功的命令。'
            if tool_def.name == "execute_commands" else "请按工具定义修正参数。"
        )
        # Return only sanitized diagnostics to the model, too. The tool manager
        # enforces the tool's one-retry budget before sending this correction.
        raise ModelRetry(detail + "\n" + hint) from error
