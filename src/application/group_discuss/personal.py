"""Private discuss entry and Super management, reusing the shared metered harness."""

import asyncio
import copy
import json
import shlex
from dataclasses import replace

from ...domain.context import qq_id
from ...domain.errors import BusinessError
from ...domain.group_discuss.config import (
    effective,
    mask_key,
    parse_value,
    validate_group,
)
from ...infrastructure.group_discuss.store import scope_key
from ...infrastructure.storage.json_store import atomic_json, read_json
from ...presentation.group_discuss.configuration import render_personal_configuration
from .service import DiscussService


class PersonalDiscussService(DiscussService):
    """Share storage, live policy and scheduler with group discuss, not its roles.

    Distinct CHAT scopes isolate keys, histories, budgets and user overrides. The
    engine owns shared state so global concurrency and daily limits cover both.
    """

    def __init__(self, engine):
        self.engine = engine
        self.switch_path = engine.store.directory / "discuss_switch.json"
        if self.switch_path.exists():
            self.switch_override = read_json(self.switch_path)["enabled"]
            if type(self.switch_override) is not bool:
                raise BusinessError("discuss 总开关必须为 true 或 false。")
        else:
            self.switch_override = None

    def __getattr__(self, name):
        return getattr(self.engine, name)

    @property
    def global_waiting(self):
        return self.engine.global_waiting

    @global_waiting.setter
    def global_waiting(self, value):
        self.engine.global_waiting = value

    @property
    def enabled(self):
        value = self.switch_override
        if value is None:
            value = self.system_config.get("discuss", {}).get("enabled", True)
        return value is True

    def access_enabled(self, scope):
        row = self.store.db.execute(
            "SELECT enabled FROM groups WHERE scope=?", (scope,)
        ).fetchone()
        return bool(row[0]) if row else self.global_super(json.loads(scope)[3])

    def config(self, scope):
        stored = self.store.group(scope)["config"]
        config = effective(stored, self.policy)
        config["max_sessions"] = 1
        config["tools.query_group_data.enabled"] = False
        if not config["model_name"] and self.policy["allowed_models"]:
            config["model_name"] = self.policy["allowed_models"][0]
        return config

    def auto_moderation_allowed(self, ctx, scope):
        return False

    async def require_user(self, ctx, gateway, scope):
        if ctx.group or scope != scope_key(ctx):
            raise BusinessError("个人 discuss 只能访问当前私聊用户自己的会话。")
        if not self.enabled:
            raise BusinessError("个人 discuss 总开关已关闭，请联系 Super。")
        if not self.access_enabled(scope):
            raise BusinessError("Super 尚未为你开放个人 discuss。")

    def ready(self, scope, config):
        validate_group("system_prompt", config["system_prompt"], self.policy)
        if not self.policy["api_address"] or not self.store.secret(scope):
            raise BusinessError("请先私聊设置 /discuss apikey = sk-XXX。")
        if config["model_name"] not in self.policy["allowed_models"]:
            raise BusinessError("当前 DeepSeek 模型未获系统允许，请联系 Super。")
        if config["reasoning_effort"] not in self.policy["allowed_efforts"]:
            raise BusinessError("当前思考强度已被系统停用。")

    @staticmethod
    def command(ctx):
        if ctx.group:
            return None
        parts = ctx.text.strip().split(maxsplit=2)
        if parts and parts[0].lower() == "/discuss":
            return False, ctx.text.strip()[len(parts[0]) :].strip()
        if parts and parts[0].lower() == "/new":
            return False, "new " + ctx.text.strip()[len(parts[0]) :].strip()
        if len(parts) > 1 and [p.lower() for p in parts[:2]] == ["/super", "discuss"]:
            return True, parts[2] if len(parts) > 2 else "help"
        return None

    def candidate(self, ctx):
        if ctx.group or ctx.actor == ctx.bot:
            return False
        if self.command(ctx) is not None:
            return True
        scope = scope_key(ctx)
        return (
            not ctx.text.lstrip().startswith("/")
            and self.enabled
            and self.access_enabled(scope)
            and bool(self.store.secret(scope))
        )

    async def _handle(self, ctx, gateway):
        if not self.candidate(ctx):
            return False
        try:
            parsed = self.command(ctx)
            if parsed is not None:
                global_command, raw = parsed
                if global_command:
                    if not self.global_super(ctx.actor):
                        raise BusinessError("仅全局 Super 可管理个人 discuss。")
                    text = await self.manage_personal(ctx, gateway, raw)
                else:
                    text = await self.user_command(ctx, gateway, raw)
                if text:
                    await self.send(ctx, gateway, text)
            else:
                await self.require_user(ctx, gateway, scope_key(ctx))
                await self.chat(ctx, gateway, scope_key(ctx))
        except BusinessError as exc:
            await self.send(ctx, gateway, str(exc))
        return True

    async def chat(self, ctx, gateway, scope, session=None):
        await self.require_user(ctx, gateway, scope)
        replies = [p for p in ctx.segments if p.get("type") == "reply"]
        if replies:
            for reply in replies:
                session = self.store.message_session(
                    scope, str((reply.get("data") or {}).get("id", ""))
                )
                if not session:
                    raise BusinessError(
                        "无法确认引用属于你的个人 discuss 会话，请用 /discuss 提问。"
                    )
        else:
            active = self.store.sessions(scope, ctx.actor)
            session = active[-1]["id"] if active else None
        # The command prefix is removed before metering; quotes never change identity.
        await super().chat(replace(ctx, mentioned_bot=True), gateway, scope, session)

    async def user_command(self, ctx, gateway, raw):
        scope = scope_key(ctx)
        words = raw.split(maxsplit=1)
        word = words[0].lower() if words else ""
        tail = words[1] if len(words) > 1 else ""
        if not raw or word == "help":
            topics = tail.split()
            if len(topics) > 1:
                raise BusinessError("用法：/discuss help [tools|configuration]")
            return await self.personal_help(
                ctx, gateway, topics[0] if topics else "help"
            )
        if word == "apikey":
            tail = tail.strip()
            if tail == "show":
                return "个人 DeepSeek API Key：" + mask_key(self.store.secret(scope))
            if tail == "clear":
                self.store.set_secret(scope, ctx.actor, "")
                self.store.end(scope, "all", "用户清除 API Key", ctx.actor)
                return "已清除个人 API Key 并结束会话。普通私聊已恢复原 autoanalysis 分发，仍须满足原有权限和开关。"
            if not tail.startswith("="):
                raise BusinessError(
                    "用法：/discuss apikey = sk-XXX；或 apikey show|clear"
                )
            await self.require_user(ctx, gateway, scope)
            key = tail[1:].strip()
            if not key or any(c.isspace() for c in key):
                raise BusinessError("API Key 不得为空或包含空白。")
            validate_group("api_key", key, self.policy)
            self.guard.secrets.register(key)
            self.store.set_secret(scope, ctx.actor, key)
            self.store.end(scope, "all", "用户更换 API Key", ctx.actor)
            return (
                "已保存个人 API Key，密钥不回显；之后的 discuss 请求仅使用此 Key。\n"
                "普通私聊现在由 discuss 接管，不再使用 autoanalysis；每句话自动加入当前会话上下文。\n"
                "discuss 可通过业务命令工具代替 DDL 自动分析；须由 Super 开启 tools.execute_commands，且你拥有 ddl 权限。\n"
                "用 /new 开始新话题；用 /discuss apikey clear 移除 Key 后可继续使用 autoanalysis（须满足原权限与开关）。"
            )
        if word == "status" and not tail.strip():
            await self.show_config(ctx, gateway, scope)
            return json.dumps(
                {
                    "total_enabled": self.enabled,
                    "budget": self.store.budget(scope, self.config(scope), self.policy),
                },
                ensure_ascii=False,
                indent=2,
            )
        if word == "end" and not tail.strip():
            self.store.end(scope, "all", "用户结束会话", ctx.actor)
            return "个人会话已结束，使用 /discuss 内容 开始新会话。"
        await self.require_user(ctx, gateway, scope)
        if word == "new":
            self.store.end(scope, "all", "用户新建会话", ctx.actor)
            if not tail.strip():
                return "已结束旧上下文，下一条私聊将开启新会话；每日已用额度保留。"
            raw = tail.strip()
            ctx = replace(ctx, segments=[])
        await self.chat(replace(ctx, text=raw), gateway, scope)
        return None

    @staticmethod
    def target_user(ctx, value):
        return scope_key(replace(ctx, actor=qq_id(value), group=""))

    async def show_config(self, ctx, gateway, scope, key=None):
        stored = self.store.group(scope)["config"]
        shown = {
            "enabled": self.access_enabled(scope),
            **self.config(scope),
            "api_key": mask_key(self.store.secret(scope)),
        }
        shown.pop("user_mode", None)
        for setting in tuple(shown):
            if setting.startswith("tools.query_group_data."):
                shown.pop(setting)
        if key is not None:
            if key not in shown:
                raise BusinessError("未知个人配置项。")
            shown = {key: shown[key]}
        self.guard.secrets.check([shown, stored, self.policy])
        image = await asyncio.to_thread(
            render_personal_configuration,
            json.loads(scope)[3],
            shown,
            stored,
            copy.deepcopy(self.policy),
        )
        await gateway.send_image(image, group="", user=ctx.actor)

    async def manage_personal(self, ctx, gateway, raw):
        if ctx.group or not self.global_super(ctx.actor):
            raise BusinessError("个人 discuss 管理仅限全局 Super 私聊。")
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            raise BusinessError("命令引号未闭合。") from exc
        if not parts or parts == ["help"]:
            return await self.personal_help(ctx, gateway, "super")
        op = parts[0]
        if (
            op == "switch"
            and len(parts) == 2
            and parts[1] in ("true", "false", "reset")
        ):
            if parts[1] == "reset":
                self.switch_path.unlink(missing_ok=True)
                self.switch_override = None
            else:
                value = parts[1] == "true"
                atomic_json(self.switch_path, {"enabled": value})
                self.switch_path.chmod(0o600)
                self.switch_override = value
            if not self.enabled:
                for row in self.store.db.execute("SELECT scope FROM groups").fetchall():
                    if len(json.loads(row[0])) == 4:
                        self.store.end(
                            row[0], "all", "个人 discuss 总开关关闭", ctx.actor
                        )
            with self.store.db:
                self.store.log(
                    "system", ctx.actor, "personal switch", str(self.enabled)
                )
            return "个人 discuss 总开关：" + str(self.enabled).lower()
        if op == "limits":
            if parts == ["limits", "show"]:
                return json.dumps(
                    {"discuss.enabled": self.enabled, "shared_policy": self.policy},
                    ensure_ascii=False,
                    indent=2,
                )
            return await self.engine.manage(ctx, gateway, True, raw)
        if op == "users" and len(parts) == 1:
            rows = []
            for row in self.store.db.execute(
                "SELECT scope,enabled FROM groups ORDER BY scope"
            ):
                scope = json.loads(row["scope"])
                if len(scope) == 4 and scope[:3] == [ctx.platform, ctx.bot, "CHAT"]:
                    rows.append(
                        f"{scope[3]}：{'开启' if row['enabled'] else '关闭'}；Key {mask_key(self.store.secret(row['scope']))}"
                    )
            return "个人 discuss 用户：\n" + ("\n".join(rows) or "无")
        if op in ("enable", "disable") and len(parts) == 2:
            scope = self.target_user(ctx, parts[1])
            self.store.save_group(scope, ctx.actor, enabled=op == "enable")
            if op == "disable":
                self.store.end(scope, "all", "Super 关闭用户 discuss", ctx.actor)
            return (
                "已" + ("开启" if op == "enable" else "关闭") + "该用户的个人 discuss。"
            )
        if op == "config" and len(parts) >= 3:
            action, scope = parts[1], self.target_user(ctx, parts[2])
            if action == "show" and len(parts) in (3, 4):
                return await self.show_config(
                    ctx, gateway, scope, parts[3] if len(parts) == 4 else None
                )
            if action in ("set", "reset") and len(parts) >= (
                5 if action == "set" else 4
            ):
                key = parts[3]
                if key in ("user_mode", "max_sessions") or key.startswith(
                    "tools.query_group_data."
                ):
                    raise BusinessError(
                        "个人入口固定一个活动会话，不使用群准入模式或群数据查询工具。"
                    )
                if key == "api_key":
                    if action != "reset" or len(parts) != 4:
                        raise BusinessError(
                            "Super 仅可重置用户 Key；设置请由用户私聊 /discuss apikey = XXX。"
                        )
                    self.store.set_secret(scope, ctx.actor, "")
                    self.store.end(scope, "all", "Super 清除用户 Key", ctx.actor)
                    return "已清除用户 Key 并结束会话。"
                stored = self.store.group(scope)["config"]
                if action == "reset":
                    if len(parts) != 4 or key not in self.policy["defaults"]:
                        raise BusinessError("用法：config reset USER KEY")
                    stored.pop(key, None)
                else:
                    value = parse_value(" ".join(parts[4:]))
                    validate_group(key, value, self.policy)
                    self.guard.secrets.check(value)
                    stored[key] = value
                self.store.save_group(
                    scope, ctx.actor, config=stored, enabled=self.access_enabled(scope)
                )
                return "已保存用户 discuss 配置。"
        if op in ("sessions", "end", "statistics", "stats") and len(parts) >= 2:
            scope = self.target_user(ctx, parts[1])
            if op == "sessions" and len(parts) == 2:
                return "活跃个人会话：\n" + (
                    "\n".join(r["id"] for r in self.store.sessions(scope)) or "无"
                )
            if op == "end" and len(parts) == 3:
                if parts[2] != "all":
                    self.store.session(scope, parts[2])
                self.store.end(scope, parts[2], "Super 结束个人会话", ctx.actor)
                return "个人会话已结束。"
            if op in ("statistics", "stats") and len(parts) in (2, 3):
                report = self.store.stats(
                    scope, parts[2] if len(parts) == 3 else "today"
                )
                report["current_budget"] = self.store.budget(
                    scope, self.config(scope), self.policy
                )
                return json.dumps(report, ensure_ascii=False, indent=2)
        if parts[:2] == ["usage", "resolve"] and len(parts) >= 6:
            scope = self.target_user(ctx, parts[2])
            try:
                amount = int(parts[4])
            except ValueError as exc:
                raise BusinessError("TOKENS 须为非负整数。") from exc
            if not 0 <= amount < 2**63:
                raise BusinessError("TOKENS 须为非负整数。")
            self.store.resolve(scope, parts[3], amount, ctx.actor, " ".join(parts[5:]))
            return "已核销个人用量，差额已审计。"
        raise BusinessError("未知命令或参数不完整，请使用 /super discuss help。")

    async def personal_help(self, ctx, gateway, topic):
        if topic not in {"help", "tools", "configuration", "super"}:
            raise BusinessError("无此个人 discuss 帮助主题。")
        if topic == "super" and not self.global_super(ctx.actor):
            raise BusinessError("Super 帮助仅限全局 Super。")
        name = "discuss" if topic in {"help", "super"} else "discuss-" + topic
        data = await asyncio.to_thread(
            self.images.read, name, "CHAT", super_help=topic == "super"
        )
        await gateway.send_image(data, group="", user=ctx.actor)
