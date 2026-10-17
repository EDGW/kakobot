"""Extensible private automatic analysis with bounded admission and dedupe."""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime

from ..domain.analysis import referenced_deadlines
from ..domain.deadlines import BEIJING
from ..domain.errors import BusinessError
from ..infrastructure.messages import MessageExpander


@dataclass(frozen=True)
class AnalysisTask:
    task_type: str
    extractor: object
    apply: object


class AutomaticAnalysis:
    def __init__(self, roles, config, deadlines, sessions, model):
        self.roles, self.config, self.deadlines, self.sessions, self.model = (
            roles,
            config,
            deadlines,
            sessions,
            model,
        )
        self.tasks = {"ddl": AnalysisTask("ddl", deadlines.extractor, deadlines.commit)}

    def enabled(self, ctx):
        return (
            not ctx.group
            and "autoanalysis" in self.roles.effective(ctx.actor)
            and ctx.actor
            not in {
                str(user) for user in self.config.get("autoanalysis_disabled_users", [])
            }
            and any(
                name in self.tasks
                for name in self.config.get("enabled_analysis_tasks", ["ddl"])
            )
        )

    async def handle(self, ctx, gateway, names, on_submitted=None):
        if not self.enabled(ctx):
            raise BusinessError("自动分析当前未启用。")
        results = []
        async with self.sessions.enter(ctx, automatic=True):
            if not self.enabled(ctx):
                raise BusinessError("自动分析资格已变更，未处理消息。")
            for name in self.config.get("enabled_analysis_tasks", ["ddl"]):
                task = self.tasks.get(name)
                if task is None:
                    continue
                result = await self._run(task, ctx, gateway, names, on_submitted)
                results.extend(result)
        return results

    async def _run(self, task, ctx, gateway, names, on_submitted=None):
        data = self.deadlines.data
        if not ctx.message_id:
            raise BusinessError("本消息缺少可靠的事件ID，无法安全去重，请重新发送。")
        key = (ctx.platform, ctx.bot, ctx.actor, ctx.message_id, task.task_type)
        async with data.lock:
            if not data.begin_event(key):
                return []
        version = self.deadlines.version(ctx.scope)

        def check_current():
            if not self.enabled(ctx):
                raise BusinessError("自动分析资格已变更，未注册任务。")
            if self.deadlines.version(ctx.scope) != version:
                raise BusinessError("个人 DDL 已清除，此次分析已取消。")

        try:
            nodes = await MessageExpander(
                gateway, self.model.secrets, ctx.received_at, readable_only=True
            ).expand(ctx.segments, ctx.actor)
            if not any("".join(node["text_segments"]).strip() for node in nodes):
                raise BusinessError(
                    "消息中没有可直接读取的文字；历史回复引用不追查，图片、音频或文件请先提供文字内容。"
                )
            # Source timestamps participate when available; fresh ordinary text uses receipt time.
            normalized = [
                {
                    key: node[key]
                    for key in (
                        "parent_id",
                        "author_id",
                        "sent_at",
                        "time_source",
                        "text",
                        "native_mentions",
                        "omitted_reply_count",
                    )
                }
                for node in nodes
                if node["text"]
            ]
            for node in normalized:
                if node["time_source"] == "submission":
                    node["sent_at"] = datetime.fromtimestamp(
                        node["sent_at"], BEIJING
                    ).strftime("%Y-%m-%d")
            preference = self.deadlines.preferences.get(ctx)
            direct_text = "".join(nodes[0]["text_segments"])
            digest = hashlib.sha256(
                json.dumps(
                    [normalized, preference], ensure_ascii=False, sort_keys=True
                ).encode()
            ).hexdigest()
            # An explicit task instruction must be evaluated against current data,
            # even if the owner sent the same wording on a different occasion.
            package = (
                (ctx.platform, ctx.bot, ctx.actor, task.task_type, digest)
                if not referenced_deadlines(direct_text)
                else None
            )
            async with data.lock:
                check_current()
                previous = (
                    data.package_result(package, ctx.scope, time.time())
                    if package
                    else None
                )
                if previous is not None:
                    data.create_batch(
                        ctx.scope, ctx.actor, [], "auto", time.time(), key
                    )
            if previous is not None:
                return [
                    "此消息包已处理，未重复注册。已有 DDL："
                    + (", ".join(f"#{identifier}" for identifier in previous) or "无")
                ]
            if not self.enabled(ctx):
                raise BusinessError("自动分析资格已变更，未调用模型。")

            async def preflight():
                if not self.enabled(ctx):
                    raise BusinessError("自动分析资格已变更，未调用模型。")
                if self.deadlines.version(ctx.scope) != version:
                    raise BusinessError("个人 DDL 已清除，此次分析已取消。")

            async with data.lock:
                check_current()
                existing = data.list(ctx.scope, time.time())
            extracted = await task.extractor.extract(
                nodes,
                ctx.actor,
                [ctx.actor],
                time.time(),
                "auto",
                preflight=preflight,
                on_submitted=on_submitted,
                location=ctx.location,
                existing=existing,
                preference=preference,
                direct_text=direct_text,
                actor_profile=await names.profile(ctx.actor),
            )
            if not self.enabled(ctx):
                raise BusinessError("自动分析资格已变更，未注册任务。")
            if not extracted.has_actions:
                async with data.lock:
                    check_current()
                    data.create_batch(
                        ctx.scope,
                        ctx.actor,
                        [],
                        "auto",
                        time.time(),
                        key,
                        package if not extracted.reply else None,
                    )
                messages = (
                    ["\n\n".join(extracted.rejected)] if extracted.rejected else []
                )
                if extracted.reply:
                    messages.append(extracted.reply)
                return messages or ["未发现可添加的未过期 DDL。"]
            confirmation = await task.apply(
                ctx,
                gateway,
                names,
                extracted.plans,
                extracted.rejected,
                version,
                "auto",
                key,
                package,
                precommit=check_current,
                duplicates=extracted.duplicates,
                updates=extracted.updates,
            )
            return [confirmation] + ([extracted.reply] if extracted.reply else [])
        except BaseException:
            async with data.lock:
                data.fail_event(key)
            raise
