"""Resolve current QQ names for display, keeping numeric identities authoritative."""

from ..domain.context import qq_id
from ..domain.text import display_name


def _name(value) -> str:
    return display_name(value)


class NameDirectory:
    """Reuse verified QQ identities and bounded name labels within one command."""

    def __init__(self, gateway, guard):
        self.gateway = gateway
        self.guard = guard
        self.groups = {}
        self.members = {}
        self.users = {}
        self.failed_members = set()

    def seed_members(self, group: str, members: list[dict]):
        self.members[group] = {str(member.get("user_id")): member for member in members}
        self.failed_members.discard(group)

    async def load_members(self, group: str) -> bool:
        """Best-effort display lookup; never use this to authorize an action."""
        if group in self.members:
            return group not in self.failed_members
        try:
            self.seed_members(group, await self.gateway.members(group))
            return True
        except Exception as exc:
            self.members[group] = {}
            self.failed_members.add(group)
            await self._report("展示查询；群成员列表 " + group, exc)
            return False

    async def _report(self, stage, error):
        await self.guard.report_error(
            self.gateway.bot, self.gateway.self_id, stage, error
        )

    async def _info(self, action: str, **params) -> dict:
        try:
            result = await self.gateway.bot.call_action(
                action, **params, self_id=self.gateway.self_id
            )
            if not isinstance(result, dict):
                raise RuntimeError("名称查询接口未返回有效对象。")
            return result
        except Exception as exc:
            await self._report(f"名称查询；{action}", exc)
            return {}

    async def group(self, group: str) -> str:
        group = qq_id(group)
        if group not in self.groups:
            info = await self._info("get_group_info", group_id=int(group))
            self.groups[group] = _name(info.get("group_name"))
        name = self.groups[group]
        return f"{name}（{group}）" if name else group

    async def profile(self, user: str, group: str = "") -> dict:
        if user == "000000000":
            return {
                "qq_id": user,
                "display_name": user,
                "nickname": "",
                "group_card": "",
            }
        user = qq_id(user)
        member = {}
        if group:
            group = qq_id(group)
            if group not in self.members:
                await self.load_members(group)
            member = self.members[group].get(user, {})
        card = _name(member.get("card"))
        nickname = _name(member.get("nickname"))
        if not nickname:
            if user not in self.users:
                info = await self._info("get_stranger_info", user_id=int(user))
                self.users[user] = _name(info.get("nickname"))
            nickname = self.users[user]
        return {
            "qq_id": user,
            "display_name": card or nickname or user,
            "nickname": nickname,
            "group_card": card,
        }

    async def user(self, user: str, group: str = "") -> str:
        profile = await self.profile(user, group)
        names = list(
            dict.fromkeys(
                name for name in (profile["group_card"], profile["nickname"]) if name
            )
        )
        return (
            f"{' / '.join(names)}（{profile['qq_id']}）" if names else profile["qq_id"]
        )

    async def user_list(self, users, group: str = "", separator=", ") -> str:
        return (
            separator.join([await self.user(user, group) for user in users]) or "（空）"
        )
