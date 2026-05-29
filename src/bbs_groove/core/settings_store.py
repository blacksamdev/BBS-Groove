"""Gestion des paramètres utilisateur — ~/.config/bbs-groove/settings.json."""
import json
import os
from pathlib import Path


class SettingsStore:
    DEFAULTS = {
        'autoplay_mode': 'off',   # 'off' | 'youtube' | 'lastfm'
        'lastfm_api_key': '',
    }

    def __init__(self):
        config_dir = Path.home() / '.config' / 'bbs-groove'
        config_dir.mkdir(parents=True, exist_ok=True)
        self._path = config_dir / 'settings.json'
        self._data = {**self.DEFAULTS, **self._load()}

    def get(self, key: str):
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

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
            logging.getLogger('bbs_groove').warning(f'SettingsStore save error: {e}')
