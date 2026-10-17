"""Deterministic, local PNG rendering of the nearest ten active deadlines."""

import math
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..domain.deadlines import BEIJING
from ..domain.text import display_name

MAX_CARDS = 10
WIDTH = 1120
MARGIN = 32
GAP = 18
CARD_HEIGHT = 180
BACKGROUND = "#F0F3F8"
WHITE = "#FFFFFF"
COLORS = {
    "urgent": "#861F35",
    "today": "#C73D4F",
    "soon": "#187C58",
    "later": "#2868B4",
}
FONT_PATH = Path(__file__).resolve().parents[2] / "assets/fonts/NotoSansSC.ttf"


def active_tasks(tasks, now):
    return sorted(
        (
            task
            for task in tasks
            if task["deadline"] > now
            and not task.get("cancelled", False)
            and task.get("targets", True)
        ),
        key=lambda task: (task["deadline"], task.get("id", 0)),
    )


def urgency(deadline, now):
    if deadline - now <= 3 * 3600:
        return "urgent"
    if (
        datetime.fromtimestamp(deadline, BEIJING).date()
        == datetime.fromtimestamp(now, BEIJING).date()
    ):
        return "today"
    return "soon" if deadline - now <= 3 * 86400 else "later"


def remaining(deadline, now):
    seconds = max(0, deadline - now)
    if seconds < 60:
        return "不足1分钟"
    minutes = math.ceil(seconds / 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)
    return "".join(
        f"{value}{unit}"
        for value, unit in ((days, "天"), (hours, "小时"), (minutes, "分钟"))
        if value
    )


def _font(size, *, bold=False):
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_axes([650 if bold else 400])
    return font


def _title(text, available, fonts):
    # A task name is always one line; control characters cannot create rows.
    text = display_name(text, 200) or "未命名 DDL"
    for font in fonts:
        if font.getlength(text) <= available:
            return text, font
    font = fonts[-1]
    while text and font.getlength(text + "…") > available:
        text = text[:-1]
    return text + "…", font


def render_deadlines(tasks, now):
    """Return a single PNG; no network, model, names lookup or persistent files."""
    tasks = active_tasks(tasks, now)
    visible, overflow = tasks[:MAX_CARDS], max(0, len(tasks) - MAX_CARDS)
    count = max(1, len(visible))
    height = MARGIN * 2 + count * CARD_HEIGHT + (count - 1) * GAP
    if overflow:
        height += 70
    canvas = Image.new("RGB", (WIDTH, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    title_fonts = [_font(size, bold=True) for size in (48, 44, 40, 36)]
    detail_fonts, footer_font = [_font(size) for size in (30, 28, 26, 24)], _font(28)
    if not visible:
        draw.rounded_rectangle(
            (MARGIN, MARGIN, WIDTH - MARGIN, height - MARGIN),
            radius=24,
            fill="#48566D",
        )
        draw.text(
            (WIDTH / 2, height / 2),
            "暂无有效 DDL",
            font=title_fonts[0],
            fill=WHITE,
            anchor="mm",
        )
    for index, task in enumerate(visible):
        top = MARGIN + index * (CARD_HEIGHT + GAP)
        draw.rounded_rectangle(
            (MARGIN, top, WIDTH - MARGIN, top + CARD_HEIGHT),
            radius=24,
            fill=COLORS[urgency(task["deadline"], now)],
        )
        left, right = MARGIN + 36, WIDTH - MARGIN - 36
        title, font = _title(
            f"#{task['id']} {task['title']}", right - left, title_fonts
        )
        draw.text((left, top + 54), title, font=font, fill=WHITE, anchor="lm")
        deadline = datetime.fromtimestamp(task["deadline"], BEIJING).strftime(
            "%Y-%m-%d %H:%M"
        )
        due = f"DDL  {deadline}"
        rest = "剩余 " + remaining(task["deadline"], now)
        detail_font = next(
            (
                font
                for font in detail_fonts
                if font.getlength(due + rest) + 32 <= right - left
            ),
            detail_fonts[-1],
        )
        draw.text((left, top + 125), due, font=detail_font, fill=WHITE, anchor="lm")
        draw.text((right, top + 125), rest, font=detail_font, fill=WHITE, anchor="rm")
    if overflow:
        label = f"还有 {overflow} 个 DDL 未展示"
        half_width = footer_font.getlength(label) / 2 + 22
        draw.rounded_rectangle(
            (
                WIDTH / 2 - half_width,
                height - MARGIN - 48,
                WIDTH / 2 + half_width,
                height - MARGIN + 4,
            ),
            radius=16,
            fill="#48566D",
        )
        draw.text(
            (WIDTH / 2, height - MARGIN - 24),
            label,
            font=footer_font,
            fill=WHITE,
            anchor="mm",
        )
    with BytesIO() as output:
        canvas.save(output, format="PNG", optimize=True)
        return output.getvalue()
