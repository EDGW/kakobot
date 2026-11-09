"""Validated results and narrowly scoped personal task changes."""

import re
from dataclasses import dataclass, field

from .deadlines import DeadlinePlan, title_key

DEFAULT_TIME_PROMPT = (
    "提前3天的白天中午和傍晚合适时间，提前1天的白天中午和傍晚合适时间，"
    "当前的中午傍晚等合适时间，提前6h，3h，30min，5min"
)
MAX_DEFAULT_PROMPT = 1000
EDIT_INTENT = re.compile(
    r"改|修改|调整|编辑|换成|提前|推迟|延后|取消|删除|作废|去掉"
)
EDIT_REFERENCE = re.compile(
    r"DDL|任务|作业|第\s*[0-9零〇一二三四五六七八九十百两]+\s*"
    r"(?:个|项|条)?\s*(?:任务|DDL)|#\s*[0-9]+|刚才|这个|那个|上一个",
    re.IGNORECASE,
)


def looks_like_edit_request(text):
    if (
        re.search(r"提前\s*\d+\s*(?:天|日|小时|时|分钟|min|h|d)?\s*(?:提醒|通知)", text)
        and not re.search(r"(?:把|将|对|针对).{0,20}提前", text)
    ):
        return False
    return bool(
        EDIT_INTENT.search(text)
        and (EDIT_REFERENCE.search(text) or re.search(r"把|将|对|针对", text))
    )

ORDINAL_PATTERN = re.compile(
    r"第\s*([0-9]{1,3}|[零〇一二三四五六七八九十百两]+)\s*"
    r"(?:个|项|条)?\s*(?:任务|DDL)",
    re.IGNORECASE,
)


def _ordinal_value(value):
    if value.isdigit():
        return int(value)
    digits = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    units = {"十": 10, "百": 100}
    total = section = 0
    for char in value:
        if char in units:
            section = (section or 1) * units[char]
            total += section
            section = 0
        else:
            section = section * 10 + digits[char]
    return total + section


def ordinal_references(text):
    return tuple(
        _ordinal_value(value) for value in ORDINAL_PATTERN.findall(text)
    )


def referenced_deadlines(text, ordered_ids=(), titled_tasks=()):
    references = {
        int(match)
        for match in re.findall(
            r"(?:DDL\s*#?\s*|#)([0-9]{1,19})(?![0-9])", text, re.I
        )
    }
    for ordinal in ordinal_references(text):
        if 1 <= ordinal <= len(ordered_ids):
            references.add(ordered_ids[ordinal - 1])
    normalized = title_key(text)
    for identifier, title in titled_tasks:
        if title_key(title) and title_key(title) in normalized:
            references.add(identifier)
    return references


@dataclass(frozen=True)
class TaskChange:
    previous: dict
    plan: DeadlinePlan
    replace_reminders: bool
    source: dict
    cancelled: bool = False

@dataclass
class ExtractionResult:
    plans: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    updates: list[TaskChange] = field(default_factory=list)
    reply: str = ""

    @property
    def has_actions(self):
        return bool(self.plans or self.duplicates or self.updates)
