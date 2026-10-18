"""Library-backed public-web retrieval and extraction; no computer tools."""

import asyncio
from urllib.parse import urljoin, urlsplit

import httpx
import safehttpx
import trafilatura

from ...domain.errors import BusinessError


async def fetch_webpage(url, policy):
    for hop in range(policy["web_max_redirects"] + 1):
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 80, 443)
        ):
            raise BusinessError("只允许无认证的公开 HTTP(S) 网页。")
        # safehttpx resolves a public IP and pins the connection to it while
        # retaining TLS SNI. Do not use its proxy/whitelist bypass paths.
        ip = await safehttpx.async_validate_url(parsed.hostname)
        transport = safehttpx.AsyncSecureTransport(ip)
        async with httpx.AsyncClient(
            transport=transport, trust_env=False, timeout=policy["tool_timeout"]
        ) as client:
            async with client.stream(
                "GET",
                url,
                follow_redirects=False,
                headers={"User-Agent": "KakoBot/GroupDiscuss"},
            ) as response:
                if response.is_redirect:
                    if (
                        hop == policy["web_max_redirects"]
                        or "location" not in response.headers
                    ):
                        raise BusinessError("网页重定向次数超限。")
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if not any(
                    t in content_type
                    for t in ("text/", "application/xhtml+xml", "application/json")
                ):
                    raise BusinessError("此链接不是可读取的文本网页。")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > policy["web_max_bytes"]:
                        raise BusinessError("网页超过下载大小限制。")
        text = bytes(body).decode(response.encoding or "utf-8", errors="replace")
        if "html" in content_type:
            text = await asyncio.to_thread(
                trafilatura.extract,
                text,
                include_comments=False,
                include_tables=True,
                url=url,
            )
        return {"url": url, "text": text or "未提取到正文。"}
    raise BusinessError("网页读取失败。")


async def search_web(query, policy, client):
    if not policy["search_api_key"]:
        raise BusinessError("系统未配置搜索服务密钥。")
    response = await client.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": 3, "include_raw_content": False},
        headers={"Authorization": "Bearer " + policy["search_api_key"]},
        timeout=policy["tool_timeout"],
    )
    response.raise_for_status()
    return [
        {k: row.get(k) for k in ("title", "url", "content")}
        for row in response.json().get("results", [])[:3]
    ]
