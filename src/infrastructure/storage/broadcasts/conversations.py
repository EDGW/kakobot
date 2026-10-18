"""Observed private conversations and persistent broadcast opt-out preferences."""

import sqlite3
from pathlib import Path

from ....domain.context import qq_id


class ConversationStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise ValueError("不支持的会话记录版本，拒绝覆盖。")
            with self.db:
                self.db.execute(
                    """CREATE TABLE IF NOT EXISTS private_conversations (
                        platform TEXT NOT NULL, bot TEXT NOT NULL, actor TEXT NOT NULL,
                        first_seen REAL, last_seen REAL,
                        announce_rejected INTEGER NOT NULL DEFAULT 0
                            CHECK(announce_rejected IN (0,1)),
                        PRIMARY KEY(platform,bot,actor)
                    )"""
                )
                self.db.execute("PRAGMA user_version=1")
            if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("会话记录完整性检查失败。")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def seed_private(self, identities):
        """Zero means a persisted private interaction with an unknown timestamp."""
        with self.db:
            for platform, bot, actor in identities:
                bot, actor = qq_id(bot), qq_id(actor)
                if actor == bot:
                    continue
                self.db.execute(
                    """INSERT INTO private_conversations
                        (platform,bot,actor,first_seen,last_seen) VALUES (?,?,?,0,0)
                    ON CONFLICT(platform,bot,actor) DO UPDATE SET
                        first_seen=COALESCE(first_seen,0),last_seen=COALESCE(last_seen,0)""",
                    (platform, bot, actor),
                )

    def observe(self, ctx):
        if ctx.group or ctx.actor == ctx.bot:
            return
        bot, actor = qq_id(ctx.bot), qq_id(ctx.actor)
        with self.db:
            self.db.execute(
                """INSERT INTO private_conversations
                    (platform,bot,actor,first_seen,last_seen) VALUES (?,?,?,?,?)
                ON CONFLICT(platform,bot,actor) DO UPDATE SET
                    first_seen=COALESCE(first_seen,excluded.first_seen),
                    last_seen=excluded.last_seen""",
                (ctx.platform, bot, actor, ctx.received_at, ctx.received_at),
            )

    def reject(self, ctx, enabled):
        # A command in a group can set a preference without claiming that a
        # private conversation ever took place (first_seen stays NULL).
        with self.db:
            self.db.execute(
                """INSERT INTO private_conversations
                    (platform,bot,actor,announce_rejected) VALUES (?,?,?,?)
                ON CONFLICT(platform,bot,actor) DO UPDATE SET
                    announce_rejected=excluded.announce_rejected""",
                (ctx.platform, qq_id(ctx.bot), qq_id(ctx.actor), int(enabled)),
            )

    def accepts(self, platform, bot, actor):
        row = self.db.execute(
            """SELECT 1 FROM private_conversations WHERE platform=? AND bot=? AND actor=?
                AND first_seen IS NOT NULL AND announce_rejected=0""",
            (platform, bot, actor),
        ).fetchone()
        return row is not None

    def recipients(self, platform, bot):
        return [
            row[0]
            for row in self.db.execute(
                """SELECT actor FROM private_conversations WHERE platform=? AND bot=?
                    AND first_seen IS NOT NULL AND announce_rejected=0 ORDER BY actor""",
                (platform, bot),
            )
        ]
