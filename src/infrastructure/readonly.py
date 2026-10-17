"""Readonly is an independent policy, outside the role hierarchy."""

from pathlib import Path

from ..domain.context import qq_id
from .json_store import atomic_json, read_json


class ReadonlyPolicy:
    def __init__(self, path: Path, super_user: str):
        self.path, self.super_user = path, super_user
        data = read_json(path)
        if (
            not isinstance(data, dict)
            or set(data) != {"groups"}
            or not isinstance(data["groups"], list)
            or any(
                not isinstance(group, str) or qq_id(group) != group
                for group in data["groups"]
            )
            or len(set(data["groups"])) != len(data["groups"])
        ):
            raise ValueError("readonly.json 格式错误。")
        self.readonly_groups = frozenset(qq_id(group) for group in data["groups"])
        self.listeners = []

    def set(self, group: str, enabled: bool):
        group = qq_id(group)
        groups = (
            self.readonly_groups | {group}
            if enabled
            else self.readonly_groups - {group}
        )
        atomic_json(self.path, {"groups": sorted(groups, key=int)})
        self.readonly_groups = groups
        for listener in self.listeners:
            listener(group)
