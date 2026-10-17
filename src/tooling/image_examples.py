"""Generate requested DDL view samples locally, without AstrBot or AI calls."""

from datetime import datetime, timedelta
from itertools import count
from pathlib import Path

from ..domain.deadlines import BEIJING
from ..presentation.deadline_image import render_deadlines


def main():
    root = Path(__file__).resolve().parents[2]
    output = root / "examples/ddl-view"
    output.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 10, 17, 10, 0, tzinfo=BEIJING)
    identifiers = count(1)

    def task(title, **offset):
        return {
            "id": next(identifiers),
            "title": title,
            "deadline": (now + timedelta(**offset)).timestamp(),
        }

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

    def group_task(title, participants, **offset):
        return {**task(title, **offset), "participant_label": participants}

    group_examples = {
        "05-group-dinner.png": [
            group_task("叫AAA请BBB吃饭", "AAA(33221122)、BBB(11223344)", hours=9),
            group_task(
                "BBB提交复变函数课第三次作业（第5章）",
                "BBB(11223344)",
                days=2,
                hours=8,
            ),
        ],
        "06-group-courses.png": [
            group_task("AAA提交物理作业（第10章）", "AAA(33221122)", hours=2),
            group_task(
                "AAA与BBB提交机器学习课程项目",
                "AAA(33221122)、BBB(11223344)",
                hours=10,
            ),
            group_task("CCC提交未知课程作业", "CCC(55667788)", days=5),
        ],
        "07-group-more-than-ten.png": [
            {**item, "participant_label": "AAA(33221122)、BBB(11223344)"}
            for item in examples["02-more-than-ten.png"]
        ],
        "08-group-many-participants.png": [
            group_task(
                "课程项目小组完成联合答辩",
                "、".join(
                    f"小组成员{index}(556677{index:02d})" for index in range(1, 9)
                ),
                days=2,
            ),
        ],
    }
    for name, tasks in examples.items():
        path = output / name
        path.write_bytes(render_deadlines(tasks, now.timestamp()))
        print(path)
    for name, tasks in group_examples.items():
        path = output / name
        path.write_bytes(render_deadlines(tasks, now.timestamp(), group=True))
        print(path)


if __name__ == "__main__":
    main()
