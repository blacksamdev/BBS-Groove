#!/usr/bin/env python3
"""Génère python3-pyqt6.json depuis les wheels locaux."""
import os
import json
import sys

wheels_dir = 'pyqt6-wheels'
sources = []
pkgs = []

if not os.path.exists(wheels_dir):
    print(f'ERROR: {wheels_dir} not found', file=sys.stderr)
    sys.exit(1)

files = sorted(os.listdir(wheels_dir))
print(f'Wheels found: {files}')

for f in files:
    if not f.endswith('.whl'):
        continue
    pkg_name = f.split('-')[0]
    normalized = pkg_name.replace('_', '-')
    if normalized.lower() in ('pyqt6', 'pyqt6-qt6', 'pyqt6-sip'):
        path = os.path.join(wheels_dir, f)
        sources.append({
            'type': 'file',
            'path': path,
            'dest-filename': f,
        })
        if normalized not in pkgs:
            pkgs.append(normalized)
        print(f'  + {f}')

if not pkgs:
    print('ERROR: no PyQt6 wheels found!', file=sys.stderr)
    sys.exit(1)

print(f'Packages: {pkgs}')

module = {
    'name': 'python3-PyQt6',
    'buildsystem': 'simple',
    'build-commands': [
        'pip3 install --verbose --no-index --find-links=. '
        '--prefix=${FLATPAK_DEST} ' + ' '.join(pkgs) + ' --no-build-isolation'
    ],
    'sources': sources,
}

with open('python3-pyqt6.json', 'w') as f:
    json.dump(module, f, indent=2)

print('Generated python3-pyqt6.json')
print(json.dumps(module, indent=2))
