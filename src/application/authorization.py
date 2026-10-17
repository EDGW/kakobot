"""One policy boundary for command roles and resource scopes."""

from dataclasses import dataclass

from ..domain.context import qq_id
from ..domain.errors import BusinessError
from ..domain.roles import parse_role


@dataclass(frozen=True)
class AuthorizedAction:
    spec: object
    context: object
    arguments: str
    resources: dict


class Authorizer:
    def __init__(self, roles):
        self.roles = roles

    def effective(self, ctx):
        return self.roles.effective(ctx.actor) | (
            self.roles.effective(ctx.actor, ctx.group, member=True)
            if ctx.group
            else set()
        )

    async def authorize(self, spec, ctx, arguments, gateway):
        if not spec.allowed(ctx.location, self.effective(ctx)):
            raise BusinessError("此命令在当前位置不可用，或你没有所需的身份组。")
        resources = {}
        parts = arguments.split()
        if spec.policy == "ROLE_SCOPE":
            action = spec.subcommand
            if not action and parts:
                raise BusinessError(
                    "用法：/role；管理请使用 list/add/remove/clear/reset/group-admin。"
                )
            if action == "list":
                if len(parts) > 1:
                    raise BusinessError("用法：/role list [ROLE]")
                resources["role"] = parse_role(parts[0], ctx.group) if parts else None
            if action in {"add", "remove", "clear"}:
                if len(parts) not in ({1, 2} if action == "clear" else {2}):
                    raise BusinessError("用法：" + spec.usage)
                resources["user"] = qq_id(parts[0])
                resources["role"] = (
                    parse_role(parts[1], ctx.group) if len(parts) == 2 else None
                )
        if spec.policy == "ROLE_GROUP":
            if spec.subcommand == "reset":
                if len(parts) != (0 if ctx.group else 1):
                    raise BusinessError("群内用 /role reset；私聊用 /role reset 群号。")
                resources["group"] = ctx.group or qq_id(parts[0])
            elif spec.subcommand == "group-admin":
                if len(parts) != (1 if ctx.group else 2) or parts[0].lower() not in {
                    "on",
                    "off",
                }:
                    raise BusinessError(
                        "群内用 /role group-admin on|off；私聊须在末尾加群号。"
                    )
                resources.update(
                    group=ctx.group or qq_id(parts[1]),
                    everyone_admin=parts[0].lower() == "on",
                )
        if spec.policy == "OWN_OR_MEMBER" and ctx.group:
            await self.require_member(ctx.actor, ctx.group, gateway)
        if spec.policy == "CLEAR_SCOPE":
            if len(parts) > 1:
                raise BusinessError("用法：" + spec.usage)
            target = parts[0].lower() if parts else "this"
            is_admin = "admin" in self.roles.effective(ctx.actor)
            if target == "this":
                resources.update(
                    location=ctx.location, conversation=ctx.group or ctx.actor
                )
            elif target == "all":
                if not is_admin:
                    raise BusinessError("清除所有群需要全局 admin。")
                resources.update(location="GROUP", conversation=None)
            else:
                group = qq_id(target)
                if not is_admin and (not ctx.group or group != ctx.group):
                    raise BusinessError("跨群清除需要全局 admin。")
                resources.update(location="GROUP", conversation=group)
        if spec.policy == "SUMMARY_SCOPE":
            if ctx.group:
                if len(parts) > 1 or (
                    parts and "admin" not in self.roles.effective(ctx.actor)
                ):
                    raise BusinessError(
                        "群内指定总结群号需要全局 admin；/summary 默认本群。"
                    )
                resources["group"] = qq_id(parts[0]) if parts else ctx.group
            elif parts and parts[0].lower() == "text":
                if len(parts) < 2:
                    raise BusinessError("用法：/summary text 内容")
            elif parts:
                if parts[0].lower() == "group":
                    if len(parts) != 2:
                        raise BusinessError("用法：/summary group GROUP")
                    resources["group"] = qq_id(parts[1])
                elif len(parts) == 1 and parts[0].isascii() and parts[0].isdigit():
                    resources["group"] = qq_id(parts[0])
                if resources.get("group") and "admin" not in self.roles.effective(
                    ctx.actor
                ):
                    await self.require_member(ctx.actor, resources["group"], gateway)
        if spec.policy == "TARGET_GROUP":
            values = arguments.split(maxsplit=1)
            if len(values) != 2 or not values[1].strip():
                raise BusinessError("用法：/send GROUP 内容")
            resources.update(group=qq_id(values[0]), text=values[1])
        return AuthorizedAction(spec, ctx, arguments, resources)

    @staticmethod
    async def require_member(user, group, gateway):
        members = await gateway.members(group)
        if user not in {str(item.get("user_id")) for item in members}:
            raise BusinessError("只能访问自己所在群的这类资源。")
        return members
