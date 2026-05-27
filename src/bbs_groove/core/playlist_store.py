"""Gestion des playlists personnelles — stockage local JSON."""
import json
import os
from pathlib import Path


class PlaylistStore:
    """CRUD playlists perso dans ~/.config/bbs-groove/my_playlists.json."""

    def __init__(self):
        config_dir = Path.home() / '.config' / 'bbs-groove'
        config_dir.mkdir(parents=True, exist_ok=True)
        self._path = config_dir / 'my_playlists.json'
        self._data: dict[str, list[dict]] = self._load()

    # ------------------------------------------------------------------ #
    #  Playlists                                                           #
    # ------------------------------------------------------------------ #

    def names(self) -> list[str]:
        return list(self._data.keys())

    def create(self, name: str) -> bool:
        if name in self._data:
            return False
        self._data[name] = []
        self._save()
        return True

    def rename(self, old: str, new: str) -> bool:
        if old not in self._data or new in self._data or not new.strip():
            return False
        self._data = {(new if k == old else k): v for k, v in self._data.items()}
        self._save()
        return True

    def delete(self, name: str) -> bool:
        if name not in self._data:
            return False
        del self._data[name]
        self._save()
        return True

    def get_tracks(self, name: str) -> list[dict]:
        return list(self._data.get(name, []))

    # ------------------------------------------------------------------ #
    #  Titres                                                              #
    # ------------------------------------------------------------------ #

    def add_track(self, name: str, track: dict) -> bool:
        """Ajoute un titre. Retourne False si déjà présent dans cette playlist."""
        if name not in self._data:
            return False
        if self.has_track(name, track):
            return False
        self._data[name].append(self._normalize(track))
        self._save()
        return True

    def remove_track(self, name: str, index: int) -> bool:
        if name not in self._data or not (0 <= index < len(self._data[name])):
            return False
        self._data[name].pop(index)
        self._save()
        return True

    def has_track(self, name: str, track: dict) -> bool:
        """Vérifie si le titre est déjà dans la playlist (spotify_id ou title+artist)."""
        key = self._track_key(track)
        return any(self._track_key(t) == key for t in self._data.get(name, []))

    def playlists_containing(self, track: dict) -> list[str]:
        """Retourne les noms des playlists contenant déjà ce titre."""
        return [name for name in self._data if self.has_track(name, track)]

    # ------------------------------------------------------------------ #
    #  Privé                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _track_key(track: dict) -> str:
        sid = track.get('spotify_id', '')
        if sid:
            return f'spotify:{sid}'
        return f"{track.get('artist', '').lower()}|{track.get('title', '').lower()}"

    @staticmethod
    def _normalize(track: dict) -> dict:
        """Garde uniquement les champs nécessaires."""
        return {
            'title':       track.get('title', ''),
            'artist':      track.get('artist', ''),
            'all_artists': track.get('all_artists', ''),
            'duration_ms': track.get('duration_ms', 0),
            'artwork_url': track.get('artwork_url', ''),
            'spotify_id':  track.get('spotify_id', ''),
            'year':        track.get('year', ''),
            'youtube_url': track.get('youtube_url', ''),
        }

    def _load(self) -> dict:
        try:
            if self._path.exists():
                with open(self._path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save(self):
        import tempfile
        try:
            with tempfile.NamedTemporaryFile('w', dir=self._path.parent,
                                             delete=False, suffix='.tmp') as tmp:
                json.dump(self._data, tmp, indent=2, ensure_ascii=False)
                tmp_path = tmp.name
            os.replace(tmp_path, self._path)
        except Exception as e:
            import logging
            logging.getLogger('bbs_groove').warning(f'PlaylistStore save error: {e}')
