"""Read built documentation JPEGs from the ordinary or Super help directory."""

import re
from pathlib import Path

from ...domain.errors import BusinessError

PICS = Path(__file__).resolve().parents[3] / "docs/pics/commands"
DISCUSS_TOPICS = {
    "group-discuss": "help",
    "group-discuss-admin": "admin",
    "group-discuss-super": "admin",
    "group-discuss-roles": "roles",
    "group-discuss-tools": "tools",
    "group-discuss-statistics": "statistics",
    "group-discuss-configuration": "configuration",
}
PERSONAL_TOPICS = {
    "discuss": "help",
    "discuss-tools": "tools",
    "discuss-configuration": "configuration",
}


class HelpImageStore:
    def __init__(self, directory=PICS):
        self.directory = directory

    def read(self, topic, location, *, super_help=False):
        if not re.fullmatch(r"[a-z][a-z0-9-]*", topic) or location not in {
            "CHAT",
            "GROUP",
        }:
            raise BusinessError(
                "没有对应的帮助页面，请使用 /help 或 /super help 查看目录。"
            )
        directory = self.directory / "super" if super_help else self.directory
        sources = self.directory.parent.parent / "commands"
        if super_help:
            sources /= "super"
        if (not super_help and topic in PERSONAL_TOPICS) or (
            super_help and topic == "discuss"
        ):
            topic = "super" if super_help else PERSONAL_TOPICS[topic]
            directory = self.directory / "discuss"
            sources = self.directory.parent.parent / "commands/discuss"
        elif (not super_help and topic in DISCUSS_TOPICS) or (
            super_help and topic == "group-discuss"
        ):
            topic = "super" if super_help else DISCUSS_TOPICS[topic]
            directory = self.directory / "group-discuss"
            sources = self.directory.parent.parent / "commands/group-discuss"
        path = directory / f"{topic}-{location.lower()}.jpeg"
        try:
            data = path.read_bytes()
        except FileNotFoundError as exc:
            if topic == "help" or (sources / f"{topic}.md").is_file():
                raise BusinessError(
                    "帮助图片缺失，请联系 Super 重新执行 make publish 并安装。"
                ) from exc
            raise BusinessError(
                "没有对应的帮助页面，请使用 /help 或 /super help 查看目录。"
            ) from exc
        except OSError as exc:
            raise BusinessError(
                "帮助图片暂时无法读取，请联系 Super 检查安装文件。"
            ) from exc
        if not data.startswith(b"\xff\xd8\xff"):
            raise BusinessError("帮助图片不是有效的 JPEG，请联系 Super 重新构建。")
        return data
