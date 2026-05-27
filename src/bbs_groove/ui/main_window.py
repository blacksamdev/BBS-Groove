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
from bbs_groove.core.playlist_store import PlaylistStore


# ── Signaux thread-safe ──────────────────────────────────────────────── #
class _Signals(QObject):
    tracks_loaded    = pyqtSignal(list)
    resolved         = pyqtSignal(int, str)
    artwork_ready    = pyqtSignal(bytes)
    error            = pyqtSignal(str)
    track_ended      = pyqtSignal()
    track_enriched   = pyqtSignal(dict)
    candidates_ready = pyqtSignal(list, str)
    lyrics_ready     = pyqtSignal(str, list)


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
        self._playlist_store     = PlaylistStore()
        self._versions_expanded  = self._pref_store.get_ui_state("versions_expanded", False)
        self._sleep_timer        = QTimer()
        self._sleep_timer.setSingleShot(True)
        self._sleep_timer.timeout.connect(self._on_sleep_timer)
        self._sleep_remaining    = QTimer()
        self._sleep_remaining.setInterval(1000)
        self._sleep_remaining.timeout.connect(self._update_sleep_btn)
        self._sleep_secs         = 0
        self._lyrics_synced: list  = []
        self._lyrics_line: int     = -1
        self._connect_signals()
        self._build_ui()
        self._setup_timers()
        self.setMinimumSize(960, 600)
        self.resize(1200, 720)

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
        layout.addWidget(self._topbar())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        body.addWidget(self._center_panel(), 2)
        body.addWidget(self._right_panel(), 2)
        layout.addLayout(body, 1)
        layout.addWidget(self._player_bar())




    def _topbar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-bottom: 1px solid #222;')
        w.setFixedHeight(52)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(10)
        logo = QLabel('BBS gr<span style="color:#1DB954">OO</span>ve')
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(f'font-size: 16px; font-weight: bold; color: {TEXT_PRI}; background: transparent;')
        logo.setFixedWidth(140)
        h.addWidget(logo)
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText('URL Spotify / Deezer (track, album, playlist, artiste)…')
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

        btn_save = QPushButton('💾')
        btn_save.setToolTip('Sauvegarder comme playlist perso')
        btn_save.setFixedWidth(36)
        btn_save.setStyleSheet(BTN_STYLE)
        btn_save.clicked.connect(self._save_as_playlist)
        h.addWidget(btn_save)
        return w

    def _sidebar(self) -> QWidget:
        w = QFrame()
        w.setFixedWidth(55)
        w.setStyleSheet(f'background: {BG_PANEL}; border-right: 1px solid #222;')
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 12, 0, 12)
        v.setSpacing(4)

        def _nb(icon, label, checkable=False):
            b = QPushButton(icon)
            b.setCheckable(checkable)
            b.setFixedSize(55, 55)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {TEXT_SEC};
                    border: none; font-size: 22px; padding: 4px 2px;
                }}
                QPushButton:hover {{ background: {BG_ITEM}; color: {TEXT_PRI}; }}
                QPushButton:checked {{
                    background: {BG_ITEM}; color: {ACCENT};
                    border-left: 3px solid {ACCENT};
                }}
            """)
            return b

        self._nav_queue = _nb('🎵', 'Lecture', checkable=True)
        self._nav_queue.setToolTip('Lecture')
        self._nav_queue.setChecked(True)
        self._nav_queue.clicked.connect(lambda: self._switch_view(0))
        v.addWidget(self._nav_queue)

        self._nav_playlists = _nb('📋', 'Playlists', checkable=True)
        self._nav_playlists.setToolTip('Playlist')
        self._nav_playlists.clicked.connect(lambda: self._switch_view(1))
        v.addWidget(self._nav_playlists)

        v.addStretch()

        self._btn_gaming = _nb('🎮', 'Gaming')
        self._btn_gaming.setToolTip('Mode Gaming')
        self._btn_gaming.clicked.connect(self._switch_gaming)
        v.addWidget(self._btn_gaming)
        return w

    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)
        if index == 1:
            if hasattr(self, "_pl_detail") and self._pl_detail.isVisible():
                self._pl_detail.setVisible(False)
                if hasattr(self, "_pl_list"): self._pl_list.setVisible(True)
            self._refresh_pl_list()

    def _center_panel(self) -> QWidget:
        from PyQt6.QtWidgets import QStackedWidget
        self._center_stack = QStackedWidget()

        # Vue 0 : Queue
        queue_w = QFrame()
        queue_w.setStyleSheet(f'background: {BG_PANEL};')
        qv = QVBoxLayout(queue_w)
        qv.setContentsMargins(0, 0, 0, 0)
        qv.setSpacing(0)
        hdr = QLabel('  Lecture')
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(
            f'color: {TEXT_SEC}; font-size: 12px; font-weight: bold;'
            f' background: transparent; padding-left: 12px;'
            f' border-bottom: 1px solid #222;'
        )
        qv.addWidget(hdr)
        self._list = QListWidget()
        self._list.setStyleSheet(LIST_STYLE)
        self._list.itemDoubleClicked.connect(self._on_list_dclick)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_queue_track_menu)
        qv.addWidget(self._list)
        self._center_stack.addWidget(queue_w)

        # Vue 1 : Mes Playlists
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(0)
        ph = QWidget()
        ph.setFixedHeight(36)
        ph.setStyleSheet('background: transparent; border-bottom: 1px solid #222;')
        phl = QHBoxLayout(ph)
        phl.setContentsMargins(12, 0, 8, 0)
        ph_lbl = QLabel('Playlist')
        ph_lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 12px; font-weight: bold; background: transparent;')
        phl.addWidget(ph_lbl)
        phl.addStretch()
        btn_new = QPushButton('+ Nouvelle')
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #000; border: none;
                border-radius: 4px; font-size: 11px;
                padding: 3px 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #1ed760; }}
        """)
        btn_new.clicked.connect(self._new_playlist)
        phl.addWidget(btn_new)
        pv.addWidget(ph)
        self._pl_list = QListWidget()
        self._pl_list.setStyleSheet(LIST_STYLE)
        self._pl_list.itemClicked.connect(self._on_pl_dclick)
        self._pl_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._pl_list.customContextMenuRequested.connect(self._on_pl_list_menu)
        pv.addWidget(self._pl_list)
        self._pl_detail = QFrame()
        self._pl_detail.setStyleSheet(f'background: {BG_PANEL};')
        self._pl_detail.setVisible(False)
        pdv = QVBoxLayout(self._pl_detail)
        pdv.setContentsMargins(0, 0, 0, 0)
        pdv.setSpacing(0)
        pdh = QWidget()
        pdh.setFixedHeight(36)
        pdh.setStyleSheet('background: transparent; border-bottom: 1px solid #222;')
        pdhl = QHBoxLayout(pdh)
        pdhl.setContentsMargins(8, 0, 8, 0)
        btn_back = QPushButton('← Retour')
        btn_back.setStyleSheet(f'background: transparent; color: {TEXT_SEC}; border: none; font-size: 11px;')
        btn_back.clicked.connect(self._pl_back)
        pdhl.addWidget(btn_back)
        self._pl_detail_name = QLabel('')
        self._pl_detail_name.setStyleSheet(f'color: {TEXT_PRI}; font-size: 12px; font-weight: bold; background: transparent;')
        pdhl.addWidget(self._pl_detail_name)
        pdhl.addStretch()
        btn_rename = QPushButton('✏️')
        btn_rename.setToolTip('Renommer')
        btn_rename.setFixedWidth(30)
        btn_rename.setStyleSheet(f'background: transparent; color: {TEXT_SEC}; border: none;')
        btn_rename.clicked.connect(self._pl_rename)
        pdhl.addWidget(btn_rename)
        btn_play_pl = QPushButton('▶')
        btn_play_pl.setToolTip('Jouer')
        btn_play_pl.setFixedWidth(30)
        btn_play_pl.setStyleSheet(f'background: transparent; color: {ACCENT}; border: none;')
        btn_play_pl.clicked.connect(self._pl_play)
        pdhl.addWidget(btn_play_pl)
        pdv.addWidget(pdh)
        self._pl_tracks_list = QListWidget()
        self._pl_tracks_list.setStyleSheet(LIST_STYLE)
        pdv.addWidget(self._pl_tracks_list)
        pv.addWidget(self._pl_detail)
        self._center_stack.addWidget(playlists_w)
        self._pl_current = ''
        return self._center_stack

    def _right_panel(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f'background: {BG_PANEL}; border-radius: 6px;')
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Ligne haute : artwork + infos/versions ──────────────────────
        top = QHBoxLayout()
        top.setSpacing(14)
        top.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Artwork
        self._artwork = QLabel()
        self._artwork.setMinimumSize(180, 180)
        self._artwork.setMaximumSize(320, 320)
        self._artwork.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._artwork.setStyleSheet(
            f'background: {BG_ITEM}; border-radius: 8px; color: #444; font-size: 52px;'
        )
        self._artwork.setText('♫')
        top.addWidget(self._artwork, 0, Qt.AlignmentFlag.AlignTop)

        # Panel droit : infos + versions
        vp = QFrame()
        vp.setStyleSheet(f'background: {BG_ITEM}; border-radius: 6px;')
        vp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        vpl = QVBoxLayout(vp)
        vpl.setContentsMargins(10, 10, 10, 10)
        vpl.setSpacing(4)

        # ── QStackedWidget : info (page 0) ou versions (page 1) ──
        from PyQt6.QtWidgets import QStackedWidget
        self._info_stack = QStackedWidget()

        # Page 0 : infos titre/artiste/etc
        info_w = QWidget()
        info_w.setStyleSheet('background: transparent;')
        info_v = QVBoxLayout(info_w)
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(4)
        self._lbl_title = QLabel('—')
        self._lbl_title.setStyleSheet(
            f'color: {TEXT_PRI}; font-size: 15px; font-weight: bold; background: transparent;'
        )
        self._lbl_title.setWordWrap(True)
        info_v.addWidget(self._lbl_title)
        self._lbl_artist = QLabel('')
        self._lbl_artist.setStyleSheet(f'color: {ACCENT}; font-size: 13px; background: transparent;')
        self._lbl_artist.setWordWrap(True)
        info_v.addWidget(self._lbl_artist)
        self._lbl_album = QLabel('')
        self._lbl_album.setStyleSheet(f'color: {TEXT_SEC}; font-size: 12px; background: transparent;')
        self._lbl_album.setWordWrap(True)
        info_v.addWidget(self._lbl_album)
        self._lbl_meta = QLabel('')
        self._lbl_meta.setStyleSheet('color: #666; font-size: 11px; background: transparent;')
        info_v.addWidget(self._lbl_meta)
        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet(f'color: {ACCENT}; font-size: 11px; background: transparent;')
        info_v.addWidget(self._lbl_status)
        info_v.addStretch()
        self._info_stack.addWidget(info_w)

        # Page 1 : liste des versions
        self._versions_list = QListWidget()
        self._versions_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none;
                color: {TEXT_PRI}; font-size: 11px;
            }}
            QListWidget::item {{ padding: 4px 2px; border-bottom: 1px solid #222; }}
            QListWidget::item:hover {{ background: #2a2a2a; color: {ACCENT}; }}
            QListWidget::item:selected {{ background: #1a3a1a; color: {ACCENT}; }}
        """)
        self._versions_list.itemClicked.connect(self._on_version_clicked)
        self._info_stack.addWidget(self._versions_list)

        # Défaut : page 0 (infos, versions fermées)
        self._info_stack.setCurrentIndex(1 if self._versions_expanded else 0)
        self._info_stack.setFixedHeight(180)
        vpl.addWidget(self._info_stack)

        # ── Séparateur + header Versions EN BAS ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #333; background: #333;')
        sep.setFixedHeight(1)
        vpl.addWidget(sep)

        hdr = QHBoxLayout()
        lbl_v = QLabel('Versions')
        lbl_v.setStyleSheet(
            f'color: {TEXT_SEC}; font-size: 11px; font-weight: bold; background: transparent;'
        )
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
        self._versions_panel = vp
        top.addWidget(vp)
        v.addLayout(top)

        # Bouton ajouter à une playlist perso
        self._btn_add_to_pl = QPushButton('☰  Playlist')
        self._btn_add_to_pl.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ITEM}; color: {TEXT_SEC};
                border: 1px solid #333; border-radius: 4px;
                font-size: 11px; padding: 6px 12px; margin: 4px 0px;
            }}
            QPushButton:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
        """)
        self._btn_add_to_pl.setVisible(False)
        self._btn_add_to_pl.clicked.connect(self._on_add_to_playlist)
        v.addWidget(self._btn_add_to_pl)

        # ── Zone lyrics ─────────────────────────────────────────────────
        from PyQt6.QtWidgets import QTextEdit
        self._lyrics_widget = QTextEdit()
        self._lyrics_widget.setReadOnly(True)
        self._lyrics_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._lyrics_widget.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_ITEM};
                border-radius: 6px;
                color: {TEXT_SEC};
                font-size: 13px;
                padding: 10px;
                border: none;
            }}
        """)
        self._lyrics_widget.setPlaceholderText('Paroles non disponibles')
        self._lyrics_widget.setPlainText("")
            self._lyrics_widget.setVisible(True)
        self._lyrics_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        v.addWidget(self._lyrics_widget, 1)
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
        self._btn_sleep   = self._ctrl_btn('⏱ Timer')
        self._btn_sleep.setFixedWidth(70)

        for b in (self._btn_shuffle, self._btn_prev, self._btn_play,
                  self._btn_next, self._btn_repeat, self._btn_sleep):
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
        self._btn_sleep.clicked.connect(self._on_sleep_click)
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
        self._signals.track_enriched.connect(lambda t: self._update_track_display(t, clear_versions=False))
        self._signals.candidates_ready.connect(self._update_versions_list)
        self._signals.lyrics_ready.connect(self._on_lyrics_ready)
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
            # Détecter si c'est une URL ou une recherche libre
            is_url = url.startswith('http') or 'spotify.com' in url or 'deezer.com' in url
            if is_url:
                if self._source is None:
                    self._source = SpotifySource()
                tracks = self._source.get_tracks(url)
            else:
                tracks = self._search_youtube(url)
            if tracks:
                self._signals.tracks_loaded.emit(tracks)
            else:
                self._signals.error.emit('Aucun titre trouvé.')
        except Exception as e:
            log(f"fetch_tracks: {e}", "warning")
            self._signals.error.emit(str(e))

    def _search_youtube(self, query: str) -> list[dict]:
        """Recherche YouTube Music — retourne jusqu'à 15 résultats."""
        import yt_dlp, re as _re
        opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch15:{query}", download=False)
        entries = info.get("entries", []) if info else []
        tracks = []
        for e in entries:
            if not e:
                continue
            dur = e.get("duration") or 0
            if dur <= 0:  # Filtrer seulement les durées inconnues
                continue
            yt_url  = e.get("url", "")
            vid     = _re.search(r"v=([^&]+)", yt_url)
            thumb   = f"https://img.youtube.com/vi/{vid.group(1)}/hqdefault.jpg" if vid else None
            title   = e.get("title", "")
            channel = e.get("channel") or e.get("uploader", "")
            tracks.append({
                "title":       title,
                "artist":      channel,
                "all_artists": channel,
                "duration_ms": int(dur * 1000),
                "artwork_url": thumb,
                "spotify_id":  "",
                "year":        "",
                "needs_enrich": False,
            })
        return tracks

    # ------------------------------------------------------------------ #
    #  Slots UI                                                            #
    # ------------------------------------------------------------------ #

    def _on_tracks_loaded(self, tracks: list):
        if not tracks:
            self._lbl_status.setText('Aucun titre — URLs artiste non supportées, utilisez une playlist ou un album')
            return
        self._playlist.load(tracks)
        self._list.clear()
        for i, t in enumerate(tracks):
            item = QListWidgetItem(f"  {i+1:02d}.  {t['artist']}  —  {t['title']}")
            self._list.addItem(item)
        self._lbl_status.setText(f'{len(tracks)} titre(s) chargé(s)')
        self._btn_add_to_pl.setVisible(True)
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
            _t2.Thread(
                target=self._fetch_lyrics,
                args=(dict(track),),
                daemon=True,
            ).start()
        self._btn_play.setText('⏸')
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        self._lbl_status.setText('Lecture')

    def _update_track_display(self, track: dict, clear_versions: bool = True):
        if clear_versions:
            self._versions_list.clear()
            self._lyrics_widget.clear()
            self._lyrics_widget.setPlainText("")
            self._lyrics_widget.setVisible(True)
            self._lyrics_synced = []
            self._lyrics_line   = -1
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
        if self._lyrics_synced and pos > 0:
            self._sync_lyrics_line(pos)

    def _sync_lyrics_line(self, pos: float):
        """Surligne la ligne courante — rebuild HTML à chaque changement."""
        synced = self._lyrics_synced
        idx = 0
        for i, (t, _) in enumerate(synced):
            if t <= pos:
                idx = i
            else:
                break
        if idx == self._lyrics_line:
            return
        self._lyrics_line = idx
        parts = ['<html><body style="background:transparent;margin:0;padding:4px;">']
        for i, (_, line) in enumerate(synced):
            if not line:
                parts.append('<p style="margin:1px 0;">&nbsp;</p>')
            elif i == idx:
                parts.append(f'<p style="color:#ffffff;font-weight:bold;font-size:14px;margin:3px 0;">{line}</p>')
            elif abs(i - idx) <= 2:
                parts.append(f'<p style="color:#cccccc;font-size:13px;margin:2px 0;">{line}</p>')
            else:
                parts.append(f'<p style="color:#888888;font-size:12px;margin:1px 0;">{line}</p>')
        parts.append('</body></html>')
        self._lyrics_widget.setHtml(''.join(parts))
        from PyQt6.QtGui import QTextCursor
        block = self._lyrics_widget.document().findBlockByNumber(idx)
        if block.isValid():
            cursor = QTextCursor(block)
            self._lyrics_widget.setTextCursor(cursor)
            self._lyrics_widget.ensureCursorVisible()

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
        self._info_stack.setCurrentIndex(1 if self._versions_expanded else 0)
        self._btn_versions.setText('▼' if self._versions_expanded else '▶')
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
        # Trouver l'URL YouTube pérenne dans les candidats
        pref_url = next(
            (c.get('webpage_url', '') for c in self._candidates if c.get('url') == url),
            ''
        ) or url
        pref_key = self._current_spotify_id
        if not pref_key:
            t = self._playlist.current_track()
            if t:
                pref_key = t.get('artist','').lower() + '|' + t.get('title','').lower()
        if pref_key:
            self._pref_store.save(pref_key, pref_url)
        else:
            pass
        # Résoudre le stream frais depuis la webpage_url
        import threading
        click_idx = self._playlist.current_index
        click_sid = self._current_spotify_id
        def _resolve_and_play(yt_url, expected_idx, expected_sid):
            from bbs_groove.core.resolver import Resolver
            stream = Resolver().resolve_from_url(yt_url) if 'youtube' in yt_url else yt_url
            if not stream:
                return
            # Toujours mettre à jour _resolved pour persistance dans la session
            with self._playlist._lock:
                self._playlist._resolved[expected_idx] = stream
            # Ne jouer que si on est toujours sur le même titre
            if self._playlist.current_index != expected_idx:
                return
            self._current_playing_url = stream
            self._player.on_track_ended = self._signals.track_ended.emit
            self._player.play(stream)
        threading.Thread(target=_resolve_and_play, args=(url, click_idx, click_sid), daemon=True).start()
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
                # Chercher la préférence sauvegardée (YouTube URL) dans les candidats
                saved_yt = self._pref_store.get(spotify_id) if spotify_id else None
                if not saved_yt and track:
                    fk = track.get('artist','').lower() + '|' + track.get('title','').lower()
                    saved_yt = self._pref_store.get(fk) if fk else None
                if saved_yt and any(c['url'] == saved_yt for c in candidates):
                    effective_url = saved_yt
                elif any(c['url'] == current_url for c in candidates):
                    effective_url = current_url
                else:
                    effective_url = candidates[0]['url']
                self._signals.candidates_ready.emit(candidates, effective_url)
        except Exception as e:
            log(f"fetch_candidates: {e}", "warning")

    def _on_sleep_click(self):
        """Cycle : off → 15 → 30 → 45 → 60 → off."""
        options = [0, 15, 30, 45, 60]
        if self._sleep_timer.isActive():
            current = self._sleep_secs // 60
            try:
                idx = options.index(current)
            except ValueError:
                idx = 0
            nxt = options[(idx + 1) % len(options)]
        else:
            nxt = options[1]  # 15 min par défaut

        if nxt == 0:
            self._sleep_timer.stop()
            self._sleep_remaining.stop()
            self._btn_sleep.setFixedWidth(70)
            self._btn_sleep.setText('⏱ Timer')
            self._btn_sleep.setStyleSheet(self._btn_sleep.styleSheet().replace(
                f'border-color: {ACCENT}', 'border-color: #333'))
        else:
            self._sleep_secs = nxt * 60
            self._sleep_timer.start(self._sleep_secs * 1000)
            self._sleep_remaining.start()
            self._btn_sleep.setFixedWidth(72)
            self._update_sleep_btn()

    def _update_sleep_btn(self):
        remaining = self._sleep_timer.remainingTime() // 1000
        if remaining <= 0:
            return
        mins, secs = divmod(remaining, 60)
        self._btn_sleep.setText(f'⏱ {mins}:{secs:02d}')

    def _on_sleep_timer(self):
        self._sleep_remaining.stop()
        self._btn_sleep.setFixedWidth(70)
        self._btn_sleep.setText('⏱ Timer')
        self._player.stop()
        self._playing = False
        self._btn_play.setText('▶')
        self._lbl_status.setText('Sleep timer — lecture terminée')

    def _fetch_lyrics(self, track: dict):
        """Fetch les lyrics en arrière-plan."""
        from bbs_groove.core.lyrics_fetcher import LyricsFetcher
        artist = track.get('artist', '')
        title  = track.get('title', '')
        dur_ms = track.get('duration_ms', 0)
        try:
            result = LyricsFetcher().fetch(artist, title, dur_ms)
            text   = ''
            synced = []
            if result:
                text   = result.get('plain', '') or ''
                synced = result.get('synced', []) or []
            self._signals.lyrics_ready.emit(text, synced)
        except Exception as e:
            log(f'fetch_lyrics: {e}', 'warning')
            self._signals.lyrics_ready.emit('', [])

    def _on_lyrics_ready(self, text: str, synced: list):
        """Affiche les lyrics dans le widget."""
        self._lyrics_synced = synced
        self._lyrics_line   = -1
        if synced:
            # Afficher les synced lyrics comme texte plain pour départ
            lines = [line for _, line in synced if line]
            self._lyrics_widget.setPlainText('\n'.join(lines))
            self._lyrics_widget.setVisible(True)
        elif text:
            self._lyrics_synced = []
            self._lyrics_widget.setPlainText(text)
            self._lyrics_widget.setVisible(True)
        else:
            self._lyrics_synced = []
            self._lyrics_widget.clear()
            self._lyrics_widget.setPlainText("")
            self._lyrics_widget.setVisible(True)

    # ------------------------------------------------------------------ #
    #  Playlists perso                                                    #
    # ------------------------------------------------------------------ #

    def _refresh_pl_list(self):
        """Rafraîchit la liste des playlists perso avec boutons inline."""
        if not hasattr(self, "_pl_list"):
            return
        self._pl_list.clear()
        for name in self._playlist_store.names():
            tracks = self._playlist_store.get_tracks(name)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, name)
            from PyQt6.QtCore import QSize
            item.setSizeHint(QSize(0, 44))
            self._pl_list.addItem(item)
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 4, 6, 4)
            rl.setSpacing(4)
            lbl = QLabel(f"📋  {name}  ({len(tracks)})")
            lbl.setStyleSheet(f"color: {TEXT_PRI}; font-size: 12px; background: transparent;")
            rl.addWidget(lbl)
            rl.addStretch()
            for icon, tip, fn in [
                ("✏️", "Renommer", lambda checked=False, n=name: self._pl_rename_from_list(n)),
                ("🗑", "Supprimer", lambda checked=False, n=name: self._pl_delete(n)),
            ]:
                btn = QPushButton(icon)
                btn.setFixedSize(28, 28)
                btn.setToolTip(tip)
                btn.setStyleSheet(
                    f"background: transparent; border: none; font-size: 14px; color: {TEXT_SEC};"
                )
                btn.clicked.connect(fn)
                rl.addWidget(btn)
            self._pl_list.setItemWidget(item, row)

    def _new_playlist(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, 'Nouvelle playlist', 'Nom :')
        if ok and name.strip():
            if self._playlist_store.create(name.strip()):
                self._refresh_pl_list()
            else:
                self._lbl_status.setText(f'Playlist "{name}" existe déjà')

    def _on_pl_dclick(self, item: QListWidgetItem):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self._pl_current = name
            self._pl_play()

    def _pl_open(self, name: str):
        self._pl_current = name
        self._pl_detail_name.setText(name)
        self._pl_tracks_list.clear()
        for i, t in enumerate(self._playlist_store.get_tracks(name)):
            lbl = f"  {i+1:02d}.  {t.get('artist', '')}  —  {t.get('title', '')}"
            item = QListWidgetItem(lbl)
            item.setData(Qt.ItemDataRole.UserRole, i)
            # Bouton supprimer via context menu
            self._pl_tracks_list.addItem(item)
        self._pl_list.setVisible(False)
        self._pl_detail.setVisible(True)
        self._pl_tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._pl_tracks_list.customContextMenuRequested.connect(self._pl_track_menu)

    def _pl_rename_from_list(self, name: str):
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, 'Renommer', 'Nouveau nom :', text=name)
        if ok and new_name.strip():
            self._playlist_store.rename(name, new_name.strip())
            self._refresh_pl_list()

    def _pl_delete(self, name: str):
        from PyQt6.QtWidgets import QMessageBox
        r = QMessageBox.question(self, 'Supprimer', f'Supprimer la playlist "{name}" ?')
        if r == QMessageBox.StandardButton.Yes:
            self._playlist_store.delete(name)
            self._refresh_pl_list()

    def _pl_back(self):
        self._pl_detail.setVisible(False)
        self._pl_list.setVisible(True)
        self._refresh_pl_list()

    def _pl_rename(self):
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, 'Renommer', 'Nouveau nom :', text=self._pl_current
        )
        if ok and new_name.strip():
            if self._playlist_store.rename(self._pl_current, new_name.strip()):
                self._pl_current = new_name.strip()
                self._pl_detail_name.setText(new_name.strip())

    def _pl_play(self):
        tracks = self._playlist_store.get_tracks(self._pl_current)
        if tracks:
            self._player.stop()
            self._playing = False
            self._playlist.load(tracks)
            self._list.clear()
            for i, t in enumerate(tracks):
                self._list.addItem(QListWidgetItem(
                    f"  {i+1:02d}.  {t.get('artist', '')}  —  {t.get('title', '')}"
                ))
            self._lbl_status.setText(f'Playlist : {self._pl_current}')
            self._btn_add_to_pl.setVisible(True)
            self._switch_view(0)
            self._start_track(0)

    def _pl_track_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        item = self._pl_tracks_list.itemAt(pos)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        act_del = menu.addAction('🗑 Retirer de la playlist')
        act = menu.exec(self._pl_tracks_list.mapToGlobal(pos))
        if act == act_del:
            self._playlist_store.remove_track(self._pl_current, idx)
            self._pl_open(self._pl_current)  # refresh

    def _save_as_playlist(self):
        """Sauvegarde la queue courante comme playlist perso."""
        tracks = self._playlist.tracks
        if not tracks:
            self._lbl_status.setText('Aucun titre à sauvegarder')
            return
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, 'Sauvegarder la playlist', 'Nom :')
        if ok and name.strip():
            name = name.strip()
            self._playlist_store.create(name)
            added = 0
            for t in tracks:
                if self._playlist_store.add_track(name, t):
                    added += 1
            self._lbl_status.setText(f'✅ "{name}" — {added} titre(s) sauvegardé(s)')
            self._refresh_pl_list()

    def _on_add_to_playlist(self):
        """Ajouter/retirer le titre courant (ou cible) d'une playlist."""
        track = getattr(self, '_ctx_track', None) or self._playlist.current_track()
        if not track:
            return
        # Enrichir avec l'URL YouTube actuellement jouée
        cur_url = self._current_playing_url
        if cur_url:
            track = dict(track)
            track['youtube_url'] = cur_url
        from PyQt6.QtWidgets import QMenu
        names = self._playlist_store.names()
        if not names:
            self._new_playlist()
            return
        already = self._playlist_store.playlists_containing(track)
        menu = QMenu(self)
        from PyQt6.QtGui import QPixmap, QIcon, QColor
        def _dot(color):
            px = QPixmap(12, 12)
            px.fill(QColor(color))
            return QIcon(px)
        icon_add = _dot("#1DB954")
        icon_rem = _dot("#e05252")
        for name in names:
            if name in already:
                act = menu.addAction(icon_rem, f' {name}')
                act.setData(f'REMOVE:{name}')
            else:
                act = menu.addAction(icon_add, f' {name}')
                act.setData(f'ADD:{name}')
        menu.addSeparator()
        act_new = menu.addAction('+ Nouvelle playlist…')
        chosen = menu.exec(self._btn_add_to_pl.mapToGlobal(
            self._btn_add_to_pl.rect().bottomLeft()
        ))
        if not chosen:
            return
        if chosen == act_new:
            from PyQt6.QtWidgets import QInputDialog
            pl_name, ok = QInputDialog.getText(self, 'Nouvelle playlist', 'Nom :')
            if ok and pl_name.strip():
                self._playlist_store.create(pl_name.strip())
                if self._playlist_store.add_track(pl_name.strip(), track):
                    self._lbl_status.setText(f'✅ Ajouté à "{pl_name.strip()}"')
                self._refresh_pl_list()
        elif chosen.data() and chosen.data().startswith('ADD:'):
            pl_name = chosen.data()[4:]
            if self._playlist_store.add_track(pl_name, track):
                self._lbl_status.setText(f'✅ Ajouté à "{pl_name}"')
        elif chosen.data() and chosen.data().startswith('REMOVE:'):
            pl_name = chosen.data()[7:]
            tracks_in = self._playlist_store.get_tracks(pl_name)
            key = self._playlist_store._track_key(track)
            idx = next((i for i, t in enumerate(tracks_in)
                        if self._playlist_store._track_key(t) == key), None)
            if idx is not None:
                self._playlist_store.remove_track(pl_name, idx)
                self._lbl_status.setText(f'✅ Retiré de "{pl_name}"')

    def _on_queue_track_menu(self, pos):
        """Clic droit sur un titre de la queue → gérer les playlists."""
        item = self._list.itemAt(pos)
        if not item:
            return
        idx = self._list.row(item)
        tracks = self._playlist.tracks
        if idx < len(tracks):
            track = tracks[idx]
            # Stocker temporairement le track cible
            self._ctx_track = track
            self._on_add_to_playlist()
            self._ctx_track = None

    def _on_pl_list_menu(self, pos):
        """Clic droit sur une playlist → renommer / supprimer."""
        item = self._pl_list.itemAt(pos)
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        if not name:
            return
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        act_rename = menu.addAction('✏️  Renommer')
        act_delete = menu.addAction('🗑  Supprimer')
        chosen = menu.exec(self._pl_list.mapToGlobal(pos))
        if chosen == act_rename:
            self._pl_rename_from_list(name)
        elif chosen == act_delete:
            self._pl_delete(name)

    def _on_volume(self, value: int):
        self._player.set_volume(value)

    def closeEvent(self, event):
        self._player.stop()
        event.accept()
