"""Extract visible answer links without visiting them or asking a model."""

import re
from urllib.parse import urlsplit

from markdown_it import MarkdownIt


def answer_links(source):
    found = {}

    def add(url, label=""):
        try:
            parsed = urlsplit(url)
            if (
                parsed.scheme.lower() not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                return
            if any(ord(char) < 33 for char in url):
                return
        except ValueError:
            return
        label = label.strip()
        if url not in found or (found[url] == url and label):
            found[url] = label or url

    def visit(tokens):
        for i, token in enumerate(tokens):
            if token.type == "link_open":
                # Only include this link's label, not subsequent paragraph content.
                end = next(
                    (
                        j
                        for j in range(i + 1, len(tokens))
                        if tokens[j].type == "link_close"
                    ),
                    i + 1,
                )
                label = "".join(
                    t.content
                    for t in tokens[i + 1 : end]
                    if t.type in {"text", "code_inline"}
                )
                add(token.attrGet("href") or "", label)
            elif token.type == "image":
                add(token.attrGet("src") or "", token.content)
            elif token.type == "text":
                for match in re.finditer(r"https?://[^\s<>\\]+", token.content):
                    url = match[0].rstrip(".,;:!?。，；：！？、】》\"'")
                    while url.endswith(")") and url.count(")") > url.count("("):
                        url = url[:-1]
                    add(url)
            if token.children and token.type != "image":
                visit(token.children)

    visit(MarkdownIt("commonmark", {"html": False}).parse(source))
    return [(label, url) for url, label in found.items()]
