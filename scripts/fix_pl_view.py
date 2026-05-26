import py_compile
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Icône note sur bouton Lecture
content = content.replace("'🏠', 'Lecture'", "'🎵', 'Lecture'")
print('1 icone note:', "'🎵', 'Lecture'" in content)

# 2. Remplacer placeholder playlists par la vraie vue
old = """        # Vue 1 : Mes Playlists (v2.1)
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel('📋  Mes Playlists\\n\\nFonctionnalité à venir')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 13px; background: transparent;')
        pv.addWidget(lbl)
        self._center_stack.addWidget(playlists_w)
        return self._center_stack"""

new = """        # Vue 1 : Mes Playlists
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(0)
        # Header
        ph = QWidget()
        ph.setFixedHeight(36)
        ph.setStyleSheet('background: transparent; border-bottom: 1px solid #222;')
        phl = QHBoxLayout(ph)
        phl.setContentsMargins(12, 0, 8, 0)
        ph_lbl = QLabel('Mes Playlists')
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
        # Liste des playlists
        self._pl_list = QListWidget()
        self._pl_list.setStyleSheet(LIST_STYLE)
        self._pl_list.itemDoubleClicked.connect(self._on_pl_dclick)
        pv.addWidget(self._pl_list)
        # Vue détail
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
        btn_rename.setStyleSheet(f'background: transparent; color: {TEXT_SEC}; border: none; font-size: 13px;')
        btn_rename.clicked.connect(self._pl_rename)
        pdhl.addWidget(btn_rename)
        btn_play_pl = QPushButton('▶')
        btn_play_pl.setToolTip('Jouer la playlist')
        btn_play_pl.setFixedWidth(30)
        btn_play_pl.setStyleSheet(f'background: transparent; color: {ACCENT}; border: none; font-size: 13px;')
        btn_play_pl.clicked.connect(self._pl_play)
        pdhl.addWidget(btn_play_pl)
        pdv.addWidget(pdh)
        self._pl_tracks_list = QListWidget()
        self._pl_tracks_list.setStyleSheet(LIST_STYLE)
        pdv.addWidget(self._pl_tracks_list)
        pv.addWidget(self._pl_detail)
        self._center_stack.addWidget(playlists_w)
        self._pl_current = ''
        return self._center_stack"""

print('2 playlist view:', old in content)
content = content.replace(old, new)

# 3. _switch_view refresh la liste quand on va sur playlists
old_switch = """    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)"""
new_switch = """    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)
        if index == 1:
            self._refresh_pl_list()"""
print('3 switch_view:', old_switch in content)
content = content.replace(old_switch, new_switch)

with open(path, 'w') as f:
    f.write(content)
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK ✅')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
