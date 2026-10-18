"""Route friend/group requests to Super and process explicit approvals only."""

import asyncio
import time

from ...domain.context import qq_id
from ...domain.deadlines import local_time
from ...domain.errors import BusinessError
from ...domain.management import arguments, csv, page_number
from ...presentation.names import NameDirectory

KINDS = {
    ("friend", ""): "好友申请",
    ("group", "add"): "加群申请",
    ("group", "invite"): "入群邀请",
}
STATES = {
    "pending": "待处理",
    "processing": "处理中",
    "approved": "已同意",
    "denied": "已拒绝",
    "failed": "接口拒绝/失败",
    "uncertain": "结果不确定",
}


class RequestService:
    def __init__(self, store, roles, guard, audit):
        self.store, self.roles, self.guard, self.audit = store, roles, guard, audit
        self.lock = asyncio.Lock()
        self.incoming_lock = asyncio.Lock()

    async def receive(self, platform, raw, gateway):
        kind = str(raw.get("request_type", ""))
        subtype = str(raw.get("sub_type", "")) if kind == "group" else ""
        if raw.get("post_type") != "request" or (kind, subtype) not in KINDS:
            return
        flag = raw.get("flag")
        if not isinstance(flag, str) or not flag or len(flag) > 4096:
            raise ValueError("申请事件缺少有效 flag，无法安全审批。")
        bot, user = qq_id(raw.get("self_id")), qq_id(raw.get("user_id"))
        if bot != gateway.self_id:
            raise ValueError("申请事件的机器人账号与路由不一致。")
        group = qq_id(raw.get("group_id")) if kind == "group" else ""
        comment = self.guard.secrets.redact(str(raw.get("comment") or ""))
        async with self.incoming_lock:
            item = self.store.add(
                platform, bot, kind, subtype, flag, user, group, comment, time.time()
            )
            if (
                item["notified"]
                or item["state"] != "pending"
                or self.roles.super_user == "000000000"
            ):
                return
            names = NameDirectory(gateway, self.guard)
            text = "[KakoBot] 新申请\n" + await self.describe(item, names)
            text += f"\n/super request approve {item['id']}\n/super request deny {item['id']}"
            self.guard.secrets.check(text)
            await gateway.send(user=self.roles.super_user, text=text)
            self.store.notified(item["id"])

    async def describe(self, item, names):
        user = await names.user(item["user_id"])
        group = (
            "\n群：" + await names.group(item["group_id"]) if item["group_id"] else ""
        )
        return (
            f"申请 #{item['id']} · {KINDS[item['kind'], item['subtype']]} · {STATES[item['state']]}"
            f"\n账号：{item['bot']}\n申请人/邀请人：{user}{group}"
            f"\n收到时间：{local_time(item['received'])}\n附言：{self.guard.secrets.redact(item['comment']) or '无'}"
            + (
                "\n处理说明：" + self.guard.secrets.redact(item["error"])
                if item["error"]
                else ""
            )
        )

    async def handle(self, action, gateway, names):
        ctx, sub = action.context, action.spec.subcommand.split()[-1]
        values, opts = arguments(
            action.arguments, options=("page",) if sub == "list" else (), flags=()
        )
        if len(values) > 1 or (not values and sub != "list"):
            raise BusinessError("用法：" + action.spec.usage)
        if sub == "list":
            state = values[0].lower() if values else "pending"
            if state not in set(STATES) | {"all"}:
                raise BusinessError("未知申请状态。")
            rows = self.store.list(ctx.platform, ctx.bot, state)
            page = page_number(opts.get("page", "1"))
            pages = max(1, (len(rows) + 19) // 20)
            if page > pages:
                raise BusinessError(f"页码超出范围，共{pages}页。")
            details = [
                await self.describe(row, names)
                for row in rows[(page - 1) * 20 : page * 20]
            ]
            return f"申请（{len(rows)}项，第{page}/{pages}页，仅当前机器人）：\n" + (
                "\n\n".join(details) or "（空）"
            )
        async with self.lock:
            if "super" not in self.roles.effective(ctx.actor):
                raise BusinessError("Super 权限已变更。")
            if values[0].lower() == "all":
                rows = self.store.list(ctx.platform, ctx.bot)
            else:
                identifiers = csv(values[0], lambda value: int(qq_id(value)))
                if any(identifier > 9223372036854775807 for identifier in identifiers):
                    raise BusinessError("申请编号无效。")
                rows = [
                    self.store.get(ctx.platform, ctx.bot, identifier)
                    for identifier in identifiers
                ]
                if any(row is None for row in rows):
                    raise BusinessError("某个编号不属于当前机器人，未处理任何申请。")
                if any(row["state"] != "pending" for row in rows):
                    raise BusinessError("仅能处理 pending 申请；未处理任何申请。")
            counts = {"approved": 0, "denied": 0, "failed": 0, "uncertain": 0}
            details = []
            for item in rows:
                if "super" not in self.roles.effective(ctx.actor):
                    details.append("Super 权限变更，已停止后续处理。")
                    break
                approve = sub == "approve"
                desired = "approved" if approve else "denied"
                # Keep the opaque flag out of request summaries and audit records.
                public = {key: value for key, value in item.items() if key != "flag"}
                ticket = self.audit.prepare(
                    ctx, "request " + sub, public, {"id": item["id"], "state": desired}
                )
                if not self.store.claim(item["id"], ctx.actor, time.time()):
                    self.audit.finish(ticket, "skipped")
                    continue
                params = {"flag": item["flag"], "approve": approve, "self_id": ctx.bot}
                if item["kind"] == "group":
                    params["sub_type"] = item["subtype"]
                try:
                    result = await gateway.bot.call_action(
                        "set_" + item["kind"] + "_add_request", **params
                    )
                    if isinstance(result, dict) and (
                        result.get("status") == "failed"
                        or result.get("retcode", 0) not in {0, None}
                    ):
                        raise RuntimeError("OneBot 未确认申请处理成功。")
                except asyncio.CancelledError:
                    self.store.finish(
                        item["id"], "uncertain", "操作被中断，未自动重试。"
                    )
                    self.audit.finish(ticket, "uncertain")
                    raise
                except Exception as exc:
                    state = (
                        "failed"
                        if type(exc).__name__ == "ActionFailed"
                        else "uncertain"
                    )
                    self.store.finish(
                        item["id"], state, "接口未成功确认；完整错误已通知 Super。"
                    )
                    self.audit.finish(ticket, state)
                    counts[state] += 1
                    details.append(f"#{item['id']}：{STATES[state]}")
                    await self.guard.report_error(
                        gateway.bot, ctx.bot, f"申请 #{item['id']}；{sub}", exc
                    )
                else:
                    self.store.finish(item["id"], desired)
                    self.audit.finish(ticket)
                    counts[desired] += 1
                    details.append(f"#{item['id']}：{STATES[desired]}")
            return (
                "申请处理完成："
                + "，".join(
                    f"{STATES[state]}{count}项" for state, count in counts.items()
                )
                + "\n"
                + ("\n".join(details) or "没有 pending 申请。")
            )
