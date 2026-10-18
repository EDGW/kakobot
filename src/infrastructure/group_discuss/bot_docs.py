"""Lossless, deduplicated automation references derived from user documentation."""

import hashlib
import json
import re
from collections import Counter


def compact_document(text):
    # Compare paragraph, line and sentence dictionaries. Only shared passages
    # are indexed; adjacent literals are merged. Every character is reversible.
    candidates = [text]
    for pattern in (r'(\n\s*\n)', r'(?<=\n)', r'(?<=[。；\n])'):
        pieces = re.split(pattern, text)
        counts = Counter(pieces)
        blocks = list(dict.fromkeys(piece for piece in pieces if counts[piece] > 1 and len(piece) >= 16))
        indexes = {piece: index for index, piece in enumerate(blocks)}
        order = []
        for piece in pieces:
            if piece in indexes:
                order.append(indexes[piece])
            elif order and isinstance(order[-1], str):
                order[-1] += piece
            else:
                order.append(piece)
        candidates.append(json.dumps({'blocks': blocks, 'order': order}, ensure_ascii=False, separators=(',', ':')))
    encoded = min(candidates, key=lambda value: len(value.encode()))
    return {
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'format': 'text' if encoded == text else 'blocks-v1',
        'text': encoded,
    }
