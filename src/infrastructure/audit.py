"""Durable before/after records, including interrupted administrative writes."""

import json
import sqlite3
import time


class AuditStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in {0, 1}:
            self.db.close()
            raise ValueError("管理日志数据库版本未知。")
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                platform TEXT NOT NULL, bot TEXT NOT NULL, actor TEXT NOT NULL,
                operation TEXT NOT NULL, before_json TEXT NOT NULL,
                after_json TEXT NOT NULL, state TEXT NOT NULL)""")
            self.db.execute(
                "UPDATE operations SET state='uncertain' WHERE state='prepared'"
            )
            self.db.execute("PRAGMA user_version=1")
        if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            self.db.close()
            raise ValueError("管理日志完整性检查失败。")

    def prepare(self, ctx, operation, before, after):
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO operations(at,platform,bot,actor,operation,before_json,after_json,state) "
                "VALUES (?,?,?,?,?,?,?,'prepared')",
                (
                    time.time(),
                    ctx.platform,
                    ctx.bot,
                    ctx.actor,
                    operation,
                    json.dumps(before, ensure_ascii=False),
                    json.dumps(after, ensure_ascii=False),
                ),
            )
        return cursor.lastrowid

    def finish(self, identifier, state="committed"):
        with self.db:
            self.db.execute(
                "UPDATE operations SET state=? WHERE id=?", (state, identifier)
            )

    def close(self):
        self.db.close()
