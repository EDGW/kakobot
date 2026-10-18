"""Unified /role operations with context-limited membership enumeration."""


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
        ctx = action.context
        groups = None
        if not ctx.group:
            groups = sorted(self.roles.groups(), key=int)
            for group in groups:
                if not self.roles.data["group_admin_enabled"].get(group, True):
                    names.seed_members(group, await names.gateway.members(group))
        return await self._description(ctx.actor, ctx, names, groups)
