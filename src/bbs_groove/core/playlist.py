import random
import threading
from typing import Callable
from bbs_groove.core.resolver import Resolver
from bbs_groove.core.pref_store import PrefStore
from bbs_groove.config.settings import PREFETCH_COUNT


class Playlist:
    """Gère la file de lecture et la résolution YouTube en arrière-plan."""

    def __init__(self):
        self._tracks:    list[dict] = []
        self._resolved:  dict[int, str] = {}   # index → url audio
        self._current:   int = 0
        self.shuffle:    bool = False
        self.repeat:     bool = False
        self._shuffle_order: list[int] = []
        self._shuffle_pos:   int = 0
        self._resolver   = Resolver()
        self._pref_store = PrefStore()
        self._lock       = threading.Lock()
        self._stop_event = threading.Event()
        self._worker:    threading.Thread | None = None

        # Callbacks
        self.on_resolved:    Callable[[int, str], None] | None = None
        self.on_load_error:  Callable[[int], None] | None = None

    # ------------------------------------------------------------------ #
    #  Chargement                                                          #
    # ------------------------------------------------------------------ #

    def load(self, tracks: list[dict]):
        self._stop_event.set()  # arrêter worker précédent
        with self._lock:
            self._tracks   = tracks
            self._resolved = {}
            self._current  = 0
            self._shuffle_order = list(range(len(tracks)))
            if self.shuffle:
                random.shuffle(self._shuffle_order)
            self._shuffle_pos = 0
        self._stop_event.clear()
        self._start_worker(0)

    # ------------------------------------------------------------------ #
    #  Navigation                                                          #
    # ------------------------------------------------------------------ #

    def current_track(self) -> dict | None:
        with self._lock:
            if 0 <= self._current < len(self._tracks):
                return self._tracks[self._current]
        return None

    def current_url(self) -> str | None:
        with self._lock:
            return self._resolved.get(self._current)

    def go_next(self) -> dict | None:
        with self._lock:
            if not self._tracks:
                return None
            if self.shuffle:
                self._shuffle_pos = (self._shuffle_pos + 1) % len(self._shuffle_order)
                if self._shuffle_pos == 0:
                    random.shuffle(self._shuffle_order)  # reshuffle au cycle suivant
                self._current = self._shuffle_order[self._shuffle_pos]
            else:
                self._current = (self._current + 1) % len(self._tracks)
            idx = self._current
        self._start_worker(idx)
        return self.current_track()

    def set_shuffle(self, enabled: bool):
        """Active/désactive le shuffle et régénère l'ordre."""
        with self._lock:
            self.shuffle = enabled
            if enabled and self._tracks:
                self._shuffle_order = list(range(len(self._tracks)))
                random.shuffle(self._shuffle_order)
                self._shuffle_pos = 0

    def go_prev(self) -> dict | None:
        with self._lock:
            if not self._tracks:
                return None
            self._current = (self._current - 1) % len(self._tracks)
            idx = self._current
        self._start_worker(idx)
        return self.current_track()

    def go_to(self, index: int) -> dict | None:
        with self._lock:
            if not (0 <= index < len(self._tracks)):
                return None
            self._current = index
        self._start_worker(index)
        return self.current_track()

    def is_resolved(self, index: int) -> bool:
        with self._lock:
            return index in self._resolved

    def get_url(self, index: int) -> str | None:
        with self._lock:
            return self._resolved.get(index)

    @property
    def tracks(self) -> list[dict]:
        with self._lock:
            return list(self._tracks)

    @property
    def current_index(self) -> int:
        return self._current

    def count(self) -> int:
        with self._lock:
            return len(self._tracks)

    # ------------------------------------------------------------------ #
    #  Résolution en arrière-plan                                          #
    # ------------------------------------------------------------------ #

    def _start_worker(self, from_index: int):
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1)
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._resolve_worker,
            args=(from_index,),
            daemon=True,
        )
        self._worker.start()

    def _resolve_worker(self, start: int):
        with self._lock:
            total = len(self._tracks)
        targets = [
            (start + i) % total
            for i in range(min(PREFETCH_COUNT + 1, total))
        ]
        for idx in targets:
            if self._stop_event.is_set():
                return
            with self._lock:
                if idx in self._resolved:
                    continue
                track = self._tracks[idx] if idx < len(self._tracks) else None
            if not track:
                continue
            # Préférence utilisateur en priorité (relire le fichier pour sync avec UI)
            self._pref_store._prefs = self._pref_store._load(self._pref_store._prefs_path)
            sid = track.get('spotify_id', '')
            if not sid:
                sid = track.get('artist','').lower() + '|' + track.get('title','').lower()
            saved = self._pref_store.get(sid) if sid else None
            if saved:
                # Si c'est une URL YouTube pérenne → ré-résoudre en streaming frais
                if 'youtube.com' in saved or 'youtu.be' in saved:
                    url = self._resolver.resolve_from_url(saved) or self._resolver.resolve(track)
                else:
                    # URL streaming ou format inconnu → re-résoudre normalement
                    url = self._resolver.resolve(track)
            else:
                url = self._resolver.resolve(track)
            if self._stop_event.is_set():
                return
            with self._lock:
                if url:
                    self._resolved[idx] = url
            if url and self.on_resolved:
                self.on_resolved(idx, url)
            elif not url and self.on_load_error:
                self.on_load_error(idx)
