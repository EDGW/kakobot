"""Reject outbound QQ payloads containing configured API credentials."""

from collections.abc import Mapping


class SecretViolation(PermissionError):
    """A message was blocked without including its content in the exception."""

    def __init__(self):
        super().__init__("消息包含受保护的 API Key，已拦截发送。")


class SecretFilter:
    """Inspect nested payloads and text split across multiple message segments."""

    def __init__(self, config: Mapping):
        self.config = config
        self._keys: set[str] = set()
        self._refresh()

    def _refresh(self) -> None:
        key = str(self.config.get("api_key") or "").strip()
        if key:
            # Keep previously observed keys protected if live configuration changes.
            self._keys.add(key)

    def contains(self, payload) -> bool:
        self._refresh()
        return bool(self._keys) and (
            any(self._matches(text) for text in _strings(payload))
            or self._matches("".join(_text_fragments(payload)))
        )

    def _matches(self, text: str) -> bool:
        return any(key in text for key in self._keys)

    def check(self, payload) -> None:
        if self.contains(payload):
            raise SecretViolation()


def _strings(value):
    """Inspect string values, metadata, dictionary keys, and byte payloads."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, bytes):
        yield value.decode("utf-8", errors="replace")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _text_fragments(value):
    """Join visible text without JSON structure hiding a split credential."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        if value.get("type") == "text":
            data = value.get("data")
            if isinstance(data, Mapping):
                yield from _text_fragments(data.get("text", ""))
        else:
            for field in (
                "message",
                "messages",
                "content",
                "nodes",
                "data",
                "reply",
                "text",
            ):
                if field in value:
                    yield from _text_fragments(value[field])
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _text_fragments(item)
