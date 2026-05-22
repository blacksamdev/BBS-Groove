#!/usr/bin/env python3
"""Intègre les lyrics dans main_window.py et le manifest Flatpak."""
import json

# main_window.py
mw_path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(mw_path) as f:
    content = f.read()

# Ajouter méthodes lyrics avant _on_volume
old = '    def _on_volume(self, value: int):'
new = '''    def _fetch_lyrics(self, track: dict):
        """Fetch les lyrics en arrière-plan."""
        from bbs_groove.core.lyrics_fetcher import LyricsFetcher
        artist = track.get('artist', '')
        title  = track.get('title', '')
        dur_ms = track.get('duration_ms', 0)
        try:
            result = LyricsFetcher().fetch(artist, title, dur_ms)
            text = ''
            if result:
                if result.get('plain'):
                    text = result['plain']
            self._signals.lyrics_ready.emit(text)
        except Exception as e:
            log(f'fetch_lyrics: {e}', 'warning')
            self._signals.lyrics_ready.emit('')

    def _on_lyrics_ready(self, text: str):
        """Affiche les lyrics dans le widget."""
        if text:
            self._lyrics_widget.setPlainText(text)
            self._lyrics_widget.setVisible(True)
        else:
            self._lyrics_widget.clear()
            self._lyrics_widget.setVisible(False)

    def _on_volume(self, value: int):'''
print('lyrics methods:', old in content)
content = content.replace(old, new)

# Effacer les lyrics au changement de piste
old2 = "    def _update_track_display(self, track: dict):\n        self._versions_list.clear()"
new2 = "    def _update_track_display(self, track: dict):\n        self._versions_list.clear()\n        self._lyrics_widget.clear()\n        self._lyrics_widget.setVisible(False)"
print('clear lyrics:', old2 in content)
content = content.replace(old2, new2)

with open(mw_path, 'w') as f:
    f.write(content)

# manifest : installer lyrics_fetcher.py
manifest_path = '/home/bbs/Documents/WIP/Groove/io.github.blacksamdev.Groove.json'
with open(manifest_path) as f:
    m = json.load(f)

groove = next(mod for mod in m['modules'] if isinstance(mod, dict) and mod.get('name') == 'groove')
cmds = groove['build-commands']
cmd = 'install -Dm644 src/bbs_groove/core/lyrics_fetcher.py /app/lib/bbs-groove/src/bbs_groove/core/lyrics_fetcher.py'
if cmd not in cmds:
    idx = next(i for i, c in enumerate(cmds) if 'pref_store.py' in c)
    cmds.insert(idx + 1, cmd)
    print('manifest: OK')
else:
    print('manifest: already present')

with open(manifest_path, 'w') as f:
    json.dump(m, f, indent=2)

print('All done')
