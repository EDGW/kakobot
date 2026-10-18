"""Typed, bounded settings; no provider or framework dependencies."""

import copy
import json
from urllib.parse import urlsplit

from ..errors import BusinessError

TOOLS = (
    "search_web",
    "fetch_webpage",
    "query_group_data",
    "read_session_history",
    "query_docs",
)
DEFAULT_SYSTEM_PROMPT = "符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容"
DEFAULTS = {
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "max_sessions": 5,
    "session_token_budget": 300000,
    "daily_token_budget": 2000000,
    "context_max_bytes": 65536,
    "summary_token_limit": 1800,
    "recent_turns": 4,
    "max_output_tokens": 8192,
    "max_tool_calls_per_request": 15,
    "user_mode": "whitelist",
    "model_name": "",
    "reasoning_effort": "low",
}
MAXIMA = {
    "max_sessions": 20,
    "session_token_budget": 2000000,
    "daily_token_budget": 20000000,
    "context_max_bytes": 262144,
    "summary_token_limit": 6000,
    "recent_turns": 12,
    "max_output_tokens": 32768,
    "max_tool_calls_per_request": 36,
}
for _tool in TOOLS:
    DEFAULTS[f"tools.{_tool}.enabled"] = _tool == "query_docs"
    DEFAULTS[f"tools.{_tool}.max_calls_per_request"] = 9
    MAXIMA[f"tools.{_tool}.max_calls_per_request"] = 24


def system_defaults():
    return {
        "defaults": copy.deepcopy(DEFAULTS),
        "maxima": copy.deepcopy(MAXIMA),
        "tool_enabled": dict.fromkeys(TOOLS, True),
        "allowed_models": [
            "deepseek-v4-flash",
            "deepseek-flash",
            "deepseek-v4-pro",
            "deepseek-pro",
        ],
        "allowed_efforts": ["low", "medium", "high"],
        "allowed_user_modes": ["whitelist", "all", "blacklist"],
        "api_address": "https://api.deepseek.com",
        "global_daily_token_budget": 50000000,
        "request_timeout": 180,
        "model_timeout": 90,
        "max_model_calls": 24,
        "group_concurrency": 2,
        "global_concurrency": 6,
        "group_queue_limit": 10,
        "global_queue_limit": 30,
        "tool_timeout": 20,
        "tool_result_max_bytes": 8192,
        "web_max_bytes": 2097152,
        "web_max_redirects": 3,
        "history_retention_days": 30,
        "system_prompt_max_chars": 4000,
    }


# Legacy defaults are upgraded once; non-default administrator choices keep their value.
LEGACY_DEFAULTS = {
    "session_token_budget": 30000,
    "daily_token_budget": 200000,
    "context_max_bytes": 6000,
    "summary_token_limit": 600,
    "max_output_tokens": 2048,
    "max_tool_calls_per_request": 5,
    **{f"tools.{tool}.max_calls_per_request": 3 for tool in TOOLS},
}
LEGACY_MAXIMA = {
    "session_token_budget": 200000,
    "daily_token_budget": 2000000,
    "context_max_bytes": 24000,
    "summary_token_limit": 2000,
    "max_output_tokens": 8192,
    "max_tool_calls_per_request": 12,
    **{f"tools.{tool}.max_calls_per_request": 8 for tool in TOOLS},
}


def upgrade_group_limits(values, *, maxima=False):
    """Migrate a legacy mapping in place. Caller persists a version marker atomically."""
    if "context_token_limit" in values:
        # Hosts may have already injected the new schema default beside the old key.
        values["context_max_bytes"] = values.pop("context_token_limit")
    old = LEGACY_MAXIMA if maxima else LEGACY_DEFAULTS
    new = MAXIMA if maxima else DEFAULTS
    for key, previous in old.items():
        if key in values and values[key] == previous:
            values[key] = new[key]


def upgrade_policy_limits(policy):
    for section in ("defaults", "maxima"):
        if section in policy:
            upgrade_group_limits(policy[section], maxima=section == "maxima")
    if "tool_result_tokens" in policy:
        policy["tool_result_max_bytes"] = policy.pop("tool_result_tokens")
    for key, previous, new in (
        ("tool_result_max_bytes", 3000, 8192),
        ("global_daily_token_budget", 5000000, 50000000),
        ("max_model_calls", 8, 24),
    ):
        if policy.get(key) == previous:
            policy[key] = new


def upgrade_tools_policy(policy, fallback=None):
    """Add new docs-tool settings to old nested overrides without changing choices."""
    base = fallback if fallback is not None else system_defaults()
    for section, keys in {
        "defaults": (
            "tools.query_docs.enabled",
            "tools.query_docs.max_calls_per_request",
        ),
        "maxima": ("tools.query_docs.max_calls_per_request",),
        "tool_enabled": ("query_docs",),
    }.items():
        for key in keys:
            policy[section].setdefault(key, base[section][key])


def parse_value(raw):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def validate_group(key, value, policy):
    if key == "system_prompt":
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > policy["system_prompt_max_chars"]
        ):
            raise BusinessError(
                f"系统提示词须为非空文本，最多 {policy['system_prompt_max_chars']} 字符。"
            )
        return
    if key == "api_key":
        if not isinstance(value, str) or len(value) > 512 or (value and len(value) < 8):
            raise BusinessError("API Key 须为 8～512 字符，或空字符串以清除。")
        return
    if key not in DEFAULTS:
        raise BusinessError("未知或不可修改的群配置项。")
    if key in policy["maxima"]:
        lower = 0 if ".max_calls_per_request" in key else 1
        if type(value) is not int or not lower <= value <= policy["maxima"][key]:
            raise BusinessError(f"{key} 允许范围：{lower}～{policy['maxima'][key]}。")
    elif key.endswith(".enabled"):
        if type(value) is not bool:
            raise BusinessError("开关必须是 true 或 false。")
        if value and not policy["tool_enabled"][key.split(".")[1]]:
            raise BusinessError("系统尚未允许此工具。")
    else:
        choices = {
            "user_mode": policy["allowed_user_modes"],
            "model_name": policy["allowed_models"],
            "reasoning_effort": policy["allowed_efforts"],
        }[key]
        if value not in choices:
            raise BusinessError(f"{key} 允许值：{', '.join(choices) or '尚未配置'}。")


def validate_system(policy):
    base = system_defaults()
    if set(policy) != set(base):
        raise BusinessError("系统 discuss 配置字段不完整或含未知字段。")
    if set(policy["defaults"]) != set(DEFAULTS) or set(policy["maxima"]) != set(MAXIMA):
        raise BusinessError("defaults/maxima 字段不完整。")
    if set(policy["tool_enabled"]) != set(TOOLS) or any(
        type(v) is not bool for v in policy["tool_enabled"].values()
    ):
        raise BusinessError("工具总开关配置错误。")
    for key, maximum in policy["maxima"].items():
        if type(maximum) is not int or not 1 <= maximum <= 1000000000:
            raise BusinessError(f"{key} 系统最大值须为正整数，且不超过 10 亿。")
    for key in ("allowed_models", "allowed_efforts", "allowed_user_modes"):
        values = policy[key]
        if not isinstance(values, list) or any(
            not isinstance(v, str) or not v for v in values
        ):
            raise BusinessError(f"{key} 必须为非空字符串组成的数组。")
    if any(not m.lower().startswith("deepseek") for m in policy["allowed_models"]):
        raise BusinessError("仅允许 DeepSeek 模型名称。")
    if not set(policy["allowed_user_modes"]) <= {"whitelist", "all", "blacklist"}:
        raise BusinessError("未知的 user 模式。")
    for key, value in base.items():
        if type(value) is int and (
            type(policy[key]) is not int or not 1 <= policy[key] <= 1000000000
        ):
            raise BusinessError(f"{key} 必须为正整数且不超过 10 亿。")
    address = policy["api_address"]
    if not isinstance(address, str):
        raise BusinessError("api_address 必须为字符串。")
    if address:
        parsed = urlsplit(address)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise BusinessError("模型地址须为无认证、查询及片段的 HTTPS 地址。")
    for key, value in policy["defaults"].items():
        # Empty model is intentionally not ready; global tool switches may override defaults.
        if key == "model_name" and value == "":
            continue
        if key.endswith(".enabled"):
            if type(value) is not bool:
                raise BusinessError("默认工具开关须为 true 或 false。")
            continue
        validate_group(
            key,
            min(value, policy["maxima"][key])
            if key in policy["maxima"] and type(value) is int
            else value,
            policy,
        )


def effective(stored, policy):
    result = {**policy["defaults"], **stored}
    for key, maximum in policy["maxima"].items():
        result[key] = min(result[key], maximum)
    for tool in TOOLS:
        key = f"tools.{tool}.enabled"
        result[key] = result[key] and policy["tool_enabled"][tool]
    return result


def mask_key(key):
    if not key:
        return "未设置"
    value = key.removeprefix("sk-")
    return "sk-" + value[:2] + "*****" + value[-2:] if len(value) >= 8 else "*****"


def input_size_bytes(value):
    """Serialized UTF-8 bytes plus protocol allowance; never a token count."""
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8")) + 256
