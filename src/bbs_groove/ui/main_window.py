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


# ── Signaux thread-safe ──────────────────────────────────────────────── #
class _Signals(QObject):
    tracks_loaded    = pyqtSignal(list)
    resolved         = pyqtSignal(int, str)
    artwork_ready    = pyqtSignal(bytes)
    error            = pyqtSignal(str)
    track_ended      = pyqtSignal()
    track_enriched   = pyqtSignal(dict)


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

        # Artwork
        self._artwork = QLabel()
        self._artwork.setFixedSize(220, 220)
        self._artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._artwork.setStyleSheet(
            f'background: {BG_ITEM}; border-radius: 8px; color: #444; font-size: 52px;'
        )
        self._artwork.setText('♫')
        v.addWidget(self._artwork, alignment=Qt.AlignmentFlag.AlignHCenter)

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
        # Enrichir les métadonnées en arrière-plan si nécessaire
        track = self._playlist.current_track()
        if track and track.get('needs_enrich'):
            import threading as _t
            _t.Thread(target=self._enrich_track, args=(self._playlist.current_index,), daemon=True).start()
        self._btn_play.setText('⏸')
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        self._lbl_status.setText('Lecture')

    def _update_track_display(self, track: dict):
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
        track = self._playlist.current_track()
        if track:
            self._update_track_display(track)
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

    def _on_volume(self, value: int):
        self._player.set_volume(value)

    def closeEvent(self, event):
        self._player.stop()
        event.accept()
