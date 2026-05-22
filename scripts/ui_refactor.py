#!/usr/bin/env python3
"""Refacto _right_panel : titre/artiste/année dans le panel versions + zone lyrics."""
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

old = '''    def _right_panel(self) -> QWidget:
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
        return w'''

new = '''    def _right_panel(self) -> QWidget:
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
        self._artwork.setFixedSize(220, 220)
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

        # Titre
        self._lbl_title = QLabel('—')
        self._lbl_title.setStyleSheet(
            f'color: {TEXT_PRI}; font-size: 15px; font-weight: bold; background: transparent;'
        )
        self._lbl_title.setWordWrap(True)
        vpl.addWidget(self._lbl_title)

        # Artistes
        self._lbl_artist = QLabel('')
        self._lbl_artist.setStyleSheet(
            f'color: {ACCENT}; font-size: 13px; background: transparent;'
        )
        self._lbl_artist.setWordWrap(True)
        vpl.addWidget(self._lbl_artist)

        # Album · Année
        self._lbl_album = QLabel('')
        self._lbl_album.setStyleSheet(
            f'color: {TEXT_SEC}; font-size: 12px; background: transparent;'
        )
        self._lbl_album.setWordWrap(True)
        vpl.addWidget(self._lbl_album)

        # Durée · Explicit
        self._lbl_meta = QLabel('')
        self._lbl_meta.setStyleSheet('color: #666; font-size: 11px; background: transparent;')
        vpl.addWidget(self._lbl_meta)

        # Status
        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet(
            f'color: {ACCENT}; font-size: 11px; background: transparent;'
        )
        vpl.addWidget(self._lbl_status)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #333; background: #333;')
        sep.setFixedHeight(1)
        vpl.addWidget(sep)

        # Header versions avec bouton collapse
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

        # Liste des versions
        self._versions_list = QListWidget()
        self._versions_list.setMaximumHeight(140)
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
        top.addWidget(vp)
        v.addLayout(top)

        # ── Zone lyrics ─────────────────────────────────────────────────
        from PyQt6.QtWidgets import QTextEdit
        self._lyrics_widget = QTextEdit()
        self._lyrics_widget.setReadOnly(True)
        self._lyrics_widget.setMaximumHeight(180)
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
        self._lyrics_widget.setVisible(False)
        v.addWidget(self._lyrics_widget)

        v.addStretch()
        return w'''

print('Found:', old in content)
content = content.replace(old, new)
with open(path, 'w') as f:
    f.write(content)
print('Done')
