"""Direct role assignments; effective membership is derived, never persisted."""

from pathlib import Path

from ....domain.context import qq_id
from ....domain.roles import (
    GLOBAL_ROLES,
    GROUP_ROLES,
    expand_global,
    expand_group,
)
from ..json_store import atomic_json, read_json


def empty_roles() -> dict:
    return {
        "version": 2,
        "global_roles": {role: [] for role in sorted(GLOBAL_ROLES - {"super"})},
        "group_roles": {},
        "group_admin_enabled": {},
    }


def validate_roles(data: dict) -> None:
    if (
        not isinstance(data, dict)
        or set(data) != set(empty_roles())
        or type(data["version"]) is not int
        or data["version"] != 2
    ):
        raise ValueError("roles.json 格式或结构版本错误。")
    globals_ = data["global_roles"]
    groups, switches = data["group_roles"], data["group_admin_enabled"]
    if (
        not isinstance(globals_, dict)
        or set(globals_) != GLOBAL_ROLES - {"super"}
        or not isinstance(groups, dict)
        or not isinstance(switches, dict)
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
            or set(roles) != GROUP_ROLES
        ):
            raise ValueError("群身份组结构无效。")
        for values in roles.values():
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
        validate_roles(self.data)

    def direct(self, user: str, group: str = "") -> set[str]:
        if group:
            return {
                role
                for role, users in self.data["group_roles"].get(group, {}).items()
                if user in users
            }
        result = {
            role for role, users in self.data["global_roles"].items() if user in users
        }
        if user == self.super_user and user != "000000000":
            result.add("super")
        return result

    def effective(self, user: str, group: str = "", member: bool = False) -> set[str]:
        direct = self.direct(user, group)
        if group:
            if member and not self.data["group_admin_enabled"].get(group, True):
                direct.add("group.admin")
            return expand_group(direct)
        return expand_global(direct)

    def sources(
        self, user: str, group: str = "", member: bool = False
    ) -> dict[str, list[str]]:
        sources = {}
        expand = expand_group if group else expand_global
        for direct in sorted(self.direct(user, group)):
            for role in expand({direct}):
                sources.setdefault(role, []).append(
                    "直接授权" if role == direct else f"继承自 {direct}"
                )
        if group and member and not self.data["group_admin_enabled"].get(group, True):
            for role in GROUP_ROLES:
                sources.setdefault(role, []).append("全员 group.admin 模式")
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
        if self.super_user != "000000000":
            users.add(self.super_user)
        return users

    def groups(self) -> set[str]:
        return set(self.data["group_roles"]) | set(self.data["group_admin_enabled"])

    def replace(self, data):
        """One atomic replacement for a fully validated management batch."""
        validate_roles(data)
        atomic_json(self.path, data)
        self.data = data
