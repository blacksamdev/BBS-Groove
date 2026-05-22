from bbs_groove.logging_utils import log
import io
import subprocess
import threading
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QSlider, QSizePolicy, QFrame, QMessageBox,
)

import requests

from bbs_groove.core.playlist import Playlist
from bbs_groove.core.player import MPVPlayer
from bbs_groove.core.sources.spotify import SpotifySource
from bbs_groove.core.pref_store import PrefStore


# ── Signaux thread-safe ──────────────────────────────────────────────── #
class _Signals(QObject):
    tracks_loaded    = pyqtSignal(list)
    resolved         = pyqtSignal(int, str)
    artwork_ready    = pyqtSignal(bytes)
    error            = pyqtSignal(str)
    track_ended      = pyqtSignal()
    track_enriched   = pyqtSignal(dict)
    candidates_ready = pyqtSignal(list, str)


# ── Styles ───────────────────────────────────────────────────────────── #
BG_MAIN   = '#0d0d0d'
BG_PANEL  = '#1a1a1a'
BG_ITEM   = '#222222'
BG_ACTIVE = '#2a2a2a'
ACCENT    = '#1DB954'
TEXT_PRI  = '#ffffff'
TEXT_SEC  = '#aaaaaa'
BTN_STYLE = f"""
    QPushButton {{
        background: {BG_PANEL};
        color: {TEXT_PRI};
        border: 1px solid #333;
        border-radius: 4px;
        padding: 6px 14px;
        font-size: 13px;
    }}
    QPushButton:hover  {{ background: {BG_ACTIVE}; border-color: {ACCENT}; }}
    QPushButton:pressed {{ background: #1a4a2a; }}
    QPushButton:disabled {{ color: #555; border-color: #333; }}
"""
GAMING_BTN = f"""
    QPushButton {{
        background: #1a1a00;
        color: #cccc00;
        border: 1px solid #555500;
        border-radius: 4px;
        padding: 6px 14px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: #2a2a00; border-color: #aaaa00; }}
"""
SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        background: #333; height: 4px; border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT}; height: 4px; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT_PRI}; width: 12px; height: 12px;
        margin: -4px 0; border-radius: 6px;
    }}
"""
LIST_STYLE = f"""
    QListWidget {{
        background: {BG_PANEL};
        color: {TEXT_PRI};
        border: none;
        font-size: 13px;
    }}
    QListWidget::item {{ padding: 6px 8px; border-bottom: 1px solid #222; }}
    QListWidget::item:selected {{ background: {BG_ACTIVE}; color: {ACCENT}; }}
    QListWidget::item:hover {{ background: #202020; }}
"""


class BBSGrooveWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('BBS grOOve')
        self.setMinimumSize(720, 560)
        self.setStyleSheet(f'background: {BG_MAIN}; color: {TEXT_PRI};')

        self._signals  = _Signals()
        self._playlist = Playlist()
        self._player   = MPVPlayer()
        self._source: SpotifySource | None = None
        self._playing  = False

        self._pref_store         = PrefStore()
        self._versions_expanded  = self._pref_store.get_ui_state("versions_expanded", True)
        self._connect_signals()
        self._build_ui()
        self._setup_timers()

    # ------------------------------------------------------------------ #
    #  Construction UI                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f'background: {BG_MAIN};')
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._header())
        layout.addWidget(self._url_bar())

        body = QHBoxLayout()
        body.setContentsMargins(12, 12, 12, 12)
        body.setSpacing(12)
        body.addWidget(self._left_panel(), 1)
        body.addWidget(self._right_panel(), 2)
        layout.addLayout(body)

        layout.addWidget(self._player_bar())

    def _header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-bottom: 1px solid #222;')
        w.setFixedHeight(48)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 0, 16, 0)

        logo = QLabel('BBS gr<span style="color:#1DB954">OO</span>ve')
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(f'font-size: 18px; font-weight: bold; color: {TEXT_PRI}; background: transparent;')
        h.addWidget(logo)
        h.addStretch()

        self._btn_gaming = QPushButton('🎮  Mode Gaming')
        self._btn_gaming.setStyleSheet(GAMING_BTN)
        self._btn_gaming.clicked.connect(self._switch_gaming)
        h.addWidget(self._btn_gaming)
        return w

    def _url_bar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-bottom: 1px solid #222;')
        w.setFixedHeight(52)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 8, 16, 8)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText(
            'Coller une URL Spotify (track, album, playlist) ou recherche libre…'
        )
        self._url_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_MAIN}; color: {TEXT_PRI};
                border: 1px solid #333; border-radius: 4px;
                padding: 4px 10px; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self._url_input.returnPressed.connect(self._load_url)
        h.addWidget(self._url_input)

        btn_load = QPushButton('Charger')
        btn_load.setStyleSheet(BTN_STYLE)
        btn_load.clicked.connect(self._load_url)
        h.addWidget(btn_load)
        return w

    def _left_panel(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f'background: {BG_PANEL}; border-radius: 6px;')
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QLabel('  Playlist')
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(f'color: {TEXT_SEC}; font-size: 12px; font-weight: bold; background: transparent;')
        v.addWidget(hdr)

        self._list = QListWidget()
        self._list.setStyleSheet(LIST_STYLE)
        self._list.itemDoubleClicked.connect(self._on_list_dclick)
        v.addWidget(self._list)
        return w

    def _right_panel(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f'background: {BG_PANEL}; border-radius: 6px;')
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(8)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Ligne haute : artwork + versions — hauteur fixe 220px
        top_w = QWidget()
        top_w.setFixedHeight(220)
        top_w.setStyleSheet('background: transparent;')
        top_w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top = QHBoxLayout(top_w)
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)
        top.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Artwork
        self._artwork = QLabel()
        self._artwork.setFixedSize(220, 220)
        self._artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._artwork.setStyleSheet(
            f'background: {BG_ITEM}; border-radius: 8px; color: #444; font-size: 52px;'
        )
        self._artwork.setText('♫')
        top.addWidget(self._artwork)

        # Panel versions (à droite de l artwork)
        vp = QFrame()
        vp.setStyleSheet(f'background: {BG_ITEM}; border-radius: 6px;')
        vp.setFixedWidth(220)
        vp.setSizePolicy(__import__('PyQt6.QtWidgets', fromlist=['QSizePolicy']).QSizePolicy.Policy.Fixed,
                         __import__('PyQt6.QtWidgets', fromlist=['QSizePolicy']).QSizePolicy.Policy.Minimum)
        vpl = QVBoxLayout(vp)
        vpl.setContentsMargins(6, 6, 6, 6)
        vpl.setSpacing(4)

        # Header versions avec bouton collapse
        hdr = QHBoxLayout()
        lbl_v = QLabel('Versions')
        lbl_v.setStyleSheet(f'color: {TEXT_SEC}; font-size: 11px; font-weight: bold; background: transparent;')
        self._btn_versions = QPushButton('▼' if self._versions_expanded else '▶')
        self._btn_versions.setFixedSize(20, 20)
        self._btn_versions.setStyleSheet(
            f'background: transparent; color: {TEXT_SEC}; border: none; font-size: 10px;'
        )
        self._btn_versions.clicked.connect(self._toggle_versions)
        hdr.addWidget(lbl_v)
        hdr.addStretch()
        hdr.addWidget(self._btn_versions)
        vpl.addLayout(hdr)

        # Liste des versions
        self._versions_list = QListWidget()
        self._versions_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {TEXT_PRI};
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 4px 2px;
                border-bottom: 1px solid #222;
            }}
            QListWidget::item:hover {{
                background: #2a2a2a;
                color: {ACCENT};
            }}
            QListWidget::item:selected {{
                background: #1a3a1a;
                color: {ACCENT};
            }}
        """)
        self._versions_list.setVisible(self._versions_expanded)
        self._versions_list.itemClicked.connect(self._on_version_clicked)
        vpl.addWidget(self._versions_list)

        self._versions_panel = vp
        if not self._versions_expanded:
            vp.setFixedHeight(32)
        top.addWidget(vp, 0, Qt.AlignmentFlag.AlignTop)
        v.addWidget(top_w)

        # Titre
        self._lbl_title = QLabel('—')
        self._lbl_title.setStyleSheet(
            f'color: {TEXT_PRI}; font-size: 15px; font-weight: bold; background: transparent;'
        )
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._lbl_title.setWordWrap(True)
        v.addWidget(self._lbl_title)

        # Artistes
        self._lbl_artist = QLabel('')
        self._lbl_artist.setStyleSheet(
            f'color: {ACCENT}; font-size: 13px; background: transparent;'
        )
        self._lbl_artist.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._lbl_artist.setWordWrap(True)
        v.addWidget(self._lbl_artist)

        # Album · Année
        self._lbl_album = QLabel('')
        self._lbl_album.setStyleSheet(
            f'color: {TEXT_SEC}; font-size: 12px; background: transparent;'
        )
        self._lbl_album.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._lbl_album.setWordWrap(True)
        v.addWidget(self._lbl_album)

        # Durée · Explicit
        self._lbl_meta = QLabel('')
        self._lbl_meta.setStyleSheet(
            f'color: #666; font-size: 11px; background: transparent;'
        )
        self._lbl_meta.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self._lbl_meta)

        # Status
        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet(
            f'color: {ACCENT}; font-size: 11px; background: transparent;'
        )
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self._lbl_status)

        v.addStretch()
        return w

    def _player_bar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-top: 1px solid #222;')
        w.setFixedHeight(90)
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 8, 16, 8)
        v.setSpacing(4)

        # Boutons de contrôle
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addStretch()

        self._btn_shuffle = self._ctrl_btn('⇄', checkable=True)
        self._btn_prev    = self._ctrl_btn('◀◀')
        self._btn_play    = self._ctrl_btn('▶', size=20)
        self._btn_next    = self._ctrl_btn('▶▶')
        self._btn_repeat  = self._ctrl_btn('↺', checkable=True)

        for b in (self._btn_shuffle, self._btn_prev, self._btn_play,
                  self._btn_next, self._btn_repeat):
            ctrl.addWidget(b)

        ctrl.addStretch()
        v.addLayout(ctrl)

        # Progress bar + temps
        prog_row = QHBoxLayout()
        prog_row.setSpacing(8)

        self._lbl_time = QLabel('0:00')
        self._lbl_time.setStyleSheet(f'color: {TEXT_SEC}; font-size: 11px; background: transparent;')
        prog_row.addWidget(self._lbl_time)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setStyleSheet(SLIDER_STYLE)
        self._slider.setRange(0, 1000)
        self._slider.sliderMoved.connect(self._on_seek)
        prog_row.addWidget(self._slider)

        self._lbl_duration = QLabel('0:00')
        self._lbl_duration.setStyleSheet(f'color: {TEXT_SEC}; font-size: 11px; background: transparent;')
        prog_row.addWidget(self._lbl_duration)

        # Volume
        vol_lbl = QLabel('🔊')
        vol_lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 11px; background: transparent;')
        prog_row.addWidget(vol_lbl)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setStyleSheet(SLIDER_STYLE)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(100)
        self._vol_slider.setFixedWidth(80)
        self._vol_slider.valueChanged.connect(self._on_volume)
        prog_row.addWidget(self._vol_slider)

        v.addLayout(prog_row)

        # Connexions
        self._btn_play.clicked.connect(self._on_play_pause)
        self._btn_next.clicked.connect(self._on_next)
        self._btn_prev.clicked.connect(self._on_prev)
        self._btn_shuffle.toggled.connect(self._on_shuffle)
        self._btn_repeat.toggled.connect(self._on_repeat)
        return w

    def _ctrl_btn(self, label: str, size: int = 14,
                  checkable: bool = False) -> QPushButton:
        b = QPushButton(label)
        b.setCheckable(checkable)
        b.setFixedSize(40, 32)
        b.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_PRI};
                border: none; font-size: {size}px;
            }}
            QPushButton:hover {{ color: {ACCENT}; }}
            QPushButton:checked {{ color: {ACCENT}; }}
        """)
        return b

    # ------------------------------------------------------------------ #
    #  Timers & signaux                                                    #
    # ------------------------------------------------------------------ #

    def _connect_signals(self):
        self._signals.tracks_loaded.connect(self._on_tracks_loaded)
        self._signals.track_enriched.connect(self._update_track_display)
        self._signals.candidates_ready.connect(self._update_versions_list)
        self._signals.resolved.connect(self._on_resolved)
        self._signals.artwork_ready.connect(self._on_artwork)
        self._signals.error.connect(self._on_error)
        self._signals.track_ended.connect(self._on_next)
        self._playlist.on_resolved = self._signals.resolved.emit

    def _setup_timers(self):
        self._progress_timer = QTimer()
        self._progress_timer.setInterval(500)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start()

    # ------------------------------------------------------------------ #
    #  Chargement URL                                                      #
    # ------------------------------------------------------------------ #

    def _load_url(self):
        url = self._url_input.text().strip()
        if not url:
            return
        self._lbl_status.setText('Chargement…')
        threading.Thread(target=self._fetch_tracks, args=(url,), daemon=True).start()

    def _fetch_tracks(self, url: str):
        try:
            if self._source is None:
                self._source = SpotifySource()
            tracks = self._source.get_tracks(url)
            if tracks:
                self._signals.tracks_loaded.emit(tracks)
            else:
                self._signals.error.emit('Aucun titre trouvé.')
        except Exception as e:
            self._signals.error.emit(str(e))

    # ------------------------------------------------------------------ #
    #  Slots UI                                                            #
    # ------------------------------------------------------------------ #

    def _on_tracks_loaded(self, tracks: list):
        self._playlist.load(tracks)
        self._list.clear()
        for i, t in enumerate(tracks):
            item = QListWidgetItem(f"  {i+1:02d}.  {t['artist']}  —  {t['title']}")
            self._list.addItem(item)
        self._lbl_status.setText(f'{len(tracks)} titre(s) chargé(s)')
        self._start_track(0)

    def _on_resolved(self, index: int, url: str):
        if index == self._playlist.current_index and not self._player.is_running():
            self._play_current()

    def _on_artwork(self, data: bytes):
        pix = QPixmap()
        pix.loadFromData(data)
        pix = pix.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
        self._artwork.setPixmap(pix)
        self._artwork.setText('')

    def _on_error(self, msg: str):
        self._lbl_status.setText(f'Erreur : {msg}')

    def _on_play_pause(self):
        if self._player.is_running():
            self._player.toggle_pause()
            paused = self._player.get_paused()
            self._btn_play.setText('▶' if paused else '⏸')
        else:
            self._start_track(self._playlist.current_index)

    def _on_next(self):
        if self._playlist.repeat and self._playing:
            self._play_current()
            return
        track = self._playlist.go_next()
        if track:
            self._update_track_display(track)
            self._play_current()

    def _on_prev(self):
        track = self._playlist.go_prev()
        if track:
            self._update_track_display(track)
            self._play_current()

    def _on_shuffle(self, state: bool):
        self._playlist.shuffle = state

    def _on_repeat(self, state: bool):
        self._playlist.repeat = state

    def _on_list_dclick(self, item: QListWidgetItem):
        idx = self._list.row(item)
        self._player.stop()
        self._playing = False
        track = self._playlist.go_to(idx)
        if track:
            self._update_track_display(track)
            self._play_current()

    def _on_seek(self, value: int):
        dur = self._player.get_duration()
        if dur:
            self._player.seek(dur * value / 1000)

    # ------------------------------------------------------------------ #
    #  Lecture                                                             #
    # ------------------------------------------------------------------ #

    def _start_track(self, index: int):
        track = self._playlist.go_to(index)
        if not track:
            return
        self._update_track_display(track)
        self._play_current()

    def _play_current(self):
        url = self._playlist.current_url()
        if not url:
            self._lbl_status.setText('Résolution en cours…')
            return
        self._player.on_track_ended = self._signals.track_ended.emit
        self._player.play(url)
        self._playing = True
        self._current_playing_url = url
        track = self._playlist.current_track()
        if track:
            self._current_spotify_id = track.get('spotify_id', '')
            if track.get('needs_enrich'):
                import threading as _t
                _t.Thread(target=self._enrich_track, args=(self._playlist.current_index,), daemon=True).start()
            # Fetch candidats YouTube en arrière-plan
            import threading as _t2
            _t2.Thread(
                target=self._fetch_candidates,
                args=(self._playlist.current_index, self._current_spotify_id, url),
                daemon=True,
            ).start()
        self._btn_play.setText('⏸')
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        self._lbl_status.setText('Lecture')

    def _update_track_display(self, track: dict):
        self._versions_list.clear()
        self._lbl_title.setText(track.get('title', ''))
        self._lbl_artist.setText(track.get('all_artists') or track.get('artist', ''))

        album = track.get('album', '')
        year  = track.get('year', '')
        album_year = f"{album}  ·  {year}" if album and year else album or year
        self._lbl_album.setText(album_year)

        dur_ms   = track.get('duration_ms', 0)
        dur_s    = int(dur_ms / 1000)
        dur_str  = f"{dur_s // 60}:{dur_s % 60:02d}" if dur_s else ''
        explicit = '🅴  ' if track.get('is_explicit') else ''
        tnum     = track.get('track_number', '')
        meta_parts = [p for p in [explicit + dur_str, f'Track {tnum}' if tnum else ''] if p]
        self._lbl_meta.setText('  ·  '.join(meta_parts))

        # Reset artwork
        self._artwork.clear()
        self._artwork.setText('♫')

        url = track.get('artwork_url')
        if url:
            threading.Thread(
                target=self._fetch_artwork, args=(url,), daemon=True
            ).start()

    def _fetch_artwork(self, url: str):
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                self._signals.artwork_ready.emit(r.content)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Progress bar                                                        #
    # ------------------------------------------------------------------ #

    def _update_progress(self):
        if not self._player.is_running():
            return
        pos = self._player.get_time_pos()
        dur = self._player.get_duration()
        if dur and dur > 0:
            self._slider.setValue(int(pos / dur * 1000))
        self._lbl_time.setText(self._fmt(pos))
        self._lbl_duration.setText(self._fmt(dur))

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f'{s // 60}:{s % 60:02d}'

    # ------------------------------------------------------------------ #
    #  Mode gaming                                                         #
    # ------------------------------------------------------------------ #

    def _switch_gaming(self):
        from bbs_groove.ui.tray import GrooveTray
        # Sauvegarder l'état
        state = {
            'tracks':  self._playlist.tracks,
            'index':   self._playlist.current_index,
            'shuffle': self._playlist.shuffle,
            'repeat':  self._playlist.repeat,
        }
        self._tray = GrooveTray(player=self._player, playlist=self._playlist,
                                state=state, on_return=self._on_return_from_gaming)
        self._tray.show()
        self.hide()

    def _on_return_from_gaming(self):
        self.show()
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        track = self._playlist.current_track()
        if not track:
            return
        self._update_track_display(track)
        # Artwork
        art_url = track.get('artwork_url')
        import threading
        if art_url:
            threading.Thread(target=self._fetch_artwork, args=(art_url,), daemon=True).start()
        elif track.get('spotify_id'):
            # Track pas encore enrichi (changement en gaming mode) — enrichir maintenant
            threading.Thread(target=self._enrich_track, args=(idx,), daemon=True).start()
        # URL courante depuis la playlist
        cur_url = self._playlist.current_url() or self._current_playing_url
        self._current_playing_url = cur_url or ''
        # Toujours re-fetcher les versions au retour du gaming mode
        import threading
        self._candidates = []
        if track.get('spotify_id'):
            threading.Thread(
                target=self._fetch_candidates,
                args=(idx, track.get('spotify_id', ''), cur_url or ''),
                daemon=True,
            ).start()
        self._lbl_status.setText('Retour mode normal')

    def _enrich_track(self, index: int):
        """Enrichit les métadonnées d un track en arrière-plan."""
        print(f'[enrich] index={index} source={self._source is not None}', flush=True)
        if self._source is None:
            return
        tracks = self._playlist.tracks
        if index >= len(tracks):
            return
        enriched = self._source.enrich_track(dict(tracks[index]))
        # Mettre à jour le track dans la playlist sans la remplacer
        tracks[index].update(enriched)
        # Rafraîchir l affichage si c est le titre courant
        if index == self._playlist.current_index:
            self._signals.track_enriched.emit(enriched)

    def _toggle_versions(self):
        self._versions_expanded = not self._versions_expanded
        self._versions_list.setVisible(self._versions_expanded)
        self._btn_versions.setText('▼' if self._versions_expanded else '▶')
        if self._versions_expanded:
            self._versions_panel.setMaximumHeight(16777215)
            self._versions_panel.setMinimumHeight(0)
        else:
            self._versions_panel.setFixedHeight(32)
        self._pref_store.save_ui_state('versions_expanded', self._versions_expanded)

    def _update_versions_list(self, candidates: list, current_url: str):
        self._versions_list.clear()
        for c in candidates:
            dur  = c.get('duration_s', 0)
            mins = int(dur // 60)
            secs = int(dur % 60)
            dur_str  = f"{mins}:{secs:02d}" if dur else '?:??'
            channel  = c.get('channel', '') or c.get('title', '')
            if len(channel) > 22:
                channel = channel[:20] + '…'
            check = '✓ ' if c['url'] == current_url else '   '
            full_title = c.get('title', '')
            item = QListWidgetItem(f"{check}{channel}  {dur_str}")
            item.setData(Qt.ItemDataRole.UserRole, c['url'])
            item.setToolTip(full_title)
            if c['url'] == current_url:
                from PyQt6.QtGui import QBrush, QFont
                item.setForeground(QColor(ACCENT))
                item.setBackground(QBrush(QColor('#0f2f0f')))
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            self._versions_list.addItem(item)

    def _on_version_clicked(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if not url or url == self._current_playing_url:
            return
        print(f'[pref] sid={self._current_spotify_id!r} url={url[:40]!r}', flush=True)
        # Sauvegarder la préférence
        if self._current_spotify_id:
            self._pref_store.save(self._current_spotify_id, url)
            print(f'[pref] saved OK', flush=True)
        else:
            print(f'[pref] ERROR: no spotify_id!', flush=True)
        # Mettre à jour l URL résolue dans la playlist
        idx = self._playlist.current_index
        with self._playlist._lock:
            self._playlist._resolved[idx] = url
        # Rejouer immédiatement
        self._current_playing_url = url
        self._player.on_track_ended = self._signals.track_ended.emit
        self._player.play(url)
        self._btn_play.setText('⏸')
        # Mettre à jour le ✓ dans la liste
        self._update_versions_check(url)

    def _update_versions_check(self, current_url: str):
        for i in range(self._versions_list.count()):
            item = self._versions_list.item(i)
            url  = item.data(Qt.ItemDataRole.UserRole)
            text = item.text()
            if url == current_url:
                if not text.startswith('✓'):
                    item.setText('✓ ' + text[3:])
                item.setForeground(QColor(ACCENT))
            else:
                if text.startswith('✓'):
                    item.setText('   ' + text[3:])
                item.setForeground(QColor(TEXT_PRI))

    def _fetch_candidates(self, index: int, spotify_id: str, current_url: str):
        """Fetch les candidats YouTube en arrière-plan."""
        track = self._playlist.tracks[index] if index < self._playlist.count() else None
        if not track:
            return
        try:
            from bbs_groove.core.resolver import Resolver
            candidates = Resolver().resolve_candidates(track)
            if candidates and index == self._playlist.current_index:
                self._candidates = candidates
                # Si l URL courante ne matche aucun candidat,
                # le premier EST ce qui joue (même algo durée)
                if not any(c['url'] == current_url for c in candidates):
                    effective_url = candidates[0]['url']
                else:
                    effective_url = current_url
                self._signals.candidates_ready.emit(candidates, effective_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')

    def _on_volume(self, value: int):
        self._player.set_volume(value)

    def closeEvent(self, event):
        self._player.stop()
        event.accept()
