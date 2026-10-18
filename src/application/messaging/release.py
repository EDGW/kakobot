"""Expose installed version text and changelog cards to all conversations."""

import asyncio

from ...domain.errors import BusinessError


class ReleaseService:
    def __init__(self, store):
        self.store = store

    async def handle(self, action, gateway):
        if action.arguments.strip():
            raise BusinessError("用法：" + action.spec.usage)
        if action.spec.handler == "version":
            version = await asyncio.to_thread(self.store.version)
            return "KakoBot " + version
        ctx = action.context
        data = await asyncio.to_thread(self.store.changelog)
        await gateway.send_image(
            data, group=ctx.group, user="" if ctx.group else ctx.actor
        )
