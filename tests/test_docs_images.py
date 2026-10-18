from src.tooling.docs_images.document import blocks, cards_for, parse_document


def test_subheadings_stay_inside_parent_card():
    document = parse_document("""# 配置

## 新手常用设置

#### 第一步

先开通。

##### 注意

保留已有模型。

#### 第二步

配置 Key。

## 管理命令

### 查询 - CHAT

私聊查询。

#### 示例

```text
#### 这是一段代码
```

### 查询 - GROUP

群聊不可用。
""")
    cards = cards_for(document, "CHAT")
    assert [title for title, _ in cards] == ["新手常用设置", "查询 - CHAT"]
    beginner = list(blocks(cards[0][1]))
    assert beginner == [
        ("heading", "第一步"),
        ("paragraph", "先开通。"),
        ("heading", "注意"),
        ("paragraph", "保留已有模型。"),
        ("heading", "第二步"),
        ("paragraph", "配置 Key。"),
    ]
    assert list(blocks(cards[1][1]))[-1] == ("code", "#### 这是一段代码")
    assert [title for title, _ in cards_for(document, "GROUP")] == [
        "新手常用设置",
        "查询 - GROUP",
    ]


def test_table_preserves_inline_markup_and_escaped_pipe():
    rows = list(
        blocks(
            [
                "| 用法 | 说明 |",
                "| --- | --- |",
                r"| `/group-discuss admin user add\|remove` | **管理员** [帮助](help.md) |",
            ]
        )
    )
    assert rows == [
        ("table", ["用法", "说明"]),
        (
            "table",
            ["`/group-discuss admin user add|remove`", "**管理员** [帮助](help.md)"],
        ),
    ]


def test_table_commands_render_with_code_highlight():
    from src.tooling.docs_images.render import ACCENT, Layout

    layout = Layout(1200, 25)
    layout.card("表格", [r"| 用法 | `/help group-discuss` 与 **说明** |"], 1)
    code_backgrounds = [
        op for op in layout.ops if op[0] == "box" and op[2] == "#EAF0FF"
    ]
    assert code_backgrounds
    code_text = "".join(
        op[2] for op in layout.ops if op[0] == "text" and op[4] == ACCENT
    )
    assert "/help group-discuss" in code_text
    visible = "".join(op[2] for op in layout.ops if op[0] == "text")
    assert "`" not in visible
    assert "**" not in visible
