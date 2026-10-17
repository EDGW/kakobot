"""Strict argument and resource parsing for explicit Super operations."""

import re
import shlex

from .context import qq_id
from .deadlines import _timestamp
from .errors import BusinessError


def arguments(text, *, options=(), flags=("dry-run",)):
    try:
        tokens = shlex.split(text)
    except ValueError as exc:
        raise BusinessError("参数引号不完整。") from exc
    positional, values = [], {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token.startswith("--"):
            positional.append(token)
            continue
        key, sep, value = token[2:].partition("=")
        if key in values or key not in set(options) | set(flags):
            raise BusinessError("未知或重复参数：--" + key)
        if key in flags:
            if sep:
                raise BusinessError("--" + key + " 不接受值。")
            values[key] = True
        else:
            if not sep:
                if index == len(tokens) or tokens[index].startswith("--"):
                    raise BusinessError("--" + key + " 缺少值。")
                value = tokens[index]
                index += 1
            if not value:
                raise BusinessError("--" + key + " 缺少值。")
            values[key] = value
    return positional, values


def csv(value, convert=str, *, limit=100):
    parts = value.split(",")
    if not 1 <= len(parts) <= limit or any(not item.strip() for item in parts):
        raise BusinessError(f"列表须用逗号分隔，最多{limit}项，不允许空项。")
    return list(dict.fromkeys(convert(item.strip()) for item in parts))


def page_number(value):
    if not re.fullmatch(r"[1-9][0-9]{0,8}", str(value)):
        raise BusinessError("页码必须为正整数。")
    return int(value)


def target_scope(value, ctx, *, allow_all=False):
    value = value.lower()
    if value == "this":
        return ctx.scope
    if value == "all" and allow_all and not ctx.group:
        return None
    kind, sep, identity = value.partition(":")
    if not sep or kind not in {"user", "group"}:
        raise BusinessError("对象须为 this、user:QQ 或 group:群号；私聊查询支持 all。")
    identity = qq_id(identity)
    if ctx.group and (kind != "group" or identity != ctx.group):
        raise BusinessError("群内只能管理本群 DDL；跨会话管理请私聊 Super 命令。")
    return ctx.platform, ctx.bot, "CHAT" if kind == "user" else "GROUP", identity


def task_reference(value, ctx):
    target, sep, number = value.rpartition("#")
    if not sep:
        target, number = "this", value
    identifier = int(qq_id(number))
    if identifier > 9223372036854775807:
        raise BusinessError("DDL 编号无效。")
    return target_scope(target, ctx), identifier


def reference(task):
    return f"{'group' if task['location'] == 'GROUP' else 'user'}:{task['conversation']}#{task['id']}"


def reminder_times(value, deadline):
    result = []
    for part in csv(value, limit=20):
        if part == "0":
            seconds = 0
        elif re.fullmatch(r"-(?:\d+(?:min|d|h|m|s))+", part):
            seconds = sum(
                int(amount) * {"d": 86400, "h": 3600, "min": 60, "m": 60, "s": 1}[unit]
                for amount, unit in re.findall(r"(\d+)(min|d|h|m|s)", part[1:])
            )
        else:
            raise BusinessError("提醒格式：--remind=-1d,-3h,-30min,0；0 表示到期。")
        result.append(deadline - seconds)
    return sorted(set(result))


def time_filter(value):
    return _timestamp(value)
