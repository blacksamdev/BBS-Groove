#!/usr/bin/env python3
import re, py_compile
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Remplacer _header par _topbar
content = re.sub(
    r'    def _header\(self\).*?return w\n',
    '', content, flags=re.DOTALL
)
# Remplacer _url_bar
content = re.sub(
    r'    def _url_bar\(self\).*?return w\n',
    '', content, flags=re.DOTALL
)
# Remplacer _left_panel
content = re.sub(
    r'    def _left_panel\(self\).*?return w\n',
    '', content, flags=re.DOTALL
)
print('Removed old methods OK')

# Insérer les nouvelles méthodes avant _right_panel
new_methods = '''    def _topbar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f'background: {BG_PANEL}; border-bottom: 1px solid #222;')
        w.setFixedHeight(52)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(10)
        logo = QLabel('BBS gr<span style="color:#1DB954">OO</span>ve')
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(f'font-size: 16px; font-weight: bold; color: {TEXT_PRI}; background: transparent;')
        logo.setFixedWidth(130)
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
        return w

    def _sidebar(self) -> QWidget:
        w = QFrame()
        w.setFixedWidth(65)
        w.setStyleSheet(f'background: {BG_PANEL}; border-right: 1px solid #222;')
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 12, 0, 12)
        v.setSpacing(4)

        def _nb(icon, label, checkable=False):
            b = QPushButton(f'{icon}\\n{label}')
            b.setCheckable(checkable)
            b.setFixedSize(65, 56)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {TEXT_SEC};
                    border: none; font-size: 9px; padding: 4px 2px;
                }}
                QPushButton:hover {{ background: {BG_ITEM}; color: {TEXT_PRI}; }}
                QPushButton:checked {{
                    background: {BG_ITEM}; color: {ACCENT};
                    border-left: 3px solid {ACCENT};
                }}
            """)
            return b

        self._nav_queue = _nb('🏠', 'Queue', checkable=True)
        self._nav_queue.setChecked(True)
        self._nav_queue.clicked.connect(lambda: self._switch_view(0))
        v.addWidget(self._nav_queue)

        self._nav_playlists = _nb('📋', 'Playlists', checkable=True)
        self._nav_playlists.clicked.connect(lambda: self._switch_view(1))
        v.addWidget(self._nav_playlists)

        v.addStretch()

        self._btn_gaming = _nb('🎮', 'Gaming')
        self._btn_gaming.clicked.connect(self._switch_gaming)
        v.addWidget(self._btn_gaming)
        return w

    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)

    def _center_panel(self) -> QWidget:
        from PyQt6.QtWidgets import QStackedWidget
        self._center_stack = QStackedWidget()

        # Vue 0 : Queue
        queue_w = QFrame()
        queue_w.setStyleSheet(f'background: {BG_PANEL};')
        qv = QVBoxLayout(queue_w)
        qv.setContentsMargins(0, 0, 0, 0)
        qv.setSpacing(0)
        hdr = QLabel('  Queue')
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
        qv.addWidget(self._list)
        self._center_stack.addWidget(queue_w)

        # Vue 1 : Mes Playlists (v2.1)
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel('📋  Mes Playlists\\n\\nFonctionnalité à venir')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 13px; background: transparent;')
        pv.addWidget(lbl)
        self._center_stack.addWidget(playlists_w)
        return self._center_stack

    def _right_panel'''

content = content.replace('    def _right_panel', new_methods)
print('New methods inserted:', '_topbar' in content and '_sidebar' in content)

with open(path, 'w') as f:
    f.write(content)
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK ✅')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
