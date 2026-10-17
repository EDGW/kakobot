"""AstrBot discovery entry. Event adaptation and all implementation live in src/."""

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .src.adapters.astrbot import AstrBotAdapter, InputFilter


class KakoBotPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.adapter = AstrBotAdapter(context, config)

    async def initialize(self):
        await self.adapter.initialize()

    @filter.on_platform_loaded()
    async def platforms_loaded(self):
        await self.adapter.platforms_loaded()

    @filter.on_astrbot_loaded()
    async def astrbot_loaded(self):
        await self.adapter.astrbot_loaded()

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.event_message_type(
        filter.EventMessageType.GROUP_MESSAGE | filter.EventMessageType.PRIVATE_MESSAGE
    )
    @filter.custom_filter(InputFilter, priority=1000)
    async def handle_message(self, event: AstrMessageEvent):
        await self.adapter.handle_message(event)

    async def terminate(self):
        await self.adapter.terminate()
