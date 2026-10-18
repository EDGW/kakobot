"""Offline Markdown/KaTeX rendering. No model, shell or network capability."""

import asyncio
import base64
import html
import math
import re
from functools import lru_cache
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.amsmath import amsmath_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.texmath import texmath_plugin
from playwright.async_api import async_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets"
WIDTH, PAGE_HEIGHT, MAX_HEIGHT, MAX_CHARS = 1120, 1800, 40000, 60000
RENDER_TIMEOUT = 30
_RENDER_SLOTS = asyncio.Semaphore(2)


def _highlight(code, language, _attrs):
    try:
        lexer = get_lexer_by_name(language or "text")
    except ClassNotFound:
        return ""
    return highlight(code, lexer, HtmlFormatter(nowrap=True))


def _math_rule(renderer, tokens, idx, options, env):
    token = tokens[idx]
    display = token.type != "math_inline"
    tag = "div" if display else "span"
    return (
        f'<{tag} class="formula" data-display="{str(display).lower()}" '
        f'data-tex="{html.escape(token.content, quote=True)}"></{tag}>'
    )


def markdown_body(source):
    """CommonMark + common extensions. Raw HTML and remote images never execute."""
    md = MarkdownIt("commonmark", {"html": False, "highlight": _highlight})
    md.enable(["table", "strikethrough"])
    md.use(texmath_plugin, delimiters="brackets")
    md.use(dollarmath_plugin, allow_labels=False, allow_space=False, double_inline=True)
    md.use(amsmath_plugin)
    md.use(footnote_plugin).use(tasklists_plugin).use(deflist_plugin)
    for name in (
        "math_inline",
        "math_inline_double",
        "math_block",
        "math_block_eqno",
        "amsmath",
    ):
        md.add_render_rule(name, _math_rule)

    def image_rule(renderer, tokens, idx, options, env):
        return (
            '<span class="image-alt">[图片：'
            + html.escape(tokens[idx].content)
            + "]</span>"
        )

    md.add_render_rule("image", image_rule)
    return md.render(source)


@lru_cache(maxsize=1)
def _styles():
    css = (ASSETS / "katex/katex.min.css").read_text()

    def font(match):
        name = match[1].split("/")[-1]
        path = ASSETS / "katex/fonts" / name
        if path.suffix != ".woff2":
            return "url(data:font/woff2;base64,)"
        return (
            "url(data:font/woff2;base64,"
            + base64.b64encode(path.read_bytes()).decode()
            + ")"
        )

    css = re.sub(r"url\(([^)]+)\)", font, css)
    chinese = base64.b64encode((ASSETS / "fonts/NotoSansSC.ttf").read_bytes()).decode()
    return (
        css
        + f"@font-face{{font-family:Kako;src:url(data:font/ttf;base64,{chinese})}}"
        + HtmlFormatter().get_style_defs("pre")
        + """
* { box-sizing: border-box; }
body { margin:0; padding:20px; background:#edf2f8; color:#20304a; font:25px/1.55 Kako,sans-serif; }
main { padding:24px 30px; border:1px solid #dde5f1; border-radius:24px; background:white; }
header { color:#315be8; font-size:19px; letter-spacing:2px; margin-bottom:14px; }
h1,h2,h3,h4,h5,h6 { line-height:1.35; margin:.7em 0 .3em; color:#193763; }
h1 { font-size:34px; } h2 { font-size:29px; } h3 { font-size:27px; }
p { margin:.4em 0; } a { color:#315be8; overflow-wrap:anywhere; }
blockquote { margin:12px 0; padding:4px 16px; border-left:5px solid #7596e8; background:#f2f6fc; }
code { font:22px/1.45 monospace; background:#eef2f8; padding:2px 5px; border-radius:5px; }
pre { background:#f3f6fa; padding:8px 12px; border-radius:10px; white-space:pre-wrap; overflow-wrap:anywhere; }
pre code { background:none; padding:0; }
table { width:100%; border-collapse:collapse; font-size:23px; margin:12px 0; table-layout:fixed; }
th,td { border:1px solid #dbe3ef; padding:8px 12px; overflow-wrap:anywhere; }
th { background:#eaf0fc; color:#284b80; } tr:nth-child(even) { background:#f8faff; }
hr { border:0; border-top:1px solid #dce4ef; margin:16px 0; }
ul,ol { padding-left:1.5em; } .task-list-item { list-style:none; }
.katex { font-size:1.15em; } .katex-display { margin:12px 0; }
.formula[data-display=true] { overflow:hidden; padding:6px 0; }
footer { white-space:pre-wrap; font:18px/1.5 Kako,sans-serif; color:#677890; border-top:1px solid #dce4ef; margin-top:16px; padding-top:12px; }
"""
    )


def document_html(source, footer=""):
    if len(source) > MAX_CHARS:
        raise ValueError("回答超出卡片渲染字符上限。")
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "script-src 'unsafe-inline'; style-src 'unsafe-inline'; font-src data:; img-src data:; connect-src 'none'\">"
        f"<style>{_styles()}</style></head><body><main>"
        "<header>KAKOBOT · 群内讨论</header>"
        + markdown_body(source)
        + "<footer>"
        + html.escape(footer)
        + "</footer></main></body></html>"
    )


async def _render(source, footer):
    document = await asyncio.to_thread(document_html, source, footer)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            context = await browser.new_context(
                viewport={"width": WIDTH, "height": PAGE_HEIGHT},
                device_scale_factor=1,
                service_workers="block",
            )
            await context.route("**/*", lambda route: route.abort())
            page = await context.new_page()
            await page.set_content(document, wait_until="load")
            await page.add_script_tag(
                content=(ASSETS / "katex/katex.min.js").read_text()
            )
            await page.evaluate("""() => {
                for (const el of document.querySelectorAll('.formula')) {
                    katex.render(el.dataset.tex, el, {
                        displayMode: el.dataset.display === 'true', throwOnError: false,
                        trust: false, strict: 'warn', maxExpand: 1000, maxSize: 20
                    });
                    if (el.scrollWidth > el.clientWidth && el.dataset.display === 'true') {
                        const math = el.querySelector('.katex');
                        math.style.fontSize = Math.max(.4, el.clientWidth / el.scrollWidth) + 'em';
                    }
                }
            }""")
            await page.evaluate("document.fonts.ready")
            height = await page.evaluate(
                "Math.ceil(document.body.getBoundingClientRect().height)"
            )
            if height > MAX_HEIGHT:
                raise ValueError("回答超出卡片渲染高度上限。")
            # Prefer line/row boundaries so pagination does not cut through glyphs or formulas.
            rects = await page.evaluate("""() => {
                const rects = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    if (!node.textContent.trim() || node.parentElement.closest('.formula,script,style')) continue;
                    const range = document.createRange(); range.selectNodeContents(node);
                    for (const r of range.getClientRects()) rects.push([r.top, r.bottom]);
                }
                for (const el of document.querySelectorAll('.formula[data-display=true], tr, footer')) {
                    const r = el.getBoundingClientRect(); rects.push([r.top, r.bottom]);
                }
                return rects;
            }""")
            pages, start = [], 0
            while start < height:
                end = min(start + PAGE_HEIGHT, height)
                if end < height:
                    candidates = sorted(
                        {
                            math.ceil(bottom) + 3
                            for _, bottom in rects
                            if start + PAGE_HEIGHT / 2 < bottom < end - 4
                        },
                        reverse=True,
                    )
                    end = next(
                        (
                            y
                            for y in candidates
                            if not any(top < y < bottom for top, bottom in rects)
                        ),
                        end,
                    )
                pages.append(
                    await page.screenshot(
                        type="png",
                        full_page=True,
                        clip={
                            "x": 0,
                            "y": start,
                            "width": WIDTH,
                            "height": end - start,
                        },
                    )
                )
                start = end
            return pages
        finally:
            await browser.close()


async def render_markdown_cards(source, footer=""):
    """Bound CPU/memory concurrency and total rendering time, including browser startup."""
    async with _RENDER_SLOTS:
        return await asyncio.wait_for(_render(source, footer), timeout=RENDER_TIMEOUT)
