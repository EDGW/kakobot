"""One-shot scheduling with exact-account routing and cancellation serialization."""

import asyncio
import logging
import time

from ...domain.security import SecretViolation
from ...infrastructure.messaging.onebot import ReadonlyViolation
from ...presentation.deadlines.details import participant_labels
from ...presentation.deadlines.image import render_reminder
from ...presentation.names import NameDirectory

logger = logging.getLogger("astrbot")


class DeadlineScheduler:
    def __init__(self, service, resolve_gateway, diagnostic_gateway):
        self.service, self.resolve_gateway, self.diagnostic_gateway = (
            service,
            resolve_gateway,
            diagnostic_gateway,
        )
        self.task = None

    def start(self):
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run(), name="kakobot-deadlines")

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def report(self, gateway, stage, exc):
        gateway = gateway or self.diagnostic_gateway()
        if gateway:
            await self.service.guard.report_error(
                gateway.bot, gateway.self_id, stage, exc
            )
        else:
            logger.error(
                "KakoBot %s failed (%s), no diagnostic route", stage, type(exc).__name__
            )

    async def _run(self):
        while True:
            try:
                await self.tick()
            except Exception as exc:
                self.service.failed = True
                await self.report(None, "DDL 存储/调度已停止", exc)
                return
            await asyncio.sleep(15)

    async def tick(self):
        service, data = self.service, self.service.data
        if service.failed:
            raise RuntimeError("DDL 存储不可用。")
        async with data.lock:
            nodes = data.due(time.time())
        for node in nodes:
            gateway = None
            async with data.lock:
                scope = data.scope_of(node)
                task = data.get(scope, node["ddl_id"])
                group = scope[3] if scope[2] == "GROUP" else ""
                if task["cancelled"] or not task["targets"] or self.expired(node, task):
                    data.finish(node, "skipped")
                    continue
                if group in service.readonly.readonly_groups:
                    data.finish(node, "skipped")
                    continue
                if not data.claim(node):
                    continue
                try:
                    gateway = self.resolve_gateway(scope[0], scope[1])
                    if gateway is None:
                        data.finish(node, "failed")
                        await self.report(
                            None,
                            f"DDL #{task['id']} 原平台/账号连接不可确认",
                            RuntimeError(f"原连接：{scope[0]}；机器人：{scope[1]}"),
                        )
                        continue
                    names = NameDirectory(gateway, service.guard)
                    users = task["targets"]
                    if group:
                        members = await gateway.members(group)
                        names.seed_members(group, members)
                        users = [user for user in users if user in names.members[group]]
                    if not users:
                        data.finish(node, "skipped")
                        continue
                    if not group and users != [task["conversation"]]:
                        raise RuntimeError("个人任务通知对象与所有者不一致，拒绝发送。")
                    labels = [task["title"]]
                    if group:
                        task["participant_label"] = await participant_labels(
                            task, names, group
                        )
                        labels.append(task["participant_label"])
                    service.guard.secrets.check(labels)
                    # Serialize reminder renders without taking the view semaphore
                    # while holding the cancellation lock.
                    png = await asyncio.to_thread(
                        render_reminder, task, time.time(), group=bool(group)
                    )
                    if self.expired(node, task):
                        data.finish(node, "skipped")
                        continue
                    service.guard.secrets.check(labels)
                    if group:
                        await gateway.remind_card(group, users, png)
                    else:
                        await gateway.send_image(png, user=task["conversation"])
                    data.finish(node, "sent")
                except ReadonlyViolation:
                    data.finish(node, "skipped")
                except SecretViolation as exc:
                    data.finish(node, "failed")
                    await self.report(gateway, "DDL 密钥拦截", exc)
                except Exception as exc:
                    data.finish(node, "uncertain")
                    await self.report(
                        gateway, f"DDL #{task['id']}；{scope[2]} {scope[3]}", exc
                    )

    @staticmethod
    def expired(node, task):
        now = time.time()
        return now - node["at"] > 60 or now > task["deadline"] + (
            60 if node["at"] == task["deadline"] else 0
        )
