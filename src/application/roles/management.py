"""Batch role administration with explicit scopes and direct-grant semantics."""

import asyncio
import copy

from ...domain.context import qq_id
from ...domain.errors import BusinessError
from ...domain.management import arguments, csv, page_number
from ...domain.roles import GROUP_ROLES, parse_role
from ...infrastructure.messaging.onebot import ReadonlyViolation
from ...infrastructure.storage.access.roles import validate_roles
from .service import RoleService


class SuperRoleService:
    def __init__(self, roles, audit, readonly):
        self.roles, self.audit = roles, audit
        self.readonly = readonly
        self.lock = asyncio.Lock()
        self.descriptions = RoleService(roles)

    def _group(self, value, ctx):
        group = ctx.group if value == "this" and ctx.group else qq_id(value)
        if ctx.group and group != ctx.group:
            raise BusinessError("群内只能管理本群身份组，其他群请在私聊操作。")
        return group

    def _scope(self, value, ctx):
        if value == "global":
            return [""]
        if value == "legacy":
            return [""] + ([ctx.group] if ctx.group else sorted(self.roles.groups()))
        if value == "all" and not ctx.group:
            return [""] + sorted(self.roles.groups())
        if value == "group" and ctx.group:
            return [ctx.group]
        if value.startswith("group:"):
            return [self._group(value[6:], ctx)]
        raise BusinessError(
            "必须指定 --scope global、group:群号；私聊 clear 还可用 all。"
        )

    async def _seed(self, ctx, names, groups):
        for group in groups:
            if ctx.group or not self.roles.data["group_admin_enabled"].get(group, True):
                names.seed_members(group, await names.gateway.members(group))

    async def handle(self, action, names):
        async with self.lock:
            return await self._handle(action, names)

    async def _handle(self, action, names):
        ctx = action.context
        sub = action.spec.subcommand.split()[-1]
        allowed = {
            "show": ("page",),
            "list": ("group", "source", "page"),
            "add": (),
            "remove": (),
            "set": ("scope",),
            "clear": ("scope",),
            "reset": ("roles",),
            "group-admin": (),
        }[sub]
        values, opts = arguments(
            action.arguments,
            options=allowed,
            flags=() if sub in {"show", "list"} else ("dry-run",),
        )
        if sub in {"show", "list"}:
            return await self.query(sub, values, opts, ctx, names)
        data = copy.deepcopy(self.roles.data)
        touched = set()
        if sub in {"reset", "group-admin"}:
            minimum, maximum = (1, 2) if sub == "group-admin" else (0, 1)
            if not minimum <= len(values) <= maximum:
                raise BusinessError("用法：" + action.spec.usage)
            if sub == "group-admin" and values[0].lower() not in {"on", "off"}:
                raise BusinessError("开关须为 on 或 off。")
            raw_groups = values[-1] if len(values) == maximum else "this"
            if not ctx.group and raw_groups == "this":
                raise BusinessError("私聊必须明确提供目标群号。")
            groups = csv(raw_groups, lambda value: self._group(value, ctx))
            selected = csv(opts["roles"]) if "roles" in opts else sorted(GROUP_ROLES)
            if not set(selected) <= GROUP_ROLES:
                raise BusinessError(
                    "--roles 仅接受 group.admin、group.ddl、group.summary。"
                )
            for group in groups:
                if sub == "group-admin":
                    data["group_admin_enabled"][group] = values[0].lower() != "on"
                else:
                    for role in selected:
                        entries = data["group_roles"].get(group, {})
                        touched.update(entries.get(role, []))
                        if role in entries:
                            entries[role] = []
            labels = [await names.group(group) for group in groups]
            prefix = (
                "全员 group.admin 模式"
                if sub == "group-admin"
                else "清空群直接授权名单"
            )
            description = prefix + "：" + "、".join(labels)
            if sub == "group-admin":
                description += "；" + values[0].lower()
            else:
                description += "；身份组：" + ",".join(selected)
                if any(
                    not data["group_admin_enabled"].get(group, True) for group in groups
                ):
                    description += (
                        "\n全员 group.admin 模式仍为 on；reset 不改变此开关。"
                    )
        else:
            if len(values) != (1 if sub == "clear" else 2):
                raise BusinessError("用法：" + action.spec.usage)
            users = csv(values[0], qq_id)
            touched.update(users)
            refs = (
                csv(values[1], lambda value: parse_role(value, ctx.group))
                if sub != "clear"
                else []
            )
            if any(ref.name == "super" for ref in refs):
                raise BusinessError("Super 仅由 super_user 配置，不能通过命令编辑。")
            if sub in {"set", "clear"}:
                if "scope" not in opts:
                    raise BusinessError("set/clear 必须通过 --scope 明确修改范围。")
                scopes = self._scope(opts["scope"].lower(), ctx)
                if sub == "set" and (
                    len(scopes) != 1 or any(ref.group not in scopes for ref in refs)
                ):
                    raise BusinessError(
                        "set 的身份组必须全部属于 --scope 指定的单一范围。"
                    )
                for group in scopes:
                    entries = (
                        data["group_roles"].get(group, {})
                        if group
                        else data["global_roles"]
                    )
                    for role, members in entries.items():
                        entries[role] = [user for user in members if user not in users]
            for ref in refs:
                entries = (
                    data["group_roles"].setdefault(
                        ref.group, {role: [] for role in GROUP_ROLES}
                    )
                    if ref.group
                    else data["global_roles"]
                )
                members = set(entries[ref.name])
                if sub in {"add", "set"}:
                    members.update(users)
                else:
                    members.difference_update(users)
                entries[ref.name] = sorted(members, key=int)
            description = f"{sub}：{len(users)}人；" + (
                ",".join(ref.display(ctx.location) for ref in refs)
                if refs
                else "范围 " + opts["scope"]
            )
        validate_roles(data)
        before = self.roles.data
        changes = self._diff(before, data)
        self._require_super(ctx)
        if ctx.group in self.readonly.readonly_groups:
            raise ReadonlyViolation(ctx.group)
        if opts.get("dry-run"):
            return (
                "预览（未保存）：\n"
                + description
                + "\n"
                + ("\n".join(changes) or "无变更。")
            )
        if not changes:
            return (
                "无变更。\n"
                + description
                + "\n继承权限和全员模式不受直接授权增减影响。"
            )
        ticket = self.audit.prepare(ctx, "role " + sub, before, data)
        try:
            self.roles.replace(data)
        except Exception:
            self.audit.finish(ticket, "failed")
            raise
        self.audit.finish(ticket)
        result = "已保存：\n" + description + "\n" + "\n".join(changes)
        groups = [ctx.group] if ctx.group else sorted(self.roles.groups(), key=int)
        try:
            await self._seed(ctx, names, groups)
        except Exception as exc:
            await names.guard.report_error(
                names.gateway.bot, ctx.bot, "权限已保存；刷新成员列表失败", exc
            )
            return (
                result
                + "\n权限已保存，完整有效权限暂无法刷新，请稍后使用 /super role show。"
            )
        details = [
            await self.descriptions._description(user, ctx, names, groups)
            for user in sorted(touched, key=int)[:20]
        ]
        if details:
            result += "\n当前有效权限及来源：\n" + "\n\n".join(details)
        if len(touched) > 20:
            result += "\n其余人员请使用 /super role show 查询。"
        return result + "\n直接授权移除不会屏蔽继承权限；全员模式需单独关闭。"

    def _require_super(self, ctx):
        if "super" not in self.roles.effective(ctx.actor):
            raise BusinessError("Super 权限已变更。")

    @staticmethod
    def _diff(before, after):
        def flatten(data):
            result = {
                (user, role)
                for role, users in data["global_roles"].items()
                for user in users
            }
            result.update(
                (user, group + role[5:])
                for group, roles in data["group_roles"].items()
                for role, users in roles.items()
                for user in users
            )
            return result

        old, new = flatten(before), flatten(after)
        lines = [
            f"{'增加' if added else '移除'} {user}：{role}"
            for added, pairs in ((True, new - old), (False, old - new))
            for user, role in sorted(pairs)
        ]
        for group in sorted(
            set(before["group_admin_enabled"]) | set(after["group_admin_enabled"])
        ):
            old_switch = before["group_admin_enabled"].get(group, True)
            new_switch = after["group_admin_enabled"].get(group, True)
            if old_switch != new_switch:
                lines.append(
                    f"群 {group} 全员模式：{'off' if old_switch else 'on'} → {'off' if new_switch else 'on'}"
                )
        return lines

    async def query(self, sub, values, opts, ctx, names):
        if len(values) > 1 or (sub == "show" and not values):
            raise BusinessError(
                "用法：/super role show QQ[,QQ] 或 /super role list [ROLE]。"
            )
        ref = parse_role(values[0], ctx.group) if values and sub == "list" else None
        group = self._group(opts["group"], ctx) if "group" in opts else ctx.group
        if ref and ref.group and group and ref.group != group:
            raise BusinessError("身份组与 --group 范围不一致。")
        groups = (
            [group or ref.group]
            if group or (ref and ref.group)
            else []
            if ref
            else sorted(self.roles.groups(), key=int)
        )
        await self._seed(ctx, names, groups)
        users = (
            set(csv(values[0], qq_id)) if sub == "show" else self.roles.known_users()
        )
        if sub == "list":
            for candidate in groups:
                users.update(names.members.get(candidate, {}))
            if group:
                if group not in names.members:
                    names.seed_members(group, await names.gateway.members(group))
                users.intersection_update(names.members[group])
        source_filter = opts.get("source")
        if source_filter not in {None, "direct", "inherited", "everyone"}:
            raise BusinessError("--source 须为 direct、inherited 或 everyone。")
        matches = []
        for user in sorted(users, key=int):
            sources = dict(self.roles.sources(user))
            for candidate in groups:
                sources.update(
                    {
                        candidate + role[5:]: origins
                        for role, origins in self.roles.sources(
                            user, candidate, user in names.members.get(candidate, {})
                        ).items()
                    }
                )
            if ref:
                code = ref.group + ref.name[5:] if ref.group else ref.name
                sources = {code: sources[code]} if code in sources else {}
            origins = [origin for entries in sources.values() for origin in entries]
            matched = not source_filter or any(
                origin == "直接授权"
                if source_filter == "direct"
                else origin.startswith("继承自 ")
                if source_filter == "inherited"
                else origin == "全员 group.admin 模式"
                for origin in origins
            )
            if sub == "show" or sources and matched:
                matches.append(user)
        page = page_number(opts.get("page", "1"))
        pages = max(1, (len(matches) + 19) // 20)
        if page > pages:
            raise BusinessError(f"页码超出范围，共{pages}页。")
        details = [
            await self.descriptions._description(user, ctx, names, groups)
            for user in matches[(page - 1) * 20 : page * 20]
        ]
        return f"身份组（{len(matches)}人，第{page}/{pages}页）：\n" + (
            "\n\n".join(details) or "（空）"
        )
