"""Single command catalog consumed by dispatch, authorization and help."""

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
        "/help",
        "",
        ALL_ANY,
        "CURRENT",
        "help",
        "/help [命令]",
        "显示可用命令及资源限制",
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
        "/role",
        "list",
        ALL_SUPER,
        "ROLE_SCOPE",
        "roles",
        "/role list [ROLE]",
        "列出范围内身份组成员及继承来源",
    ),
    CommandSpec(
        "/role",
        "add",
        ALL_SUPER,
        "ROLE_SCOPE",
        "roles",
        "/role add QQ ROLE",
        "添加直接身份组",
    ),
    CommandSpec(
        "/role",
        "remove",
        ALL_SUPER,
        "ROLE_SCOPE",
        "roles",
        "/role remove QQ ROLE",
        "移除直接身份组，继承权限保留",
    ),
    CommandSpec(
        "/role",
        "clear",
        ALL_SUPER,
        "ROLE_SCOPE",
        "roles",
        "/role clear QQ [ROLE]",
        "清除指定用户范围内的直接身份组",
    ),
    CommandSpec(
        "/role",
        "reset",
        ALL_SUPER,
        "ROLE_GROUP",
        "roles",
        "/role reset [GROUP]",
        "清空本群全部直接身份组；私聊须指定群号，不改全局组和全员模式",
    ),
    CommandSpec(
        "/role",
        "group-admin",
        ALL_SUPER,
        "ROLE_GROUP",
        "roles",
        "/role group-admin on|off [GROUP]",
        "on启用全员group.admin，off恢复名单校验；私聊须指定群号",
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
        "/readonly",
        "add",
        {"CHAT": SUPER},
        "CURRENT",
        "readonly",
        "/readonly add GROUP",
        "设置群只读，停止群发送",
    ),
    CommandSpec(
        "/readonly",
        "remove",
        {"CHAT": SUPER},
        "CURRENT",
        "readonly",
        "/readonly remove GROUP",
        "解除群只读，不补发旧提醒",
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
        "/announce",
        "",
        ALL_SUPER,
        "CURRENT",
        "announce",
        "/announce [text 广播内容]",
        "向有私聊记录、有 autoanalysis 权限且未拒收的用户广播；默认发送本版本使用提示",
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
        "/cost",
        "",
        ALL_SUPER,
        "CURRENT",
        "cost",
        "/cost [user QQ号|group 群号]",
        "按账号和群查询近1/3/7/30天及累计 tokens、人民币费用，仅统计当前机器人",
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
SUBCOMMANDS = {"/role", "/readonly", "/ddl"}


def resolve(name, arguments):
    sub = ""
    if name in SUBCOMMANDS:
        parts = arguments.split(maxsplit=1)
        sub = parts[0].lower() if parts else ""
        arguments = parts[1] if len(parts) > 1 else ""
    return next(
        (spec for spec in CATALOG if spec.name == name and spec.subcommand == sub), None
    ), arguments
