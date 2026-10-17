"""Scope-aware DDL commands and shared atomic commit for automatic analysis."""

import asyncio
import hashlib
import json
import time
from datetime import datetime

from ..domain.analysis import DEFAULT_TIME_PROMPT, MAX_DEFAULT_PROMPT
from ..domain.context import qq_id
from ..domain.costs import UsageContext
from ..domain.deadlines import (
    BEIJING,
    DeadlineConfirmation,
    parse_strict,
    split_targets,
)
from ..domain.errors import BusinessError
from ..domain.security import SecretViolation
from ..domain.text import display_name
from ..infrastructure.messages import command_body, visible_text
from ..infrastructure.onebot import ReadonlyViolation
from ..presentation.deadline_image import MAX_CARDS, active_tasks, render_deadlines
from ..presentation.deadlines import participant_labels, show_task


class DeadlineService:
    def __init__(
        self, data, roles, readonly, guard, extractor, authorizer, sessions, preferences
    ):
        self.data, self.roles, self.readonly, self.guard = data, roles, readonly, guard
        self.extractor, self.authorizer, self.sessions = extractor, authorizer, sessions
        self.preferences = preferences
        self.image_slots = asyncio.Semaphore(2)
        self.versions = {}
        self.failed = False
        readonly.listeners.append(self.readonly_changed)

    def readonly_changed(self, group):
        try:
            self.data.skip_group(group, time.time())
        except Exception:
            self.failed = True
            raise

    def version(self, scope):
        group_version = (
            self.versions.get(scope[:2] + ("GROUP",), 0) if scope[2] == "GROUP" else 0
        )
        return self.versions.get(scope, 0), group_version

    async def members_and_targets(self, values, ctx, gateway, names):
        members = await gateway.members(ctx.group)
        names.seed_members(ctx.group, members)
        result = []
        for value in values:
            if value in {"all", "全体成员", "0", ctx.bot}:
                raise BusinessError("不能通知机器人或全体成员。")
            matches = {
                str(item["user_id"])
                for item in members
                if value == str(item.get("user_id"))
                or value in (item.get("card"), item.get("nickname"))
            }
            if len(matches) != 1:
                raise BusinessError("通知对象不在本群或名字有歧义，请使用真实@或QQ号。")
            user = matches.pop()
            if user == ctx.bot:
                raise BusinessError("不能把机器人作为通知对象。")
            result.append(qq_id(user))
        result = list(dict.fromkeys(result))
        if len(result) > 20:
            raise BusinessError("每条 DDL 最多通知20人。")
        return result

    async def handle(self, action, gateway, names, on_submitted=None):
        if self.failed:
            raise RuntimeError("DDL 存储不可用。")
        ctx, sub, value = action.context, action.spec.subcommand, action.arguments
        if sub == "defaulttime":
            return self.defaulttime(ctx, value)
        if sub in {"add", "add-strict"}:
            return await self.add(action, gateway, names, on_submitted)
        if sub == "clear":
            return await self.clear(action, gateway, names)
        if sub == "view":
            if value.strip():
                raise BusinessError("用法：/ddl view")
            await self.send_view(ctx, gateway, names)
            return None
        if sub == "list":
            page = int(qq_id(value)) if value else 1
            async with self.data.lock:
                tasks = self.data.list(ctx.scope, time.time())
            pages = (len(tasks) + 19) // 20
            if tasks and page > pages:
                raise BusinessError(f"页码超出范围，共{pages}页。")
            if not tasks:
                return "当前会话暂无有效 DDL。"
            details = [
                await show_task(task, names, time.time())
                for task in tasks[(page - 1) * 20 : page * 20]
            ]
            return (
                f"DDL（共{len(tasks)}项，第{page}/{pages}页）：\n"
                + "\n\n".join(details)
                + (f"\n下一页：/ddl list {page + 1}" if page < pages else "")
            )
        identifier = int(qq_id(value))
        if identifier > 9223372036854775807:
            raise BusinessError("DDL 编号无效。")
        async with self.data.lock:
            task = self.data.get(ctx.scope, identifier)
            if sub == "remove":
                return DeadlineConfirmation(
                    self.data.remove(ctx.scope, identifier, ctx.actor), True
                )
        return await show_task(task, names, time.time())

    async def send_view(self, ctx, gateway, names, *, scope=None, require_member=True):
        self.check_writable(ctx)
        scope = scope or ctx.scope
        group = scope[3] if scope[2] == "GROUP" else ""
        if ctx.group and require_member:
            members = await self.authorizer.require_member(
                ctx.actor, ctx.group, gateway
            )
            names.seed_members(ctx.group, members)
        async with self.image_slots:
            async with self.data.lock:
                now = time.time()
                tasks = active_tasks(self.data.list(scope, now), now)
            for task in tasks[:MAX_CARDS]:
                if group:
                    task["participant_label"] = await participant_labels(
                        task, names, group
                    )
            # Inspect complete strings before rasterization or truncation.
            labels = [
                [task["title"], task.get("participant_label", "")]
                for task in tasks[:MAX_CARDS]
            ]
            self.guard.secrets.check(labels)
            png = await asyncio.to_thread(
                render_deadlines, tasks, now, group=bool(group)
            )
        if ctx.group and require_member:
            await self.authorizer.require_member(ctx.actor, ctx.group, gateway)
        self.check_writable(ctx)
        self.guard.secrets.check(labels)
        await gateway.send_image(
            png, group=ctx.group, user="" if ctx.group else ctx.actor
        )

    def defaulttime(self, ctx, value):
        if ctx.group:
            raise BusinessError("默认提醒提示词仅能在私聊设置。")
        if not value.strip():
            current = self.preferences.get(ctx)
            return "当前自动识别默认提醒提示词：\n" + (current or DEFAULT_TIME_PROMPT)
        try:
            prompt = json.loads(value)
        except ValueError as exc:
            raise BusinessError(
                '/ddl defaulttime "提示词"；使用空字符串恢复系统默认。'
            ) from exc
        if not isinstance(prompt, str) or len(prompt.strip()) > MAX_DEFAULT_PROMPT:
            raise BusinessError(f"提示词须用双引号包裹，最多{MAX_DEFAULT_PROMPT}字。")
        prompt = prompt.strip()
        self.guard.secrets.check(prompt)
        self.preferences.set(ctx, prompt)
        return (
            (
                "已保存自动识别默认提醒提示词。"
                if prompt
                else "已恢复系统默认提醒提示词。"
            )
            + "仅影响之后自动识别的新个人 DDL，明确指定的提醒优先；无效提示词回退系统默认，每项最多20次通知。"
        )

    async def add(self, action, gateway, names, on_submitted=None):
        ctx, sub = action.context, action.spec.subcommand
        version = self.version(ctx.scope)
        parts = command_body(ctx, sub)
        if any(part.get("type") not in {"text", "at"} for part in parts):
            raise BusinessError(
                "手动创建只接受文字和真实@；转发记录请直接私聊机器人自动分析。"
            )
        raw = visible_text(parts)
        body, suffix = split_targets(raw)
        self.guard.secrets.check(raw)
        native = [
            str(part.get("data", {}).get("qq", ""))
            for part in parts
            if part.get("type") == "at"
        ]
        mentions, explicit = [], []
        if not ctx.group:
            if suffix is not None or native:
                raise BusinessError("私聊 DDL 只通知自己，不接受指定其他成员。")
            allowed = [ctx.actor]
            annotated = body
        else:
            allowed = [ctx.actor]
            if suffix is not None:
                explicit = await self.members_and_targets(suffix, ctx, gateway, names)
                allowed.extend(explicit)
            if native:
                allowed.extend(
                    await self.members_and_targets(native, ctx, gateway, names)
                )
            else:
                await self.members_and_targets([ctx.actor], ctx, gateway, names)
            allowed = list(dict.fromkeys(allowed))
            chunks = []
            cutoff = len(raw.rpartition(";")[0]) if suffix is not None else len(raw)
            position = 0
            original_length = 0
            for index, part in enumerate(parts):
                data = part.get("data", {})
                if part.get("type") == "text":
                    text = str(data.get("text", ""))
                    visible = text[: max(0, cutoff - position)]
                    chunks.append(visible)
                    original_length += len(visible)
                    position += len(text)
                else:
                    user = qq_id(data.get("qq", ""))
                    member = names.members[ctx.group].get(user, {})
                    display = display_name(
                        member.get("card") or member.get("nickname") or user
                    )
                    mentions.append(
                        {
                            "token": f"m{len(mentions) + 1}",
                            "qq_id": user,
                            "display": display,
                            "position": index,
                            "source": "native_at",
                        }
                    )
                    if position < cutoff:
                        chunks.append(f"@{display}[{user}]")
                        original_length += len(display) + 1
                    position += len(" @" + user + " ")
            annotated = "".join(chunks).strip()
        if sub == "add-strict":
            if native and suffix is None:
                raise BusinessError("add-strict 请在末尾用 ;@成员,@成员 指定对象。")
            plans = [(parse_strict(body, time.time()), explicit or [ctx.actor], {})]
            rejected = []
            method = "strict"
        else:
            if not ctx.group:
                original_length = len(body)
            if not 1 <= original_length <= 200:
                raise BusinessError(
                    "/ddl add 正文须为1～200字（不含程序添加的QQ标注与候选表）。"
                )
            async with self.sessions.enter(ctx):
                await self.authorizer.authorize(
                    action.spec, ctx, action.arguments, gateway
                )
                self.check_writable(ctx)
                nodes = [
                    {
                        "node_id": "n1",
                        "author_id": ctx.actor,
                        "text": annotated,
                        "sent_at": ctx.received_at,
                        "local_time": datetime.fromtimestamp(
                            ctx.received_at, BEIJING
                        ).isoformat(),
                        "time_source": "submission",
                    }
                ]

                async def preflight():
                    await self.authorizer.authorize(
                        action.spec, ctx, action.arguments, gateway
                    )
                    self.check_writable(ctx)
                    if self.version(ctx.scope) != version:
                        raise BusinessError("本范围 DDL 已清除，创建已取消。")

                extracted = await self.extractor.extract(
                    nodes,
                    ctx.actor,
                    allowed,
                    time.time(),
                    "manual",
                    mentions,
                    explicit,
                    preflight=preflight,
                    on_submitted=on_submitted,
                    location=ctx.location,
                    actor_profile=await names.profile(ctx.actor, ctx.group),
                    member_profiles=[
                        await names.profile(user, ctx.group) for user in allowed
                    ]
                    if ctx.group
                    else (),
                    usage_context=UsageContext.from_command(ctx, "ddl.add"),
                )
                plans, rejected = extracted.plans, extracted.rejected
            method = "manual"
        if not plans:
            return "\n".join(rejected) or "未发现可添加的未过期 DDL。"
        await self.authorizer.authorize(action.spec, ctx, action.arguments, gateway)
        return await self.commit(ctx, gateway, names, plans, rejected, version, method)

    def check_writable(self, ctx):
        if self.failed:
            raise RuntimeError("DDL 存储不可用。")
        if ctx.group in self.readonly.readonly_groups:
            raise ReadonlyViolation(ctx.group)

    async def commit(
        self,
        ctx,
        gateway,
        names,
        plans,
        rejected,
        version,
        method,
        event=None,
        package=None,
        precommit=None,
        duplicates=(),
        updates=(),
    ):
        self.check_writable(ctx)
        if ctx.group:
            current = {
                str(item.get("user_id")) for item in await gateway.members(ctx.group)
            }
            if ctx.actor not in current:
                raise BusinessError("你已不在本群，未注册本次任务。")
            if any(user not in current for _, targets, _ in plans for user in targets):
                raise BusinessError("通知对象已离群，未注册本次任务。")
        async with self.data.lock:
            self.check_writable(ctx)
            if precommit:
                precommit()
            if method == "auto":
                if not {"autoanalysis", "ddl"} <= self.roles.effective(ctx.actor):
                    raise BusinessError("自动分析权限已撤销，未注册任务。")
            else:
                required = {"admin", "group.ddl"} if ctx.group else {"ddl"}
                if not (self.authorizer.effective(ctx) & required):
                    raise BusinessError("创建权限已变更，未注册任务。")
            if self.version(ctx.scope) != version:
                raise BusinessError(
                    "此范围的 DDL 已清除，尚未完成的创建已取消，请重新提交。"
                )
            now = time.time()
            proposals = []
            rejected = list(rejected)
            existing_ids = []
            valid_updates = []
            for change in updates:
                if ctx.group or change.previous["conversation"] != ctx.actor:
                    raise BusinessError("自动修改只能访问本人的个人 DDL。")
                self.guard.secrets.check(change.plan.title)
                if change.plan.deadline <= now:
                    rejected.append(
                        f"DDL #{change.previous['id']} 的截止时间已过，未修改。"
                    )
                    continue
                valid_updates.append(change)
            for previous in duplicates:
                current = self.data.get(ctx.scope, previous["id"])
                if current["deadline"] <= now:
                    continue
                if (
                    current["cancelled"]
                    or not current["targets"]
                    or current["deadline"] != previous["deadline"]
                ):
                    raise BusinessError("已有 DDL 在分析期间已变更，请重新提交消息。")
                existing_ids.append(current["id"])
            for plan, targets, source in plans:
                self.guard.secrets.check(plan.title)
                if plan.deadline <= now:
                    if method != "strict":
                        continue
                    raise BusinessError("截止时间已过，未注册本次任务。")
                signature = None
                if method == "auto":
                    signature = hashlib.sha256(
                        json.dumps(
                            [
                                ctx.actor,
                                plan.title.strip(),
                                plan.deadline,
                                source.get("requested_reminders", plan.reminders),
                                sorted(targets),
                            ],
                            ensure_ascii=False,
                        ).encode()
                    ).hexdigest()
                proposals.append((plan, targets, source, signature))
            identifiers = self.data.create_batch(
                ctx.scope,
                ctx.actor,
                proposals,
                method,
                now,
                event,
                package,
                existing_ids=existing_ids,
                updates=valid_updates,
            )
            tasks = [
                (self.data.get(ctx.scope, identifier), created)
                for identifier, created in identifiers
            ]
        updated_ids = {change.previous["id"] for change in valid_updates}
        lines = [
            (
                "已修改 "
                if task["id"] in updated_ids
                else "已创建 "
                if created
                else "已跳过重复录入，已有 "
            )
            + await show_task(task, names, time.time())
            for task, created in tasks
        ]
        return DeadlineConfirmation(
            "\n\n".join(lines + rejected) or "未发现可添加的未过期 DDL。",
            bool(valid_updates) or any(created for _, created in identifiers),
        )

    async def clear(self, action, gateway, names):
        ctx = action.context
        location, conversation = (
            action.resources["location"],
            action.resources["conversation"],
        )
        key = (ctx.platform, ctx.bot, location) + (
            (conversation,) if conversation is not None else ()
        )
        async with self.data.lock:
            self.check_writable(ctx)
            self.versions[key] = self.versions.get(key, 0) + 1
            cleared = self.data.clear(ctx.platform, ctx.bot, location, conversation)
        if location == "CHAT":
            count = sum(item["count"] for item in cleared.values())
            return DeadlineConfirmation(f"已清除你的 {count} 条个人 DDL。", count > 0)
        lines = []
        for group, entry in cleared.items():
            label = await names.group(group)
            state = "已通知"
            try:
                users = sorted(entry["targets"], key=int)
                text = f"[KakoBot] 群 {label} 的 {entry['count']} 条 DDL 通知已被移除。\n操作人：{await names.user(ctx.actor, group)}\n这些 DDL 将不再发送提醒。"
                for start in range(0, max(1, len(users)), 20):
                    await gateway.remind(group, users[start : start + 20], text)
            except ReadonlyViolation:
                state = "Readonly 拦截通知"
            except SecretViolation:
                state = "安全拦截通知"
            except Exception as exc:
                state = "通知失败"
                await self.guard.report_error(
                    gateway.bot, gateway.self_id, f"清除通知；群 {group}", exc
                )
            lines.append(f"群 {label}：{entry['count']} 条，{state}")
        return DeadlineConfirmation(
            "\n".join(lines) if lines else "没有可清除的 DDL。", ctx.group in cleared
        )
