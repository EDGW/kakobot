"""Validate change data and ground AI-selected edits in the owner's text."""

import json
import re

from ...domain.analysis import TaskChange, referenced_deadlines
from ...domain.deadlines import DeadlinePlan, _timestamp, make_plan
from ...domain.errors import BusinessError
from .reminders import reminder_plan

CHANGE_INTENT = re.compile(
    r"改|修改|调整|换成|提前|推迟|延后|截止|提醒|取消|关闭|开启|增加|减少|去掉"
)

CHANGE_FIELDS = {"title", "deadline_at", "remind_at", "notify_on_deadline", "cancel"}


def validate_change(item, existing, direct_text, *, allow_cancel=False):
    if (
        not isinstance(item, dict)
        or set(item) != {"id", "changes", "instruction_quote", "reminder_source"}
        or type(item["id"]) is not int
        or item["id"] not in existing
        or not isinstance(item["instruction_quote"], str)
        or not item["instruction_quote"].strip()
        or len(item["instruction_quote"]) > 2000
        or not isinstance(item["changes"], dict)
        or not item["changes"]
        or not set(item["changes"]) <= CHANGE_FIELDS
        or item["reminder_source"] not in {"explicit", "preference", "fallback"}
    ):
        raise ValueError("invalid personal DDL change")
    quote = item["instruction_quote"]
    ordered_ids = tuple(task["id"] for task in existing.values())
    titled_tasks = tuple(
        (task["id"], task["title"]) for task in existing.values()
    )
    references = referenced_deadlines(quote, ordered_ids, titled_tasks)
    if (
        quote not in direct_text
        or (references and (len(references) != 1 or item["id"] not in references))
        or (not references and not CHANGE_INTENT.search(quote))
    ):
        raise ValueError("DDL change is not grounded in a direct owner instruction")
    changes = item["changes"]
    if "cancel" in changes:
        if (
            not allow_cancel
            or set(changes) != {"cancel"}
            or changes["cancel"] is not True
        ):
            raise ValueError("invalid personal DDL cancellation")
        return
    if "title" in changes and (
        not isinstance(changes["title"], str)
        or not 1 <= len(changes["title"].strip()) <= 200
    ):
        raise ValueError("invalid changed title")
    if "deadline_at" in changes:
        _timestamp(changes["deadline_at"], aware=True)
    if (
        "notify_on_deadline" in changes
        and type(changes["notify_on_deadline"]) is not bool
    ):
        raise ValueError("invalid changed deadline notification flag")
    if "remind_at" in changes and changes["remind_at"] is not None:
        if not isinstance(changes["remind_at"], list):
            raise ValueError("invalid changed reminder list")
        for value in changes["remind_at"]:
            _timestamp(value, aware=True)


def propose_change(item, previous, now, preference, default_valid):
    changes = item["changes"]
    if changes.get("cancel"):
        source = json.loads(previous["source"])
        source["last_change_fields"] = ["cancel"]
        return (
            TaskChange(
                previous,
                DeadlinePlan(previous["title"], previous["deadline"], ()),
                False,
                source,
                True,
            ),
            False,
        )
    title = changes.get("title", previous["title"]).strip()
    deadline = (
        _timestamp(changes["deadline_at"], aware=True)
        if "deadline_at" in changes
        else previous["deadline"]
    )
    if deadline <= now:
        raise BusinessError(f"DDL #{previous['id']} 的截止时间已过，未修改。")
    replace = bool(set(changes) - {"title"})
    source = json.loads(previous["source"])
    invalid_default = False
    if replace:
        notify = changes.get(
            "notify_on_deadline",
            source.get(
                "notify_on_deadline",
                any(
                    node["at"] == previous["deadline"] and node["state"] != "cancelled"
                    for node in previous["reminders"]
                ),
            ),
        )
        if "remind_at" in changes:
            values = changes["remind_at"]
            plan, extra, invalid_default = reminder_plan(
                {
                    "remind_at": values,
                    "notify_on_deadline": notify,
                    "reminder_source": item["reminder_source"],
                },
                title,
                deadline,
                now,
                "auto",
                preference,
                default_valid,
            )
            source.update(extra)
        else:
            delta = deadline - previous["deadline"]
            times = [
                node["at"] + delta
                for node in previous["reminders"]
                if node["state"] == "pending" and node["at"] != previous["deadline"]
            ]
            if notify:
                times.append(deadline)
            plan = make_plan(title, deadline, times, now)
            source.update(requested_reminders=sorted(times), notify_on_deadline=notify)
    else:
        plan = DeadlinePlan(title, deadline, ())
    source["last_change_fields"] = sorted(changes)
    return TaskChange(previous, plan, replace, source), invalid_default
