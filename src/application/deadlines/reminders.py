"""Apply explicit schedules, private defaults and bounded calendar fallbacks."""

from datetime import datetime, timedelta

from ...domain.deadlines import (
    BEIJING,
    DEFAULT_MINUTES,
    MAX_REMINDERS,
    _timestamp,
    make_plan,
)
from ...domain.errors import BusinessError


def fallback_times(deadline):
    day = datetime.fromtimestamp(deadline, BEIJING).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    calendar = [
        (day - timedelta(days=days) + timedelta(hours=hour)).timestamp()
        for days in (3, 1, 0)
        for hour in (12, 18)
    ]
    return [at for at in calendar if at < deadline] + [
        deadline - minutes * 60 for minutes in (360, 180, 30, 5)
    ]


def reminder_plan(item, title, deadline, now, mode, preference, default_valid):
    source = item.get("reminder_source", "explicit")
    values = item["remind_at"]
    uses_default = mode == "auto" and (values is None or source != "explicit")
    fallback = uses_default and (
        not preference or not default_valid or source != "preference" or values is None
    )
    invalid_default = bool(preference and uses_default and not default_valid)

    def build(times):
        if len(times) > MAX_REMINDERS:
            raise BusinessError(f"单个 DDL 最多{MAX_REMINDERS}次通知（含到期通知）。")
        times = list(times)
        if item.get("notify_on_deadline", True):
            if deadline not in times:
                times.append(deadline)
        else:
            times = [at for at in times if at != deadline]
        return make_plan(title, deadline, times, now), sorted(times)

    use_model_default = (
        uses_default
        and values is not None
        and (
            (source == "preference" and bool(preference) and default_valid is True)
            or (source == "fallback" and fallback)
        )
    )
    if fallback and not use_model_default:
        times = fallback_times(deadline)
    elif values is None:
        times = [deadline - minutes * 60 for minutes in DEFAULT_MINUTES]
    else:
        times = [_timestamp(value, aware=True) for value in values]
    try:
        if item.get("recurring", False):
            raise BusinessError("不支持周期重复提醒。")
        plan, times = build(times)
    except BusinessError:
        if not uses_default:
            raise
        # Invalid personal preferences never discard an otherwise valid task.
        plan, times = build(fallback_times(deadline))
        invalid_default = bool(preference)
        fallback = True
    return (
        plan,
        {
            "requested_reminders": times,
            "notify_on_deadline": item.get("notify_on_deadline", True),
            "reminder_source": "fallback"
            if fallback
            else "preference"
            if uses_default
            else source,
        },
        invalid_default,
    )
