"""Serialize each user's AI work and bound automatically queued packages."""

import asyncio
from contextlib import asynccontextmanager

from ..domain.errors import BusinessError


class UserSessions:
    def __init__(self):
        self.locks, self.queued, self.users = {}, {}, {}
        self.total = 0
        self.automatic_slots = asyncio.Semaphore(2)

    @asynccontextmanager
    async def enter(self, ctx, automatic=False):
        key = ctx.platform, ctx.bot, ctx.actor
        if automatic:
            if self.queued.get(key, 0) >= 3 or self.total >= 20:
                raise BusinessError("自动分析排队已满，请稍后重新提交。")
            self.queued[key] = self.queued.get(key, 0) + 1
            self.total += 1
        lock = self.locks.setdefault(key, asyncio.Lock())
        self.users[key] = self.users.get(key, 0) + 1
        waiting = automatic
        try:
            async with lock:
                if automatic:
                    async with self.automatic_slots:
                        self.queued[key] -= 1
                        self.total -= 1
                        waiting = False
                        yield
                else:
                    yield
        finally:
            if waiting:
                self.queued[key] -= 1
                self.total -= 1
            self.users[key] -= 1
            if not self.users[key]:
                self.users.pop(key)
                self.locks.pop(key, None)
                self.queued.pop(key, None)
