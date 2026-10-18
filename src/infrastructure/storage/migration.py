"""Fail-closed startup migration with compatible 1.0.x upgrades."""

import os
import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ...domain.context import qq_id
from ..group_discuss.store import DiscussStore
from .access.readonly import ReadonlyPolicy
from .access.roles import RoleStore, empty_roles, validate_roles
from .broadcasts.conversations import ConversationStore
from .broadcasts.upgrades import UpgradeStore
from .deadlines.preferences import PreferenceStore
from .deadlines.tasks import initialize_schema, validate_database
from .json_store import atomic_json, read_json

VERSION = "2.0.0-alpha.3"


@contextmanager
def migration_lock(path):
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            stream.write(b"0")
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _old_access(path):
    try:
        data = read_json(path)
    except FileNotFoundError:
        return {
            "admins": [],
            "readonly_groups": [],
            "group_admins": {},
            "group_admin_disabled": [],
        }
    allowed = {"admins", "readonly_groups", "group_admins", "group_admin_disabled"}
    if (
        not isinstance(data, dict)
        or not {"admins", "readonly_groups"} <= set(data)
        or not set(data) <= allowed
    ):
        raise ValueError("旧 access.json 格式错误，拒绝迁移。")
    for key in ("admins", "readonly_groups", "group_admin_disabled"):
        if not isinstance(data.get(key, []), list):
            raise ValueError(f"旧权限 {key} 不是列表。")
        data[key] = sorted({qq_id(value) for value in data.get(key, [])}, key=int)
    groups = data.get("group_admins", {})
    if not isinstance(groups, dict) or any(
        not isinstance(values, list) for values in groups.values()
    ):
        raise ValueError("旧群身份组格式错误。")
    data["group_admins"] = {
        qq_id(group): sorted({qq_id(value) for value in values}, key=int)
        for group, values in groups.items()
    }
    return data


def _expected_access(old):
    roles = empty_roles()
    roles["global_roles"]["admin"] = old["admins"]
    for group, users in old["group_admins"].items():
        roles["group_roles"][group] = {
            "group.admin": users,
            "group.ddl": [],
            "group.summary": [],
        }
    roles["group_admin_enabled"] = {
        group: False for group in old["group_admin_disabled"]
    }
    return roles, {"groups": old["readonly_groups"]}


def _save_or_verify(path, expected):
    try:
        actual = read_json(path)
    except FileNotFoundError:
        atomic_json(path, expected)
        actual = read_json(path)
    if actual != expected:
        raise ValueError(f"迁移目标 {path.name} 与旧数据不一致，拒绝覆盖。")


def _database(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1, 2):
            raise ValueError("旧 DDL 数据版本不支持。")
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if version == 0 and tables:
            raise ValueError("DDL 数据库含未知的未版本化数据，拒绝当作空数据。")
        with db:
            db.execute("BEGIN IMMEDIATE")
            if version != 2:
                initialize_schema(db)
            if version == 1:
                if not {"deadlines", "reminders"} <= tables:
                    raise ValueError("旧 DDL 数据表不完整。")
                db.execute(
                    "INSERT INTO tasks SELECT platform,bot,'GROUP',group_id,id,title,deadline,creator,created,targets,cancelled,'legacy','{}',NULL FROM deadlines"
                )
                db.execute(
                    "INSERT INTO notifications SELECT platform,bot,'GROUP',group_id,ddl_id,at,state FROM reminders"
                )
            db.execute("PRAGMA user_version=2")
            validate_database(db)
            if "deadlines" in tables:
                old = db.execute(
                    "SELECT platform,bot,group_id,id,title,deadline,creator,created,targets,cancelled FROM deadlines ORDER BY platform,bot,group_id,id"
                ).fetchall()
                new = db.execute(
                    "SELECT platform,bot,conversation,id,title,deadline,creator,created,targets,cancelled FROM tasks WHERE location='GROUP' ORDER BY platform,bot,conversation,id"
                ).fetchall()
                old_nodes = db.execute(
                    "SELECT * FROM reminders ORDER BY platform,bot,group_id,ddl_id,at"
                ).fetchall()
                new_nodes = db.execute(
                    "SELECT platform,bot,conversation,ddl_id,at,state FROM notifications WHERE location='GROUP' ORDER BY platform,bot,conversation,ddl_id,at"
                ).fetchall()
                if old != new or old_nodes != new_nodes:
                    raise ValueError("迁移前后的 DDL 或提醒内容不一致。")
    finally:
        db.close()


def _validate(directory):
    RoleStore(directory / "roles.json", "000000000")
    ReadonlyPolicy(directory / "readonly.json", "000000000")
    PreferenceStore(directory / "ddl_preferences.json")
    database = directory / "deadlines.sqlite3"
    if not database.is_file():
        raise ValueError("已标记当前数据版本但 DDL 数据库缺失。")
    db = sqlite3.connect(database)
    try:
        validate_database(db)
    finally:
        db.close()


def _mark_version(marker, *, upgraded=False):
    if upgraded:
        conversations = ConversationStore(marker.parent / "conversations.sqlite3")
        try:
            UpgradeStore(conversations).queue(VERSION)
        finally:
            conversations.close()
    atomic_json(marker, {"version": VERSION})
    if read_json(marker) != {"version": VERSION}:
        raise ValueError("迁移版本标记回读失败。")


def _backup_upgrade(directory, version):
    backup = directory / ("migration-backup-" + version)
    backup.mkdir(exist_ok=True)
    for source in directory.iterdir():
        if not source.is_file() or source.suffix not in {".json", ".sqlite3", ".key"}:
            continue
        target = backup / source.name
        if target.exists():
            continue
        if source.suffix == ".sqlite3":
            temporary = target.with_suffix(".tmp")
            temporary.unlink(missing_ok=True)
            before, after = sqlite3.connect(source), sqlite3.connect(temporary)
            try:
                before.backup(after)
                if after.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ValueError("升级备份完整性检查失败。")
            finally:
                before.close()
                after.close()
            os.replace(temporary, target)
        else:
            shutil.copy2(source, target)
        os.chmod(target, 0o600)


def migrate(directory: Path):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with migration_lock(directory / ".migration.lock"):
        marker = directory / "version.json"
        try:
            data = read_json(marker)
        except FileNotFoundError:
            data = {"version": "0.5.4"}
        if (
            not isinstance(data, dict)
            or set(data) != {"version"}
            or not isinstance(data["version"], str)
        ):
            raise ValueError("version.json 格式错误，停止启动。")
        version = data["version"]
        if version in {
            VERSION,
            "2.0.0-alpha.1",
            "2.0.0-alpha.2",
            "1.0.0",
            "1.0.1",
            "1.0.2",
            "1.1.0",
            "1.2.0",
            "1.2.1",
            "1.2.2",
            "1.3.0",
            "1.3.1",
            "1.3.2",
        }:
            if version != VERSION:
                _backup_upgrade(directory, version)
            _validate(directory)
            if (
                version == VERSION
                and not (directory / "group_discuss.sqlite3").exists()
            ):
                raise ValueError("当前版本的 discuss 数据库缺失，拒绝清空重建。")
            discussions = DiscussStore(directory)
            discussions.close()
            if version != VERSION:
                # Compatible patches keep the existing schema and all data.
                _mark_version(marker, upgraded=True)
            return
        if version != "0.5.4":
            raise ValueError(f"不支持从 {version} 迁移至 {VERSION}，禁止降级或覆盖。")
        existing = marker.exists() or any(
            (directory / name).exists()
            for name in (
                "access.json",
                "roles.json",
                "deadlines.sqlite3",
                "ddl_preferences.json",
                "conversations.sqlite3",
            )
        )
        old = _old_access(directory / "access.json")
        backup = directory / "migration-backup-0.5.4"
        backup.mkdir(exist_ok=True)
        for name in ("access.json", "version.json"):
            path = directory / name
            if path.is_file() and not (backup / name).exists():
                shutil.copy2(path, backup / name)
        database = directory / "deadlines.sqlite3"
        if database.exists() and not (backup / database.name).exists():
            temporary = backup / "deadlines.sqlite3.tmp"
            temporary.unlink(missing_ok=True)
            source, target = sqlite3.connect(database), sqlite3.connect(temporary)
            try:
                source.backup(target)
                if target.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ValueError("旧数据库备份完整性检查失败。")
            finally:
                source.close()
                target.close()
            os.replace(temporary, backup / database.name)
        roles, readonly = _expected_access(old)
        validate_roles(roles)
        _save_or_verify(directory / "roles.json", roles)
        _save_or_verify(directory / "readonly.json", readonly)
        _database(database)
        _validate(directory)
        discussions = DiscussStore(directory)
        discussions.close()
        _mark_version(marker, upgraded=existing)
