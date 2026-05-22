#!/usr/bin/env python3
"""Supprime tous les prints de debug de BBS Groove."""
import re
from pathlib import Path

base = Path('/home/bbs/Documents/WIP/Groove/src/bbs_groove')

# Patterns à supprimer ligne par ligne
DEBUG_PATTERNS = [
    r"^\s*print\(f'\[enrich\].*\n",
    r"^\s*print\(f'\[enrich_track\].*\n",
    r"^\s*print\(f'\[pref\].*\n",
    r"^\s*print\(f'\[PrefStore\].*\n",
    r"^\s*print\(f'\[playlist\._resolve\].*\n",
    r"^\s*print\(f'\[fetch_candidates\].*\n",
    r"^\s*# Debug enrichment result\n",
    r"^\s*# Ligne \d+ -.*\n",
]

files = list(base.rglob('*.py'))
total = 0

for path in files:
    content = path.read_text()
    original = content
    for pattern in DEBUG_PATTERNS:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    if content != original:
        removed = original.count('\n') - content.count('\n')
        total += removed
        path.write_text(content)
        print(f'  {path.name}: -{removed} lignes')

print(f'\nTotal: -{total} lignes de debug supprimées')
