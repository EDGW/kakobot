"""Generate compact Bot references without maintaining a second source of truth."""

import json
from pathlib import Path

from ..infrastructure.group_discuss.bot_docs import compact_document


def build(root):
    source, target = root / 'docs', root / 'docs-bot'
    expected = set()
    original = compressed = 0
    for path in sorted(source.rglob('*.md')):
        if 'pics' in path.relative_to(source).parts or path.is_symlink():
            continue
        text = path.read_text(encoding='utf-8')
        reference = compact_document(text)
        output = target / path.relative_to(source).with_suffix('.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(reference, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        expected.add(output)
        original += len(text.encode())
        compressed += len(reference['text'].encode())
    for old in target.rglob('*.json'):
        if old not in expected:
            old.unlink()
    print(f'Bot 文档：{len(expected)} 篇，正文 {original} → {compressed} bytes；保留全部原文信息。')


if __name__ == '__main__':
    build(Path(__file__).resolve().parents[2])
