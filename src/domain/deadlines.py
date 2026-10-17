"""Parse one-shot deadlines and isolate model output from permissions and actions."""

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .errors import BusinessError

BEIJING = timezone(timedelta(hours=8))
DEFAULT_MINUTES = (30, 180, 720, 1440, 2160)
MAX_REMINDERS = 20
FINAL_GRACE_SECONDS = 60
USAGE = '/ddl add 内容 | /ddl add-strict "NAME" [YYYY-MM-DD HH:mm] -30min,-3h;@成员 | /ddl defaulttime ["提示词"] | /ddl list | /ddl view | /ddl show ID | /ddl remove ID | /ddl clear [GROUP|this|all]'


@dataclass(frozen=True)
class DeadlinePlan:
    title: str
    deadline: float
    reminders: tuple[float, ...]


def title_key(title):
    return " ".join(unicodedata.normalize("NFKC", title).casefold().split())


def local_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, BEIJING).strftime("%Y-%m-%d %H:%M:%S")


def split_targets(text: str) -> tuple[str, list[str] | None]:
    """Parse an explicit terminal suffix; AI mode also receives these constraints."""
    body, sep, suffix = text.rpartition(";")
    if not sep or not suffix.lstrip().startswith("@"):
        return text.strip(), None
    values = suffix.split(",")
    if not 1 <= len(values) <= 20 or any(
        not re.fullmatch(r"@[^@,;\n]+", value.strip()) for value in values
    ):
        raise BusinessError("通知对象格式：;@成员,@成员，最多20人，不支持@全体成员。")
    return body.strip(), [value.strip()[1:].strip() for value in values]


def _title(value) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 200:
        raise BusinessError("DDL 标题须为1～200字。")
    return value.strip()


def _timestamp(value, *, aware=False) -> float:
    if not isinstance(value, str):
        raise BusinessError("DDL 时间无效。")
    if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", value):
        raise BusinessError("DDL 时间须明确到时分。")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if aware and parsed.tzinfo is None:
            raise BusinessError("Missing timezone")
        return parsed.replace(tzinfo=parsed.tzinfo or BEIJING).timestamp()
    except (ValueError, OverflowError, OSError) as exc:
        raise BusinessError("DDL 日期、时间或时区无效。") from exc


def make_plan(title, deadline: float, times: list[float], now: float) -> DeadlinePlan:
    if len(times) > MAX_REMINDERS:
        raise BusinessError(
            f"每个 DDL 最多{MAX_REMINDERS}个提醒时间，不能设置重复循环提醒。"
        )
    if deadline <= now:
        raise BusinessError("截止时间已经过去，未创建 DDL。")
    if any(at > deadline for at in times):
        raise BusinessError("提醒时间不能晚于截止时间。")
    return DeadlinePlan(
        _title(title), deadline, tuple(sorted({at for at in times if at > now}))
    )


def parse_strict(text: str, now: float) -> DeadlinePlan:
    try:
        title, end = json.JSONDecoder().raw_decode(text.lstrip())
    except ValueError as exc:
        raise BusinessError(
            '标题须用双引号，例如 /ddl add-strict "报告" [2026-10-20 18:00] -3h,-30min'
        ) from exc
    rest = text.lstrip()[end:].strip()
    match = re.fullmatch(
        r'(?:\[([^\]]+)\]|"([^"]+)"|(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?))\s*(.*)',
        rest,
    )
    if not match:
        raise BusinessError("截止时间格式：YYYY-MM-DD HH:mm，可加方括号或双引号。")
    deadline = _timestamp(next(value for value in match.groups()[:3] if value))
    offsets = match[4].strip()
    if not offsets:
        minutes = list(DEFAULT_MINUTES)
    else:
        values = offsets.split(",")
        if len(values) > MAX_REMINDERS:
            raise BusinessError(f"每个 DDL 最多{MAX_REMINDERS}个提醒时间。")
        minutes = []
        for value in values:
            value = value.strip()
            if not re.fullmatch(r"-(?:\d+(?:min|d|h|m))+", value):
                raise BusinessError("提醒须为负偏移量，例如 -30min,-3h,-1d20h。")
            amount = sum(
                int(number) * {"d": 1440, "h": 60, "min": 1, "m": 1}[unit]
                for number, unit in re.findall(r"(\d+)(min|d|h|m)", value[1:])
            )
            minutes.append(amount)
    return make_plan(title, deadline, [deadline - value * 60 for value in minutes], now)
