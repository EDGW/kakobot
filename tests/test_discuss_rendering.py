"""Offline output routing and real browser layout; no AstrBot or paid model calls."""

from io import BytesIO

import pytest
from PIL import Image

from src.infrastructure.group_discuss.rendering import (
    markdown_body,
    render_markdown_cards,
)
from src.presentation.group_discuss.output import output_mode


@pytest.mark.parametrize(
    "source,card",
    [
        ("简短回答", False),
        ("[[render:card]]\n简短回答", True),
        ("[[render:text]]\n简短回答", False),
        ("字" * 1001, True),
        ("[[render:text]]\n$x^2$", True),
        (r"公式 \(x^2\)", True),
        (r"\[x^2\]", True),
        ("| A | B |\n| --- | --- |\n| 1 | 2 |", True),
        ("`$x$`", False),
    ],
)
def test_output_mode(source, card):
    text, actual = output_mode(source)
    assert actual is card
    assert not text.startswith("[[render:")


def test_markdown_extensions_and_untrusted_html():
    body = markdown_body("""# 标题

| A | B |
| --- | --- |
| 1 | 2 |

- [x] 完成

~~删除~~ **粗体**

<script>fetch("https://example.com")</script>

![图片](https://example.com/image.png)

$$\\frac{1}{2}$$

\\(a^2\\)

```python
print("hello")
```
""")
    for expected in (
        "<table>",
        "<strong>",
        "<s>",
        "checkbox",
        "data-tex=",
        'class="formula"',
        "<pre>",
    ):
        assert expected in body
    assert "<script>" not in body
    assert "<img" not in body
    assert "&lt;script&gt;" in body


@pytest.mark.asyncio
async def test_actual_browser_renders_math_and_multiple_pages():
    # Browser installation is a documented deployment dependency.
    source = "# 公式与表格\n\n$$\\int_0^1 x^2 dx=\\frac{1}{3}$$\n\n"
    source += "| A | B |\n| --- | --- |\n| 西安 | 24°C |\n\n"
    source += "\n\n".join(f"第 {i} 段：" + "内容与排版测试。" * 12 for i in range(30))
    images = await render_markdown_cards(
        source, "tokens input: 100(+0) output: 20. toolcall(s) 0."
    )
    assert len(images) > 1
    for data in images:
        image = Image.open(BytesIO(data))
        assert image.width == 1120
        assert 0 < image.height <= 1800
        assert image.convert("L").getextrema()[0] < 100
