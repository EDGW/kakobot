"""Explicit Super DDL management, separated from owner-authorized AI updates."""

import copy
import json
import time
from dataclasses import replace

from ..domain.context import qq_id
from ..domain.deadlines import _timestamp, local_time, make_plan
from ..domain.errors import BusinessError
from ..domain.management import (
    arguments,
    csv,
    page_number,
    reference,
    reminder_times,
    target_scope,
    task_reference,
    time_filter,
)
from ..infrastructure.deadline_management import DeadlineManagementStore
from ..infrastructure.onebot import ReadonlyViolation
from ..presentation.deadlines import show_task


class SuperDeadlineService:
    def __init__(self, service, audit):
        self.service, self.audit = service, audit
        self.store = DeadlineManagementStore(service.data)

    async def handle(self, action, gateway, names):
        service, ctx = self.service, action.context
        service.check_writable(ctx)
        sub = action.spec.subcommand.split()[-1]
        options = {
            "list": ("creator", "target", "status", "from", "to", "page"),
            "show": (),
            "view": (),
            "remove": (),
            "clear": (),
            "edit": (
                "title",
                "due",
                "remind",
                "targets",
                "targets-add",
                "targets-remove",
            ),
        }[sub]
        values, opts = arguments(
            action.arguments,
            options=options,
            flags=("dry-run",) if sub in {"edit", "remove", "clear"} else (),
        )
        if len(values) > 1 or (
            not values and sub in {"edit", "remove", "clear", "show"}
        ):
            raise BusinessError("用法：" + action.spec.usage)
        value = values[0] if values else "this"
        if sub == "view":
            scope = target_scope(value, ctx)
            await service.send_view(
                ctx, gateway, names, scope=scope, require_member=False
            )
            return None
        if sub == "show":
            scope, identifier = task_reference(value, ctx)
            async with service.data.lock:
                task = service.data.get(scope, identifier)
            return reference(task) + "\n" + await show_task(task, names, time.time())
        if sub == "list":
            return await self.list(value, opts, ctx, names)
        if sub == "edit" and not (set(opts) - {"dry-run"}):
            raise BusinessError("edit 至少需要一个修改字段。")
        target_options = set(opts) & {"targets", "targets-add", "targets-remove"}
        if "targets" in target_options and len(target_options) > 1:
            raise BusinessError(
                "--targets 不能与 --targets-add/--targets-remove 同用。"
            )
        for key in target_options:
            opts[key] = csv(opts[key], qq_id, limit=20)
        if set(opts.get("targets-add", [])) & set(opts.get("targets-remove", [])):
            raise BusinessError("同一通知对象不能同时添加和移除。")
        clear_scope = target_scope(value, ctx) if sub == "clear" else None
        refs = (
            None
            if sub == "clear"
            else csv(value, lambda item: task_reference(item, ctx))
        )
        # Membership requests happen before the DB lock; all data is re-read inside it.
        scopes = {clear_scope} if clear_scope else {scope for scope, _ in refs}
        for scope in scopes:
            if scope[2] == "GROUP":
                self.check_scope(scope)
                if target_options:
                    names.seed_members(scope[3], await gateway.members(scope[3]))
        async with service.data.lock:
            service.check_writable(ctx)
            if "super" not in service.roles.effective(ctx.actor):
                raise BusinessError("Super 权限已变更。")
            for scope in scopes:
                self.check_scope(scope)
            now = time.time()
            if sub == "clear":
                refs = self.store.search(ctx, clear_scope, {}, now)
            changes = []
            for scope, identifier in refs:
                old = service.data.get(scope, identifier)
                if sub == "edit" and (
                    old["cancelled"] or not old["targets"] or old["deadline"] <= now
                ):
                    raise BusinessError(
                        reference(old) + " 已取消、退订或过期，不能修改。"
                    )
                if sub != "edit" and (old["cancelled"] or not old["targets"]):
                    continue
                new, reschedule = self.change(old, sub, opts, now, names)
                if (
                    any(
                        old[key] != new[key]
                        for key in (
                            "title",
                            "deadline",
                            "targets",
                            "cancelled",
                            "source",
                        )
                    )
                    or reschedule
                ):
                    changes.append((old, new, reschedule))
            preview = [
                self.describe(old, new, reschedule) for old, new, reschedule in changes
            ]
            if opts.get("dry-run"):
                return f"预览（未保存），{len(changes)}项：\n" + (
                    "\n\n".join(preview) or "无变更。"
                )
            if not changes and sub != "clear":
                return "无可变更的 DDL。"
            before = [old for old, _, _ in changes]
            after = [new for _, new, _ in changes]
            service.guard.secrets.check([before, after])
            ticket = self.audit.prepare(ctx, "ddl " + sub, before, after)
            try:
                self.store.apply(changes, now)
            except Exception:
                self.audit.finish(ticket, "failed")
                raise
            # Invalidate AI work that was prepared against the old scope contents.
            for scope in scopes:
                service.versions[scope] = service.versions.get(scope, 0) + 1
            self.audit.finish(ticket)
        delivery = await self.notify(ctx, gateway, names, changes)
        return (
            f"已保存 {len(changes)} 项 DDL 变更：\n"
            + ("\n\n".join(preview) or "没有有效任务；已取消本会话尚未完成的创建。")
            + delivery
        )

    def check_scope(self, scope):
        if scope[2] == "GROUP" and scope[3] in self.service.readonly.readonly_groups:
            raise BusinessError(f"群 {scope[3]} 为 Readonly，未修改任何任务。")

    def change(self, old, sub, opts, now, names):
        new = copy.deepcopy(old)
        if sub != "edit":
            new.update(cancelled=1, targets=[])
            for node in new["reminders"]:
                if node["state"] == "pending":
                    node["state"] = "cancelled"
            return new, False
        deadline = _timestamp(opts["due"]) if "due" in opts else old["deadline"]
        title = opts.get("title", old["title"])
        self.service.guard.secrets.check(title)
        times = [node["at"] for node in old["reminders"] if node["state"] == "pending"]
        reschedule = "remind" in opts or deadline != old["deadline"]
        if "remind" in opts:
            times = reminder_times(opts["remind"], deadline)
        elif reschedule:
            times = [at + deadline - old["deadline"] for at in times]
        plan = make_plan(title, deadline, times, now)
        target_options = set(opts) & {"targets", "targets-add", "targets-remove"}
        if old["location"] == "CHAT" and target_options:
            raise BusinessError("个人 DDL 只通知所属用户，不能修改通知对象。")
        targets = set(opts.get("targets", old["targets"]))
        targets.update(opts.get("targets-add", []))
        targets.difference_update(opts.get("targets-remove", []))
        if target_options:
            if old["bot"] in targets or len(targets) > 20:
                raise BusinessError("每条 DDL 最多20位通知对象，不能通知机器人。")
            if not targets <= set(names.members[old["conversation"]]):
                raise BusinessError(reference(old) + " 的通知对象不全在群内。")
        new.update(
            title=plan.title,
            deadline=plan.deadline,
            targets=sorted(targets, key=int),
            cancelled=int(not targets),
            pending_times=list(plan.reminders),
        )
        if reschedule:
            source = json.loads(old["source"])
            source.update(
                requested_reminders=times,
                notify_on_deadline=deadline in times,
                reminder_source="super",
            )
            new["source"] = json.dumps(source, ensure_ascii=False)
        if reschedule or not targets:
            nodes = {node["at"]: dict(node) for node in old["reminders"]}
            for node in nodes.values():
                if node["state"] == "pending":
                    node["state"] = "cancelled"
            if targets:
                for at in plan.reminders:
                    if at not in nodes or nodes[at]["state"] in {
                        "pending",
                        "cancelled",
                    }:
                        nodes[at] = {"at": at, "state": "pending"}
            new["reminders"] = [nodes[at] for at in sorted(nodes)]
            new["pending_times"] = [
                node["at"] for node in new["reminders"] if node["state"] == "pending"
            ]
        return new, reschedule

    @staticmethod
    def describe(old, new, reschedule):
        lines = [reference(old) + " " + old["title"]]
        if new["cancelled"] or not new["targets"]:
            return lines[0] + "：已取消全部未发通知。"
        if new["title"] != old["title"]:
            lines.append("名称：" + old["title"] + " → " + new["title"])
        if new["deadline"] != old["deadline"]:
            lines.append(
                "截止："
                + local_time(old["deadline"])
                + " → "
                + local_time(new["deadline"])
            )
        if set(new["targets"]) != set(old["targets"]):
            lines.append(
                "通知对象："
                + ",".join(old["targets"])
                + " → "
                + ",".join(new["targets"])
            )
        if reschedule:
            lines.append(
                "新提醒："
                + (
                    "、".join(local_time(at) for at in new["pending_times"])
                    or "无待发提醒"
                )
            )
        return "\n".join(lines)

    async def list(self, value, opts, ctx, names):
        scope = target_scope(value, ctx, allow_all=True)
        if opts.get("status", "active") not in {
            "active",
            "expired",
            "cancelled",
            "all",
        }:
            raise BusinessError("--status 须为 active、expired、cancelled 或 all。")
        for key in ("creator", "target"):
            if key in opts:
                opts[key] = qq_id(opts[key])
        for key in ("from", "to"):
            if key in opts:
                opts[key] = time_filter(opts[key])
        if "from" in opts and "to" in opts and opts["from"] > opts["to"]:
            raise BusinessError("--from 不能晚于 --to。")
        page = page_number(opts.get("page", "1"))
        async with self.service.data.lock:
            now = time.time()
            refs = self.store.search(ctx, scope, opts, now)
            pages = max(1, (len(refs) + 19) // 20)
            if page > pages:
                raise BusinessError(f"页码超出范围，共{pages}页。")
            tasks = [
                self.service.data.get(target, identifier)
                for target, identifier in refs[(page - 1) * 20 : page * 20]
            ]
        details = [
            reference(task) + "\n" + await show_task(task, names, now) for task in tasks
        ]
        return f"DDL（{len(refs)}项，第{page}/{pages}页）：\n" + (
            "\n\n".join(details) or "（空）"
        )

    async def notify(self, ctx, gateway, names, changes):
        grouped = {}
        for old, new, reschedule in changes:
            scope = self.service.data.scope_of(old)
            entry = grouped.setdefault(scope, {"users": set(), "lines": []})
            entry["users"].update(old["targets"] + new["targets"])
            entry["lines"].append(self.describe(old, new, reschedule))
        results = []
        for scope, entry in grouped.items():
            group = scope[3] if scope[2] == "GROUP" else ""
            try:
                text = "[KakoBot] Super 已调整 DDL：\n" + "\n\n".join(entry["lines"])
                self.service.guard.secrets.check(text)
                if group:
                    members = {
                        str(item["user_id"]) for item in await gateway.members(group)
                    }
                    users = sorted(entry["users"] & members, key=int)
                    for start in range(0, max(1, len(users)), 20):
                        await gateway.remind(
                            group,
                            users[start : start + 20],
                            text if start == 0 else "以上 DDL 通知已调整。",
                        )
                else:
                    await gateway.send(user=scope[3], text=text)
                target_ctx = replace(
                    ctx, group=group, actor=ctx.actor if group else scope[3]
                )
                await self.service.send_view(
                    target_ctx, gateway, names, scope=scope, require_member=False
                )
            except ReadonlyViolation:
                results.append(scope[3] + "：Readonly 拦截通知。")
            except Exception as exc:
                results.append(scope[3] + "：数据已保存，通知或卡片发送失败。")
                await self.service.guard.report_error(
                    gateway.bot, ctx.bot, "Super DDL 变更通知；" + scope[3], exc
                )
        return (
            "\n" + "\n".join(results)
            if results
            else "\n已向受影响会话发送变更通知与卡片。"
            if changes
            else ""
        )
