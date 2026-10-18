"""DeepSeek search/fetch APIs authenticated exclusively with the group's key."""

import ipaddress
import json
from urllib.parse import urlsplit

from ...domain.errors import BusinessError

DEEPSEEK_TOOLS_BASE = "https://api.deepseek.com/v1/tools"


def validate_public_url(url):
    parsed = urlsplit(url)
    if (
        len(url) > 8192
        or parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise BusinessError("仅允许无认证的 HTTP(S) 网页 URL，最多 8192 字符。")
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise BusinessError("不允许本机或内网地址。")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return  # DNS/redirect/connection checks are performed by DeepSeek Fetch security policy.
    if not address.is_global:
        raise BusinessError("不允许本机或内网地址。")


async def _call(name, payload, policy, client, api_key):
    if not api_key:
        raise BusinessError("目标群未配置 API Key。")
    async with client.stream(
        "POST",
        DEEPSEEK_TOOLS_BASE + "/" + name,
        json=payload,
        headers={"Authorization": "Bearer " + api_key},
        timeout=policy["tool_timeout"],
        follow_redirects=False,
    ) as response:
        response.raise_for_status()
        body = bytearray()
        async for chunk in response.aiter_bytes():
            body.extend(chunk)
            if len(body) > policy["web_max_bytes"]:
                raise BusinessError("DeepSeek 工具响应超过大小限制。")
    return json.loads(body)


async def fetch_webpage(url, policy, client, api_key):
    validate_public_url(url)
    return await _call("fetch", {"url": url}, policy, client, api_key)


async def search_web(query, policy, client, api_key):
    if not isinstance(query, str) or not query.strip() or len(query) > 128:
        raise BusinessError("搜索词须为 1～128 字符的非空文本。")
    data = await _call(
        "search",
        {"query": query, "count": 3, "need_content": False},
        policy,
        client,
        api_key,
    )
    return [
        {k: row.get(k) for k in ("title", "url", "summary", "snippet")}
        for row in data["results"][:3]
    ]
