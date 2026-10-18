"""Static validation only: never import the plugin, AstrBot or network clients."""

import ast
import json
import re
from pathlib import Path


def check(root):
    files = [
        root / "main.py",
        root / "__init__.py",
        *sorted((root / "src").rglob("*.py")),
    ]
    trees = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path), feature_version=(3, 10))
        compile(tree, str(path), "exec")
        trees[path] = tree
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            base = path.parent
            for _ in range(node.level - 1):
                base = base.parent
            target = base.joinpath(*(node.module or "").split("."))
            if (
                not target.with_suffix(".py").is_file()
                and not (target / "__init__.py").is_file()
            ):
                raise ValueError(
                    f"本地导入不存在：{path.relative_to(root)}:{node.lineno}"
                )
            domain = root / "src/domain"
            if path.is_relative_to(domain) and not target.is_relative_to(domain):
                raise ValueError("领域层依赖了其他实现层。")
    root_python = {path.name for path in root.glob("*.py")}
    if root_python != {"__init__.py", "main.py"}:
        raise ValueError("根目录仍有入口以外的 Python 实现。")
    metadata = (root / "metadata.yaml").read_text(encoding="utf-8")
    version = re.search(r"^version:\s*v([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)\s*$", metadata, re.MULTILINE)
    assignments = trees[root / "src/infrastructure/storage/migration.py"].body
    expected = next(
        ast.literal_eval(node.value)
        for node in assignments
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets
        )
    )
    if version is None or version[1] != expected:
        raise ValueError("插件版本与迁移目标版本不一致。")
    config = json.loads((root / "_conf_schema.json").read_text(encoding="utf-8"))
    for key in ("enabled_analysis_tasks", "autoanalysis_disabled_users"):
        if not isinstance(config[key]["default"], list):
            raise ValueError(f"配置 {key} 的默认值应为列表。")
    font = root / "assets/fonts/NotoSansSC.ttf"
    if not font.is_file() or font.read_bytes()[:4] != b"\x00\x01\x00\x00":
        raise ValueError("DDL 图片缺少有效的随包中文 TrueType 字体。")
    if "SIL OPEN FONT LICENSE" not in (root / "assets/fonts/OFL.txt").read_text(
        encoding="utf-8"
    ):
        raise ValueError("中文字体缺少 OFL 许可证。")
    for document in [
        root / "README.md",
        root / "DESIGN.md",
        *sorted((root / "docs").rglob("*.md")),
    ]:
        name = str(document.relative_to(root))
        if name == "DESIGN.md" and not document.is_file():
            continue
        body = document.read_text(encoding="utf-8")
        if len(re.findall(r"^```", body, re.MULTILINE)) % 2:
            raise ValueError(f"{name} 代码围栏不完整。")
        for block in re.findall(r"```json\n(.*?)\n```", body, re.DOTALL):
            json.loads(block)
        if name != "DESIGN.md":
            for target in re.findall(r"\]\(([^\s)]+)\)", body):
                if "://" not in target and not target.startswith("#"):
                    if not (document.parent / target.split("#")[0]).is_file():
                        raise ValueError(f"{name} 文档链接不存在：{target}")
    print(
        f"静态校验通过：{len(files)} 个 Python 文件、层次与导入路径、版本 {expected}、配置及文档。"
    )


def main():
    check(Path(__file__).resolve().parents[2])


if __name__ == "__main__":
    main()
