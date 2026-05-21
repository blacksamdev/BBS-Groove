import threading
from typing import Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from bbs_groove.core.player import MPVPlayer
from bbs_groove.core.playlist import Playlist


class _Signals(QObject):
    track_changed = pyqtSignal()


class GrooveTray(QWidget):
    """Mode gaming — mini-player flottant toujours visible.
    Fonctionne dans le sandbox Flatpak contrairement à QSystemTrayIcon."""

    def __init__(
        self,
        player:    MPVPlayer  | None = None,
        playlist:  Playlist   | None = None,
        state:     dict       | None = None,
        on_return: Callable   | None = None,
    ):
        super().__init__()
        self._player    = player   or MPVPlayer()
        self._playlist  = playlist or Playlist()
        self._on_return = on_return
        self._signals   = _Signals()

        self._build_ui()
        self._refresh()

        # Timer pour rafraîchir le titre en cours
        self._timer = QTimer()
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.setWindowTitle('BBS grOOve')
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet('''
            QWidget { background: #0d0d0d; color: #ffffff; border-radius: 8px; }
            QPushButton {
                background: #1a1a1a; color: #ffffff; border: 1px solid #333;
                border-radius: 4px; padding: 4px 10px; font-size: 14px;
            }
            QPushButton:hover { background: #2a2a2a; border-color: #1DB954; }
        ''')
        self.setFixedSize(320, 90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Titre
        self._lbl = QLabel('♫  —')
        self._lbl.setStyleSheet('color: #1DB954; font-size: 12px; background: transparent;')
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl)

        # Contrôles
        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        self._btn_prev  = self._btn('⏮', self._prev)
        self._btn_play  = self._btn('⏸', self._toggle)
        self._btn_next  = self._btn('⏭', self._next)
        sep             = QLabel('|')
        sep.setStyleSheet('color: #333; background: transparent;')
        self._btn_back  = self._btn('🖥', self._return, color='#cccc00')

        for w in (self._btn_prev, self._btn_play, self._btn_next, sep, self._btn_back):
            ctrl.addWidget(w)
        layout.addLayout(ctrl)

        # Drag pour déplacer la fenêtre
        self._drag_pos = None
        self._drag_win = None

    def _btn(self, label: str, slot, color: str = '#ffffff') -> QPushButton:
        b = QPushButton(label)
        b.setFixedSize(36, 28)
        b.setStyleSheet(f'font-size: 14px; color: {color}; background: #1a1a1a; border: 1px solid #333; border-radius: 4px;')
        b.clicked.connect(slot)
        return b

    # ------------------------------------------------------------------ #
    #  Drag                                                                #
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            if handle:
                handle.startSystemMove()
        self._drag_win = None

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def _refresh(self):
        track = self._playlist.current_track()
        if track:
            title = track.get('title', '')
            artist = track.get('artist', '')
            text = f"♫  {artist} — {title}"
            if len(text) > 40:
                text = text[:38] + '…'
            self._lbl.setText(text)
        paused = self._player.get_paused()
        self._btn_play.setText('▶' if paused else '⏸')

    def _toggle(self):
        self._player.toggle_pause()
        self._refresh()

    def _next(self):
        track = self._playlist.go_next()
        if track:
            url = self._playlist.current_url()
            if url:
                self._player.on_track_ended = lambda: threading.Thread(target=self._next, daemon=True).start()
                self._player.play(url)
            self._refresh()

    def _prev(self):
        track = self._playlist.go_prev()
        if track:
            url = self._playlist.current_url()
            if url:
                self._player.play(url)
            self._refresh()

    def _return(self):
        self._timer.stop()
        self.hide()
        if self._on_return:
            self._on_return()

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def show(self):
        # Positionner en bas à droite de l'écran
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                  screen.height() - self.height() - 60)
        super().show()

    def hide(self):
        self._timer.stop()
        super().hide()
