"""Translate verified QQ mentions at the model boundary, never trust labels as IDs."""

import re

from ...domain.context import qq_id
from ...domain.text import display_name

AT = re.compile(r'<at@[^<>:\n]{1,80}:([0-9]{1,20})>')
CODE_OR_AT = re.compile(r'```[\s\S]*?```|`[^`\n]*`|<at@[^<>:\n]{1,80}:([0-9]{1,20})>')


def label(member, user):
    name = display_name(member.get('card') or member.get('nickname') or user, 60)
    return re.sub(r'[<>:@]', '', name) or user


async def model_mentions(text, parts, group, gateway):
    native = {str((part.get('data') or {}).get('qq', '')) for part in parts if part.get('type') == 'at'}
    if not group or not native:
        return text, []
    members = {str(m['user_id']): m for m in await gateway.members(group)}
    verified = []
    for user in sorted(native):
        if user not in members:
            continue
        token = f'<at@{label(members[user], user)}:{user}>'
        text = re.sub(r'(?<![\w@])@' + re.escape(user) + r'(?!\d)', lambda _, mention=token: mention, text)
        verified.append({'qq_id': user, 'mention': token})
    return text, verified


async def reply_mentions(text, group, gateway, bot):
    matches = [m for m in CODE_OR_AT.finditer(text) if m[1]]
    if not group or not matches:
        return text, None
    members = {str(m['user_id']): m for m in await gateway.members(group)}
    parts, cursor, canonical = [], 0, []
    for match in matches:
        user = qq_id(match[1])
        # Invalid targets stay literal; never create native all/bot/nonmember pings.
        if user not in members or user == bot:
            continue
        prefix = text[cursor:match.start()]
        parts.append({'type': 'text', 'data': {'text': prefix}})
        parts.append({'type': 'at', 'data': {'qq': user}})
        canonical.extend([prefix, f'@{label(members[user], user)}'])
        cursor = match.end()
    if not parts:
        return text, None
    tail = text[cursor:]
    parts.append({'type': 'text', 'data': {'text': tail}})
    canonical.append(tail)
    return ''.join(canonical), parts


def automation_command(command):
    # Marker labels may contain spaces; replace with authoritative numeric targets
    # before the original strict suffix parser and current member validation.
    return AT.sub(lambda m: '@' + qq_id(m[1]), command)


def automation_segments(command):
    """Preserve model mention markers as native components for DDL parsing."""
    parts, cursor = [], 0
    for match in AT.finditer(command):
        if match.start() > cursor:
            parts.append({"type": "text", "data": {"text": command[cursor:match.start()]}})
        parts.append({"type": "at", "data": {"qq": qq_id(match[1])}})
        cursor = match.end()
    if cursor < len(command):
        parts.append({"type": "text", "data": {"text": command[cursor:]}})
    return parts
