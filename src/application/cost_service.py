"""Super-only cost queries with optional QQ account or group filters."""

import time

from ..domain.context import qq_id
from ..domain.errors import BusinessError
from ..presentation.costs import render_cost_report


class CostService:
    def __init__(self, usage):
        self.usage = usage

    async def handle(self, action, names):
        parts = action.arguments.split()
        filters = {}
        if parts:
            if len(parts) != 2 or parts[0].lower() not in {"user", "group"}:
                raise BusinessError("用法：" + action.spec.usage)
            filters["actor" if parts[0].lower() == "user" else "group"] = qq_id(
                parts[1]
            )
        ctx, now = action.context, time.time()
        report = self.usage.report(ctx.platform, ctx.bot, now, **filters)
        return await render_cost_report(report, ctx.bot, now, names, **filters)
