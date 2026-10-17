"""Atomic, per-account and per-owner preferences for private DDL analysis."""

from ..domain.analysis import MAX_DEFAULT_PROMPT
from ..domain.context import qq_id
from .json_store import atomic_json, read_json


class PreferenceStore:
    def __init__(self, path):
        self.path = path
        try:
            self.data = read_json(path)
        except FileNotFoundError:
            self.data = {"version": 1, "users": []}
        self._validate()

    def _validate(self):
        data = self.data
        if (
            not isinstance(data, dict)
            or set(data) != {"version", "users"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or not isinstance(data["users"], list)
        ):
            raise ValueError("ddl_preferences.json 格式错误。")
        seen = set()
        for item in data["users"]:
            if (
                not isinstance(item, dict)
                or set(item) != {"platform", "bot", "actor", "defaulttime"}
                or any(not isinstance(value, str) for value in item.values())
                or not item["platform"]
                or qq_id(item["bot"]) != item["bot"]
                or qq_id(item["actor"]) != item["actor"]
                or not 1 <= len(item["defaulttime"].strip()) <= MAX_DEFAULT_PROMPT
            ):
                raise ValueError("DDL 默认提醒提示词数据无效。")
            key = self._key(item)
            if key in seen:
                raise ValueError("DDL 默认提醒提示词有重复所有者。")
            seen.add(key)

    @staticmethod
    def _key(item):
        return item["platform"], item["bot"], item["actor"]

    def owners(self):
        return {self._key(item) for item in self.data["users"]}

    def get(self, ctx):
        key = ctx.platform, ctx.bot, ctx.actor
        return next(
            (
                item["defaulttime"]
                for item in self.data["users"]
                if self._key(item) == key
            ),
            "",
        )

    def set(self, ctx, prompt):
        key = ctx.platform, ctx.bot, ctx.actor
        users = [item for item in self.data["users"] if self._key(item) != key]
        if prompt:
            users.append(
                {
                    "platform": ctx.platform,
                    "bot": ctx.bot,
                    "actor": ctx.actor,
                    "defaulttime": prompt,
                }
            )
        updated = {"version": 1, "users": users}
        atomic_json(self.path, updated)
        self.data = updated
