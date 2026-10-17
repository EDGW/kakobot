"""SQLite repositories for isolated CHAT/GROUP tasks and durable analysis dedupe."""

import asyncio
import json
import math
import sqlite3
from pathlib import Path

from ..domain.context import Scope, qq_id
from ..domain.deadlines import title_key
from ..domain.errors import BusinessError

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS tasks (platform TEXT NOT NULL,bot TEXT NOT NULL,location TEXT NOT NULL CHECK(location IN ('CHAT','GROUP')),conversation TEXT NOT NULL,id INTEGER NOT NULL,title TEXT NOT NULL,deadline REAL NOT NULL,creator TEXT NOT NULL,created REAL NOT NULL,targets TEXT NOT NULL,cancelled INTEGER NOT NULL DEFAULT 0,method TEXT NOT NULL,source TEXT NOT NULL DEFAULT '{}',signature TEXT,PRIMARY KEY(platform,bot,location,conversation,id))",
    "CREATE TABLE IF NOT EXISTS notifications (platform TEXT NOT NULL,bot TEXT NOT NULL,location TEXT NOT NULL,conversation TEXT NOT NULL,ddl_id INTEGER NOT NULL,at REAL NOT NULL,state TEXT NOT NULL,PRIMARY KEY(platform,bot,location,conversation,ddl_id,at),FOREIGN KEY(platform,bot,location,conversation,ddl_id) REFERENCES tasks(platform,bot,location,conversation,id))",
    "CREATE INDEX IF NOT EXISTS notifications_due ON notifications(state,at)",
    "CREATE TABLE IF NOT EXISTS analysis_events (platform TEXT NOT NULL,bot TEXT NOT NULL,actor TEXT NOT NULL,message_id TEXT NOT NULL,task_type TEXT NOT NULL,state TEXT NOT NULL,PRIMARY KEY(platform,bot,actor,message_id,task_type))",
    "CREATE TABLE IF NOT EXISTS analysis_packages (platform TEXT NOT NULL,bot TEXT NOT NULL,actor TEXT NOT NULL,task_type TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(platform,bot,actor,task_type,digest))",
)
WHERE = "platform=? AND bot=? AND location=? AND conversation=?"


def initialize_schema(db):
    for statement in SCHEMA:
        db.execute(statement)


def validate_database(db):
    if db.execute("PRAGMA user_version").fetchone()[0] != 2:
        raise ValueError("DDL 数据结构版本不是2。")
    if (
        db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
        or db.execute("PRAGMA foreign_key_check").fetchall()
    ):
        raise ValueError("DDL 数据库完整性校验失败。")
    required = {
        "tasks": {
            "platform",
            "bot",
            "location",
            "conversation",
            "id",
            "title",
            "deadline",
            "creator",
            "created",
            "targets",
            "cancelled",
            "method",
            "source",
            "signature",
        },
        "notifications": {
            "platform",
            "bot",
            "location",
            "conversation",
            "ddl_id",
            "at",
            "state",
        },
        "analysis_events": {
            "platform",
            "bot",
            "actor",
            "message_id",
            "task_type",
            "state",
        },
        "analysis_packages": {
            "platform",
            "bot",
            "actor",
            "task_type",
            "digest",
            "result",
        },
    }
    for table, columns in required.items():
        actual = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
        if actual != columns:
            raise ValueError(f"DDL 数据表 {table} 结构不完整。")
    for row in db.execute(
        "SELECT location,conversation,creator,targets,title,deadline,created,cancelled,source FROM tasks"
    ):
        (
            location,
            conversation,
            creator,
            targets,
            title,
            deadline,
            created,
            cancelled,
            source,
        ) = row
        values = json.loads(targets)
        if (
            location not in {"CHAT", "GROUP"}
            or qq_id(conversation) != conversation
            or qq_id(creator) != creator
            or not isinstance(values, list)
            or len(values) > 20
            or any(
                not isinstance(value, str) or qq_id(value) != value for value in values
            )
            or len(set(values)) != len(values)
            or not isinstance(title, str)
            or not 1 <= len(title) <= 200
            or not math.isfinite(deadline)
            or not math.isfinite(created)
            or cancelled not in {0, 1}
            or not isinstance(json.loads(source), dict)
        ):
            raise ValueError("DDL 任务数据无效。")
        if location == "CHAT" and (
            creator != conversation or any(value != conversation for value in values)
        ):
            raise ValueError("个人任务空间或通知对象不属于所有者。")
    for at, state in db.execute("SELECT at,state FROM notifications"):
        if not math.isfinite(at) or state not in {
            "pending",
            "sending",
            "sent",
            "skipped",
            "cancelled",
            "failed",
            "uncertain",
        }:
            raise ValueError("DDL 提醒时间或发送状态无效。")


class DeadlineStore:
    def __init__(self, path: Path, now: float):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        validate_database(self.db)
        self.lock = asyncio.Lock()
        with self.db:
            self.db.execute(
                "UPDATE notifications SET state='uncertain' WHERE state='sending'"
            )
            self.db.execute(
                "UPDATE notifications SET state='skipped' WHERE state='pending' AND at<=?",
                (now,),
            )
            self.db.execute(
                "UPDATE analysis_events SET state='interrupted' WHERE state='processing'"
            )
        self.last_scan = now

    def close(self):
        self.db.close()

    def private_contacts(self):
        return {
            tuple(row)
            for row in self.db.execute(
                "SELECT platform,bot,conversation FROM tasks WHERE location='CHAT' "
                "UNION SELECT platform,bot,actor FROM analysis_events"
            )
        }

    def get(self, scope: Scope, identifier: int) -> dict:
        row = self.db.execute(
            "SELECT * FROM tasks WHERE " + WHERE + " AND id=?", (*scope, identifier)
        ).fetchone()
        if row is None:
            raise BusinessError("当前会话没有这个 DDL。")
        task = dict(row)
        task["targets"] = json.loads(task["targets"])
        task["reminders"] = [
            dict(item)
            for item in self.db.execute(
                "SELECT at,state FROM notifications WHERE "
                + WHERE
                + " AND ddl_id=? ORDER BY at",
                (*scope, identifier),
            )
        ]
        return task

    def list(self, scope: Scope, now: float):
        return [
            self.get(scope, row[0])
            for row in self.db.execute(
                "SELECT id FROM tasks WHERE "
                + WHERE
                + " AND cancelled=0 AND targets!='[]' AND deadline>? ORDER BY deadline,id",
                (*scope, now),
            )
        ]

    def create_batch(
        self,
        scope,
        actor,
        proposals,
        method,
        now,
        event=None,
        package=None,
        *,
        existing_ids=(),
        updates=(),
    ):
        identifiers = [(identifier, False) for identifier in existing_ids]
        with self.db:
            for change in updates:
                self._apply_change(scope, actor, change, now)
                identifiers.append((change.previous["id"], False))
            for plan, targets, source, signature in proposals:
                existing = (
                    self.db.execute(
                        "SELECT id FROM tasks WHERE "
                        + WHERE
                        + " AND signature=? AND cancelled=0 AND targets!='[]' AND deadline>?",
                        (*scope, signature, now),
                    ).fetchone()
                    if signature
                    else None
                )
                if existing is None and method == "auto":
                    existing = next(
                        (
                            row
                            for row in self.db.execute(
                                "SELECT id,title,targets FROM tasks WHERE "
                                + WHERE
                                + " AND deadline=? AND deadline>? AND cancelled=0 AND targets!='[]'",
                                (*scope, plan.deadline, now),
                            )
                            if title_key(row["title"]) == title_key(plan.title)
                            and sorted(json.loads(row["targets"])) == sorted(targets)
                        ),
                        None,
                    )
                if existing:
                    identifiers.append((existing[0], False))
                    continue
                identifier = self.db.execute(
                    "SELECT COALESCE(MAX(id),0)+1 FROM tasks WHERE " + WHERE, scope
                ).fetchone()[0]
                self.db.execute(
                    "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?,?)",
                    (
                        *scope,
                        identifier,
                        plan.title,
                        plan.deadline,
                        actor,
                        now,
                        json.dumps(targets),
                        method,
                        json.dumps(source),
                        signature,
                    ),
                )
                self.db.executemany(
                    "INSERT INTO notifications VALUES (?,?,?,?,?,?,'pending')",
                    [(*scope, identifier, at) for at in plan.reminders if at > now],
                )
                identifiers.append((identifier, True))
            unique = {}
            for identifier, created in identifiers:
                unique[identifier] = unique.get(identifier, False) or created
            identifiers = list(unique.items())
            if event:
                self.db.execute(
                    "UPDATE analysis_events SET state='complete' WHERE platform=? AND bot=? AND actor=? AND message_id=? AND task_type=?",
                    event,
                )
            if package:
                self.db.execute(
                    "INSERT OR REPLACE INTO analysis_packages VALUES (?,?,?,?,?,?)",
                    (*package, json.dumps([value[0] for value in identifiers])),
                )
        return identifiers

    def _apply_change(self, scope, actor, change, now):
        previous, plan = change.previous, change.plan
        if (
            scope[2:] != ("CHAT", actor)
            or tuple(
                previous[key] for key in ("platform", "bot", "location", "conversation")
            )
            != scope
        ):
            raise BusinessError("只能修改本人的个人 DDL。")
        current = self.get(scope, previous["id"])
        if (
            current["cancelled"]
            or current["targets"] != [actor]
            or current["creator"] != actor
            or current["deadline"] <= now
            or any(
                current[key] != previous[key]
                for key in ("title", "deadline", "source", "targets")
            )
        ):
            raise BusinessError(
                f"DDL #{previous['id']} 已变更或失效，请重新提交修改要求。"
            )
        self.db.execute(
            "UPDATE tasks SET title=?,deadline=?,source=?,signature=NULL WHERE "
            + WHERE
            + " AND id=?",
            (
                plan.title,
                plan.deadline,
                json.dumps(change.source),
                *scope,
                current["id"],
            ),
        )
        if not change.replace_reminders:
            return
        self.db.execute(
            "UPDATE notifications SET state='cancelled' WHERE "
            + WHERE
            + " AND ddl_id=? AND state='pending'",
            (*scope, current["id"]),
        )
        # Keep delivery history; only unsubmitted/cancelled future nodes can be
        # activated. Sent, failed and uncertain sends are never replayed.
        self.db.executemany(
            "INSERT INTO notifications VALUES (?,?,?,?,?,?,'pending') "
            "ON CONFLICT(platform,bot,location,conversation,ddl_id,at) DO UPDATE SET state='pending' "
            "WHERE notifications.state IN ('pending','cancelled')",
            [(*scope, current["id"], at) for at in plan.reminders if at > now],
        )

    def begin_event(self, key):
        with self.db:
            return (
                self.db.execute(
                    "INSERT OR IGNORE INTO analysis_events VALUES (?,?,?,?,?,'processing')",
                    key,
                ).rowcount
                == 1
            )

    def fail_event(self, key):
        with self.db:
            self.db.execute(
                "UPDATE analysis_events SET state='failed' WHERE platform=? AND bot=? AND actor=? AND message_id=? AND task_type=?",
                key,
            )

    def package_result(self, key, scope, now):
        row = self.db.execute(
            "SELECT result FROM analysis_packages WHERE platform=? AND bot=? AND actor=? AND task_type=? AND digest=?",
            key,
        ).fetchone()
        if row is None:
            return None
        identifiers = json.loads(row[0])
        if not isinstance(identifiers, list) or any(
            type(identifier) is not int or not 0 < identifier <= 9223372036854775807
            for identifier in identifiers
        ):
            raise ValueError("自动分析的去重记录损坏。")
        for identifier in identifiers:
            task = self.db.execute(
                "SELECT cancelled,targets,deadline FROM tasks WHERE "
                + WHERE
                + " AND id=?",
                (*scope, identifier),
            ).fetchone()
            if task is None or task[0] or not json.loads(task[1]) or task[2] <= now:
                return None
        return identifiers

    def remove(self, scope, identifier, actor):
        task = self.get(scope, identifier)
        if actor != task["creator"] and actor not in task["targets"]:
            raise BusinessError(
                "只有设置者可取消全部通知；被通知者只能退出自己的通知。"
            )
        targets = (
            []
            if actor == task["creator"]
            else [user for user in task["targets"] if user != actor]
        )
        with self.db:
            self.db.execute(
                "UPDATE tasks SET targets=?,cancelled=? WHERE " + WHERE + " AND id=?",
                (
                    json.dumps(targets),
                    int(actor == task["creator"]),
                    *scope,
                    identifier,
                ),
            )
            if not targets:
                self.db.execute(
                    "UPDATE notifications SET state='cancelled' WHERE "
                    + WHERE
                    + " AND ddl_id=? AND state='pending'",
                    (*scope, identifier),
                )
        return (
            "已移除全部未发通知。"
            if actor == task["creator"]
            else "已退出对你自己的全部未发通知。"
        )

    def clear(self, platform, bot, location, conversation=None):
        where = "platform=? AND bot=? AND location=?"
        params = (platform, bot, location)
        if conversation is not None:
            where += " AND conversation=?"
            params += (conversation,)
        result = {}
        with self.db:
            for row in self.db.execute(
                "SELECT conversation,targets FROM tasks WHERE "
                + where
                + " AND cancelled=0",
                params,
            ):
                item = result.setdefault(row[0], {"count": 0, "targets": set()})
                item["count"] += 1
                item["targets"].update(json.loads(row[1]))
            self.db.execute(
                "UPDATE tasks SET cancelled=1,targets='[]' WHERE " + where, params
            )
            self.db.execute(
                "UPDATE notifications SET state='cancelled' WHERE "
                + where
                + " AND state='pending'",
                params,
            )
        return result

    def skip_group(self, group, now):
        with self.db:
            self.db.execute(
                "UPDATE notifications SET state='skipped' WHERE location='GROUP' AND conversation=? AND state='pending' AND at<=?",
                (group, now),
            )

    def due(self, now):
        with self.db:
            if now - self.last_scan > 60:
                self.db.execute(
                    "UPDATE notifications SET state='skipped' WHERE state='pending' AND at<=?",
                    (now,),
                )
            self.db.execute(
                "UPDATE notifications SET state='skipped' WHERE state='pending' AND at<?",
                (now - 60,),
            )
        self.last_scan = max(self.last_scan, now)
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM notifications WHERE state='pending' AND at<=? ORDER BY at",
                (now,),
            )
        ]

    def claim(self, node):
        with self.db:
            return (
                self.db.execute(
                    "UPDATE notifications SET state='sending' WHERE "
                    + WHERE
                    + " AND ddl_id=? AND at=? AND state='pending'",
                    (*self.scope_of(node), node["ddl_id"], node["at"]),
                ).rowcount
                == 1
            )

    def finish(self, node, state):
        with self.db:
            self.db.execute(
                "UPDATE notifications SET state=? WHERE "
                + WHERE
                + " AND ddl_id=? AND at=?",
                (state, *self.scope_of(node), node["ddl_id"], node["at"]),
            )

    @staticmethod
    def scope_of(node):
        return tuple(
            node[key] for key in ("platform", "bot", "location", "conversation")
        )
