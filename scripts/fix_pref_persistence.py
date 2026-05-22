#!/usr/bin/env python3
"""Persiste les prefs avec l'URL YouTube (pérenne) au lieu de l'URL streaming (expire)."""

import sys

# 1. resolver.py : ajouter webpage_url dans les candidats
resolver_path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/core/resolver.py'
with open(resolver_path) as f:
    content = f.read()

old = """                    candidates.append({
                        'url':        url,
                        'title':      entry.get('title', ''),
                        'channel':    entry.get('channel') or entry.get('uploader', ''),
                        'duration_s': yt_dur,
                        'score':      score,
                    })"""
new = """                    candidates.append({
                        'url':         url,
                        'webpage_url': entry.get('webpage_url', ''),
                        'title':       entry.get('title', ''),
                        'channel':     entry.get('channel') or entry.get('uploader', ''),
                        'duration_s':  yt_dur,
                        'score':       score,
                    })"""
print('resolver candidates:', old in content)
content = content.replace(old, new)

# Ajouter méthode resolve_from_url pour re-résoudre une URL YouTube
old2 = '    @staticmethod\n    def _extract_url(entry: dict) -> str | None:'
new2 = '''    def resolve_from_url(self, yt_url: str) -> str | None:
        """Résout une URL YouTube (pérenne) en URL streaming fraîche."""
        try:
            with yt_dlp.YoutubeDL(self._YDL_OPTS) as ydl:
                info = ydl.extract_info(yt_url, download=False)
                if info:
                    return self._extract_url(info)
        except Exception as e:
            print(f"[Resolver] resolve_from_url: {e}")
        return None

    @staticmethod
    def _extract_url(entry: dict) -> str | None:'''
print('resolver resolve_from_url:', old2 in content)
content = content.replace(old2, new2)

with open(resolver_path, 'w') as f:
    f.write(content)

# 2. playlist.py : utiliser resolve_from_url pour les prefs
playlist_path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/core/playlist.py'
with open(playlist_path) as f:
    content = f.read()

old3 = """            # Préférence utilisateur en priorité
            sid = track.get('spotify_id', '')
            saved = self._pref_store.get(sid) if sid else None
            url = saved if saved else self._resolver.resolve(track)"""
new3 = """            # Préférence utilisateur en priorité
            sid = track.get('spotify_id', '')
            saved = self._pref_store.get(sid) if sid else None
            if saved:
                # Si c'est une URL YouTube pérenne → ré-résoudre en streaming frais
                if 'youtube.com' in saved or 'youtu.be' in saved:
                    url = self._resolver.resolve_from_url(saved) or self._resolver.resolve(track)
                else:
                    url = saved  # URL streaming directe (anciens formats)
            else:
                url = self._resolver.resolve(track)"""
print('playlist pref resolve:', old3 in content)
content = content.replace(old3, new3)

with open(playlist_path, 'w') as f:
    f.write(content)

# 3. main_window.py : sauvegarder la webpage_url (pérenne) au lieu de l'URL streaming
mw_path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(mw_path) as f:
    content = f.read()

old4 = """        print(f'[pref] sid={self._current_spotify_id!r} url={url[:40]!r}', flush=True)
        # Sauvegarder la préférence
        if self._current_spotify_id:
            self._pref_store.save(self._current_spotify_id, url)
            print(f'[pref] saved OK', flush=True)
        else:
            print(f'[pref] ERROR: no spotify_id!', flush=True)"""
new4 = """        # Trouver l'URL YouTube pérenne dans les candidats
        pref_url = next(
            (c.get('webpage_url', '') for c in self._candidates if c.get('url') == url),
            ''
        ) or url
        print(f'[pref] sid={self._current_spotify_id!r} pref_url={pref_url[:50]!r}', flush=True)
        if self._current_spotify_id:
            self._pref_store.save(self._current_spotify_id, pref_url)
            print(f'[pref] saved OK', flush=True)
        else:
            print(f'[pref] ERROR: no spotify_id!', flush=True)"""
print('mainwindow save webpage_url:', old4 in content)
content = content.replace(old4, new4)

with open(mw_path, 'w') as f:
    f.write(content)

print('All done')
