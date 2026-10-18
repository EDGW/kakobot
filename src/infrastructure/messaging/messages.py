"""Bounded message-tree expansion with explicit provenance and cycle detection."""

import asyncio
import html
import re
from datetime import datetime

from ...domain.deadlines import BEIJING
from ...domain.errors import BusinessError
from ...domain.text import display_name

MAX_DEPTH = 4


def message_content(record):
    """NapCat may include both fields, with one of them an empty placeholder."""
    for field in ("message", "content"):
        value = record.get(field)
        if value not in (None, "", []):
            return value
    for field in ("message", "content"):
        if field in record and record[field] is not None:
            return record[field]
    return None


def segments(value) -> list[dict]:
    if isinstance(value, list):
        if any(not isinstance(item, dict) for item in value):
            raise BusinessError("消息包含无法解析的组件。")
        return value
    if not isinstance(value, str):
        raise BusinessError("不支持的消息格式，未导入任何任务。")
    # CQ strings may encode native references; plain fabricated @ text stays plain.
    result, cursor = [], 0
    for match in re.finditer(r"\[CQ:([a-z_]+)((?:,[^\]]*)?)\]", value):
        if match.start() > cursor:
            result.append(
                {
                    "type": "text",
                    "data": {"text": html.unescape(value[cursor : match.start()])},
                }
            )
        data = {}
        for pair in match[2].lstrip(",").split(","):
            key, sep, val = pair.partition("=")
            if sep:
                data[key] = html.unescape(val)
        result.append({"type": match[1], "data": data})
        cursor = match.end()
    if cursor < len(value):
        result.append({"type": "text", "data": {"text": html.unescape(value[cursor:])}})
    return result


def visible_text(parts) -> str:
    return "".join(
        str(item.get("data", {}).get("text", ""))
        if item.get("type") == "text"
        else " @" + str(item.get("data", {}).get("qq", "")) + " "
        if item.get("type") == "at"
        else ""
        for item in parts
    )


class MessageExpander:
    def __init__(self, gateway, secrets, received_at, *, readable_only=False):
        self.gateway, self.secrets, self.received_at = gateway, secrets, received_at
        self.readable_only = readable_only
        self.nodes, self.cache, self.queries, self.characters = [], {}, 0, 0

    async def expand(self, parts, actor):
        try:
            await asyncio.wait_for(
                self._node(
                    {"message": parts, "sender": {"user_id": actor}}, None, 0, ()
                ),
                timeout=20,
            )
        except asyncio.TimeoutError as exc:
            raise BusinessError("展开聊天记录超过20秒，未注册本包任务。") from exc
        for node in self.nodes:
            node["children"] = [
                child["node_id"]
                for child in self.nodes
                if child["parent_id"] == node["node_id"]
            ]
        self.secrets.check(self.nodes)
        return self.nodes

    async def _fetch(self, kind, identifier, path):
        if kind == "reply" and self.readable_only:
            raise BusinessError("仅分析可读取的文字，不查询历史回复。")
        key = (kind, str(identifier))
        if key in path:
            raise BusinessError("聊天记录含循环引用，未注册本包任务。")
        if key not in self.cache:
            self.queries += 1
            if self.queries > 20:
                raise BusinessError("聊天记录引用超过20次查询，未注册本包任务。")
            self.cache[key] = await (
                self.gateway.message(str(identifier))
                if kind == "reply"
                else self.gateway.forward(str(identifier))
            )
        return self.cache[key], path + (key,)

    @staticmethod
    def _check_depth(depth):
        if depth > MAX_DEPTH:
            raise BusinessError("聊天记录超过4层，未注册本包任务。")

    async def _reference(self, kind, data, parent, depth, path, *, forwarded=False):
        # Check before any remote lookup, including a fifth-level reference.
        self._check_depth(depth)
        content = message_content(data)
        identifier = data.get("id")
        next_path = path
        if identifier not in (None, ""):
            key = (kind, str(identifier))
            if key in path:
                raise BusinessError("聊天记录含循环引用，未注册本包任务。")
            next_path = path + (key,)
        if content not in (None, "", []):
            if kind == "reply":
                await self._node(data, parent, depth, next_path, forwarded=forwarded)
            else:
                if not isinstance(content, list):
                    raise BusinessError("合并转发内容格式不支持，未注册本包任务。")
                for item in content:
                    await self._forward_node(item, parent, depth, next_path)
            return
        if identifier not in (None, ""):
            fetched, next_path = await self._fetch(kind, identifier, path)
            if kind == "reply":
                await self._node(fetched, parent, depth, next_path, forwarded=forwarded)
            else:
                for item in fetched:
                    await self._forward_node(item, parent, depth, next_path)
        elif content is not None:
            # An explicitly empty inline record needs no API lookup.
            if kind == "reply":
                await self._node(data, parent, depth, next_path, forwarded=forwarded)
        else:
            raise BusinessError("引用缺少ID或正文，未注册本包任务。")

    async def _node(self, record, parent, depth, path, *, forwarded=False):
        self._check_depth(depth)
        if len(self.nodes) >= 500:
            raise BusinessError("聊天记录超过500个节点，未注册本包任务。")
        if not isinstance(record, dict):
            raise BusinessError("聊天记录节点格式不支持，未注册本包任务。")
        sender = record.get("sender") or {}
        if not isinstance(sender, dict):
            raise BusinessError("记录作者格式无效，未注册本包任务。")
        stamp, time_source = self.received_at, "submission"
        value = record.get("time")
        if isinstance(value, bool):
            raise BusinessError("记录源时间无效，未注册本包任务。")
        if value not in (None, "", 0, "0"):
            try:
                candidate = float(value)
                if not 0 < candidate <= self.received_at + 300:
                    raise ValueError("unreasonable source timestamp")
                datetime.fromtimestamp(candidate, BEIJING)
                stamp, time_source = candidate, "source"
            except (TypeError, ValueError, OverflowError, OSError) as exc:
                raise BusinessError("记录源时间无效，未注册本包任务。") from exc
        node = {
            "node_id": f"n{len(self.nodes) + 1}",
            "type": "message",
            "source_forward_id": next(
                (
                    identifier
                    for kind, identifier in reversed(path)
                    if kind == "forward"
                ),
                "",
            ),
            "parent_id": parent,
            "author_id": str(
                sender.get("user_id", record.get("user_id", record.get("uin", "")))
            ),
            "author_display": display_name(
                sender.get("card")
                or sender.get("nickname")
                or record.get("nickname")
                or record.get("name", ""),
                100,
            ),
            "sent_at": stamp,
            "local_time": datetime.fromtimestamp(stamp, BEIJING).isoformat(),
            "time_source": time_source,
            "source_message_id": str(record.get("message_id", "")),
            "text": "",
            "text_segments": [],
            "native_mentions": [],
            "omitted_reply_count": 0,
        }
        self.nodes.append(node)
        content = message_content(record)
        if content is None:
            raise BusinessError("聊天记录节点缺少正文，未注册本包任务。")
        self.secrets.check(content)
        for index, part in enumerate(segments(content)):
            kind, data = part.get("type"), part.get("data") or {}
            if not isinstance(data, dict):
                raise BusinessError("消息组件数据格式无效。")
            if kind == "text":
                value = str(data.get("text", ""))
                node["text"] += value
                node["text_segments"].append(value)
            elif kind == "at":
                user = str(data.get("qq", ""))
                node["native_mentions"].append({"qq_id": user, "position": index})
                node["text"] += f"@{user}[{user}]"
            elif kind in {"reply", "forward"}:
                if kind == "reply" and (
                    forwarded
                    or (self.readable_only and message_content(data) in (None, "", []))
                ):
                    # Forwarded reply IDs belong to the source conversation,
                    # not the bot's local message cache. Read only body text.
                    node["omitted_reply_count"] += 1
                    continue
                await self._reference(
                    kind, data, node["node_id"], depth + 1, path, forwarded=forwarded
                )
            elif kind == "node":
                await self._forward_node(part, node["node_id"], depth + 1, path)
            elif kind in {
                "image",
                "record",
                "audio",
                "video",
                "file",
                "face",
                "json",
                "xml",
                "markdown",
            }:
                node["text"] += f"[{kind}]"
            else:
                raise BusinessError(
                    f"记录中存在不支持的组件 {str(kind)[:30]}，未注册本包任务。"
                )
        self.characters += len(node["text"]) + len(node["author_display"])
        if self.characters > 50000:
            raise BusinessError("聊天记录超过50000字，未注册本包任务。")

    async def _forward_node(self, item, parent, depth, path):
        self._check_depth(depth)
        if not isinstance(item, dict):
            raise BusinessError("转发记录节点格式不支持，未注册本包任务。")
        if item.get("type") == "node":
            data = item.get("data") or {}
            if not isinstance(data, dict):
                raise BusinessError("转发记录节点数据无效，未注册本包任务。")
            if message_content(data) not in (None, "", []):
                await self._node(data, parent, depth, path, forwarded=True)
            elif "id" in data:
                # A forward-resource ID is not a cached ordinary message ID.
                await self._reference("forward", data, parent, depth, path)
            elif message_content(data) is not None:
                await self._node(data, parent, depth, path, forwarded=True)
            else:
                raise BusinessError("嵌套节点内容不可读，未注册本包任务。")
        elif "message" in item or "content" in item:
            await self._node(item, parent, depth, path, forwarded=True)
        elif item.get("type"):
            await self._node({"message": [item]}, parent, depth, path, forwarded=True)
        else:
            raise BusinessError("转发记录格式不支持，未注册本包任务。")


def command_body(ctx, subcommand=""):
    """Strip the top-level text prefix while retaining leading quote components."""
    pattern = (
        r"^\s*"
        + re.escape(ctx.command[0])
        + (r"\s+" + re.escape(subcommand) if subcommand else "")
        + r"(?:\s+|$)"
    )
    indices, initial, started = [], "", False
    for index, part in enumerate(ctx.segments):
        if part.get("type") == "text":
            started = True
            indices.append(index)
            initial += str(part.get("data", {}).get("text", ""))
        elif started:
            break
    match = re.match(pattern, initial, re.IGNORECASE)
    if not match:
        raise BusinessError("命令前缀格式无效。")
    remaining, output = match.end(), []
    for index, part in enumerate(ctx.segments):
        if remaining and index in indices:
            value = str(part.get("data", {}).get("text", ""))
            consumed = min(remaining, len(value))
            remaining -= consumed
            if value[consumed:]:
                output.append({"type": "text", "data": {"text": value[consumed:]}})
        else:
            output.append(part)
    return output
