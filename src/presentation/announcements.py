"""Version-specific usage announcement and the shared broadcast envelope."""

VERSION_ANNOUNCEMENT = (
    "kakobot已更新到v1.3.0版本。您可以直接与kakobot私聊来设置或调整个人DDL；"
    "调整时请给出具体的DDL编号和修改要求。取消DDL请使用 /ddl remove 编号。\n\n"
    "机器人默认不会关联多条消息。若添加失败后需要补充，可以回复原消息（引用正文需可读取）；"
    "若要关联多条消息，请使用合并转发。"
)


def format_announcement(content):
    return "【广播】\n" + content + "\n\n使用/announce-reject on来拒收广播消息。"
