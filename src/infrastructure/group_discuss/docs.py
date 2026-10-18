"""Read-only access to the plugin's bundled Markdown documentation."""

import re
from pathlib import Path

from ...domain.errors import BusinessError

DOCS = Path(__file__).resolve().parents[3] / "docs"


def query_docs(query="", path="", offset=0, *, directory=DOCS, preferred=""):
    """List/search documents or read a bounded page from an allowlisted file."""
    if len(query) > 128 or type(offset) is not int or offset < 0:
        raise BusinessError("文档关键词最多 128 字符，分页起点须非负。")
    root = directory.resolve()
    catalog = {
        file.relative_to(root).as_posix(): file
        for file in sorted(root.rglob("*.md"))
        if file.is_file()
        and not file.is_symlink()
        and file.resolve().is_relative_to(root)
        and "pics" not in file.relative_to(root).parts
        and file.stat().st_size <= 1024 * 1024
    }
    if path:
        if path not in catalog:
            raise BusinessError("只能读取文档目录返回的 Markdown 路径。")
        text = catalog[path].read_text(encoding="utf-8")
        end = min(len(text), offset + 400)
        return {
            "path": path,
            "offset": offset,
            "next_offset": end if end < len(text) else None,
            "text": text[offset:end],
        }
    terms = re.findall(r"[\w./-]+", query.casefold())
    matches = []
    for name, file in catalog.items():
        text = file.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ") if text else name
        lower = text.casefold()
        score = sum(3 * (term in name.casefold()) + (term in lower) for term in terms)
        if terms and not score:
            continue
        item = {"path": name, "title": title[:60]}
        if terms:
            first = min(
                (lower.index(term) for term in terms if term in lower), default=0
            )
            item["snippet"] = text[max(0, first - 30) : first + 90]
        matches.append(
            (score + (2 if preferred and name.startswith(preferred) else 0), name, item)
        )
    matches.sort(key=lambda row: (-row[0], row[1]))
    size = 2 if terms else 8
    page = [item for _, _, item in matches[offset : offset + size]]
    return {
        "results": page,
        "next_offset": offset + len(page)
        if offset + len(page) < len(matches)
        else None,
    }
