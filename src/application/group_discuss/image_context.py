"""Project OneBot image components into model inputs without local downloads."""

from dataclasses import replace
from urllib.parse import urlsplit

from pydantic_ai import ImageUrl
from pydantic_ai.messages import UserPromptPart

from ...domain.errors import BusinessError


def message_images(segments):
    images = []
    for segment in segments:
        if segment.get("type") != "image":
            continue
        data = segment.get("data") or {}
        # file may be a platform-local filename; only remote URLs can be sent.
        url = data.get("url") or data.get("file")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
            valid = (
                parsed and parsed.scheme in {"https", "http"} and parsed.hostname
                and not parsed.username and not parsed.password
            )
        except ValueError:
            valid = False
        if not valid:
            raise BusinessError("图片缺少可供模型读取的 HTTP(S) 地址，请重新发送图片。")
        # QQ download URLs often have no extension. Responses only needs the URL;
        # the generic media type prevents the SDK from guessing from that path.
        images.append(ImageUrl(url, media_type="image/*", force_download=False))
    return images


def project_images(messages, allow_images):
    """A live switch also removes previously archived images from model context."""
    if allow_images:
        return messages
    return [replace(message, parts=[
        replace(part, content=[
            "[历史图片已禁用]" if isinstance(item, ImageUrl) else item
            for item in part.content
        ])
        if isinstance(part, UserPromptPart) and not isinstance(part.content, str)
        else part
        for part in message.parts
    ]) for message in messages]
