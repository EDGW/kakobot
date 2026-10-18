"""Administrative DDL queries and atomic batches on the existing task database."""

import json

from .tasks import WHERE


class DeadlineManagementStore:
    def __init__(self, data):
        self.data = data

    def scheduled(self, ctx, scope, now):
        clauses = [
            "tasks.platform=?",
            "tasks.bot=?",
            "tasks.cancelled=0",
            "tasks.targets!='[]'",
            "notifications.state='pending'",
            "notifications.at>?",
            "notifications.at<=tasks.deadline",
        ]
        params = [ctx.platform, ctx.bot, now]
        if scope:
            clauses += ["tasks.location=?", "tasks.conversation=?"]
            params += list(scope[2:])
        rows = self.data.db.execute(
            "SELECT tasks.platform,tasks.bot,tasks.location,tasks.conversation,tasks.id "
            "FROM tasks JOIN notifications ON "
            "tasks.platform=notifications.platform AND tasks.bot=notifications.bot "
            "AND tasks.location=notifications.location "
            "AND tasks.conversation=notifications.conversation "
            "AND tasks.id=notifications.ddl_id WHERE "
            + " AND ".join(clauses)
            + " GROUP BY tasks.platform,tasks.bot,tasks.location,tasks.conversation,tasks.id "
            "ORDER BY MIN(notifications.at),tasks.location,tasks.conversation,tasks.id",
            params,
        ).fetchall()
        tasks = []
        for row in rows:
            task = self.data.get(tuple(row[:4]), row[4])
            task["reminders"] = [
                node
                for node in task["reminders"]
                if node["state"] == "pending" and now < node["at"] <= task["deadline"]
            ]
            tasks.append(task)
        return tasks

    def search(self, ctx, scope, filters, now):
        clauses, params = ["platform=?", "bot=?"], [ctx.platform, ctx.bot]
        if scope:
            clauses += ["location=?", "conversation=?"]
            params += list(scope[2:])
        status = filters.get("status", "active")
        if status == "active":
            clauses += ["cancelled=0", "targets!='[]'", "deadline>?"]
            params.append(now)
        elif status == "expired":
            clauses += ["cancelled=0", "deadline<=?"]
            params.append(now)
        elif status == "cancelled":
            clauses.append("(cancelled=1 OR targets='[]')")
        if "creator" in filters:
            clauses.append("creator=?")
            params.append(filters["creator"])
        if "target" in filters:
            clauses.append(
                "EXISTS(SELECT 1 FROM json_each(tasks.targets) WHERE value=?)"
            )
            params.append(filters["target"])
        for key, comparison in (("from", ">="), ("to", "<=")):
            if key in filters:
                clauses.append("deadline" + comparison + "?")
                params.append(filters[key])
        rows = self.data.db.execute(
            "SELECT platform,bot,location,conversation,id FROM tasks WHERE "
            + " AND ".join(clauses)
            + " ORDER BY deadline,location,conversation,id",
            params,
        ).fetchall()
        return [(tuple(row[:4]), row[4]) for row in rows]

    def apply(self, changes, now):
        db = self.data.db
        with db:
            for old, new, replace in changes:
                scope = self.data.scope_of(old)
                db.execute(
                    "UPDATE tasks SET title=?,deadline=?,targets=?,cancelled=?,source=?,signature=NULL WHERE "
                    + WHERE
                    + " AND id=?",
                    (
                        new["title"],
                        new["deadline"],
                        json.dumps(new["targets"]),
                        new["cancelled"],
                        new["source"],
                        *scope,
                        old["id"],
                    ),
                )
                if replace or new["cancelled"] or not new["targets"]:
                    db.execute(
                        "UPDATE notifications SET state='cancelled' WHERE "
                        + WHERE
                        + " AND ddl_id=? AND state='pending'",
                        (*scope, old["id"]),
                    )
                if replace and not new["cancelled"] and new["targets"]:
                    db.executemany(
                        "INSERT INTO notifications VALUES (?,?,?,?,?,?,'pending') "
                        "ON CONFLICT(platform,bot,location,conversation,ddl_id,at) DO UPDATE SET state='pending' "
                        "WHERE notifications.state IN ('pending','cancelled')",
                        [
                            (*scope, old["id"], at)
                            for at in new["pending_times"]
                            if at > now
                        ],
                    )
