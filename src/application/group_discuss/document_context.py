"""Keep full document results in archives, small references in later turns."""

import hashlib
import json
from dataclasses import replace

from pydantic_ai.messages import ToolReturnPart


def reference(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {"note": "历史文档结果已归档，需要时重新查询。"}
    if not isinstance(value, dict):
        return {"note": "历史文档结果已归档，需要时重新查询。"}
    if "documents" in value:
        return {"documents": [reference(item) for item in value["documents"]]}
    result = {key: value[key] for key in ("path", "audience", "sha256", "offset", "next_offset", "results") if key in value}
    if "text" in value:
        text = str(value["text"])
        result.update({
            "sha256": value.get("sha256") or hashlib.sha256(text.encode()).hexdigest(),
            "excerpt": text[:240],
            "note": "仅为历史摘录，不能据此猜测参数；需完整规则时按路径重新读取。当前轮结论见随后回答。",
        })
    return result


def project_documents(messages):
    return [replace(message, parts=[
        replace(part, content=json.dumps(reference(part.content), ensure_ascii=False))
        if isinstance(part, ToolReturnPart) and part.tool_name == "query_docs"
        else part
        for part in message.parts
    ]) for message in messages]


def deduplicate_documents(value, seen):
    if isinstance(value, dict) and "documents" in value:
        return {**value, "documents": [deduplicate_documents(item, seen) for item in value["documents"]]}
    if not isinstance(value, dict) or "text" not in value:
        return value
    key = (value.get("path"), value.get("audience", "user"), value.get("offset", 0), hashlib.sha256(value["text"].encode()).hexdigest())
    if key in seen:
        return {**reference(value), "note": "本轮已读取相同内容，完整文档仍在本轮工具结果中。"}
    seen.add(key)
    return value
