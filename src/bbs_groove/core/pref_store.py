"""Stockage des préférences de version YouTube + état UI."""
import json
import os
from pathlib import Path


class PrefStore:
    """Associe un spotify_id à une URL YouTube préférée + état UI persistant."""

    def __init__(self):
        # Utiliser ~/.config/bbs-groove/ (chemin réel exposé via --filesystem=xdg-config/bbs-groove:create)
        # XDG_CONFIG_HOME dans Flatpak pointe vers le namespace interne non visible depuis l'hôte
        config_dir = Path.home() / '.config' / 'bbs-groove'
        config_dir.mkdir(parents=True, exist_ok=True)
        self._prefs_path = config_dir / 'track_prefs.json'
        self._ui_path    = config_dir / 'ui_state.json'
        self._prefs:    dict[str, str]  = self._load(self._prefs_path)
        self._ui_state: dict[str, object] = self._load(self._ui_path)

    # ------------------------------------------------------------------ #
    #  Préférences de tracks                                               #
    # ------------------------------------------------------------------ #

    def get(self, spotify_id: str) -> str | None:
        return self._prefs.get(spotify_id)

    def save(self, spotify_id: str, url: str):
        self._prefs[spotify_id] = url
        self._write(self._prefs_path, self._prefs)

    # ------------------------------------------------------------------ #
    #  État UI persistant                                                  #
    # ------------------------------------------------------------------ #

    def get_ui_state(self, key: str, default=None):
        return self._ui_state.get(key, default)

    def save_ui_state(self, key: str, value):
        self._ui_state[key] = value
        self._write(self._ui_path, self._ui_state)

    # ------------------------------------------------------------------ #
    #  Privé                                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load(path: Path) -> dict:
        try:
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    @staticmethod
    def _write(path: Path, data: dict):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass
