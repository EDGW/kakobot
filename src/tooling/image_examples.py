"""Generate requested DDL view samples locally, without AstrBot or AI calls."""

from datetime import datetime, timedelta
from pathlib import Path

from ..domain.deadlines import BEIJING
from ..presentation.deadline_image import render_deadlines


def main():
    root = Path(__file__).resolve().parents[2]
    output = root / "examples/ddl-view"
    output.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 10, 17, 10, 0, tzinfo=BEIJING)

    def task(title, **offset):
        return {"title": title, "deadline": (now + timedelta(**offset)).timestamp()}

    examples = {
        "01-colors.png": [
            task("提交项目最终报告", days=5, hours=8),
            task("算法作业 · 第四章", hours=2, minutes=20),
            task("物理实验数据整理", days=1, hours=2),
            task("完成小组汇报幻灯片", hours=9),
        ],
        "02-more-than-ten.png": [
            task(title, hours=hours)
            for title, hours in (
                ("提交课程选题", 1),
                ("确认实验分组", 2),
                ("整理采访记录", 5),
                ("提交本周学习总结", 10),
                ("线性代数作业", 26),
                ("项目中期汇报", 34),
                ("英语阅读报告", 50),
                ("完成调研问卷", 70),
                ("实验报告终稿", 92),
                ("学期项目答辩", 116),
                ("准备下一次例会", 140),
                ("提交结课论文", 164),
                ("整理学期归档", 188),
            )
        ],
        "03-long-titles.png": [
            task("项目最终验收报告与完整附件材料提交截止", minutes=45),
            task("Machine Learning · Final Project", days=2, hours=6),
            task(
                "关于本学期跨学科综合实践项目结题报告及附件材料汇总提交的最后期限",
                days=8,
            ),
        ],
        "04-empty.png": [],
    }
    for name, tasks in examples.items():
        path = output / name
        path.write_bytes(render_deadlines(tasks, now.timestamp()))
        print(path)


if __name__ == "__main__":
    main()
