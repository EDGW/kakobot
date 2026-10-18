"""Persistent upgrade broadcasts and per-recipient, single-attempt delivery."""


class UpgradeStore:
    def __init__(self, conversations):
        self.db = conversations.db
        with self.db:
            self.db.execute(
                """CREATE TABLE IF NOT EXISTS upgrade_broadcasts (
                    version TEXT PRIMARY KEY,
                    prepared INTEGER NOT NULL DEFAULT 0 CHECK(prepared IN (0,1))
                )"""
            )
            self.db.execute(
                """CREATE TABLE IF NOT EXISTS upgrade_deliveries (
                    version TEXT NOT NULL, platform TEXT NOT NULL,
                    bot TEXT NOT NULL, actor TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending'
                        CHECK(state IN ('pending','attempted','sent','skipped','failed')),
                    PRIMARY KEY(version,platform,bot,actor)
                )"""
            )

    def queue(self, version):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO upgrade_broadcasts(version) VALUES (?)",
                (version,),
            )

    def prepare(self, version, eligible):
        with self.db:
            row = self.db.execute(
                "SELECT prepared FROM upgrade_broadcasts WHERE version=?", (version,)
            ).fetchone()
            if row != (0,):
                return
            recipients = self.db.execute(
                """SELECT platform,bot,actor FROM private_conversations
                    WHERE first_seen IS NOT NULL AND announce_rejected=0"""
            ).fetchall()
            self.db.executemany(
                """INSERT OR IGNORE INTO upgrade_deliveries(version,platform,bot,actor)
                    VALUES (?,?,?,?)""",
                [
                    (version, platform, bot, actor)
                    for platform, bot, actor in recipients
                    if actor != bot and eligible(actor)
                ],
            )
            self.db.execute(
                "UPDATE upgrade_broadcasts SET prepared=1 WHERE version=?", (version,)
            )

    def pending(self, version):
        return self.db.execute(
            """SELECT platform,bot,actor FROM upgrade_deliveries
                WHERE version=? AND state='pending' ORDER BY platform,bot,actor""",
            (version,),
        ).fetchall()

    def claim(self, version, recipient):
        # Persist before the network call: a crash or unknown QQ response must
        # not cause the same update to be sent again after a restart.
        with self.db:
            return (
                self.db.execute(
                    """UPDATE upgrade_deliveries SET state='attempted'
                    WHERE version=? AND platform=? AND bot=? AND actor=?
                    AND state='pending'""",
                    (version, *recipient),
                ).rowcount
                == 1
            )

    def finish(self, version, recipient, state):
        with self.db:
            self.db.execute(
                """UPDATE upgrade_deliveries SET state=?
                    WHERE version=? AND platform=? AND bot=? AND actor=?""",
                (state, version, *recipient),
            )
