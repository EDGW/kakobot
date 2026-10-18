"""CLI for rendering every docs Markdown file into CHAT and GROUP JPEGs."""

import argparse
import shutil
from pathlib import Path

from .changelog import render_changelog
from .document import cards_for, documentation_files, parse_document
from .render import render_document

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(
        description="将 Markdown 文档渲染为 CHAT/GROUP 卡片 JPEG。"
    )
    parser.add_argument(
        "--docs", type=Path, default=ROOT / "docs", help="源文档目录，默认仓库 docs/"
    )
    parser.add_argument("--output", type=Path, help="输出目录，默认源文档目录下 pics/")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=ROOT / "CHANGELOG.md",
        help="更新日志源文件，默认仓库 CHANGELOG.md",
    )
    parser.add_argument(
        "--width", type=int, default=1200, help="图片宽度，默认1200像素，至少640"
    )
    parser.add_argument(
        "--font-size", type=int, default=25, help="正文字号，默认25像素，范围16至48"
    )
    args = parser.parse_args()
    source = args.docs.resolve()
    output = (args.output or source / "pics").resolve()
    if not source.is_dir():
        parser.error("源文档目录不存在。")
    if not 640 <= args.width <= 65000 or not 16 <= args.font_size <= 48:
        parser.error("width 须在640至65000之间，font-size 须在16至48之间。")
    files = documentation_files(source, output)
    if not files:
        parser.error("源目录中没有可生成图片的功能文档。")
    # A complete rebuild must not retain images from deleted or moved pages.
    if source.is_relative_to(output) or any(
        path.is_relative_to(output) for path in source.rglob("*.md")
    ):
        parser.error("输出目录不能包含源文档，拒绝清理。")
    if output.exists():
        if not output.is_dir():
            parser.error("输出路径必须是目录。")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in files:
        document = parse_document(path.read_text(encoding="utf-8"))
        title = next(
            (child.title for child in document.children if child.level == 1), path.stem
        )
        relative = path.relative_to(source)
        for location in ("CHAT", "GROUP"):
            cards = cards_for(document, location)
            if not cards:
                cards = [("暂无内容", ["此文档在当前会话类型下没有可展示的内容。"])]
            elif document.locations() and location not in document.locations():
                cards.append(
                    ("当前会话不可用", ["此文档没有提供该会话类型的命令入口。"])
                )
            target = (
                output / relative.parent / f"{relative.stem}-{location.lower()}.jpeg"
            )
            width, height = render_document(
                title,
                relative.as_posix(),
                cards,
                location,
                target,
                width=args.width,
                size=args.font_size,
            )
            print(f"{target} ({width} × {height})")
            count += 1
    target = output / "changelog.jpeg"
    width, height = render_changelog(
        args.changelog, target, width=args.width, size=args.font_size
    )
    print(f"{target} ({width} × {height})")
    print(f"完成：{len(files)} 个功能文档及更新日志，{count + 1} 张 JPEG。")


if __name__ == "__main__":
    main()
