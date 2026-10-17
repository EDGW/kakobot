"""Chinese rolling token and RMB cost reports."""

from ..domain.costs import WINDOWS
from ..domain.deadlines import local_time


def _money(value):
    amount = f"{value:.6f}"
    return "<¥0.000001" if value > 0 and amount == "0.000000" else "¥" + amount


def _windows(windows):
    lines = []
    for (label, _), total in zip(WINDOWS, windows, strict=True):
        suffix = f"；{total.requests}次请求"
        if total.unknown:
            suffix += f"，{total.unknown}次用量不完整"
        if total.pending:
            suffix += f"（其中{total.pending}次处理中）"
        lines.append(
            f"{label}：输入 {total.input:,} / 输出 {total.output:,} / "
            f"合计 {total.total:,} tokens；{_money(total.cost)}{suffix}"
        )
    return lines


async def render_cost_report(report, bot, now, names, *, actor=None, group=None):
    lines = [
        "[KakoBot] Token 用量与费用",
        f"机器人 QQ：{bot}；统计截至：{local_time(now)}（北京时间）",
        f"开始记录：{local_time(report.started_at)}；近1/3/7/30天均按滚动24小时计算。",
    ]
    if actor:
        lines.append("筛选账号：" + await names.user(actor))
    if group:
        lines.append("筛选群：" + await names.group(group))
    lines.extend(["", "【汇总】", *_windows(report.total)])
    if not report.total[-1].requests:
        lines.append("尚无符合条件的 AI 请求记录。")
    if report.accounts:
        lines.extend(["", "【按发起请求的 QQ 账号】"])
        for user, windows in sorted(
            report.accounts.items(), key=lambda item: int(item[0])
        ):
            lines.extend([await names.user(user), *_windows(windows), ""])
    if report.groups:
        lines.extend(["", "【按群及私聊归属】"])
        for identifier, windows in sorted(
            report.groups.items(), key=lambda item: int(item[0] or 0)
        ):
            title = (
                "群 " + await names.group(identifier)
                if identifier
                else "私聊（未归属群）"
            )
            lines.extend([title, *_windows(windows), ""])
    lines.extend(
        [
            "【计费说明】",
            "金额按每次请求当时的输入/输出人民币单价估算；单价默认为0，调价不重算历史费用。",
            "tokens 取 API usage，缓存及思考 tokens 不重复累加；缺失用量的请求不按0推定，以上仅汇总已知用量和费用。",
            "账号和群是同一批请求的不同视角，不能相加；群总结归到被总结的群，其他私聊归到本人私聊。",
            "从启用此功能后开始记录，升级前的历史消耗无法补算。",
        ]
    )
    return "\n".join(lines)
