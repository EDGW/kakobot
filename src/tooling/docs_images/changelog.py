"""Render the repository changelog without changing its released sections."""

import re

from .document import cards_for, parse_document
from .render import render_document


def render_changelog(source, output, *, width=1200, size=25):
    text = source.read_text(encoding="utf-8")
    # Normalize only the rendering copy: # Dev and historical version headings
    # belong under one visible title while the on-disk source stays untouched.
    text = re.sub(r"^# 更新日志\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^# (Dev|v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+|\.(?:alpha|beta|rc)\.[0-9]+(?:\.[0-9]+)*)?)\s*$",
        r"## \1",
        text,
        flags=re.MULTILINE,
    )
    document = parse_document("# 更新日志\n\n" + text)
    cards = []
    for version in document.children[0].children:
        for heading, lines in cards_for(version, "CHAT"):
            title = (
                heading if heading == version.title else version.title + " · " + heading
            )
            cards.append((title, lines))
    return render_document(
        "更新日志",
        "CHANGELOG.md",
        cards,
        "ALL",
        output,
        width=width,
        size=size,
    )
