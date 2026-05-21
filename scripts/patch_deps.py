#!/usr/bin/env python3
"""Patch python-deps.json pour forcer les wheels binaires."""
import json

with open('python-deps.json') as f:
    data = json.load(f)

data['build-commands'] = [
    c.replace('pip3 install', 'pip3 install --only-binary=:all:')
    for c in data.get('build-commands', [])
]

with open('python-deps.json', 'w') as f:
    json.dump(data, f, indent=2)

print('python-deps.json patched')
