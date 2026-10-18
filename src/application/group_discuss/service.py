"""Isolated commands, authorization and conversation entry point."""

import asyncio
import copy
import json
import shlex
from dataclasses import replace
from pathlib import Path

from ...domain.context import qq_id
from ...domain.errors import BusinessError
from ...domain.group_discuss.config import (
    effective,
    mask_key,
    parse_value,
    system_defaults,
    validate_group,
    validate_system,
)
from ...domain.security import SecretViolation
from ...infrastructure.group_discuss.store import DiscussStore, scope_key
from ...infrastructure.messaging.onebot import ReadonlyViolation
from ...infrastructure.storage.json_store import atomic_json, read_json
from ...presentation.group_discuss.output import usage_footer
from .harness import Turn, run_turn

DOCS = Path(__file__).resolve().parents[3] / "docs/group-dicsuss"


class DiscussService:
    def __init__(self, directory, config, roles, guard, http, deadlines):
        self.store = DiscussStore(directory)
        self.system_config, self.roles, self.guard = config, roles, guard
        self.http, self.deadlines = http, deadlines
        self.policy_path = directory / "group_discuss_policy.json"
        self.policy = system_defaults()
        self.policy.update(copy.deepcopy(config.get("group_discuss", {})))
        # Command changes are a durable override of the deployment defaults.
        if self.policy_path.exists():
            self.policy.update(read_json(self.policy_path))
        validate_system(self.policy)
        self.policy = self._protect_policy(self.policy)
        for row in self.store.db.execute("SELECT scope FROM secrets"):
            self.guard.secrets.register(self.store.secret(row[0]))
        self.global_waiting = 0
        self.group_waiting = {}
        self.running = {}
        self.session_locks = {}
        self.lock_users = {}
        self.active_tasks = {}
        self.store.on_end = self.cancel_session
        self.store.cleanup(self.policy["history_retention_days"])
        self.store.apply_limits(self.policy)

    def cancel_session(self, session):
        task = self.active_tasks.get(session)
        if task is not None and task is not asyncio.current_task():
            task.cancel()

    def _protect_policy(self, policy):
        # The search credential is separately encrypted, including in persisted policy.
        if policy["search_api_key"]:
            self.store.set_secret("system:search", "system", policy["search_api_key"])
        policy["search_api_key"] = self.store.secret("system:search")
        self.guard.secrets.register(policy["search_api_key"])
        return policy

    def global_super(self, actor):
        return "super" in self.roles.effective(actor)

    def rank(self, scope, actor):
        if self.global_super(actor):
            return 3
        if self.store.role(scope, "super", actor):
            return 2
        return 1 if self.store.role(scope, "admin", actor) else 0

    def authorize(self, scope, actor, rank):
        if self.rank(scope, actor) < rank:
            raise BusinessError("没有目标群所需的 discuss 管理身份。")

    def config(self, scope):
        return effective(self.store.group(scope)["config"], self.policy)

    async def require_user(self, ctx, gateway, scope):
        if self.global_super(ctx.actor) or self.rank(scope, ctx.actor):
            return
        config = self.config(scope)
        if config["user_mode"] not in self.policy["allowed_user_modes"]:
            raise BusinessError("当前 user 模式已被系统停用。")
        mode = config["user_mode"]
        allowed = (
            mode == "all"
            or (mode == "whitelist" and self.store.role(scope, "user", ctx.actor))
            or (
                mode == "blacklist"
                and not self.store.role(scope, "blacklist", ctx.actor)
            )
        )
        if not allowed:
            raise BusinessError("没有本群 group.discuss.user 身份。")
        group = json.loads(scope)[2]
        if ctx.group != group:
            members = await gateway.members(group)
            if ctx.actor not in {str(item.get("user_id")) for item in members}:
                raise BusinessError("你不是目标群成员。")

    def ready(self, scope, config):
        validate_group("system_prompt", config["system_prompt"], self.policy)
        if not self.policy["api_address"] or not self.store.secret(scope):
            raise BusinessError(
                "本群讨论功能尚未配置模型地址或 API Key，请联系管理员。"
            )
        if config["model_name"] not in self.policy["allowed_models"]:
            raise BusinessError("本群尚未配置系统允许的 DeepSeek 模型。")
        if config["reasoning_effort"] not in self.policy["allowed_efforts"]:
            raise BusinessError("当前思考强度已被系统停用。")
        if config["user_mode"] not in self.policy["allowed_user_modes"]:
            raise BusinessError("当前 user 模式已被系统停用。")
        if config["summary_token_limit"] >= config["context_token_limit"]:
            raise BusinessError("摘要上限必须小于上下文上限。")

    @staticmethod
    def command(ctx):
        parts = ctx.text.strip().split(maxsplit=2)
        if ctx.group and not ctx.mentioned_bot:
            return None
        if parts and parts[0].lower() == "/group-discuss":
            return False, ctx.text.strip().partition(" ")[2].strip()
        if (
            len(parts) > 1
            and parts[0].lower() == "/super"
            and parts[1].lower() == "group-discuss"
        ):
            return True, parts[2] if len(parts) > 2 else "help"
        return None

    def candidate(self, ctx):
        if ctx.actor == ctx.bot:
            return False
        if self.command(ctx) is not None:
            return True
        return bool(
            ctx.group
            and not ctx.text.lstrip().startswith("/")
            and (
                ctx.mentioned_bot or any(p.get("type") == "reply" for p in ctx.segments)
            )
        )

    async def handle(self, ctx, gateway):
        try:
            return await self._handle(ctx, gateway)
        except ReadonlyViolation:
            return True
        except SecretViolation as exc:
            await self.guard.report_error(gateway.bot, ctx.bot, "discuss 密钥拦截", exc)
            return True
        except Exception as exc:
            await self.guard.report_error(gateway.bot, ctx.bot, "discuss 消息处理", exc)
            return True

    async def _handle(self, ctx, gateway):
        """Return whether the event belongs to this feature; never fall into autoanalysis."""
        command = self.command(ctx)
        if command is not None:
            try:
                if ctx.group:
                    await self.guard.check(gateway.bot, ctx.group, ctx.bot, "讨论命令")
                text = await self.manage(ctx, gateway, *command)
                if text:
                    await self.send(ctx, gateway, text)
            except BusinessError as exc:
                await self.send(ctx, gateway, str(exc))
            return True
        if not self.candidate(ctx):
            return False
        scope = scope_key(ctx)
        if not ctx.mentioned_bot:
            reply = next((p for p in ctx.segments if p.get("type") == "reply"), None)
            identifier = str((reply.get("data") or {}).get("id", "")) if reply else ""
            if not self.store.message_session(scope, identifier):
                try:
                    original = await gateway.message(identifier)
                except Exception:
                    return False
                if (
                    str((original.get("sender") or {}).get("user_id", "")) != ctx.bot
                    or str(original.get("group_id", "")) != ctx.group
                ):
                    return False
        if not self.store.group(scope)["enabled"]:
            # Keep disabled discuss from falling through into paid group analysis.
            return True
        try:
            await self.require_user(ctx, gateway, scope)
        except BusinessError:
            return True
        try:
            await self.chat(ctx, gateway, scope)
        except BusinessError as exc:
            await self.send(ctx, gateway, str(exc))
        return True

    async def send(self, ctx, gateway, text, session=None):
        self.guard.secrets.check(text)
        result = await gateway.send(
            text=text, group=ctx.group, user="" if ctx.group else ctx.actor
        )
        if (
            session
            and isinstance(result, dict)
            and result.get("message_id") is not None
        ):
            self.store.map_message(scope_key(ctx), result["message_id"], session)

    async def chat(self, ctx, gateway, scope):
        await self.guard.check(gateway.bot, ctx.group, ctx.bot, "群讨论")
        config = self.config(scope)
        self.ready(scope, config)
        if not ctx.text.strip():
            raise BusinessError("请附上问题文字。")
        quote, session = "", None
        for segment in ctx.segments:
            if segment.get("type") != "reply":
                continue
            identifier = str((segment.get("data") or {}).get("id", ""))
            session = self.store.message_session(scope, identifier)
            if session:
                break
            # Fetch authoritative platform data; cached user-supplied sender fields are not trusted.
            try:
                message = await gateway.message(identifier)
                sender = str((message.get("sender") or {}).get("user_id", ""))
                group = str(message.get("group_id", ""))
                if group != ctx.group:
                    raise BusinessError("无法确认引用消息属于本群，请直接 @ 提问。")
                if not ctx.mentioned_bot and sender != ctx.bot:
                    return
                from ...infrastructure.messaging.messages import segments, visible_text

                quote = visible_text(
                    segments(message.get("message", message.get("raw_message", "")))
                )[:2000]
            except BusinessError:
                raise
            except Exception as exc:
                raise BusinessError("无法核验引用消息，请直接 @ 机器人提问。") from exc
            break
        if not ctx.mentioned_bot and not session and not quote:
            return
        if session and self.store.session(scope, session)["ended"] is not None:
            raise BusinessError("该会话已结束，请重新 @ 开始新会话。")
        waiting = self.group_waiting.get(scope, 0)
        if (
            waiting >= self.policy["group_queue_limit"]
            or self.global_waiting >= self.policy["global_queue_limit"]
        ):
            raise BusinessError("讨论排队已满，请稍后重试。")
        if not self.store.claim_message(scope, ctx.message_id):
            return
        session = session or self.store.create_session(
            scope, ctx.actor, config["max_sessions"]
        )
        self.global_waiting += 1
        self.group_waiting[scope] = waiting + 1
        lock = self.session_locks.setdefault(session, asyncio.Lock())
        self.lock_users[session] = self.lock_users.get(session, 0) + 1
        entered = False
        try:
            async with lock:
                # One scheduling loop reads live global limits without replacing active semaphores.
                while (
                    sum(self.running.values()) >= self.policy["global_concurrency"]
                    or self.running.get(scope, 0) >= self.policy["group_concurrency"]
                ):
                    if self.store.session(scope, session)["ended"] is not None:
                        raise BusinessError("会话已结束。")
                    await asyncio.sleep(0.1)
                self.running[scope] = self.running.get(scope, 0) + 1
                entered = True
                self.global_waiting -= 1
                self.group_waiting[scope] -= 1
                try:
                    await self.execute_turn(ctx, gateway, scope, session, quote)
                finally:
                    self.running[scope] -= 1
        finally:
            self.lock_users[session] -= 1
            if not self.lock_users[session]:
                self.lock_users.pop(session, None)
                self.session_locks.pop(session, None)
            if not entered:
                self.global_waiting -= 1
                self.group_waiting[scope] -= 1

    async def execute_turn(self, ctx, gateway, scope, session, quote):
        identifier = self.store.new_turn(session, ctx.actor)
        turn = Turn(self, ctx, gateway, scope, session, identifier)
        self.active_tasks[session] = asyncio.current_task()
        state = "completed"
        try:
            prompt = json.dumps(
                {
                    "untrusted_user_input": {"actor": ctx.actor, "text": ctx.text},
                    "untrusted_quoted_material": quote,
                },
                ensure_ascii=False,
            )
            self.guard.secrets.check(prompt)
            text = await asyncio.wait_for(
                run_turn(turn, prompt), self.policy["request_timeout"]
            )
            self.guard.secrets.check(text)
        except asyncio.TimeoutError:
            state, text = "failed", "本轮处理超时，未确认的用量仍预留，请稍后重试。"
        except BusinessError as exc:
            state, text = "failed", str(exc)
        except asyncio.CancelledError:
            state = "interrupted"
            if self.store.session(scope, session)["ended"] is None:
                raise
            text = "会话已结束，在途请求已尝试取消。"
        except Exception as exc:
            state, text = "failed", "本轮处理失败，请联系 Super 检查模型或工具配置。"
            await self.guard.report_error(gateway.bot, ctx.bot, "group-discuss", exc)
        finally:
            self.active_tasks.pop(session, None)
            self.store.finish_turn(identifier, state)
        ended = self.store.session(scope, session)
        if ended["ended"] is not None:
            text = f"会话已结束：{ended['reason']}。请重新 @ 开始。"
        elif (
            self.store.total("session=?", [session])
            >= self.config(scope)["session_token_budget"]
        ):
            self.store.end(scope, session, "会话预算耗尽")
            text += "\n会话预算已耗尽，本会话结束。"
        await self.send(
            ctx,
            gateway,
            text + "\n\n" + usage_footer(self.store.turn_usage(identifier)),
            session,
        )

    def target(self, ctx, value):
        group = qq_id(value)
        if ctx.group and group != ctx.group:
            raise BusinessError("群聊只能管理本群，跨群请私聊。")
        return scope_key(ctx, group)

    @staticmethod
    def private(ctx):
        if ctx.group:
            raise BusinessError(
                "群配置、统计和会话管理仅限私聊，请私聊并明确目标群号。"
            )

    async def manage(self, ctx, gateway, global_command, raw):
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            raise BusinessError("命令引号未闭合。") from exc
        if global_command and not self.global_super(ctx.actor):
            raise BusinessError("仅全局 super 可使用此入口。")
        if not parts or parts[0] == "help":
            return self.help(
                ctx, global_command, parts[1] if len(parts) > 1 else "help"
            )
        if not global_command and parts[0] in ("admin", "super"):
            prefix, parts = parts[0], parts[1:]
            if not parts or parts == ["help"]:
                return self.help(
                    ctx, False, "group-super" if prefix == "super" else "admin"
                )
        else:
            prefix = "global" if global_command else "user"
        if not parts:
            raise BusinessError("请使用 /group-discuss help 查看用法。")
        op = parts[0]
        if prefix == "global" and op == "limits":
            self.private(ctx)
            if parts[1:] == ["show"]:
                shown = copy.deepcopy(self.policy)
                shown["search_api_key"] = mask_key(shown["search_api_key"])
                return json.dumps(shown, ensure_ascii=False, indent=2)
            if len(parts) >= 4 and parts[1] == "set":
                key, value = parts[2], parse_value(" ".join(parts[3:]))
                policy = copy.deepcopy(self.policy)
                container = policy
                if key.startswith(("defaults.", "maxima.", "tool_enabled.")):
                    head, key = key.split(".", 1)
                    container = policy[head]
                if key not in container:
                    raise BusinessError("未知系统设置项。")
                container[key] = value
                validate_system(policy)
                self.authorize("", ctx.actor, 3)
                if parts[2] == "search_api_key":
                    self.store.set_secret("system:search", ctx.actor, value)
                    self.guard.secrets.register(value)
                self.policy = policy
                persisted = copy.deepcopy(policy)
                persisted["search_api_key"] = ""
                atomic_json(self.policy_path, persisted)
                self.policy_path.chmod(0o600)
                self.store.apply_limits(policy)
                with self.store.db:
                    self.store.log("system", ctx.actor, "policy", parts[2])
                return "已保存系统 discuss 配置。"
            raise BusinessError("用法：/super group-discuss limits show|set KEY VALUE")
        if prefix == "global" and op in ("enable", "disable"):
            self.private(ctx)
            if len(parts) != (3 if op == "enable" else 2):
                raise BusinessError("用法：enable GROUP USER 或 disable GROUP")
            scope = self.target(ctx, parts[1])
            if op == "enable":
                user = qq_id(parts[2])
                self.store.change_role(scope, ctx.actor, "super", user, True)
            self.store.save_group(scope, ctx.actor, enabled=op == "enable")
            if op == "disable":
                self.store.end(scope, "all", "功能停用", ctx.actor)
            return (
                "已启用并指定群 discuss super。"
                if op == "enable"
                else "已停用并结束本群全部会话。"
            )
        # Role management: group-super can grant admin, admin can grant user.
        if op in ("super", "admin", "user", "blacklist") and prefix != "user":
            allowed = {
                "global": {"super", "admin", "user", "blacklist"},
                "super": {"admin"},
                "admin": {"user", "blacklist"},
            }[prefix]
            if (
                op not in allowed
                or len(parts) < 2
                or parts[1] not in ("add", "remove", "list", "show")
            ):
                raise BusinessError("无效的身份组命令。")
            action = parts[1]
            required = 3 if op == "super" else 2 if op == "admin" else 1
            base = 2 if action == "list" else 3
            if len(parts) not in (base, base + 1) or (
                len(parts) == base and not ctx.group
            ):
                raise BusinessError(
                    "私聊必须明确 USER（list 除外）和 GROUP；群聊可省略 GROUP。"
                )
            scope = self.target(ctx, parts[-1] if len(parts) == base + 1 else ctx.group)
            self.authorize(scope, ctx.actor, required)
            if action == "list":
                return f"group.discuss.{op} 直接名单：" + (
                    ", ".join(self.store.role_list(scope, op)) or "空"
                )
            user = qq_id(parts[2])
            if action == "show":
                return await self.describe_user(ctx, gateway, scope, user)
            self.store.change_role(scope, ctx.actor, op, user, action == "add")
            return "已更新直接名单；继承权限及全员模式不受直接名单移除或黑名单影响。"
        if op == "role" and prefix == "user":
            if len(parts) != (1 if ctx.group else 2):
                raise BusinessError(
                    "用法：/group-discuss role [GROUP]，私聊必须提供群号。"
                )
            scope = self.target(ctx, ctx.group or parts[1])
            return await self.describe_user(ctx, gateway, scope, ctx.actor)
        if op == "config" and prefix in ("global", "admin"):
            self.private(ctx)
            if len(parts) < 3:
                raise BusinessError(
                    "用法：config show GROUP [KEY] 或 config set GROUP KEY VALUE"
                )
            scope = self.target(ctx, parts[2])
            self.authorize(scope, ctx.actor, 1)
            stored = self.store.group(scope)["config"]
            if parts[1] == "show" and len(parts) in (3, 4):
                shown = {
                    "enabled": self.store.group(scope)["enabled"],
                    **self.config(scope),
                    "api_key": mask_key(self.store.secret(scope)),
                }
                if len(parts) == 4:
                    if parts[3] not in shown:
                        raise BusinessError("未知配置项。")
                    shown = {parts[3]: shown[parts[3]]}
                return json.dumps(
                    {
                        "effective": shown,
                        "stored": stored,
                        "system_maxima": self.policy["maxima"],
                        "allowed_models": self.policy["allowed_models"],
                        "allowed_efforts": self.policy["allowed_efforts"],
                        "allowed_user_modes": self.policy["allowed_user_modes"],
                        "tool_enabled": self.policy["tool_enabled"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            if parts[1] not in ("set", "reset") or len(parts) < (
                5 if parts[1] == "set" else 4
            ):
                raise BusinessError(
                    "用法：config set GROUP KEY VALUE 或 config reset GROUP KEY"
                )
            key = parts[3]
            value = (
                parse_value(" ".join(parts[4:]))
                if parts[1] == "set"
                else ("" if key == "api_key" else self.policy["defaults"].get(key))
            )
            if not (parts[1] == "reset" and key == "model_name" and value == ""):
                validate_group(key, value, self.policy)
            if key == "api_key":
                self.guard.secrets.register(value)
                self.store.set_secret(scope, ctx.actor, value)
            else:
                if parts[1] == "reset":
                    stored.pop(key, None)
                else:
                    stored[key] = value
                new = effective(stored, self.policy)
                if new["summary_token_limit"] >= new["context_token_limit"]:
                    raise BusinessError("摘要上限必须小于上下文上限。")
                self.store.save_group(scope, ctx.actor, config=stored)
                self.store.trim_sessions(scope, new["max_sessions"])
            return (
                "已保存群配置。API Key 不回显。"
                if key == "api_key"
                else "已保存群配置。"
            )
        if op in ("sessions", "end", "stats") and prefix in ("user", "admin", "global"):
            self.private(ctx)
            if len(parts) < 2:
                raise BusinessError("必须指定目标群号。")
            scope = self.target(ctx, parts[1])
            if prefix == "user":
                await self.require_user(ctx, gateway, scope)
                if op == "stats":
                    raise BusinessError("群统计需要 discuss admin。")
            else:
                self.authorize(scope, ctx.actor, 1)
            if op == "stats" and len(parts) in (2, 3):
                report = self.store.stats(
                    scope, parts[2] if len(parts) == 3 else "today"
                )
                report["current_budget"] = self.store.budget(
                    scope, self.config(scope), self.policy
                )
                return json.dumps(report, ensure_ascii=False, indent=2)
            if op == "sessions" and len(parts) == 2:
                rows = self.store.sessions(
                    scope, ctx.actor if prefix == "user" else None
                )
                return "活跃会话：\n" + (
                    "\n".join(
                        f"{r['id']} 创建者 {r['actor']}；已用/预留 {self.store.total('session=?', [r['id']])} tokens"
                        for r in rows
                    )
                    or "无"
                )
            if op == "end" and len(parts) == 3:
                if prefix == "user" and (
                    parts[2] == "all"
                    or self.store.session(scope, parts[2])["actor"] != ctx.actor
                ):
                    raise BusinessError("只能结束自己创建的会话。")
                if parts[2] != "all":
                    self.store.session(scope, parts[2])
                self.store.end(scope, parts[2], "手动结束", ctx.actor)
                return "会话已结束。"
        if prefix == "global" and parts[:2] == ["usage", "resolve"] and len(parts) >= 6:
            self.private(ctx)
            scope = self.target(ctx, parts[2])
            try:
                amount = int(parts[4])
            except ValueError as exc:
                raise BusinessError("TOKENS 须为非负整数。") from exc
            if not 0 <= amount < 2**63:
                raise BusinessError("TOKENS 须为非负整数。")
            self.store.resolve(scope, parts[3], amount, ctx.actor, " ".join(parts[5:]))
            return "已核销，原 usage 保留，差额已审计。"
        raise BusinessError("未知命令或参数不完整，请使用 /group-discuss help。")

    async def describe_user(self, ctx, gateway, scope, user):
        group = json.loads(scope)[2]
        candidate = replace(ctx, actor=user, group=group if ctx.group else "")
        try:
            await self.require_user(candidate, gateway, scope)
            allowed = True
        except BusinessError:
            allowed = False
        rank = self.rank(scope, user)
        return (
            f"群 {group} 用户 {user}：\n管理等级 {rank}（0普通/1admin/2群super/3全局super）\n"
            f"user 模式 {self.config(scope)['user_mode']}；白名单 {self.store.role(scope, 'user', user)}；"
            f"黑名单 {self.store.role(scope, 'blacklist', user)}\n"
            f"有效 group.discuss.user：{'是' if allowed else '否'}"
            + ("；继承自管理身份" if rank else "")
        )

    def help(self, ctx, global_command, topic):
        allowed = {"help", "roles", "tools"}
        if not ctx.group:
            allowed |= {"configuration", "statistics"}
        if global_command:
            allowed.add("super")
            topic = "super" if topic == "help" else topic
        else:
            # Admin command help is public syntax, never includes actual group data.
            allowed |= {"admin", "group-super"}
        if topic not in allowed:
            raise BusinessError("无此帮助主题，或当前位置不可查看。")
        return (DOCS / f"{topic}.md").read_text(encoding="utf-8")
