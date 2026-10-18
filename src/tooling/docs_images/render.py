"""Measured, wrapping card layout using the bundled Chinese font and Pillow."""

import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .document import blocks, plain

FONT_PATH = Path(__file__).resolve().parents[3] / "assets/fonts/NotoSansSC.ttf"
BACKGROUND = "#EEF2F7"
INK = "#1D2C45"
MUTED = "#65758D"
ACCENT = "#315BE8"


@lru_cache(maxsize=32)
def font(size, bold=False):
    result = ImageFont.truetype(str(FONT_PATH), size)
    result.set_variation_by_axes([650 if bold else 400])
    return result


def wrapped(text, available, face):
    """Wrap by measured glyph widths, including long commands and CJK text."""
    result = []
    for source in text.split("\n"):
        line = ""
        for char in source:
            if line and face.getlength(line + char) > available:
                result.append(line)
                line = ""
            line += char
        result.append(line)
    return result


class Layout:
    def __init__(self, width, size):
        self.width, self.size = width, size
        self.ops = []
        self.y = 0

    def text(self, text, x, available, *, size=None, color=INK, bold=False):
        size = size or self.size
        face = font(size, bold)
        line_height = round(size * 1.65)
        for line in wrapped(text, available, face):
            self.ops.append(("text", (x, self.y), line, face, color))
            self.y += line_height

    def box(self, bounds, fill, radius=16):
        self.ops.append(("box", bounds, fill, radius))

    def rich(self, value, x, available):
        # Inline code and strong text retain visual emphasis without displaying
        # the Markdown delimiters. Link labels stay visible as ordinary text.
        value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
        tokens = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", value)
        left, y = x, self.y
        height = round(self.size * 1.65)
        for token in tokens:
            code = token.startswith("`") and token.endswith("`")
            strong = token.startswith("**") and token.endswith("**")
            content = token[1:-1] if code else token[2:-2] if strong else token
            face = font(self.size, strong)
            for char in content:
                advance = face.getlength(char)
                if left > x and left + advance > x + available:
                    left = x
                    y += height
                if code:
                    self.box(
                        (left, y + 3, left + advance + 1, y + height - 3), "#EAF0FF", 0
                    )
                self.ops.append(
                    ("text", (left, y), char, face, ACCENT if code else INK)
                )
                left += advance
        self.y = y + height

    def card(self, title, lines, index):
        top = self.y
        start = len(self.ops)
        x, padding = 36, 32
        inner_x = x + padding
        available = self.width - 2 * inner_x
        self.y += 28
        clean_title = re.sub(r"\s+-\s+(CHAT|GROUP)\s*$", "", plain(title))
        self.text(
            f"{index:02d}  {clean_title}",
            inner_x,
            available,
            size=self.size + 5,
            bold=True,
        )
        self.y += 15
        for kind, value in blocks(lines):
            if kind == "code":
                code_top = self.y
                code_start = len(self.ops)
                self.y += 18
                self.text(
                    value,
                    inner_x + 18,
                    available - 36,
                    size=self.size - 2,
                    color="#D9E6FF",
                )
                self.y += 18
                self.ops.insert(
                    code_start,
                    (
                        "box",
                        (inner_x, code_top, inner_x + available, self.y),
                        "#192840",
                        14,
                    ),
                )
            elif kind == "table":
                # Label/value rows stay legible on a narrow portrait image.
                table_top = self.y
                table_start = len(self.ops)
                self.y += 12
                self.text(
                    value[0], inner_x + 16, available - 32, bold=True, color=ACCENT
                )
                for cell in value[1:]:
                    self.text(cell, inner_x + 16, available - 32, size=self.size - 2)
                self.y += 12
                self.ops.insert(
                    table_start,
                    (
                        "box",
                        (inner_x, table_top, inner_x + available, self.y),
                        "#F2F5FA",
                        12,
                    ),
                )
            elif kind == "list":
                self.ops.append(
                    ("text", (inner_x, self.y), "•", font(self.size, True), ACCENT)
                )
                self.rich(value, inner_x + 24, available - 24)
            elif kind == "quote":
                self.text(plain(value), inner_x + 20, available - 20, color=MUTED)
            else:
                self.rich(value, inner_x, available)
            self.y += 14
        self.y += 14
        self.ops.insert(
            start, ("box", (x, top + 5, self.width - x, self.y + 5), "#DFE5F0", 22)
        )
        self.ops.insert(
            start + 1, ("box", (x, top, self.width - x, self.y), "#FFFFFF", 22)
        )
        self.y += 24

    def save(self, output):
        height = self.y + 28
        if height > 65000:
            raise ValueError(
                f"{output}: 图片高度 {height} 超出 JPEG 上限，请拆分文档或减小字号。"
            )
        picture = Image.new("RGB", (self.width, height), BACKGROUND)
        draw = ImageDraw.Draw(picture)
        for operation in self.ops:
            if operation[0] == "box":
                _, bounds, fill, radius = operation
                draw.rounded_rectangle(bounds, radius=radius, fill=fill)
            else:
                _, position, value, face, color = operation
                draw.text(position, value, font=face, fill=color, anchor="la")
        output.parent.mkdir(parents=True, exist_ok=True)
        picture.save(output, "JPEG", quality=93, subsampling=0, optimize=True)
        return picture.size


def render_document(title, source, cards, location, output, *, width=1200, size=25):
    layout = Layout(width, size)
    layout.box((0, 0, width, 12), ACCENT, 0)
    layout.y = 42
    layout.text(
        "KAKOBOT  /  DOCUMENTATION", 40, width - 80, size=18, bold=True, color=ACCENT
    )
    layout.y += 12
    layout.text(plain(title), 40, width - 80, size=size + 18, bold=True)
    layout.y += 12
    layout.text(
        "私聊 CHAT" if location == "CHAT" else "群聊 GROUP",
        40,
        width - 80,
        size=21,
        color=ACCENT,
        bold=True,
    )
    layout.text(source, 40, width - 80, size=17, color=MUTED)
    layout.y += 25
    for index, (heading, lines) in enumerate(cards, 1):
        layout.card(heading, lines, index)
    layout.y += 4
    layout.text("KakoBot · 命令与功能参考", 40, width - 80, size=17, color=MUTED)
    return layout.save(output)
