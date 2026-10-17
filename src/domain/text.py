"""Bound and clean display labels without allowing them to become identifiers."""

import unicodedata


def display_name(value, limit=80):
    if not isinstance(value, str):
        return ""
    visible = "".join(
        character if not unicodedata.category(character).startswith("C") else " "
        for character in value
    )
    return " ".join(visible.split())[:limit]
