"""Read the bundled update announcement afresh for each default broadcast."""

from pathlib import Path

from ....domain.errors import BusinessError

UPDATE_PATH = Path(__file__).resolve().parents[3] / "UPDATE.md"


def load_update():
    try:
        content = UPDATE_PATH.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise BusinessError(
            "无法读取 src/UPDATE.md，请检查文件及 UTF-8 编码。"
        ) from exc
    if not content:
        raise BusinessError("src/UPDATE.md 内容为空，未发送广播。")
    return content
