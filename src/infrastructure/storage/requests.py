"""Numbered OneBot requests with durable deduplication and processing claims."""

import sqlite3


class RequestStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in {0, 1}:
            self.db.close()
            raise ValueError("申请数据库版本未知。")
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL, bot TEXT NOT NULL,
                kind TEXT NOT NULL, subtype TEXT NOT NULL,
                flag TEXT NOT NULL, user_id TEXT NOT NULL, group_id TEXT NOT NULL,
                comment TEXT NOT NULL, received REAL NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending', actor TEXT NOT NULL DEFAULT '',
                processed REAL, error TEXT NOT NULL DEFAULT '', notified INTEGER NOT NULL DEFAULT 0,
                UNIQUE(platform,bot,kind,subtype,flag))""")
            self.db.execute("PRAGMA user_version=1")
            self.db.execute(
                "UPDATE requests SET state='uncertain',error='处理期间插件重启；未自动重试' WHERE state='processing'"
            )
        if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            self.db.close()
            raise ValueError("申请数据库完整性校验失败。")

    def add(self, platform, bot, kind, subtype, flag, user, group, comment, received):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO requests(platform,bot,kind,subtype,flag,user_id,group_id,comment,received) VALUES (?,?,?,?,?,?,?,?,?)",
                (platform, bot, kind, subtype, flag, user, group, comment, received),
            )
        return dict(
            self.db.execute(
                "SELECT * FROM requests WHERE platform=? AND bot=? AND kind=? AND subtype=? AND flag=?",
                (platform, bot, kind, subtype, flag),
            ).fetchone()
        )

    def get(self, platform, bot, identifier):
        row = self.db.execute(
            "SELECT * FROM requests WHERE platform=? AND bot=? AND id=?",
            (platform, bot, identifier),
        ).fetchone()
        return dict(row) if row else None

    def list(self, platform, bot, state="pending"):
        sql = "SELECT * FROM requests WHERE platform=? AND bot=?"
        values = (platform, bot)
        if state != "all":
            sql += " AND state=?"
            values += (state,)
        return [dict(row) for row in self.db.execute(sql + " ORDER BY id", values)]

    def notified(self, identifier):
        with self.db:
            self.db.execute("UPDATE requests SET notified=1 WHERE id=?", (identifier,))

    def claim(self, identifier, actor, now):
        with self.db:
            return (
                self.db.execute(
                    "UPDATE requests SET state='processing',actor=?,processed=? WHERE id=? AND state='pending'",
                    (actor, now, identifier),
                ).rowcount
                == 1
            )

    def finish(self, identifier, state, error=""):
        with self.db:
            self.db.execute(
                "UPDATE requests SET state=?,error=? WHERE id=?",
                (state, error, identifier),
            )

    def close(self):
        self.db.close()
