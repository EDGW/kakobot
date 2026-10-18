"""Shared broadcast envelope and opt-out instructions."""


def format_announcement(content):
    return "【广播】\n" + content + "\n\n使用/announce-reject on来拒收广播消息。"
