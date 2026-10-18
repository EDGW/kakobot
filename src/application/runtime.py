"""Composition root; startup migration finishes before services become available."""

import asyncio
import time

import httpx

from ..infrastructure.messaging.help_images import HelpImageStore
from ..infrastructure.messaging.onebot import OutboundGuard
from ..infrastructure.messaging.release_info import ReleaseInfoStore
from ..infrastructure.model import ModelClient
from ..infrastructure.storage.access.readonly import ReadonlyPolicy
from ..infrastructure.storage.access.roles import RoleStore
from ..infrastructure.storage.audit import AuditStore
from ..infrastructure.storage.broadcasts.conversations import ConversationStore
from ..infrastructure.storage.broadcasts.upgrades import UpgradeStore
from ..infrastructure.storage.deadlines.preferences import PreferenceStore
from ..infrastructure.storage.deadlines.tasks import DeadlineStore
from ..infrastructure.storage.migration import migrate
from ..infrastructure.storage.requests import RequestStore
from ..infrastructure.storage.usage import UsageStore
from .authorization import Authorizer
from .deadlines.analysis import AutomaticAnalysis
from .deadlines.extraction import Extractor
from .deadlines.management import SuperDeadlineService
from .deadlines.scheduler import DeadlineScheduler
from .deadlines.service import DeadlineService
from .dispatcher import Dispatcher
from .group_discuss.commands import BusinessCommands
from .group_discuss.personal import PersonalDiscussService
from .group_discuss.service import DiscussService
from .management.costs import CostService
from .management.requests import RequestService
from .messaging.announcements import AnnouncementService
from .messaging.help import HelpService
from .messaging.release import ReleaseService
from .messaging.summary import SummaryService
from .messaging.upgrade_announcements import UpgradeAnnouncements
from .roles.management import SuperRoleService
from .roles.service import RoleService
from .sessions import UserSessions


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
        self.audit = AuditStore(directory / "management.sqlite3")
        self.requests_data = RequestStore(directory / "requests.sqlite3")
        self.requests = RequestService(
            self.requests_data, self.roles, self.guard, self.audit
        )
        self.conversations.seed_private(
            self.data.private_contacts() | preferences.owners()
        )
        self.http = httpx.AsyncClient()
        self.model = ModelClient(config, self.http, self.usage)
        self.discuss = DiscussService(
            directory, config, self.roles, self.guard, self.http, self.data
        )
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
        announcements = AnnouncementService(self.roles, self.conversations, self.guard)
        self.upgrade_announcements = UpgradeAnnouncements(
            announcements, UpgradeStore(self.conversations), resolve_gateway
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
            announcements,
            SuperRoleService(self.roles, self.audit, self.readonly),
            SuperDeadlineService(deadlines, self.audit),
            self.requests,
            HelpService(HelpImageStore()),
            ReleaseService(ReleaseInfoStore()),
        )
        self.discuss.command_executor = BusinessCommands(self.dispatcher)
        self.personal_discuss = PersonalDiscussService(self.discuss)
        self.scheduler = DeadlineScheduler(
            deadlines, resolve_gateway, diagnostic_gateway
        )
        self.active = set()
        self.closing = False

    def candidate(self, ctx):
        """Single admission gate shared with transport adapters."""
        return (
            self.personal_discuss.candidate(ctx)
            or self.discuss.candidate(ctx)
            or self.dispatcher.should_handle(ctx)
        )

    async def handle(self, ctx, gateway):
        if self.closing:
            return
        self.observe(ctx)
        task = asyncio.current_task()
        self.active.add(task)
        try:
            if self.personal_discuss.candidate(ctx):
                return await self.personal_discuss.handle(ctx, gateway)
            if self.discuss.candidate(ctx) and await self.discuss.handle(ctx, gateway):
                return True
            if not self.dispatcher.should_handle(ctx):
                return False
            await self.dispatcher.handle(ctx, gateway)
            return True
        finally:
            self.active.discard(task)

    def observe(self, ctx):
        if not self.closing:
            self.conversations.observe(ctx)

    async def handle_request(self, platform, raw, gateway):
        if self.closing:
            return
        task = asyncio.current_task()
        self.active.add(task)
        try:
            await self.requests.receive(platform, raw, gateway)
        finally:
            self.active.discard(task)

    async def close(self):
        self.closing = True
        await self.scheduler.stop()
        await self.upgrade_announcements.stop()
        for task in self.active:
            task.cancel()
        if self.active:
            await asyncio.gather(*list(self.active), return_exceptions=True)
        self.guard.uninstall()
        self.data.close()
        self.usage.close()
        self.conversations.close()
        self.audit.close()
        self.requests_data.close()
        self.discuss.store.close()
        await self.http.aclose()
