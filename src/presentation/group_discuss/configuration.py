"""Local configuration cards. Only masked credentials may enter this renderer."""

from ..cards import render_value_cards

SECTIONS = [
    (
        "接入与用户",
        {
            "enabled": "群 AI 功能",
            "api_key": "DeepSeek API Key",
            "model_name": "模型",
            "reasoning_effort": "思考强度",
            "user_mode": "用户准入",
        },
    ),
    (
        "会话与预算",
        {
            "max_sessions": "活跃会话数",
            "session_token_budget": "每会话 token 预算",
            "daily_token_budget": "群每日 token 预算",
            "context_token_limit": "输入上下文上限",
            "summary_token_limit": "摘要输出上限",
            "recent_turns": "优先保留最近轮次",
            "max_output_tokens": "单次模型输出上限",
            "max_tool_calls_per_request": "每请求工具总次数",
        },
    ),
    (
        "工具权限与限次",
        {
            f"tools.{tool}.{suffix}": label
            + ("开关" if suffix == "enabled" else "每请求次数")
            for tool, label in (
                ("search_web", "搜索"),
                ("fetch_webpage", "网页读取"),
                ("query_group_data", "群 DDL 查询"),
                ("read_session_history", "会话历史"),
            )
            for suffix in ("enabled", "max_calls_per_request")
        },
    ),
    ("群系统提示词", {"system_prompt": "当前提示词"}),
]


def value_text(value):
    if isinstance(value, bool):
        return "已开启" if value else "已关闭"
    if value == "" or value is None:
        return "未设置"
    if type(value) is int:
        return f"{value:,}"
    if isinstance(value, list):
        return "、".join(map(str, value)) or "无"
    return str(value)


def configuration_sections(shown, stored, policy):
    """Keep effective values, provenance and relevant system constraints together."""
    sections = []
    for title, labels in SECTIONS:
        rows = []
        for key, label in labels.items():
            if key not in shown:
                continue
            value = shown[key]
            source = "群内设置" if key in stored else "继承系统默认"
            details = [key, source]
            if key == "api_key":
                details = [key, "群独立密钥 · 仅展示脱敏值"]
            elif key == "enabled":
                details = [key, "由全局 Super 管理"]
            elif key in stored and stored[key] != value:
                details.append("存储值 " + value_text(stored[key]))
            if key in policy["maxima"]:
                details.append("全局上限 " + value_text(policy["maxima"][key]))
            choices = {
                "model_name": "allowed_models",
                "reasoning_effort": "allowed_efforts",
                "user_mode": "allowed_user_modes",
            }.get(key)
            if choices:
                details.append("允许：" + value_text(policy[choices]))
            if key.startswith("tools.") and key.endswith(".enabled"):
                details.append(
                    "系统总开关："
                    + value_text(policy["tool_enabled"][key.split(".")[1]])
                )
            if key == "system_prompt":
                details.append(f"最多 {policy['system_prompt_max_chars']:,} 字符")
            rows.append((label, value_text(value), " · ".join(details)))
        if rows:
            sections.append((title, rows))
    return sections


def render_configuration(group, shown, stored, policy):
    """Render only sanitized configuration values, including a masked API Key."""
    return render_value_cards(
        "群 AI 配置",
        f"群 {group} · 私聊管理 · 当前生效值",
        configuration_sections(shown, stored, policy),
        banner="KAKOBOT / GROUP DISCUSS",
        footer=(
            "模型及联网费用由本群 Key 承担；数值与工具权限受全局约束。",
            "/group-discuss admin config show " + str(group) + " [KEY]",
        ),
    )
