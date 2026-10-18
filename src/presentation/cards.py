"""Shared Pillow renderer for runtime identity and configuration cards."""

from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path(__file__).resolve().parents[2] / "assets/fonts/NotoSansSC.ttf"
WIDTH, MARGIN = 1120, 32
INK, MUTED, ACCENT = "#1D2C45", "#65758D", "#315BE8"


@lru_cache(maxsize=8)
def _font(size, bold=False):
    face = ImageFont.truetype(str(FONT_PATH), size)
    face.set_variation_by_axes([650 if bold else 400])
    return face


def render_value_cards(title, subtitle, sections, *, footer=(), banner="KAKOBOT"):
    """Render plain text rows; each row contains label, value and optional detail."""
    ops = []
    y = 36

    def text(value, x, width, size=25, color=INK, bold=False):
        nonlocal y
        value = "".join(c for c in value if c.isprintable() or c == "\n")
        if len(value) > 1600:
            value = value[:1600] + "…（显示已截断）"
        face = _font(size, bold)
        for paragraph in value.split("\n"):
            line = ""
            for char in paragraph:
                if line and face.getlength(line + char) > width:
                    ops.append(("text", (x, y), line, face, color))
                    y += round(size * 1.6)
                    line = ""
                line += char
            ops.append(("text", (x, y), line, face, color))
            y += round(size * 1.6)

    text(banner, 48, WIDTH - 96, 18, ACCENT, True)
    text(title, 48, WIDTH - 96, 40, bold=True)
    text(subtitle, 48, WIDTH - 96, 23, MUTED)
    y += 18
    for title, rows in sections:
        top, start = y, len(ops)
        y += 22
        text(title, 58, WIDTH - 116, 29, ACCENT, True)
        y += 12
        for label, value, details in rows:
            row_top = y
            text(label, 58, 330, 25, bold=True)
            label_end = y
            y = row_top
            text(value, 412, WIDTH - 470, 25)
            y = max(y, label_end) + 6
            if details:
                text(details, 58, WIDTH - 116, 18, MUTED)
            y += 20
        y += 2
        ops.insert(start, ("box", (MARGIN, top, WIDTH - MARGIN, y), "#FFFFFF"))
        y += 22
    for line in footer:
        text(line, 48, WIDTH - 96, 19, MUTED)
    image = Image.new("RGB", (WIDTH, y + 32), "#EEF2F7")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 10), fill=ACCENT)
    for op in ops:
        if op[0] == "box":
            draw.rounded_rectangle(op[1], radius=22, fill=op[2])
        else:
            draw.text(op[1], op[2], font=op[3], fill=op[4], anchor="la")
    with BytesIO() as output:
        image.save(output, "PNG", optimize=True)
        return output.getvalue()
