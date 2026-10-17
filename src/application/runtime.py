"""Composition root; startup migration finishes before services become available."""

import asyncio
import time

import httpx

from ..infrastructure.conversations import ConversationStore
from ..infrastructure.deadlines import DeadlineStore
from ..infrastructure.migration import migrate
from ..infrastructure.model import ModelClient
from ..infrastructure.onebot import OutboundGuard
from ..infrastructure.preferences import PreferenceStore
from ..infrastructure.readonly import ReadonlyPolicy
from ..infrastructure.roles import RoleStore
from ..infrastructure.usage import UsageStore
from .analysis import AutomaticAnalysis
from .announcement_service import AnnouncementService
from .authorization import Authorizer
from .cost_service import CostService
from .deadline_service import DeadlineService
from .dispatcher import Dispatcher
from .extraction import Extractor
from .role_service import RoleService
from .scheduler import DeadlineScheduler
from .sessions import UserSessions
from .summary_service import SummaryService


class Runtime:
    def __init__(self, directory, config, resolve_gateway, diagnostic_gateway):
        migrate(directory)
        self.roles = RoleStore(
            directory / "roles.json", str(config.get("super_user", "000000000"))
        )
        self.readonly = ReadonlyPolicy(
            directory / "readonly.json", self.roles.super_user
        )
        self.guard = OutboundGuard(self.readonly, config)
        preferences = PreferenceStore(directory / "ddl_preferences.json")
        self.data = DeadlineStore(directory / "deadlines.sqlite3", time.time())
        self.usage = UsageStore(directory / "usage.sqlite3", time.time())
        self.conversations = ConversationStore(directory / "conversations.sqlite3")
        self.conversations.seed_private(
            self.data.private_contacts() | preferences.owners()
        )
        self.http = httpx.AsyncClient()
        self.model = ModelClient(config, self.http, self.usage)
        sessions = UserSessions()
        authorizer = Authorizer(self.roles)
        deadlines = DeadlineService(
            self.data,
            self.roles,
            self.readonly,
            self.guard,
            Extractor(self.model),
            authorizer,
            sessions,
            preferences,
        )
        analysis = AutomaticAnalysis(
            self.roles, config, deadlines, sessions, self.model
        )
        self.dispatcher = Dispatcher(
            self.roles,
            self.readonly,
            self.guard,
            authorizer,
            RoleService(self.roles),
            deadlines,
            SummaryService(self.model, sessions, authorizer, self.guard),
            analysis,
            CostService(self.usage),
            AnnouncementService(self.roles, self.conversations, self.guard),
        )
        self.scheduler = DeadlineScheduler(
            deadlines, resolve_gateway, diagnostic_gateway
        )
        self.active = set()
        self.closing = False

    async def handle(self, ctx, gateway):
        if self.closing:
            return
        self.observe(ctx)
        task = asyncio.current_task()
        self.active.add(task)
        try:
            await self.dispatcher.handle(ctx, gateway)
        finally:
            self.active.discard(task)

    def observe(self, ctx):
        if not self.closing:
            self.conversations.observe(ctx)

    async def close(self):
        self.closing = True
        await self.scheduler.stop()
        for task in self.active:
            task.cancel()
        if self.active:
            await asyncio.gather(*list(self.active), return_exceptions=True)
        self.guard.uninstall()
        self.data.close()
        self.usage.close()
        self.conversations.close()
        await self.http.aclose()
