"""Read the installed version and the prebuilt root changelog image."""

import re
from pathlib import Path

from ...domain.errors import BusinessError

ROOT = Path(__file__).resolve().parents[3]


class ReleaseInfoStore:
    def __init__(self, root=ROOT):
        self.root = root

    def version(self):
        try:
            metadata = (self.root / "metadata.yaml").read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise BusinessError(
                "无法读取当前安装版本，请联系 Super 检查 metadata.yaml。"
            ) from exc
        match = re.search(
            r"^version:\s*(v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)\s*$", metadata, re.MULTILINE
        )
        if match is None:
            raise BusinessError(
                "metadata.yaml 中的版本号无效，请联系 Super 检查安装文件。"
            )
        return match[1]

    def changelog(self):
        try:
            data = (self.root / "docs/pics/changelog.jpeg").read_bytes()
        except OSError as exc:
            raise BusinessError(
                "更新日志图片无法读取，请联系 Super 重新执行 make publish 并安装。"
            ) from exc
        if not data.startswith(b"\xff\xd8\xff"):
            raise BusinessError("更新日志图片已损坏，请联系 Super 重新构建。")
        return data
