"""Send a prebuilt documentation page for the current conversation type."""

import asyncio

from ...domain.errors import BusinessError


class HelpService:
    def __init__(self, images):
        self.images = images

    async def handle(self, action, gateway):
        ctx = action.context
        parts = action.arguments.strip().lower().split()
        if len(parts) > 1:
            raise BusinessError("帮助按功能组查询，用法：" + action.spec.usage)
        topic = parts[0].removeprefix("/") if parts else "help"
        data = await asyncio.to_thread(
            self.images.read,
            topic,
            ctx.location,
            super_help=action.spec.handler == "super_help",
        )
        await gateway.send_image(
            data, group=ctx.group, user="" if ctx.group else ctx.actor
        )
        if getattr(gateway, "capture_card_text", None):
            text = await asyncio.to_thread(
                self.images.text, topic, ctx.location,
                super_help=action.spec.handler == "super_help",
            )
            gateway.capture_card_text(text)
