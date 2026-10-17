"""Human-readable task details shared by commands, import and scheduling."""

from ..domain.deadlines import local_time

STATES = {
    "pending": "待发送",
    "sending": "发送中",
    "sent": "已发送",
    "skipped": "已跳过",
    "cancelled": "已取消",
    "failed": "发送失败",
    "uncertain": "结果不确定",
}
METHODS = {
    "legacy": "旧版迁移",
    "strict": "结构化",
    "manual": "手动 AI",
    "auto": "自动分析",
}


async def show_task(task, names, now):
    group = task["conversation"] if task["location"] == "GROUP" else ""
    status = (
        "已取消"
        if task["cancelled"]
        else "已过期"
        if task["deadline"] <= now
        else "有效"
        if task["targets"]
        else "已全部退订"
    )
    conversation = (
        "群 " + await names.group(group)
        if group
        else "私聊 " + await names.user(task["conversation"])
    )
    creator = await names.user(task["creator"], group)
    users = await names.user_list(task["targets"], group) if task["targets"] else "无"
    times = "\n".join(
        f"{local_time(item['at'])}（{STATES.get(item['state'], item['state'])}）"
        for item in task["reminders"]
    )
    return f"DDL #{task['id']}（{status}）\n{task['title']}\n会话：{conversation}\n创建方式：{METHODS.get(task['method'], task['method'])}\n设置者：{creator}\n通知对象：{users}\n截止：{local_time(task['deadline'])}（北京时间）\n通知时间：\n{times or '无剩余通知（过期节点已忽略）'}"
