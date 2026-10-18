"""Command dispatch and authorization catalog, including image-help entry points."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AnyOf:
    roles: tuple[str, ...]

    def permits(self, roles):
        return bool(set(self.roles) & roles)


@dataclass(frozen=True)
class AllOf:
    roles: tuple[str, ...]

    def permits(self, roles):
        return set(self.roles) <= roles


@dataclass(frozen=True)
class CommandSpec:
    name: str
    subcommand: str
    requirements: dict[str, AnyOf | AllOf]
    policy: str
    handler: str
    usage: str
    description: str
    input_policy: str = "TEXT"

    def allowed(self, location, roles):
        expression = self.requirements.get(location)
        return expression is not None and expression.permits(roles)


ANY = AllOf(())
SUPER = AnyOf(("super",))
ADMIN = AnyOf(("admin",))
ALL_ANY = {"CHAT": ANY, "GROUP": ANY}
ALL_SUPER = {"CHAT": SUPER, "GROUP": SUPER}
CREATE = {"CHAT": AnyOf(("ddl",)), "GROUP": AnyOf(("admin", "group.ddl"))}
CATALOG = (
    CommandSpec(
        "/changelog",
        "",
        ALL_ANY,
        "CURRENT",
        "changelog",
        "/changelog",
        "发送构建时生成的更新日志图片",
    ),
    CommandSpec(
        "/version",
        "",
        ALL_ANY,
        "CURRENT",
        "version",
        "/version",
        "显示当前安装版本",
    ),
    CommandSpec(
        "/help",
        "",
        ALL_ANY,
        "CURRENT",
        "help",
        "/help [功能组]",
        "发送当前会话的功能组帮助图片，默认 help 页面",
    ),
    CommandSpec(
        "/role",
        "",
        ALL_ANY,
        "ROLE_SCOPE",
        "roles",
        "/role",
        "查看本人全局组；私聊列全部群组，群内仅本群",
    ),
    CommandSpec(
        "/readonly",
        "list",
        {"CHAT": ADMIN},
        "CURRENT",
        "readonly",
        "/readonly list",
        "查看 Readonly 群",
    ),
    CommandSpec(
        "/ddl",
        "add",
        CREATE,
        "CURRENT",
        "deadlines",
        "/ddl add 内容",
        "AI 提取一个一次性任务，最多200字；私聊只通知本人",
        "TEXT_AND_AT",
    ),
    CommandSpec(
        "/ddl",
        "add-strict",
        CREATE,
        "CURRENT",
        "deadlines",
        '/ddl add-strict "NAME" [YYYY-MM-DD HH:mm] [-30min,-3h][;@成员]',
        "结构化创建，不调用 AI；默认五个提前节点",
        "TEXT_AND_AT",
    ),
    CommandSpec(
        "/ddl",
        "defaulttime",
        {"CHAT": AnyOf(("ddl",))},
        "CURRENT",
        "deadlines",
        '/ddl defaulttime ["提示词"]',
        "查看/设置个人自动识别默认提醒；空字符串恢复系统默认",
    ),
    CommandSpec(
        "/ddl",
        "list",
        ALL_ANY,
        "OWN_OR_MEMBER",
        "deadlines",
        "/ddl list [页码]",
        "详细列出本人私聊/本群的有效任务",
    ),
    CommandSpec(
        "/ddl",
        "view",
        ALL_ANY,
        "OWN_OR_MEMBER",
        "deadlines",
        "/ddl view",
        "按截止时间生成最近10个有效DDL的卡片图片，直接发送，不调用AI",
    ),
    CommandSpec(
        "/ddl",
        "show",
        ALL_ANY,
        "OWN_OR_MEMBER",
        "deadlines",
        "/ddl show ID",
        "查看本人私聊/本群的任务详情",
    ),
    CommandSpec(
        "/ddl",
        "remove",
        ALL_ANY,
        "OWN_OR_MEMBER",
        "deadlines",
        "/ddl remove ID",
        "设置者取消全部；被通知者仅退出自己",
    ),
    CommandSpec(
        "/ddl",
        "clear",
        {"CHAT": AnyOf(("ddl",)), "GROUP": AnyOf(("admin", "group.admin"))},
        "CLEAR_SCOPE",
        "deadlines",
        "/ddl clear [this|GROUP|all]",
        "清除个人/本群；跨群及all需全局admin，all仅清除群",
    ),
    CommandSpec(
        "/summary",
        "",
        {"CHAT": AnyOf(("summary",)), "GROUP": AnyOf(("admin", "group.summary"))},
        "SUMMARY_SCOPE",
        "summary",
        "/summary [text 内容|group GROUP|GROUP]",
        "私聊总结附带记录/文字/群；群内默认本群，跨群需admin",
        "MESSAGE_TREE",
    ),
    CommandSpec(
        "/announce-reject",
        "",
        ALL_ANY,
        "CURRENT",
        "announce_reject",
        "/announce-reject on|off",
        "on 拒收全部广播，off 恢复接收；不影响 DDL 提醒",
    ),
    CommandSpec(
        "/send",
        "",
        {"CHAT": ADMIN, "GROUP": ADMIN},
        "TARGET_GROUP",
        "send",
        "/send GROUP 内容",
        "向目标群发送纯文本，Readonly仍拦截",
    ),
    CommandSpec(
        "hello",
        "",
        {"GROUP": ANY},
        "CURRENT",
        "hello",
        "你好",
        "真实@机器人且没有其他正文时问候",
    ),
)
# Compatibility aliases are hidden from help for one transition version.
LEGACY = {
    ("/role", sub) for sub in ("list", "add", "remove", "clear", "reset", "group-admin")
}
LEGACY |= {
    ("/cost", ""),
    ("/announce", ""),
    ("/readonly", "add"),
    ("/readonly", "remove"),
}


def management_specs():
    entries = [
        ("", "super_help", "/super", "发送 Super 默认帮助图片"),
        (
            "help",
            "super_help",
            "/super help [help|role|ddl|schedule|request|cost|announce|readonly]",
            "发送当前会话的 Super 功能组帮助图片，默认 help 页面",
        ),
        (
            "schedule",
            "super_deadlines",
            "/super schedule [user QQ号|group 群号]",
            "查看当前机器人全部或指定会话的未来待发提醒",
        ),
        (
            "role show",
            "super_roles",
            "/super role show QQ[,QQ] [--page 页码]",
            "查询指定用户的直接及有效权限",
        ),
        (
            "role list",
            "super_roles",
            "/super role list [ROLE] [--group 群号] [--source direct|inherited|everyone] [--page 页码]",
            "按身份组、群和来源筛选成员",
        ),
        (
            "role add",
            "super_roles",
            "/super role add QQ[,QQ] ROLE[,ROLE] [--dry-run]",
            "批量添加直接授权",
        ),
        (
            "role remove",
            "super_roles",
            "/super role remove QQ[,QQ] ROLE[,ROLE] [--dry-run]",
            "批量移除直接授权，保留继承权限",
        ),
        (
            "role set",
            "super_roles",
            "/super role set QQ[,QQ] ROLE[,ROLE] --scope global|group:群号 [--dry-run]",
            "替换指定范围的直接授权",
        ),
        (
            "role clear",
            "super_roles",
            "/super role clear QQ[,QQ] --scope global|group:群号|all [--dry-run]",
            "批量清除指定范围直接授权",
        ),
        (
            "role reset",
            "super_roles",
            "/super role reset [群号[,群号]] [--roles group.ddl,group.summary] [--dry-run]",
            "清空群的全部或指定直接身份组名单",
        ),
        (
            "role group-admin",
            "super_roles",
            "/super role group-admin on|off [群号[,群号]] [--dry-run]",
            "开关全员 group.admin 模式，保留直接名单",
        ),
        (
            "ddl list",
            "super_deadlines",
            "/super ddl list [this|user:QQ|group:群号|all] [--creator QQ] [--target QQ] [--status active|expired|cancelled|all] [--from 时间] [--to 时间] [--page 页码]",
            "筛选各对象的 DDL，编号带会话标识",
        ),
        (
            "ddl show",
            "super_deadlines",
            "/super ddl show 对象#编号",
            "查看任务详情与历史通知状态",
        ),
        (
            "ddl view",
            "super_deadlines",
            "/super ddl view [this|user:QQ|group:群号]",
            "将目标会话的 DDL 图片回给 Super",
        ),
        (
            "ddl edit",
            "super_deadlines",
            '/super ddl edit 对象#编号[,对象#编号] [--title "名称"] [--due "YYYY-MM-DD HH:mm"] [--remind=-3h,-30min,0] [--targets QQ,QQ|--targets-add QQ,QQ|--targets-remove QQ,QQ] [--dry-run]',
            "批量修改有效任务，直接解析参数，不调用 AI",
        ),
        (
            "ddl remove",
            "super_deadlines",
            "/super ddl remove 对象#编号[,对象#编号] [--dry-run]",
            "批量取消整条任务并保留历史",
        ),
        (
            "ddl clear",
            "super_deadlines",
            "/super ddl clear this|user:QQ|group:群号 [--dry-run]",
            "清除明确会话内的全部有效任务",
        ),
        (
            "request list",
            "requests",
            "/super request list [pending|approved|denied|failed|uncertain|all] [--page 页码]",
            "列出当前机器人收到的好友申请、加群申请及邀请",
        ),
        (
            "request approve",
            "requests",
            "/super request approve 编号[,编号]|all",
            "同意指定待处理申请；all 仅处理 pending",
        ),
        (
            "request deny",
            "requests",
            "/super request deny 编号[,编号]|all",
            "拒绝指定待处理申请；all 仅处理 pending",
        ),
    ]
    for sub, handler, usage, description in entries:
        yield CommandSpec(
            "/super", sub, ALL_SUPER, "SUPER", handler, usage, description
        )
    for sub, handler, usage, description, requirements in (
        (
            "cost",
            "cost",
            "/super cost [user QQ号|group 群号]",
            "近1/3/7/30天及累计 tokens 和人民币费用",
            ALL_SUPER,
        ),
        (
            "announce",
            "announce",
            "/super announce [text 广播内容]",
            "向有私聊记录、autoanalysis 权限且未拒收的人广播",
            ALL_SUPER,
        ),
        (
            "readonly list",
            "readonly",
            "/super readonly list",
            "查看独立只读群名单",
            {"CHAT": SUPER},
        ),
        (
            "readonly add",
            "readonly",
            "/super readonly add 群号",
            "设为只读群，阻止发送",
            {"CHAT": SUPER},
        ),
        (
            "readonly remove",
            "readonly",
            "/super readonly remove 群号",
            "解除只读，不补发旧提醒",
            {"CHAT": SUPER},
        ),
    ):
        yield CommandSpec(
            "/super", sub, requirements, "CURRENT", handler, usage, description
        )


CATALOG += tuple(management_specs())


def resolve(name, arguments):
    if name == "/role" and arguments.strip():
        parts = arguments.split(maxsplit=1)
        if (name, parts[0].lower()) in LEGACY:
            sub, tail = parts[0].lower(), parts[1] if len(parts) > 1 else ""
            # Preserve the old clear QQ [ROLE] meaning for this transition version.
            if sub == "clear":
                values = tail.split()
                if len(values) == 2:
                    sub = "remove"
                elif len(values) == 1:
                    tail += " --scope legacy"
            return resolve("/super", "role " + sub + " " + tail)
    if name in {"/cost", "/announce"}:
        return resolve("/super", name[1:] + " " + arguments)
    if name == "/readonly":
        first = arguments.split(maxsplit=1)
        if first and (name, first[0].lower()) in LEGACY:
            return resolve("/super", "readonly " + arguments)
    candidates = []
    for spec in CATALOG:
        if spec.name != name:
            continue
        words = spec.subcommand.split()
        pieces = arguments.split(maxsplit=len(words)) if words else []
        if words and [part.lower() for part in pieces[: len(words)]] != words:
            continue
        if not words and name in {"/ddl", "/readonly", "/super"} and arguments.strip():
            continue
        tail = (
            pieces[len(words)]
            if words and len(pieces) > len(words)
            else ""
            if words
            else arguments
        )
        candidates.append((len(words), spec, tail))
    if not candidates:
        return None, arguments
    _, spec, tail = max(candidates, key=lambda item: item[0])
    return spec, tail
