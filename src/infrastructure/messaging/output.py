"""Render plugin text as ordinary messages or one merged-forward record."""

from ...domain.context import qq_id

FORWARD_LINE_LIMIT = 15
TEXT_CHUNK_SIZE = 2500


def needs_forward(text):
    return len(text.splitlines()) > FORWARD_LINE_LIMIT


def format_text_output(action, params, *, log=False):
    """Return API calls only; callers must guard the complete original first."""
    if action not in {"send_group_msg", "send_private_msg"}:
        return [(action, params)]
    message = params.get("message")
    if not isinstance(message, list) or any(
        not isinstance(part, dict) or part.get("type") not in {"text", "at"}
        for part in message
    ):
        return [(action, params)]
    text = "".join(
        str(part.get("data", {}).get("text", ""))
        for part in message
        if part["type"] == "text"
    )
    mentions = [part for part in message if part["type"] == "at"]
    chunks = [
        text[start : start + TEXT_CHUNK_SIZE]
        for start in range(0, len(text), TEXT_CHUNK_SIZE)
    ] or [""]
    if needs_forward(text):
        author = qq_id(params.get("self_id", ""))
        destination = {key: value for key, value in params.items() if key != "message"}
        nodes = [
            {
                "type": "node",
                "data": {
                    "user_id": author,
                    "nickname": "KakoBot",
                    "content": [{"type": "text", "data": {"text": chunk}}],
                },
            }
            for chunk in chunks
        ]
        calls = []
        if mentions:
            # At components inside a forward do not reliably notify QQ members.
            calls.append(
                (
                    action,
                    {
                        **params,
                        "message": mentions
                        + [
                            {
                                "type": "text",
                                "data": {"text": "\n[KakoBot] 详情见合并聊天记录。"},
                            }
                        ],
                    },
                )
            )
        calls.append(
            (
                "send_group_forward_msg"
                if action == "send_group_msg"
                else "send_private_forward_msg",
                {**destination, "messages": nodes},
            )
        )
        return calls
    if len(chunks) == 1:
        return [(action, params)]
    calls = []
    for index, chunk in enumerate(chunks, 1):
        label = "日志分段" if log else "分段"
        calls.append(
            (
                action,
                {
                    **params,
                    "message": (mentions if index == 1 else [])
                    + [
                        {
                            "type": "text",
                            "data": {
                                "text": f"[KakoBot] {label} {index}/{len(chunks)}\n{chunk}"
                            },
                        }
                    ],
                },
            )
        )
    return calls
