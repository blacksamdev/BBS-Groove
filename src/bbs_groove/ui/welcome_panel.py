"""Écran d'accueil BBS grOOve."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

BG      = '#1a1a1a'
BG2     = '#252525'
ACCENT  = '#1DB954'
TXT     = '#ffffff'
SEC     = '#aaaaaa'
BORDER  = '#333333'

CARD_STYLE = f"""
    QPushButton {{
        background: {BG2}; color: {TXT};
        border: 1px solid {BORDER}; border-radius: 8px;
        font-size: 13px; padding: 14px 20px;
        text-align: left;
    }}
    QPushButton:hover {{
        background: #2a2a2a; border-color: {ACCENT}; color: {ACCENT};
    }}
"""

ACCENT_CARD = f"""
    QPushButton {{
        background: {BG2}; color: {TXT};
        border: 1px solid {ACCENT}; border-radius: 8px;
        font-size: 12px; padding: 12px 20px;
        text-align: left;
    }}
    QPushButton:hover {{ background: #1a2e1a; color: {ACCENT}; }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        background: {BG2}; color: {TXT};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 10px 14px; font-size: 14px;
    }}
    QLineEdit:focus {{ border-color: {ACCENT}; }}
"""

FEATURE_STYLE = f"color: {SEC}; font-size: 11px; background: transparent;"


def _sep():
    s = QFrame()
    s.setFrameShape(QFrame.Shape.HLine)
    s.setStyleSheet(f'color: {BORDER}; background: {BORDER};')
    s.setFixedHeight(1)
    return s


class WelcomePanel(QWidget):
    sig_load    = pyqtSignal(str)   # charger/rechercher une URL ou query
    sig_import  = pyqtSignal(str)   # importer dans playlists perso
    sig_playlists = pyqtSignal()    # aller à mes playlists
    sig_options   = pyqtSignal()    # ouvrir options

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background: {BG};')
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet('background: transparent; border: none;')
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setStyleSheet(f'background: {BG};')
        v = QVBoxLayout(inner)
        v.setContentsMargins(40, 32, 40, 32)
        v.setSpacing(20)

        # Titre
        title = QLabel('🎵  Par quoi commençons-nous ?')
        title.setStyleSheet(f'color: {TXT}; font-size: 20px; font-weight: bold; background: transparent;')
        v.addWidget(title)

        # Champ recherche/URL
        self._input = QLineEdit()
        self._input.setPlaceholderText('Coller une URL Spotify / Deezer  ou  recherche (artiste, titre, album)…')
        self._input.setStyleSheet(INPUT_STYLE)
        self._input.returnPressed.connect(self._on_load)
        v.addWidget(self._input)

        # Boutons principaux — une seule ligne
        row_btns = QHBoxLayout()
        row_btns.setSpacing(8)
        for icon, label, slot in [
            ('🎵', 'Charger une playlist',           self._on_load),
            ('📥', 'Importer une playlist',          self._on_import),
            ('🔍', "Recherche d'un titre / artiste", self._on_load),
        ]:
            btn = QPushButton(f'  {icon}   {label}')
            btn.setStyleSheet(CARD_STYLE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            row_btns.addWidget(btn)
        v.addLayout(row_btns)

        v.addWidget(_sep())

        # Accès rapides
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        for icon, label, sub, slot in [
            ('📋', 'Mes playlists grOOve', '', self._on_playlists),
            ('⚙', 'Lecture automatique',
             'Continuez l\'écoute après la playlist', self._on_options),
        ]:
            btn = QPushButton(f'  {icon}   {label}\n       {sub}')
            btn.setStyleSheet(ACCENT_CARD)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            row2.addWidget(btn)
        v.addLayout(row2)

        v.addWidget(_sep())

        # Features
        feat_lbl = QLabel('Fonctionnalités')
        feat_lbl.setStyleSheet(f'color: {SEC}; font-size: 12px; font-weight: bold; background: transparent;')
        v.addWidget(feat_lbl)

        feats = QHBoxLayout()
        feats.setSpacing(12)
        for icon, name, desc in [
            ('✦', 'Versions',
             'Choisissez la version YouTube pour chaque titre'),
            ('🎮', 'Mode Gaming',
             'Mini-player flottant pour garder la main sur votre jeu'),
        ]:
            f = QFrame()
            f.setStyleSheet(f'background: {BG2}; border-radius: 8px; border: 1px solid {BORDER};')
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 12, 16, 12)
            fl.setSpacing(4)
            h = QHBoxLayout()
            ico = QLabel(icon)
            ico.setStyleSheet(f'color: {ACCENT}; font-size: 18px; background: transparent; border: none;')
            h.addWidget(ico)
            nm = QLabel(name)
            nm.setStyleSheet(f'color: {TXT}; font-size: 13px; font-weight: bold; background: transparent; border: none;')
            h.addWidget(nm)
            h.addStretch()
            fl.addLayout(h)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet(f'color: {SEC}; font-size: 11px; background: transparent; border: none;')
            fl.addWidget(d)
            feats.addWidget(f)
        v.addLayout(feats)

        v.addStretch()
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Slots ───────────────────────────────────────────────────────── #

    def _on_load(self):
        self.sig_load.emit(self._input.text().strip())

    def _on_import(self):
        self.sig_import.emit(self._input.text().strip())

    def _on_playlists(self):
        self.sig_playlists.emit()

    def _on_options(self):
        self.sig_options.emit()

    def focus_input(self):
        self._input.setFocus()
