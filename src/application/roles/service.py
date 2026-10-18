"""Unified /role operations with context-limited membership enumeration."""

import asyncio

from ...presentation.roles import render_role_cards


class RoleService:
    def __init__(self, roles):
        self.roles = roles

    async def _snapshot(self, user, ctx, names, groups=None):
        title = await names.user(user, ctx.group)
        visible = []
        for group in [ctx.group] if ctx.group else (groups or []):
            member = user in names.members.get(group, {})
            if ctx.group and user == ctx.actor:
                member = True
            sources = self.roles.sources(
                user, group, member=member, platform=ctx.platform, bot=ctx.bot
            )
            if sources or ctx.group:
                visible.append((group, await names.group(group), sources))
        return title, self.roles.sources(user), visible

    async def _description(self, user, ctx, names, groups=None):
        title, global_sources, visible = await self._snapshot(user, ctx, names, groups)
        lines = [title, "全局：" + self._format(global_sources)]
        for group, label, source in visible:
            suffix = (
                ""
                if ctx.group
                else "（私聊编码："
                + ", ".join(group + role[5:] for role in sorted(source))
                + "）"
            )
            lines.append(f"群 {label}：{self._format(source)}{suffix}")
        if not ctx.group and not visible:
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
            groups = sorted(
                self.roles.groups(platform=ctx.platform, bot=ctx.bot), key=int
            )
            for group in groups:
                names.seed_members(group, await names.gateway.members(group))
        title, global_sources, visible = await self._snapshot(
            ctx.actor, ctx, names, groups
        )
        # Inspect all labels before rasterization, since pixels bypass text filters.
        payload = [title, global_sources, visible]
        names.guard.secrets.check(payload)
        images = await asyncio.to_thread(
            render_role_cards,
            title,
            global_sources,
            visible,
            private=not bool(ctx.group),
        )
        for image in images:
            names.guard.secrets.check(payload)
            await names.gateway.send_image(
                image, group=ctx.group, user="" if ctx.group else ctx.actor
            )
        return None
