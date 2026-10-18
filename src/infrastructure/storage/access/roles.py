"""Direct role assignments; effective membership is derived, never persisted."""

import copy
import json
from pathlib import Path

from ....domain.context import qq_id
from ....domain.roles import (
    DISCUSS_ROLES,
    GLOBAL_ROLES,
    LEGACY_GROUP_ROLES,
    expand_global,
    expand_group,
)
from ..json_store import atomic_json, read_json


def empty_roles() -> dict:
    return {
        "version": 4,
        "discuss_roles": {},
        "global_roles": {role: [] for role in sorted(GLOBAL_ROLES - {"super"})},
        "group_roles": {},
        "group_ddl_everyone": {},
    }


def validate_roles(data: dict) -> None:
    if (
        not isinstance(data, dict)
        or set(data) != set(empty_roles())
        or type(data["version"]) is not int
        or data["version"] != 4
    ):
        raise ValueError("roles.json 格式或结构版本错误。")
    globals_ = data["global_roles"]
    groups, switches = data["group_roles"], data["group_ddl_everyone"]
    if (
        not isinstance(globals_, dict)
        or set(globals_) != GLOBAL_ROLES - {"super"}
        or not isinstance(groups, dict)
        or not isinstance(switches, dict)
        or not isinstance(data["discuss_roles"], dict)
    ):
        raise ValueError("身份组数据结构无效。")

    def users(values):
        if (
            not isinstance(values, list)
            or any(not isinstance(user, str) or qq_id(user) != user for user in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError("身份组名单必须为不重复的规范 QQ 号列表。")

    for values in globals_.values():
        users(values)
    for group, roles in groups.items():
        if (
            qq_id(group) != group
            or not isinstance(roles, dict)
            or set(roles) != LEGACY_GROUP_ROLES
        ):
            raise ValueError("群身份组结构无效。")
        for values in roles.values():
            users(values)
    for scope, entries in data["discuss_roles"].items():
        parts = json.loads(scope)
        if (
            not isinstance(parts, list)
            or len(parts) != 3
            or any(not isinstance(v, str) or not v for v in parts)
            or qq_id(parts[1]) != parts[1]
            or qq_id(parts[2]) != parts[2]
            or not isinstance(entries, dict)
            or scope != RoleStore.scope(parts[2], parts[0], parts[1])
            or set(entries) != DISCUSS_ROLES
        ):
            raise ValueError("discuss 身份范围无效。")
        for values in entries.values():
            users(values)
    for group, enabled in switches.items():
        if qq_id(group) != group or type(enabled) is not bool:
            raise ValueError("群权限开关结构无效。")


class RoleStore:
    def __init__(self, path: Path, super_user: str):
        self.path, self.super_user = path, str(super_user).strip()
        if self.super_user != "000000000":
            self.super_user = qq_id(self.super_user)
        self.data = read_json(path)
        if self.data.get("version") in (2, 3):
            previous = copy.deepcopy(self.data)
            if self.data["version"] == 2:
                self.data["discuss_roles"] = {}
            switches = self.data.pop("group_admin_enabled")
            if not isinstance(switches, dict) or any(
                type(enabled) is not bool for enabled in switches.values()
            ):
                raise ValueError("旧群权限开关结构无效。")
            self.data["group_ddl_everyone"] = {
                group: not enabled for group, enabled in switches.items()
            }
            self.data["version"] = 4
            validate_roles(self.data)
            backup = path.with_name("roles-before-everyone-ddl.json")
            if not backup.exists():
                atomic_json(backup, previous)
            atomic_json(path, self.data)
        validate_roles(self.data)
        self.discuss_policy = None

    @staticmethod
    def scope(group, platform, bot):
        return json.dumps([platform, bot, group], separators=(",", ":"))

    @classmethod
    def entries(cls, data, group, role, platform, bot):
        if role in DISCUSS_ROLES:
            return data["discuss_roles"].setdefault(
                cls.scope(group, platform, bot), {r: [] for r in DISCUSS_ROLES}
            )
        return data["group_roles"].setdefault(
            group, {r: [] for r in LEGACY_GROUP_ROLES}
        )

    def discuss_list(self, scope, role):
        return list(
            self.data["discuss_roles"].get(scope, {}).get("group.discuss." + role, [])
        )

    def change_discuss(self, scope, role, actor, add):
        data = copy.deepcopy(self.data)
        group = json.loads(scope)[2]
        entries = self.entries(
            data, group, "group.discuss." + role, *json.loads(scope)[:2]
        )
        users = set(entries["group.discuss." + role])
        users.add(actor) if add else users.discard(actor)
        entries["group.discuss." + role] = sorted(users, key=int)
        self.replace(data)

    def direct(self, user: str, group: str = "", *, platform="", bot="") -> set[str]:
        if group:
            result = {
                role
                for role, users in self.data["group_roles"].get(group, {}).items()
                if user in users
            }
            result.update(
                role
                for role, users in self.data["discuss_roles"]
                .get(self.scope(group, platform, bot), {})
                .items()
                if user in users
            )
            return result
        result = {
            role for role, users in self.data["global_roles"].items() if user in users
        }
        if user == self.super_user and user != "000000000":
            result.add("super")
        return result

    def effective(
        self, user: str, group: str = "", member: bool = False, *, platform="", bot=""
    ) -> set[str]:
        direct = self.direct(user, group, platform=platform, bot=bot)
        if group:
            return set(self.sources(user, group, member, platform=platform, bot=bot))
        return expand_global(direct)

    def sources(
        self, user: str, group: str = "", member: bool = False, *, platform="", bot=""
    ) -> dict[str, list[str]]:
        sources = {}
        expand = expand_group if group else expand_global
        for direct in sorted(self.direct(user, group, platform=platform, bot=bot)):
            for role in expand({direct}):
                sources.setdefault(role, []).append(
                    "直接授权" if role == direct else f"继承自 {direct}"
                )
        if group and member and self.data["group_ddl_everyone"].get(group, False):
            for role in expand_group({"group.ddl"}):
                sources.setdefault(role, []).append("全员 group.ddl 模式")
        if group and platform and bot:
            if "super" in self.effective(user):
                for role in DISCUSS_ROLES:
                    sources.setdefault(role, []).append("继承自全局 super")
            if self.discuss_policy:
                scope = self.scope(group, platform, bot)
                mode, blacklisted = self.discuss_policy(scope, user)
                user_role = "group.discuss.user"
                if (
                    "group.discuss.admin" not in sources
                    and "super" not in self.effective(user)
                ):
                    sources.pop(user_role, None)
                    if member:
                        if mode == "all" or (mode == "blacklist" and not blacklisted):
                            sources.setdefault(user_role, []).append(
                                "全员 discuss 模式"
                                if mode == "all"
                                else "discuss 黑名单模式（未列入）"
                            )
                        elif mode == "whitelist" and user_role in self.direct(
                            user, group, platform=platform, bot=bot
                        ):
                            sources.setdefault(user_role, []).append("直接授权")
        return sources

    def known_users(self) -> set[str]:
        users = {
            user for values in self.data["global_roles"].values() for user in values
        }
        users.update(
            user
            for roles in self.data["group_roles"].values()
            for values in roles.values()
            for user in values
        )
        users.update(
            user
            for entries in self.data["discuss_roles"].values()
            for values in entries.values()
            for user in values
        )
        if self.super_user != "000000000":
            users.add(self.super_user)
        return users

    def groups(self, *, platform="", bot="") -> set[str]:
        result = set(self.data["group_roles"]) | set(self.data["group_ddl_everyone"])
        for scope in self.data["discuss_roles"]:
            p, b, g = json.loads(scope)
            if (p, b) == (platform, bot):
                result.add(g)
        return result

    def replace(self, data):
        """One atomic replacement for a fully validated management batch."""
        validate_roles(data)
        atomic_json(self.path, data)
        self.data = data
