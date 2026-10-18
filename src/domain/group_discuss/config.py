"""Typed, bounded settings; no provider or framework dependencies."""

import copy
import json
from urllib.parse import urlsplit

from ..errors import BusinessError

TOOLS = ("search_web", "fetch_webpage", "query_group_data", "read_session_history")
DEFAULT_SYSTEM_PROMPT = "符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容"
DEFAULTS = {
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "max_sessions": 5,
    "session_token_budget": 30000,
    "daily_token_budget": 200000,
    "context_token_limit": 6000,
    "summary_token_limit": 600,
    "recent_turns": 4,
    "max_output_tokens": 2048,
    "max_tool_calls_per_request": 5,
    "user_mode": "whitelist",
    "model_name": "",
    "reasoning_effort": "low",
}
MAXIMA = {
    "max_sessions": 20,
    "session_token_budget": 200000,
    "daily_token_budget": 2000000,
    "context_token_limit": 24000,
    "summary_token_limit": 2000,
    "recent_turns": 12,
    "max_output_tokens": 8192,
    "max_tool_calls_per_request": 12,
}
for _tool in TOOLS:
    DEFAULTS[f"tools.{_tool}.enabled"] = False
    DEFAULTS[f"tools.{_tool}.max_calls_per_request"] = 3
    MAXIMA[f"tools.{_tool}.max_calls_per_request"] = 8


def system_defaults():
    return {
        "defaults": copy.deepcopy(DEFAULTS),
        "maxima": copy.deepcopy(MAXIMA),
        "tool_enabled": dict.fromkeys(TOOLS, False),
        "allowed_models": [],
        "allowed_efforts": ["low", "medium", "high"],
        "allowed_user_modes": ["whitelist", "all", "blacklist"],
        "api_address": "",
        "search_api_key": "",
        "global_daily_token_budget": 5000000,
        "request_timeout": 180,
        "model_timeout": 90,
        "max_model_calls": 8,
        "group_concurrency": 2,
        "global_concurrency": 6,
        "group_queue_limit": 10,
        "global_queue_limit": 30,
        "tool_timeout": 20,
        "tool_result_tokens": 3000,
        "web_max_bytes": 2097152,
        "web_max_redirects": 3,
        "history_retention_days": 30,
        "system_prompt_max_chars": 4000,
    }


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
    if (
        not isinstance(policy["search_api_key"], str)
        or len(policy["search_api_key"]) > 512
    ):
        raise BusinessError("搜索密钥格式错误。")
    for key, value in policy["defaults"].items():
        # Empty model is intentionally not ready; global tool switches may override defaults.
        if key == "model_name" and value == "":
            continue
        if key.endswith(".enabled") and value is False:
            continue
        validate_group(
            key,
            min(value, policy["maxima"][key])
            if key in policy["maxima"] and type(value) is int
            else value,
            policy,
        )
    if (
        policy["defaults"]["summary_token_limit"]
        >= policy["defaults"]["context_token_limit"]
    ):
        raise BusinessError("摘要上限必须小于上下文上限。")


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


def estimate_tokens(value):
    """Conservative UTF-8 byte budget plus protocol allowance, not billed usage."""
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8")) + 256
