"""Build an installable archive without runtime data, caches or development tests."""

import ast
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .check import check


def main():
    root = Path(__file__).resolve().parents[2]
    check(root)
    metadata = (root / "metadata.yaml").read_text(encoding="utf-8")
    version = re.search(r"^version:\s*(v[0-9.]+)\s*$", metadata, re.MULTILINE)
    if version is None:
        raise ValueError("metadata.yaml 缺少有效版本号。")
    names = [
        "__init__.py",
        "main.py",
        "metadata.yaml",
        "_conf_schema.json",
        "requirements.txt",
        "README.md",
        "DESIGN.md",
        "DEADLINE.md",
    ]
    names += [
        str(path.relative_to(root))
        for path in sorted((root / "src").rglob("*.py"))
        if "tooling" not in path.parts
    ]
    names += ["assets/fonts/NotoSansSC.ttf", "assets/fonts/OFL.txt"]
    for name in names:
        if name.endswith(".py"):
            ast.parse((root / name).read_text(encoding="utf-8"), filename=name)
    json.loads((root / "_conf_schema.json").read_text(encoding="utf-8"))
    output = root / "dist" / f"astrbot_plugin_kakobot-{version[1]}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(root / name, name)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(archive.read(name) == (root / name).read_bytes() for name in names)
        assert not any(
            name.endswith(
                (
                    "version.json",
                    ".sqlite3",
                    "access.json",
                    "roles.json",
                    "readonly.json",
                    "ddl_preferences.json",
                )
            )
            for name in archive.namelist()
        )
    print(output)


if __name__ == "__main__":
    main()
