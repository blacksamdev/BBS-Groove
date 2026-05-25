#!/usr/bin/env python3
"""Corrections senior dev — bugs critiques + importants."""
import json, re, py_compile
from pathlib import Path

base = Path('/home/bbs/Documents/WIP/Groove/src/bbs_groove')

# ── 1. resolver.py — supprimer doublon _YDL_FLAT ─────────────────────
p = base / 'core/resolver.py'
content = p.read_text()
# Supprimer la deuxième définition de _YDL_FLAT
content = re.sub(
    r"    _YDL_FLAT = \{[^}]+\}\n\n    _YDL_FLAT = \{[^}]+\}\n",
    lambda m: m.group(0).split('    _YDL_FLAT')[0] + '    _YDL_FLAT' + m.group(0).split('    _YDL_FLAT')[2],
    content, flags=re.DOTALL
)
# Simpler: just find and remove the duplicate block
lines = content.split('\n')
flat_count = 0
new_lines = []
skip = False
i = 0
while i < len(lines):
    if '    _YDL_FLAT = {' in lines[i]:
        flat_count += 1
        if flat_count == 2:
            # Skip this duplicate block until closing }
            while i < len(lines) and not (lines[i].strip() == '}' and i > 0):
                i += 1
            i += 1  # skip closing }
            continue
    new_lines.append(lines[i])
    i += 1
content = '\n'.join(new_lines)
p.write_text(content)
print(f'1. resolver.py _YDL_FLAT doublon: {content.count("_YDL_FLAT = {")} occurrence(s)')

# ── 2. spotify.py — import re hors boucle + fix album_tracks ─────────
p = base / 'core/sources/spotify.py'
content = p.read_text()

# Retirer import re as _re dans la boucle
content = content.replace(
    '                import re as _re\n                yt_url  = e.get(\'url\', \'\')\n                vid     = _re.search(',
    '                yt_url  = e.get(\'url\', \'\')\n                vid     = re.search('
)
print(f'2. spotify.py import re dans boucle supprimé: {"import re as _re" not in content}')

# Fix _album_tracks : variable track non définie
old_album = """    def _album_tracks(self, url: str) -> list[dict]:
        album = self._client.get_album_info(url) if hasattr(self._client, 'get_album_info') else None
        if not album:
            track = self._client.get_track_info(url)
            return [self._format_track(track, full=True)] if track else []
        artwork      = self._extract_artwork(album)
        release_date = album.get('release_date', '') or track.get('release_date', '')"""
new_album = """    def _album_tracks(self, url: str) -> list[dict]:
        album = self._client.get_album_info(url) if hasattr(self._client, 'get_album_info') else None
        if not album:
            track = self._client.get_track_info(url)
            return [self._format_track(track, full=True)] if track else []
        artwork      = self._extract_artwork(album)
        release_date = album.get('release_date', '')"""
print(f'3. spotify.py _album_tracks track NameError: {old_album in content}')
content = content.replace(old_album, new_album)

# Log erreur enrich_track
content = content.replace(
    '        except Exception as e:\n            pass\n        return track',
    '        except Exception as e:\n            from bbs_groove.logging_utils import log\n            log(f\'enrich_track: {e}\', \'warning\')\n        return track'
)

# Log erreur _artist_top_tracks
content = content.replace(
    '        except Exception as e:\n            return []',
    '        except Exception as e:\n            from bbs_groove.logging_utils import log\n            log(f\'artist_top_tracks: {e}\', \'warning\')\n            return []'
)
p.write_text(content)

# ── 3. groove.py — gaming mode avec QApplication ─────────────────────
p = base / 'groove.py'
content = p.read_text()
old_gaming = """    if args.gaming:
        from bbs_groove.ui.tray import GrooveTray
        tray = GrooveTray()
        tray.show()
    else:"""
new_gaming = """    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName('BBS Groove')
    app.setStyle('Fusion')
    if args.gaming:
        from bbs_groove.ui.tray import GrooveTray
        window = GrooveTray()
        window.show()
    else:"""
# Remove duplicate QApplication creation in else branch
old_else = """    else:
        from PyQt6.QtWidgets import QApplication
        from bbs_groove.ui.main_window import BBSGrooveWindow
        app = QApplication(sys.argv)
        app.setApplicationName('BBS Groove')
        app.setStyle('Fusion')
        window = BBSGrooveWindow()
        window.show()
        sys.exit(app.exec())"""
new_else = """    else:
        from bbs_groove.ui.main_window import BBSGrooveWindow
        window = BBSGrooveWindow()
        window.show()
    sys.exit(app.exec())"""
print(f'4. groove.py gaming QApplication: {old_gaming in content}')
content = content.replace(old_gaming, new_gaming)
content = content.replace(old_else, new_else)
p.write_text(content)

# ── 4. pref_store.py — atomic write + log erreur ─────────────────────
p = base / 'core/pref_store.py'
content = p.read_text()
old_write = """    @staticmethod
    def _write(path: Path, data: dict):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass"""
new_write = """    @staticmethod
    def _write(path: Path, data: dict):
        \"\"\"Écriture atomique via fichier temporaire.\"\"\"
        import tempfile, os
        try:
            dir_ = path.parent
            with tempfile.NamedTemporaryFile('w', dir=dir_, delete=False, suffix='.tmp') as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = tmp.name
            os.replace(tmp_path, path)
        except Exception as e:
            import logging
            logging.getLogger('bbs_groove').warning(f'PrefStore write error: {e}')"""
print(f'5. pref_store.py atomic write: {old_write in content}')
content = content.replace(old_write, new_write)
p.write_text(content)

# ── 5. lyrics_fetcher.py — validation + lambda naming ─────────────────
p = base / 'core/lyrics_fetcher.py'
content = p.read_text()
content = content.replace(
    '        if not results:\n            return None',
    '        if not results or not isinstance(results, list):\n            return None'
)
content = content.replace(
    'key=lambda r: abs((r.get(\'duration\') or 0) - duration_s)',
    'key=lambda item: abs((item.get(\'duration\') or 0) - duration_s)'
)
p.write_text(content)
print('6. lyrics_fetcher.py validations: OK')

# ── Vérification syntaxe ──────────────────────────────────────────────
errors = 0
for p in sorted(base.rglob('*.py')):
    try:
        py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        print(f'SYNTAX ERROR: {e}')
        errors += 1
if errors == 0:
    print('\n✅ Tous les fichiers : syntaxe OK')
