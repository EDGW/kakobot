"""Role inheritance and location-dependent external role codes."""

from dataclasses import dataclass

from .context import qq_id
from .errors import BusinessError

GLOBAL_ROLES = frozenset({"super", "admin", "autoanalysis", "ddl", "summary"})
GROUP_ROLES = frozenset({"group.admin", "group.ddl", "group.summary"})


def expand_global(direct: set[str]) -> set[str]:
    result = set(direct)
    if "super" in result:
        result.add("admin")
    if "admin" in result:
        result.update(GLOBAL_ROLES - {"super"})
    if "autoanalysis" in result:
        result.update(GLOBAL_ROLES - {"super", "admin"})
    return result


def expand_group(direct: set[str]) -> set[str]:
    return direct | (
        {"group.ddl", "group.summary"} if "group.admin" in direct else set()
    )


@dataclass(frozen=True)
class RoleRef:
    name: str
    group: str = ""

    def display(self, location: str) -> str:
        if not self.group:
            return self.name
        return self.name if location == "GROUP" else self.group + self.name[5:]


def parse_role(code: str, current_group: str = "") -> RoleRef:
    code = code.lower()
    if code in GLOBAL_ROLES:
        return RoleRef(code)
    if current_group:
        if code in GROUP_ROLES:
            return RoleRef(code, current_group)
        raise BusinessError(
            "群内只能使用全局组或本群 group.admin/group.ddl/group.summary，不能访问其他群。"
        )
    prefix, sep, suffix = code.partition(".")
    if (
        sep
        and prefix.isascii()
        and prefix.isdigit()
        and "group." + suffix in GROUP_ROLES
    ):
        return RoleRef("group." + suffix, qq_id(prefix))
    raise BusinessError(
        "私聊群身份组请使用 群号.admin、群号.ddl 或 群号.summary；未知身份组不接受。"
    )
