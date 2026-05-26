#!/usr/bin/env python3
"""Refacto UI v2 — sidebar + topbar + centre stacké."""
import py_compile, re
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# ── 1. Remplacer _build_ui ────────────────────────────────────────────
old_build = '''    def _build_ui(self):
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
        layout.addWidget(self._player_bar())'''

new_build = '''    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f'background: {BG_MAIN};')
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Topbar (logo + URL + Charger)
        layout.addWidget(self._topbar())

        # Corps principal
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        body.addWidget(self._center_panel(), 1)
        body.addWidget(self._right_panel(), 2)
        layout.addLayout(body, 1)

        layout.addWidget(self._player_bar())'''

print('1 _build_ui:', old_build in content)
content = content.replace(old_build, new_build)

# ── 2. Remplacer _header + _url_bar par _topbar ───────────────────────
old_header = '''    def _header(self) -> QWidget:
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
        return w'''

new_topbar = '''    def _topbar(self) -> QWidget:
        """Barre supérieure : logo + URL + Charger."""
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-bottom: 1px solid #222;')
        w.setFixedHeight(52)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(10)

        logo = QLabel('BBS gr<span style="color:#1DB954">OO</span>ve')
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(
            f'font-size: 16px; font-weight: bold; color: {TEXT_PRI}; background: transparent;'
        )
        logo.setFixedWidth(130)
        h.addWidget(logo)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText(
            'URL Spotify / Deezer (track, album, playlist, artiste)…'
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
        return w'''

print('2 header+urlbar:', old_header in content)
content = content.replace(old_header, new_topbar)

# ── 3. Remplacer _left_panel par _sidebar + _center_panel ────────────
old_left = '''    def _left_panel(self) -> QWidget:
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
        return w'''

new_panels = '''    def _sidebar(self) -> QWidget:
        """Sidebar gauche : navigation icônes."""
        w = QFrame()
        w.setFixedWidth(65)
        w.setStyleSheet(f'background: {BG_PANEL}; border-right: 1px solid #222;')
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 12, 0, 12)
        v.setSpacing(4)

        def nav_btn(icon: str, label: str, slot=None, checkable=False) -> QPushButton:
            b = QPushButton(f'{icon}\\n{label}')
            b.setCheckable(checkable)
            b.setFixedSize(65, 56)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {TEXT_SEC};
                    border: none; font-size: 9px; padding: 4px 2px;
                    border-radius: 0px;
                }}
                QPushButton:hover {{ background: {BG_ITEM}; color: {TEXT_PRI}; }}
                QPushButton:checked {{ background: {BG_ITEM}; color: {ACCENT};
                    border-left: 3px solid {ACCENT}; }}
            """)
            if slot:
                b.clicked.connect(slot)
            return b

        self._nav_queue = nav_btn('🏠', 'Queue', checkable=True)
        self._nav_queue.setChecked(True)
        self._nav_queue.clicked.connect(lambda: self._switch_view(0))
        v.addWidget(self._nav_queue)

        self._nav_playlists = nav_btn('📋', 'Playlists', checkable=True)
        self._nav_playlists.clicked.connect(lambda: self._switch_view(1))
        v.addWidget(self._nav_playlists)

        v.addStretch()

        self._btn_gaming = nav_btn('🎮', 'Gaming')
        self._btn_gaming.setStyleSheet(self._btn_gaming.styleSheet().replace(
            f'color: {TEXT_SEC}', f'color: #aaaa00'
        ))
        self._btn_gaming.clicked.connect(self._switch_gaming)
        v.addWidget(self._btn_gaming)
        return w

    def _switch_view(self, index: int):
        """Basculer entre Queue (0) et Playlists (1)."""
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)

    def _center_panel(self) -> QWidget:
        """Zone centrale avec QStackedWidget — Queue / Playlists."""
        from PyQt6.QtWidgets import QStackedWidget
        self._center_stack = QStackedWidget()

        # Vue 0 : Queue (playlist actuelle)
        queue_w = QFrame()
        queue_w.setStyleSheet(f'background: {BG_PANEL};')
        qv = QVBoxLayout(queue_w)
        qv.setContentsMargins(0, 0, 0, 0)
        qv.setSpacing(0)
        hdr = QLabel('  Queue')
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(
            f'color: {TEXT_SEC}; font-size: 12px; font-weight: bold; background: transparent;'
            f' padding-left: 12px; border-bottom: 1px solid #222;'
        )
        qv.addWidget(hdr)
        self._list = QListWidget()
        self._list.setStyleSheet(LIST_STYLE)
        self._list.itemDoubleClicked.connect(self._on_list_dclick)
        qv.addWidget(self._list)
        self._center_stack.addWidget(queue_w)

        # Vue 1 : Mes Playlists (placeholder v2.1)
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel('📋  Mes Playlists\n\nFonctionnalité à venir — v2.1')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 13px; background: transparent;')
        pv.addWidget(lbl)
        self._center_stack.addWidget(playlists_w)

        return self._center_stack'''

print('3 left_panel:', old_left in content)
content = content.replace(old_left, new_panels)

# ── 4. Vérification syntaxe ───────────────────────────────────────────
with open(path, 'w') as f:
    f.write(content)
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK ✅')
except py_compile.PyCompileError as e:
    print(f'Syntax ERROR: {e}')
