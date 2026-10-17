"""Validated results and narrowly scoped personal task changes."""

import re
from dataclasses import dataclass, field

from .deadlines import DeadlinePlan

DEFAULT_TIME_PROMPT = (
    "提前3天的白天中午和傍晚合适时间，提前1天的白天中午和傍晚合适时间，"
    "当前的中午傍晚等合适时间，提前6h，3h，30min，5min"
)
MAX_DEFAULT_PROMPT = 1000


def referenced_deadlines(text):
    return {
        int(match)
        for match in re.findall(r"(?:DDL\s*#?\s*|#)([0-9]{1,19})(?![0-9])", text, re.I)
    }


@dataclass(frozen=True)
class TaskChange:
    previous: dict
    plan: DeadlinePlan
    replace_reminders: bool
    source: dict


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
