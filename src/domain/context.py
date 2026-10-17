"""Transport-independent event and scope values."""

import re
from dataclasses import dataclass, field

from .errors import BusinessError

Scope = tuple[str, str, str, str]  # platform, bot, CHAT|GROUP, conversation


def qq_id(value: object) -> str:
    text = str(value).strip()
    if not re.fullmatch(r"[0-9]{1,20}", text) or int(text) == 0:
        raise BusinessError("QQ 号和群号必须是大于零的数字。")
    return str(int(text))


@dataclass(frozen=True)
class CommandContext:
    actor: str
    bot: str
    platform: str
    group: str
    message_id: str
    received_at: float
    text: str
    segments: list[dict] = field(default_factory=list)
    mentioned_bot: bool = False
    text_only: bool = True

    @property
    def location(self) -> str:
        return "GROUP" if self.group else "CHAT"

    @property
    def scope(self) -> Scope:
        return self.platform, self.bot, self.location, self.group or self.actor

    @property
    def command(self) -> tuple[str, str] | None:
        if self.group and not self.mentioned_bot:
            return None
        parts = self.text.strip().split(maxsplit=1)
        if not parts:
            return None
        if parts[0].startswith("/"):
            return parts[0].lower(), parts[1] if len(parts) > 1 else ""
        if self.group and self.text_only and parts == ["你好"]:
            return "hello", ""
        return None
