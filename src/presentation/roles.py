"""Identity cards sharing the configuration card's local Pillow layout."""

from .cards import render_value_cards

SECTIONS_PER_IMAGE = 4


def render_role_cards(user_label, global_sources, groups, *, private):
    def rows(sources, group=""):
        if not sources:
            return [("有效身份", "无", "")]
        return [
            (
                role,
                "；".join(origins),
                "私聊编码：" + group + role[5:] if private and group else "",
            )
            for role, origins in sorted(sources.items())
        ]

    sections = [("全局身份", rows(global_sources))]
    sections.extend(
        ("群 " + label, rows(sources, group)) for group, label, sources in groups
    )
    if private and not groups:
        sections.append(("群身份", [("有效身份", "无", "暂无已知群内身份")]))
    pages = (len(sections) + SECTIONS_PER_IMAGE - 1) // SECTIONS_PER_IMAGE
    return [
        render_value_cards(
            "我的身份与权限",
            f"{user_label} · {'私聊' if private else '当前群'} · {index + 1}/{pages}",
            sections[start : start + SECTIONS_PER_IMAGE],
            banner="KAKOBOT / ROLES",
            footer=(
                "直接授权、继承和全员准入共同决定有效权限；此卡片仅供查看。",
                "/role · 授权调整请联系 Super 或对应群的管理者。",
            ),
        )
        for index, start in enumerate(range(0, len(sections), SECTIONS_PER_IMAGE))
    ]
