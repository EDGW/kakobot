"""Build an installable archive without runtime data, caches or development tests."""

import ast
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .check import check
from .docs_images.document import documentation_files


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
        "CHANGELOG.md",
        "src/UPDATE.md",
    ]
    names += [
        str(path.relative_to(root))
        for path in sorted((root / "src").rglob("*.py"))
        if "tooling" not in path.parts
    ]
    names += ["assets/fonts/NotoSansSC.ttf", "assets/fonts/OFL.txt"]
    names += [
        str(path.relative_to(root)) for path in sorted((root / "docs").rglob("*.md"))
    ]
    for source in documentation_files(root / "docs", root / "docs/pics"):
        relative = source.relative_to(root / "docs")
        for location in ("chat", "group"):
            image = (
                root
                / "docs/pics"
                / relative.parent
                / f"{relative.stem}-{location}.jpeg"
            )
            if not image.is_file() or not image.read_bytes().startswith(
                b"\xff\xd8\xff"
            ):
                raise ValueError(f"帮助图片缺失或无效：{image}；请运行 make publish。")
            names.append(str(image.relative_to(root)))
    changelog_image = root / "docs/pics/changelog.jpeg"
    if not changelog_image.is_file() or not changelog_image.read_bytes().startswith(
        b"\xff\xd8\xff"
    ):
        raise ValueError("更新日志图片缺失或无效；请运行 make publish。")
    names.append("docs/pics/changelog.jpeg")
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
