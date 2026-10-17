"""Unified /role operations with context-limited membership enumeration."""

from ..domain.errors import BusinessError


class RoleService:
    def __init__(self, roles):
        self.roles = roles

    async def _description(self, user, ctx, names, groups=None):
        title = await names.user(user, ctx.group)
        lines = [title, "全局：" + self._format(self.roles.sources(user))]
        for group in [ctx.group] if ctx.group else (groups or []):
            member = user in names.members.get(group, {})
            if ctx.group and user == ctx.actor:
                member = True
            source = self.roles.sources(user, group, member=member)
            if source or ctx.group:
                label = await names.group(group)
                suffix = (
                    ""
                    if ctx.group
                    else "（私聊编码："
                    + ", ".join(group + role[5:] for role in sorted(source))
                    + "）"
                )
                lines.append(f"群 {label}：{self._format(source)}{suffix}")
        if not ctx.group and len(lines) == 2:
            lines.append("群内身份组：无")
        return "\n".join(lines)

    @staticmethod
    def _format(sources):
        return (
            "；".join(
                f"{role}（{', '.join(origins)}）"
                for role, origins in sorted(sources.items())
            )
            or "无"
        )

    async def handle(self, action, names):
        ctx, resources = action.context, action.resources
        sub = action.spec.subcommand
        if not sub:
            groups = None
            if not ctx.group:
                groups = sorted(self.roles.groups(), key=int)
                for group in groups:
                    if not self.roles.data["group_admin_enabled"].get(group, True):
                        # All-member roles require actual membership, not a
                        # claim in user text or an unrelated direct assignment.
                        names.seed_members(group, await names.gateway.members(group))
            return await self._description(ctx.actor, ctx, names, groups)
        if sub == "reset":
            group = resources["group"]
            users, grants = self.roles.reset_group(group)
            everyone_admin = not self.roles.data["group_admin_enabled"].get(group, True)
            label = await names.group(group)
            return (
                f"已清空群 {label} 的全部直接群身份组：{users}人，{grants}项授权。"
                "\n包含 group.admin、group.ddl、group.summary；全局身份组及其他群不受影响。"
                + (
                    "\n全员 group.admin 模式仍为 on；如需恢复名单校验，请使用 /role group-admin off"
                    + ("" if ctx.group else " " + group)
                    + "。"
                    if everyone_admin
                    else ""
                )
            )
        if sub == "group-admin":
            group, enabled = resources["group"], resources["everyone_admin"]
            self.roles.set_group_admin_override(group, enabled)
            label = await names.group(group)
            return (
                f"群 {label} 的全员 group.admin 模式：{'on' if enabled else 'off'}。\n"
                + (
                    "所有本群成员有效拥有 group.admin，并继承 group.ddl、group.summary。"
                    if enabled
                    else "已恢复按直接群身份组及继承关系校验权限。"
                )
                + "\n直接名单保留；Readonly 仍生效。"
            )
        if sub == "list":
            ref = resources["role"]
            if ctx.group:
                names.seed_members(ctx.group, await names.gateway.members(ctx.group))
                users = set(names.members[ctx.group])
                groups = [ctx.group]
            else:
                groups = (
                    [ref.group]
                    if ref and ref.group
                    else sorted(self.roles.groups(), key=int)
                    if not ref
                    else []
                )
                users = self.roles.known_users()
                for group in groups:
                    if not self.roles.data["group_admin_enabled"].get(group, True):
                        names.seed_members(group, await names.gateway.members(group))
                        users.update(names.members[group])
            lines = []
            for user in sorted(users, key=int):
                global_roles = self.roles.effective(user)
                group_roles = {
                    group: self.roles.effective(
                        user, group, user in names.members.get(group, {})
                    )
                    for group in groups
                }
                matches = (
                    ref.name
                    in (
                        global_roles
                        if not ref.group
                        else group_roles.get(ref.group, set())
                    )
                    if ref
                    else bool(global_roles or any(group_roles.values()))
                )
                if matches:
                    lines.append(await self._description(user, ctx, names, groups))
            return "身份组成员：\n" + ("\n\n".join(lines) or "（空）")
        user, ref = resources["user"], resources["role"]
        if sub != "clear" and ref is None:
            raise BusinessError("用法：" + action.spec.usage)
        removed = self.roles.edit(sub, user, ref, ctx.group)
        groups = sorted(self.roles.groups(), key=int) if not ctx.group else None
        for group in [ctx.group] if ctx.group else groups:
            if (
                not self.roles.data["group_admin_enabled"].get(group, True)
                and group not in names.members
            ):
                # Display queries fall back; the persisted mutation already succeeded.
                await names.user(user, group)
        detail = await self._description(user, ctx, names, groups)
        change = (
            "已添加直接授权。"
            if sub == "add"
            else "已移除直接授权：" + ", ".join(removed)
            if removed
            else "无直接授权可移除。"
        )
        return change + "\n当前有效权限及来源：\n" + detail
