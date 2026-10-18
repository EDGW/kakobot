"""Deliver upgrade announcements once the original bot account is connected."""

import asyncio
import logging

from ...infrastructure.storage.broadcasts.updates import load_update
from ...infrastructure.storage.migration import VERSION
from ...presentation.announcements import format_announcement

logger = logging.getLogger("astrbot")


class UpgradeAnnouncements:
    def __init__(self, announcements, store, resolve_gateway):
        self.announcements = announcements
        self.store = store
        self.resolve_gateway = resolve_gateway
        self.task = None
        self.store.prepare(VERSION, self.eligible)

    def eligible(self, user):
        return "autoanalysis" in self.announcements.roles.effective(user)

    def start(self):
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(
                self._run(), name="kakobot-upgrade-announcements"
            )

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def _run(self):
        while True:
            try:
                await self.tick()
            except Exception as exc:
                logger.error("KakoBot 升级公告暂停发送（%s）", type(exc).__name__)
            if not self.store.pending(VERSION):
                return
            await asyncio.sleep(15)

    async def tick(self):
        pending = self.store.pending(VERSION)
        if not pending:
            return
        text = format_announcement(load_update())
        announcements = self.announcements
        announcements.guard.secrets.check(text)
        for recipient in pending:
            platform, bot, user = recipient
            gateway = self.resolve_gateway(platform, bot)
            if gateway is None:
                continue
            lock = announcements.locks.setdefault((platform, bot), asyncio.Lock())
            async with lock:
                if not self.eligible(user) or not announcements.conversations.accepts(
                    platform, bot, user
                ):
                    self.store.finish(VERSION, recipient, "skipped")
                    continue
                if not self.store.claim(VERSION, recipient):
                    continue
                try:
                    await gateway.send(text=text, user=user)
                except Exception as exc:
                    self.store.finish(VERSION, recipient, "failed")
                    await announcements.guard.report_error(
                        gateway.bot, bot, f"升级公告；接收人 {user}", exc
                    )
                else:
                    self.store.finish(VERSION, recipient, "sent")
                await asyncio.sleep(0.5)
