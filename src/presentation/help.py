"""Feature-grouped command help for the current conversation and permissions."""

from ..domain.errors import BusinessError

SECTIONS = (
    "基础与身份查询",
    "DDL · 创建",
    "DDL · 查看与取消",
    "DDL · 私聊自动识别",
    "DDL · 通用规则",
    "聊天总结",
    "用量与费用（Super）",
    "广播消息",
    "身份组管理（Super）",
    "群发送与只读管理",
)


def _section(spec):
    if spec.name == "/ddl":
        if spec.subcommand in {"add", "add-strict"}:
            return "DDL · 创建"
        if spec.subcommand == "defaulttime":
            return "DDL · 私聊自动识别"
        return "DDL · 查看与取消"
    if spec.name == "/summary":
        return "聊天总结"
    if spec.name == "/cost":
        return "用量与费用（Super）"
    if spec.name in {"/announce", "/announce-reject"}:
        return "广播消息"
    if spec.name == "/role" and spec.subcommand:
        return "身份组管理（Super）"
    if spec.name in {"/send", "/readonly"}:
        return "群发送与只读管理"
    return "基础与身份查询"


def _command_lines(spec, ctx, roles):
    usage, description = spec.usage, spec.description
    if spec.name == "/help":
        description = "查看可用命令，支持按命令查询"
    elif spec.name == "/role":
        if not spec.subcommand:
            description = (
                "查看本人全局及本群身份组"
                if ctx.group
                else "查看本人全局及全部群身份组"
            )
        elif spec.subcommand == "reset":
            usage = "/role reset" + ("" if ctx.group else " 群号")
            description = "清空目标群全部直接身份组，保留全局权限和全员模式"
        elif spec.subcommand == "group-admin":
            usage = "/role group-admin on|off" + ("" if ctx.group else " 群号")
            description = "on：全员获得 group.admin；off：恢复名单校验"
    elif spec.name == "/ddl":
        if spec.subcommand == "add":
            description = "交给 AI 提取一条 DDL，正文最多200字"
        elif spec.subcommand == "add-strict":
            usage = '/ddl add-strict "名称" [YYYY-MM-DD HH:mm] [-30min,-3h]'
            if ctx.group:
                usage += "[;@成员,@成员]"
        elif spec.subcommand == "list":
            description = "分页列出当前会话的有效 DDL 详情，每页20项"
        elif spec.subcommand == "show":
            description = "查看本群 DDL 详情" if ctx.group else "查看个人 DDL 详情"
        elif spec.subcommand == "clear":
            usage = "/ddl clear [this|群号|all]"
            description = (
                "默认清空本群；指定其他群或 all 需全局 admin，all 仅清除群 DDL"
                if ctx.group
                else "默认清空个人 DDL；指定群或 all 需全局 admin，all 仅清除群 DDL"
            )
    elif spec.name == "/summary":
        if ctx.group:
            usage = "/summary [群号]" if "admin" in roles else "/summary"
            description = "总结本群最近可读取的消息"
            if "admin" in roles:
                description += "；可指定其他群"
        else:
            return [
                "/summary（附带或引用聊天记录）：总结提供的记录",
                "/summary text 内容：总结一段文字",
                "/summary group 群号：总结目标群；非全局 admin 仅限本人所在群",
            ]
    return [f"{usage}：{description}"]


def render_help(ctx, specs, roles, *, autoanalysis_enabled=False):
    if not specs:
        raise BusinessError("没有可用的对应命令。")
    grouped = {title: [] for title in SECTIONS}
    for spec in specs:
        grouped[_section(spec)].extend(_command_lines(spec, ctx, roles))
    if any(spec.name == "/ddl" for spec in specs):
        grouped["DDL · 通用规则"] = [
            "时间均为北京时间；任务一次性，每项最多20次通知（含到期），过去的提醒时间会忽略。",
            "各群与私聊任务独立；创建者可取消整条 DDL，被通知者可取消对自己的提醒。",
            "新增、修改或取消通知成功后，会自动发送当前会话的 DDL 卡片。",
        ]

    lines = [
        f"KakoBot 帮助（{'群聊' if ctx.group else '私聊'}）",
        "仅显示当前会话中你有权限使用的命令；/role 查看本人身份组。",
    ]
    if ctx.group:
        lines.append("群内命令须先真实 @ 机器人。")
    lines.append(
        "分类查询：/help ddl、/help role、/help summary；具体用法：/help ddl add-strict。"
    )
    for title, commands in grouped.items():
        if not commands:
            continue
        lines.extend(["", f"【{title}】", *commands])
        if title == "DDL · 创建":
            if ctx.group:
                lines.append(
                    "通知谁：add 可在正文真实 @ 成员，由 AI 判断；"
                    "add-strict 在末尾写 ;@成员,@成员，不写则通知设置者。"
                )
            lines.append(
                "未指定提前提醒时，默认提前30min、3h、12h、1d、1d12h。"
                "AI 默认到期再通知一次，明确要求不要时取消；严格模式不自动追加到期通知。"
            )
        elif title == "DDL · 私聊自动识别":
            lines.append(
                "直接私聊发送文字或合并聊天记录可自动提取 DDL，忽略过期项并跳过重复项。"
                if autoanalysis_enabled
                else "直接发送消息进行自动识别，需要 autoanalysis 身份组且该功能已启用。"
            )
            if autoanalysis_enabled:
                lines.append(
                    "修改已有个人 DDL 时，请明确编号和要求，例如：把 DDL #3 的标题改为提交物理作业。"
                )
            lines.append(
                "默认提示词仅影响之后自动识别的新任务，不影响 /ddl add 或已有任务。"
            )
        elif title == "身份组管理（Super）":
            lines.append("全局身份组：super、admin、autoanalysis、ddl、summary。")
            lines.append(
                "群身份组：group.admin、group.ddl、group.summary；群内仅可编辑本群。"
                if ctx.group
                else "群身份组写作：群号.admin、群号.ddl、群号.summary，例如 3333.ddl。"
            )
            lines.append("remove/clear 只移除直接授权；由其他身份组继承的权限仍保留。")
        elif title == "用量与费用（Super）":
            lines.append(
                "不带参数查看全部；user 按发起请求的 QQ 筛选，group 按群筛选。"
                "费用按请求当时配置的人民币/百万 tokens 单价保存，重启后保留。"
            )

    return "\n".join(lines)
