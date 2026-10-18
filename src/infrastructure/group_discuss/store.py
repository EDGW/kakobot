"""Transactional discussion state, credentials and reservation ledger."""

import json
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from cryptography.fernet import Fernet

from ...domain.errors import BusinessError
from ...domain.group_discuss.config import effective, upgrade_group_limits


def scope_key(ctx, group=None):
    return json.dumps(
        [ctx.platform, ctx.bot, group or ctx.group], separators=(",", ":")
    )


def day_key(now=None):
    return (
        datetime.fromtimestamp(now or time.time(), timezone(timedelta(hours=8)))
        .date()
        .isoformat()
    )


class DiscussStore:
    def __init__(self, directory):
        self.on_end = None
        self.directory = directory
        path = directory / "group_discuss.sqlite3"
        self.db = sqlite3.connect(path)
        os.chmod(path, 0o600)
        self.db.row_factory = sqlite3.Row
        try:
            if self.db.execute("PRAGMA user_version").fetchone()[0] not in (0, 1, 2):
                raise ValueError("未知 discuss 数据库版本。")
            self.db.execute("PRAGMA journal_mode=WAL")
            with self.db:
                self.db.executescript("""
                    CREATE TABLE IF NOT EXISTS groups (
                        scope TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0,
                        config TEXT NOT NULL DEFAULT '{}');
                    CREATE TABLE IF NOT EXISTS roles (
                        scope TEXT NOT NULL, role TEXT NOT NULL, actor TEXT NOT NULL,
                        PRIMARY KEY(scope,role,actor));
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY, scope TEXT NOT NULL, actor TEXT NOT NULL,
                        created REAL NOT NULL, ended REAL, reason TEXT,
                        history BLOB, summary TEXT NOT NULL DEFAULT '',
                        summary_offset INTEGER NOT NULL DEFAULT 0);
                    CREATE TABLE IF NOT EXISTS messages (
                        scope TEXT NOT NULL, message TEXT NOT NULL, session TEXT,
                        PRIMARY KEY(scope,message));
                    CREATE TABLE IF NOT EXISTS turns (
                        id TEXT PRIMARY KEY, session TEXT NOT NULL, actor TEXT NOT NULL,
                        created REAL NOT NULL, tool_calls INTEGER NOT NULL DEFAULT 0,
                        state TEXT NOT NULL DEFAULT 'pending');
                    CREATE TABLE IF NOT EXISTS calls (
                        id TEXT PRIMARY KEY, turn TEXT NOT NULL, session TEXT NOT NULL,
                        scope TEXT NOT NULL, bot_scope TEXT NOT NULL, day TEXT NOT NULL,
                        reserved INTEGER NOT NULL, charged INTEGER NOT NULL,
                        input INTEGER, output INTEGER, cached INTEGER,
                        model TEXT NOT NULL, reasoning INTEGER,
                        state TEXT NOT NULL DEFAULT 'pending', created REAL NOT NULL);
                    CREATE INDEX IF NOT EXISTS calls_budget ON calls(scope,day);
                    CREATE INDEX IF NOT EXISTS calls_session ON calls(session);
                    CREATE TABLE IF NOT EXISTS tools (
                        id TEXT PRIMARY KEY, turn TEXT NOT NULL, name TEXT NOT NULL,
                        state TEXT NOT NULL DEFAULT 'pending');
                    CREATE TABLE IF NOT EXISTS audit (
                        id INTEGER PRIMARY KEY, scope TEXT NOT NULL, actor TEXT NOT NULL,
                        action TEXT NOT NULL, detail TEXT NOT NULL, created REAL NOT NULL);
                    CREATE TABLE IF NOT EXISTS secrets (
                        scope TEXT PRIMARY KEY, value BLOB NOT NULL);
                """)
                if self.db.execute("PRAGMA user_version").fetchone()[0] < 2:
                    for row in self.db.execute(
                        "SELECT scope,config FROM groups"
                    ).fetchall():
                        values = json.loads(row["config"])
                        upgrade_group_limits(values)
                        self.db.execute(
                            "UPDATE groups SET config=? WHERE scope=?",
                            (json.dumps(values), row["scope"]),
                        )
                    self.log(
                        "system", "system", "limits migration", "v2: bytes/token units"
                    )
                    self.db.execute("PRAGMA user_version=2")
                self.db.execute(
                    "UPDATE calls SET state='unknown' WHERE state='pending'"
                )
                self.db.execute(
                    "UPDATE turns SET state='interrupted' WHERE state='pending'"
                )
                self.db.execute(
                    "UPDATE tools SET state='interrupted' WHERE state='pending'"
                )
            if self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("discuss 数据完整性检查失败。")
            master = directory / "group_discuss.key"
            if not master.exists():
                if self.db.execute("SELECT 1 FROM secrets LIMIT 1").fetchone():
                    raise ValueError("discuss 密钥文件丢失，拒绝覆盖现有凭据。")
                descriptor = os.open(
                    master, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(Fernet.generate_key())
                    stream.flush()
                    os.fsync(stream.fileno())
            os.chmod(master, 0o600)
            self.cipher = Fernet(master.read_bytes())
            # Fail startup if existing credentials cannot be decrypted.
            for row in self.db.execute("SELECT value FROM secrets"):
                self.cipher.decrypt(row[0])
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def group(self, scope):
        row = self.db.execute("SELECT * FROM groups WHERE scope=?", (scope,)).fetchone()
        return (
            {"enabled": bool(row["enabled"]), "config": json.loads(row["config"])}
            if row
            else {"enabled": False, "config": {}}
        )

    def log(self, scope, actor, action, detail=""):
        self.db.execute(
            "INSERT INTO audit(scope,actor,action,detail,created) VALUES (?,?,?,?,?)",
            (scope, actor, action, detail, time.time()),
        )

    def save_group(self, scope, actor, *, config=None, enabled=None):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO groups(scope) VALUES (?)", (scope,))
            if config is not None:
                self.db.execute(
                    "UPDATE groups SET config=? WHERE scope=?",
                    (json.dumps(config), scope),
                )
            if enabled is not None:
                self.db.execute(
                    "UPDATE groups SET enabled=? WHERE scope=?", (int(enabled), scope)
                )
            self.log(
                scope,
                actor,
                "config",
                json.dumps(config if config is not None else {"enabled": enabled}),
            )

    def secret(self, scope):
        row = self.db.execute(
            "SELECT value FROM secrets WHERE scope=?", (scope,)
        ).fetchone()
        return self.cipher.decrypt(row[0]).decode() if row else ""

    def set_secret(self, scope, actor, value):
        with self.db:
            if value:
                self.db.execute(
                    "INSERT OR REPLACE INTO secrets VALUES (?,?)",
                    (scope, self.cipher.encrypt(value.encode())),
                )
            else:
                self.db.execute("DELETE FROM secrets WHERE scope=?", (scope,))
            self.log(scope, actor, "api_key", "已更新" if value else "已清除")

    def role(self, scope, name, actor):
        return (
            self.db.execute(
                "SELECT 1 FROM roles WHERE scope=? AND role=? AND actor=?",
                (scope, name, actor),
            ).fetchone()
            is not None
        )

    def role_list(self, scope, name):
        return [
            r[0]
            for r in self.db.execute(
                "SELECT actor FROM roles WHERE scope=? AND role=? ORDER BY actor",
                (scope, name),
            )
        ]

    def change_role(self, scope, actor, name, user, add):
        with self.db:
            if add:
                self.db.execute(
                    "INSERT OR IGNORE INTO roles VALUES (?,?,?)", (scope, name, user)
                )
            else:
                self.db.execute(
                    "DELETE FROM roles WHERE scope=? AND role=? AND actor=?",
                    (scope, name, user),
                )
            self.log(
                scope, actor, "role", f"{'add' if add else 'remove'} {name} {user}"
            )

    def claim_message(self, scope, message):
        if not message:
            raise BusinessError("消息缺少 ID，无法安全去重。")
        with self.db:
            return (
                self.db.execute(
                    "INSERT OR IGNORE INTO messages(scope,message) VALUES (?,?)",
                    (scope, message),
                ).rowcount
                == 1
            )

    def message_session(self, scope, message):
        row = self.db.execute(
            "SELECT session FROM messages WHERE scope=? AND message=?", (scope, message)
        ).fetchone()
        return row[0] if row else None

    def map_message(self, scope, message, session):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO messages VALUES (?,?,?)",
                (scope, str(message), session),
            )

    def session(self, scope, identifier):
        row = self.db.execute(
            "SELECT * FROM sessions WHERE scope=? AND id=?", (scope, identifier)
        ).fetchone()
        if row is None:
            raise BusinessError("会话不存在或不属于目标群。")
        result = dict(row)
        if result["summary"]:
            result["summary"] = self.cipher.decrypt(result["summary"]).decode()
        return result

    def sessions(self, scope, actor=None):
        sql = "SELECT * FROM sessions WHERE scope=? AND ended IS NULL"
        args = [scope]
        if actor:
            sql += " AND actor=?"
            args.append(actor)
        return [
            dict(row) for row in self.db.execute(sql + " ORDER BY created,id", args)
        ]

    def end(self, scope, identifier, reason, actor="system"):
        affected = [
            row["id"]
            for row in self.sessions(scope)
            if identifier == "all" or row["id"] == identifier
        ]
        with self.db:
            self.db.execute(
                "UPDATE sessions SET ended=?,reason=? WHERE scope=? AND ended IS NULL"
                + ("" if identifier == "all" else " AND id=?"),
                [time.time(), reason, scope]
                + ([] if identifier == "all" else [identifier]),
            )
            self.log(scope, actor, "end", f"{identifier}: {reason}")
        if self.on_end:
            for session in affected:
                self.on_end(session)

    def trim_sessions(self, scope, maximum):
        rows = self.sessions(scope)
        for row in rows[: max(0, len(rows) - maximum)]:
            self.end(scope, row["id"], "活跃会话数超限")

    def create_session(self, scope, actor, maximum):
        identifier = uuid4().hex[:16]
        with self.db:
            self.trim_sessions(scope, maximum - 1)
            self.db.execute(
                "INSERT INTO sessions(id,scope,actor,created) VALUES (?,?,?,?)",
                (identifier, scope, actor, time.time()),
            )
        return identifier

    def history(self, scope, session):
        row = self.session(scope, session)
        return self.cipher.decrypt(row["history"]) if row["history"] else b"[]"

    def save_history(self, scope, session, history, summary=None, summary_offset=None):
        with self.db:
            self.db.execute(
                "UPDATE sessions SET history=? WHERE scope=? AND id=?",
                (self.cipher.encrypt(history), scope, session),
            )
            if summary is not None:
                self.db.execute(
                    "UPDATE sessions SET summary=? WHERE scope=? AND id=?",
                    (self.cipher.encrypt(summary.encode()), scope, session),
                )
            if summary_offset is not None:
                self.db.execute(
                    "UPDATE sessions SET summary_offset=? WHERE scope=? AND id=?",
                    (summary_offset, scope, session),
                )

    def new_turn(self, session, actor):
        identifier = uuid4().hex
        with self.db:
            self.db.execute(
                "INSERT INTO turns(id,session,actor,created) VALUES (?,?,?,?)",
                (identifier, session, actor, time.time()),
            )
        return identifier

    def total(self, where, args):
        return self.db.execute(
            "SELECT COALESCE(SUM(charged),0) FROM calls WHERE " + where, args
        ).fetchone()[0]

    def budget(self, scope, config, policy, session=None):
        bot_scope = json.dumps(json.loads(scope)[:2], separators=(",", ":"))
        result = {
            "group_daily": {
                "limit": config["daily_token_budget"],
                "charged_or_reserved": self.total(
                    "scope=? AND day=?", [scope, day_key()]
                ),
            },
            "bot_daily": {
                "limit": policy["global_daily_token_budget"],
                "charged_or_reserved": self.total(
                    "bot_scope=? AND day=?", [bot_scope, day_key()]
                ),
            },
        }
        if session:
            result["session"] = {
                "limit": config["session_token_budget"],
                "charged_or_reserved": self.total("session=?", [session]),
            }
        for value in result.values():
            value["remaining"] = max(0, value["limit"] - value["charged_or_reserved"])
        return result

    def reserve(self, scope, session, turn, amount, config, policy):
        identifier, day = uuid4().hex, day_key()
        bot_scope = json.dumps(json.loads(scope)[:2], separators=(",", ":"))
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.session(scope, session)["ended"] is not None:
                raise BusinessError("会话已结束，请重新 @ 开始。")
            checks = [
                (
                    "session=?",
                    [session],
                    config["session_token_budget"],
                    "会话预算不足",
                ),
                (
                    "scope=? AND day=?",
                    [scope, day],
                    config["daily_token_budget"],
                    "群每日预算不足",
                ),
                (
                    "bot_scope=? AND day=?",
                    [bot_scope, day],
                    policy["global_daily_token_budget"],
                    "机器人每日预算不足",
                ),
            ]
            for where, args, limit, reason in checks:
                if self.total(where, args) + amount > limit:
                    # End after rollback in the caller for the session-only case.
                    raise BusinessError(reason)
            self.db.execute(
                "INSERT INTO calls(id,turn,session,scope,bot_scope,day,reserved,charged,created,model) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    identifier,
                    turn,
                    session,
                    scope,
                    bot_scope,
                    day,
                    amount,
                    amount,
                    time.time(),
                    config["model_name"],
                ),
            )
        return identifier

    def settle(self, identifier, usage, state, reasoning=None):
        incoming, outgoing, cached = usage
        known = incoming is not None and outgoing is not None
        with self.db:
            self.db.execute(
                "UPDATE calls SET input=?,output=?,cached=?,reasoning=?,charged=CASE WHEN ? THEN ? ELSE MAX(charged,?) END,state=? WHERE id=? AND state='pending'",
                (
                    incoming,
                    outgoing,
                    cached,
                    reasoning,
                    known,
                    (incoming or 0) + (outgoing or 0),
                    (incoming or 0) + (outgoing or 0),
                    state if known else "unknown",
                    identifier,
                ),
            )

    def resolve(self, scope, identifier, amount, actor, reason):
        with self.db:
            row = self.db.execute(
                "SELECT 1 FROM calls WHERE id=? AND scope=? AND state='unknown'",
                (identifier, scope),
            ).fetchone()
            if not row:
                raise BusinessError("未找到此群待核销请求。")
            self.db.execute(
                "UPDATE calls SET charged=?,state='resolved' WHERE id=?",
                (amount, identifier),
            )
            self.log(scope, actor, "resolve", f"{identifier} {amount} {reason}")

    def tool_begin(self, turn, name, config):
        with self.db:
            if self.tool_remaining(turn, name, config) <= 0:
                raise BusinessError("本轮工具调用次数已达上限。")
            identifier = uuid4().hex
            self.db.execute(
                "INSERT INTO tools(id,turn,name) VALUES (?,?,?)",
                (identifier, turn, name),
            )
            self.db.execute(
                "UPDATE turns SET tool_calls=tool_calls+1 WHERE id=?", (turn,)
            )
        return identifier

    def tool_remaining(self, turn, name, config):
        total = self.db.execute(
            "SELECT COUNT(*) FROM tools WHERE turn=?", (turn,)
        ).fetchone()[0]
        native_names = (
            ("native_search", "native_open_page", "native_find_in_page")
            if name in {"search_web", "fetch_webpage"}
            else ("", "", "")
        )
        count = self.db.execute(
            "SELECT COUNT(*) FROM tools WHERE turn=? AND name IN (?, ?, ?, ?)",
            (turn, name, *native_names),
        ).fetchone()[0]
        return min(
            config["max_tool_calls_per_request"] - total,
            config[f"tools.{name}.max_calls_per_request"] - count,
        )

    def native_tool(self, turn, action, state="completed"):
        with self.db:
            self.db.execute(
                "INSERT INTO tools(id,turn,name,state) VALUES (?,?,?,?)",
                (uuid4().hex, turn, "native_" + action, state),
            )
            self.db.execute(
                "UPDATE turns SET tool_calls=tool_calls+1 WHERE id=?", (turn,)
            )

    def tool_finish(self, identifier, state):
        with self.db:
            self.db.execute("UPDATE tools SET state=? WHERE id=?", (state, identifier))

    def turn_usage(self, turn):
        rows = list(self.db.execute("SELECT * FROM calls WHERE turn=?", (turn,)))
        result = {}
        for key in ("input", "output", "cached"):
            known = [row[key] for row in rows if row[key] is not None]
            result[key] = (
                str(sum(known))
                if len(known) == len(rows)
                else (f"至少 {sum(known)}（另有未知）" if known else "未知")
            )
        result["tools"] = self.db.execute(
            "SELECT tool_calls FROM turns WHERE id=?", (turn,)
        ).fetchone()[0]
        names = {
            row[0]
            for row in self.db.execute("SELECT name FROM tools WHERE turn=?", (turn,))
        }
        sources = []
        if any(name.startswith("native_") for name in names):
            sources.append("内置（DeepSeek Responses）")
        if names & {"search_web", "fetch_webpage"}:
            sources.append("外置（DeepSeek Search/Fetch，同群 Key）")
        result["search_source"] = "、".join(sources) or "未使用"
        return result

    def finish_turn(self, turn, state):
        with self.db:
            self.db.execute("UPDATE turns SET state=? WHERE id=?", (state, turn))

    def stats(self, scope, window):
        where, args = "scope=?", [scope]
        if window != "all":
            try:
                date = (
                    day_key()
                    if window == "today"
                    else datetime.strptime(window, "%Y-%m-%d").date().isoformat()
                )
            except ValueError as exc:
                raise BusinessError("日期格式须为 YYYY-MM-DD。") from exc
            where += " AND day=?"
            args.append(date)
        rows = [
            dict(r) for r in self.db.execute("SELECT * FROM calls WHERE " + where, args)
        ]
        breakdown = {}
        for key in ("model", "session", "day", "state", "actor"):
            values = {}
            for row in rows:
                label = (
                    row[key]
                    if key != "actor"
                    else self.db.execute(
                        "SELECT actor FROM turns WHERE id=?", (row["turn"],)
                    ).fetchone()[0]
                )
                item = values.setdefault(
                    label,
                    {"requests": 0, "charged_or_reserved": 0, "input": 0, "output": 0},
                )
                item["requests"] += 1
                item["charged_or_reserved"] += row["charged"]
                item["input"] += row["input"] or 0
                item["output"] += row["output"] or 0
            breakdown[key] = values
        return {
            "active_sessions": len(self.sessions(scope)),
            "requests": len(rows),
            "input_tokens": sum(r["input"] or 0 for r in rows),
            "output_tokens": sum(r["output"] or 0 for r in rows),
            "cached_tokens": sum(r["cached"] or 0 for r in rows),
            "reasoning_tokens": sum(r["reasoning"] or 0 for r in rows),
            "missing_cached_usage": sum(r["cached"] is None for r in rows),
            "missing_reasoning_usage": sum(r["reasoning"] is None for r in rows),
            "charged_or_reserved": sum(r["charged"] for r in rows),
            "unknown_requests": sum(r["state"] in ("unknown", "pending") for r in rows),
            "unknown_request_ids": [r["id"] for r in rows if r["state"] == "unknown"],
            "tool_calls": self.db.execute(
                "SELECT COUNT(*) FROM tools WHERE turn IN (SELECT DISTINCT turn FROM calls WHERE "
                + where
                + ")",
                args,
            ).fetchone()[0],
            "usage_note": "已知数值汇总；缺失 usage 不代表零。",
            "breakdown": breakdown,
        }

    def cleanup(self, days):
        cutoff = time.time() - days * 86400
        with self.db:
            self.db.execute(
                "UPDATE sessions SET history=NULL,summary='' WHERE ended IS NOT NULL AND ended<?",
                (cutoff,),
            )

    def apply_limits(self, policy):
        for row in self.db.execute("SELECT scope,config FROM groups").fetchall():
            self.trim_sessions(
                row["scope"],
                effective(json.loads(row["config"]), policy)["max_sessions"],
            )
