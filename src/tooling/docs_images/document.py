"""Parse the project's Markdown and select sections for one conversation type."""

import re
from dataclasses import dataclass, field

EXCLUDED_STEMS = {"readme", "configuration", "development"}


def documentation_files(directory, output):
    return [
        path
        for path in sorted(directory.rglob("*.md"))
        if not path.is_relative_to(output)
        and (
            path.stem.lower() not in EXCLUDED_STEMS
            or (path.parent.name == "group-discuss" and path.stem == "configuration")
        )
    ]


@dataclass
class Section:
    title: str
    level: int
    lines: list[str] = field(default_factory=list)
    children: list["Section"] = field(default_factory=list)

    def locations(self):
        match = re.search(r"\s+-\s+(CHAT|GROUP)\s*$", self.title)
        result = {match[1]} if match else set()
        for child in self.children:
            result.update(child.locations())
        return result

    def select(self, location):
        match = re.search(r"\s+-\s+(CHAT|GROUP)\s*$", self.title)
        if match and match[1] != location:
            return None
        children = [
            selected
            for child in self.children
            if (selected := child.select(location)) is not None
        ]
        # A command heading whose only entries belong to the other location
        # must not leave an empty card behind.
        if (
            self.children
            and not children
            and not any(line.strip() for line in self.lines)
        ):
            return None
        return Section(self.title, self.level, self.lines, children)


def parse_document(text):
    root = Section("", 0)
    stack = [root]
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        match = re.match(r"^(#{1,6})\s+(.+)$", line) if not fenced else None
        if match:
            level, title = len(match[1]), match[2]
            while stack[-1].level >= level:
                stack.pop()
            child = Section(title, level)
            stack[-1].children.append(child)
            stack.append(child)
        else:
            stack[-1].lines.append(line)
    return root


def cards_for(document, location):
    selected = document.select(location)
    cards = []
    if selected is None:
        return cards

    def visit(section):
        title = section.title
        if section.level == 1:
            title = "概览"

        # H4–H6 are subheadings within their parent card, not numbered cards.
        def inline(child):
            lines = ["", "#" * child.level + " " + child.title, "", *child.lines]
            for nested in child.children:
                lines.extend(inline(nested))
            return lines

        lines = list(section.lines)
        for child in section.children:
            if child.level >= 4:
                lines.extend(inline(child))
        if any(line.strip() for line in lines):
            cards.append((title or "概览", lines))
        for child in section.children:
            if child.level < 4:
                visit(child)

    visit(selected)
    return cards


def plain(text):
    """Keep labels and command literals while removing inline Markdown syntax."""
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return text.replace("**", "").replace("`", "").replace("\\|", "|")


def blocks(lines):
    """Yield paragraphs, code blocks, lists and table rows in source order."""
    paragraph = []
    code = None

    def flush():
        if paragraph:
            value = " ".join(paragraph)
            paragraph.clear()
            return ("paragraph", value)
        return None

    for line in lines:
        if line.lstrip().startswith("```"):
            if item := flush():
                yield item
            if code is None:
                code = []
            else:
                yield "code", "\n".join(code)
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            if item := flush():
                yield item
        elif re.match(r"^#{4,6}\s+", stripped):
            if item := flush():
                yield item
            yield "heading", re.sub(r"^#{4,6}\s+", "", stripped)
        elif stripped.startswith("|") and stripped.endswith("|"):
            if item := flush():
                yield item
            cells = re.split(r"(?<!\\)\|", stripped[1:-1])
            if not all(re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in cells):
                yield "table", [cell.strip().replace("\\|", "|") for cell in cells]
        elif re.match(r"^(?:[-*+] |\d+\. )", stripped):
            if item := flush():
                yield item
            yield "list", re.sub(r"^(?:[-*+] |\d+\. )", "", stripped)
        elif stripped.startswith(">"):
            if item := flush():
                yield item
            yield "quote", stripped.lstrip("> ")
        else:
            paragraph.append(stripped)
    if item := flush():
        yield item
    if code is not None:
        yield "code", "\n".join(code)
