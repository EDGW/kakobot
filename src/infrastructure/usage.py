"""Durable per-request token ledger; never stores prompts or credentials."""

import sqlite3
from decimal import Decimal
from pathlib import Path

from ..domain.context import qq_id
from ..domain.costs import WINDOWS, CostReport, TokenPrices, TokenUsage, empty_windows

SCHEMA = (
    """CREATE TABLE IF NOT EXISTS usage_metadata (
        id INTEGER PRIMARY KEY CHECK(id=1), started_at REAL NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS model_usage (
        request_id TEXT PRIMARY KEY,
        platform TEXT NOT NULL, bot TEXT NOT NULL, actor TEXT NOT NULL,
        group_id TEXT NOT NULL, operation TEXT NOT NULL, model TEXT NOT NULL,
        created_at REAL NOT NULL, finished_at REAL,
        state TEXT NOT NULL CHECK(state IN ('pending','completed','failed','interrupted')),
        http_status INTEGER,
        input_tokens INTEGER CHECK(input_tokens>=0),
        output_tokens INTEGER CHECK(output_tokens>=0),
        total_tokens INTEGER CHECK(total_tokens>=0),
        input_price_cny TEXT NOT NULL, output_price_cny TEXT NOT NULL,
        input_cost_cny TEXT, output_cost_cny TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS usage_by_bot ON model_usage(platform,bot,created_at)",
    "CREATE INDEX IF NOT EXISTS usage_by_actor ON model_usage(platform,bot,actor,created_at)",
    "CREATE INDEX IF NOT EXISTS usage_by_group ON model_usage(platform,bot,group_id,created_at)",
)


class UsageStore:
    def __init__(self, path: Path, now: float):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise ValueError("不支持的用量账本版本，拒绝覆盖。")
            self.db.execute("PRAGMA journal_mode=WAL")
            with self.db:
                for statement in SCHEMA:
                    self.db.execute(statement)
                self.db.execute("PRAGMA user_version=1")
                self.db.execute(
                    "INSERT OR IGNORE INTO usage_metadata VALUES (1,?)", (now,)
                )
                self.db.execute(
                    "UPDATE model_usage SET state='interrupted',finished_at=? WHERE state='pending'",
                    (now,),
                )
            if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("用量账本完整性检查失败。")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def begin(self, request_id, context, model, prices, now):
        bot, actor = qq_id(context.bot), qq_id(context.actor)
        group = qq_id(context.group) if context.group else ""
        with self.db:
            self.db.execute(
                """INSERT INTO model_usage (
                    request_id,platform,bot,actor,group_id,operation,model,
                    created_at,state,input_price_cny,output_price_cny
                ) VALUES (?,?,?,?,?,?,?,?,'pending',?,?)""",
                (
                    request_id,
                    context.platform,
                    bot,
                    actor,
                    group,
                    context.operation,
                    model,
                    now,
                    str(prices.input),
                    str(prices.output),
                ),
            )

    def finish(self, request_id, tokens, state, http_status, now):
        with self.db:
            row = self.db.execute(
                "SELECT * FROM model_usage WHERE request_id=? AND state='pending'",
                (request_id,),
            ).fetchone()
            if row is None:
                raise ValueError("用量请求不存在或已经结算。")
            prices = TokenPrices(
                Decimal(row["input_price_cny"]), Decimal(row["output_price_cny"])
            )
            costs = prices.costs(tokens)
            self.db.execute(
                """UPDATE model_usage SET
                    finished_at=?,state=?,http_status=?,
                    input_tokens=?,output_tokens=?,total_tokens=?,
                    input_cost_cny=?,output_cost_cny=?
                WHERE request_id=?""",
                (
                    now,
                    state,
                    http_status,
                    tokens.input,
                    tokens.output,
                    tokens.total,
                    *(str(cost) if cost is not None else None for cost in costs),
                    request_id,
                ),
            )

    def report(self, platform, bot, now, *, actor=None, group=None):
        started = self.db.execute(
            "SELECT started_at FROM usage_metadata WHERE id=1"
        ).fetchone()[0]
        report = CostReport(started)
        clauses, parameters = (
            ["platform=?", "bot=?", "created_at<=?"],
            [
                platform,
                bot,
                now,
            ],
        )
        if actor is not None:
            clauses.append("actor=?")
            parameters.append(actor)
        if group is not None:
            clauses.append("group_id=?")
            parameters.append(group)
        for row in self.db.execute(
            "SELECT * FROM model_usage WHERE " + " AND ".join(clauses), parameters
        ):
            tokens = TokenUsage(
                row["input_tokens"], row["output_tokens"], row["total_tokens"]
            )
            input_cost, output_cost = (
                Decimal(row[field]) if row[field] is not None else None
                for field in ("input_cost_cny", "output_cost_cny")
            )
            if row["actor"] not in report.accounts:
                report.accounts[row["actor"]] = empty_windows()
            if row["group_id"] not in report.groups:
                report.groups[row["group_id"]] = empty_windows()
            account = report.accounts[row["actor"]]
            target = report.groups[row["group_id"]]
            for index, (_, days) in enumerate(WINDOWS):
                if days is None or row["created_at"] >= now - days * 86400:
                    for window in (report.total, account, target):
                        window[index].add(tokens, input_cost, output_cost, row["state"])
        return report
