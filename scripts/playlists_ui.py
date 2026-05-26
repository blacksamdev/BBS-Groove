#!/usr/bin/env python3
"""Patch UI — playlists perso : vue, sauvegarde, ajout titre."""
import re, py_compile
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Import PlaylistStore
if 'PlaylistStore' not in content:
    content = content.replace(
        'from bbs_groove.core.pref_store import PrefStore',
        'from bbs_groove.core.pref_store import PrefStore\nfrom bbs_groove.core.playlist_store import PlaylistStore'
    )
    print('1 import OK')

# 2. Init PlaylistStore dans __init__
content = content.replace(
    '        self._pref_store         = PrefStore()',
    '        self._pref_store         = PrefStore()\n        self._playlist_store     = PlaylistStore()'
)
print('2 init OK')

# 3. Bouton Sauvegarder dans _topbar après btn_load
old_topbar_end = '''        btn_load = QPushButton('Charger')
        btn_load.setStyleSheet(BTN_STYLE)
        btn_load.clicked.connect(self._load_url)
        h.addWidget(btn_load)
        return w'''
new_topbar_end = '''        btn_load = QPushButton('Charger')
        btn_load.setStyleSheet(BTN_STYLE)
        btn_load.clicked.connect(self._load_url)
        h.addWidget(btn_load)

        btn_save = QPushButton('💾')
        btn_save.setToolTip('Sauvegarder comme playlist perso')
        btn_save.setFixedWidth(36)
        btn_save.setStyleSheet(BTN_STYLE)
        btn_save.clicked.connect(self._save_as_playlist)
        h.addWidget(btn_save)
        return w'''
print('3 topbar save btn:', old_topbar_end in content)
content = content.replace(old_topbar_end, new_topbar_end)

# 4. Bouton + sur le titre en cours dans _right_panel (après lbl_status)
old_status = '''        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet(
            f'color: {ACCENT}; font-size: 11px; background: transparent;'
        )
        vpl.addWidget(self._lbl_status)'''
new_status = '''        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet(
            f'color: {ACCENT}; font-size: 11px; background: transparent;'
        )
        vpl.addWidget(self._lbl_status)

        # Bouton ajouter à une playlist perso
        self._btn_add_to_pl = QPushButton('➕ Ajouter à une playlist')
        self._btn_add_to_pl.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ITEM}; color: {TEXT_SEC};
                border: 1px solid #333; border-radius: 4px;
                font-size: 11px; padding: 4px 8px;
            }}
            QPushButton:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
        """)
        self._btn_add_to_pl.setVisible(False)
        self._btn_add_to_pl.clicked.connect(self._on_add_to_playlist)
        vpl.addWidget(self._btn_add_to_pl)'''
print('4 add btn:', old_status in content)
content = content.replace(old_status, new_status)

# 5. Vue Playlists dans _center_panel
old_placeholder = '''        # Vue 1 : Mes Playlists (placeholder v2.1)
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel('📋  Mes Playlists\\n\\nFonctionnalité à venir')
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 13px; background: transparent;')
        pv.addWidget(lbl)
        self._center_stack.addWidget(playlists_w)'''
new_playlist_view = '''        # Vue 1 : Mes Playlists
        playlists_w = QFrame()
        playlists_w.setStyleSheet(f'background: {BG_PANEL};')
        pv = QVBoxLayout(playlists_w)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(0)

        # Header playlists
        ph = QWidget()
        ph.setFixedHeight(36)
        ph.setStyleSheet(f'background: transparent; border-bottom: 1px solid #222;')
        phl = QHBoxLayout(ph)
        phl.setContentsMargins(12, 0, 8, 0)
        ph_lbl = QLabel('Mes Playlists')
        ph_lbl.setStyleSheet(f'color: {TEXT_SEC}; font-size: 12px; font-weight: bold; background: transparent;')
        phl.addWidget(ph_lbl)
        phl.addStretch()
        btn_new = QPushButton('+ Nouvelle')
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #000;
                border: none; border-radius: 4px;
                font-size: 11px; padding: 3px 10px; font-weight: bold;
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

        # Vue détail d'une playlist (sous-stack)
        self._pl_detail = QFrame()
        self._pl_detail.setStyleSheet(f'background: {BG_PANEL};')
        self._pl_detail.setVisible(False)
        pdv = QVBoxLayout(self._pl_detail)
        pdv.setContentsMargins(0, 0, 0, 0)
        pdv.setSpacing(0)

        # Header détail
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

        # Titres de la playlist
        self._pl_tracks_list = QListWidget()
        self._pl_tracks_list.setStyleSheet(LIST_STYLE)
        pdv.addWidget(self._pl_tracks_list)
        pv.addWidget(self._pl_detail)

        self._center_stack.addWidget(playlists_w)
        self._pl_current = ''  # nom de la playlist ouverte'''
print('5 playlist view:', old_placeholder in content)
content = content.replace(old_placeholder, new_playlist_view)

# 6. Ajouter les méthodes playlists avant _on_volume
old_vol = '    def _on_volume(self, value: int):'
new_methods = '''    # ------------------------------------------------------------------ #
    #  Playlists perso                                                    #
    # ------------------------------------------------------------------ #

    def _refresh_pl_list(self):
        """Rafraîchit la liste des playlists perso."""
        self._pl_list.clear()
        for name in self._playlist_store.names():
            tracks = self._playlist_store.get_tracks(name)
            item = QListWidgetItem(f'  📋  {name}   ({len(tracks)} titre(s))')
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._pl_list.addItem(item)

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
            self._pl_open(name)

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
            self._pl_open(self._pl_current)

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
        """Ajouter le titre courant à une playlist perso."""
        track = self._playlist.current_track()
        if not track:
            return
        from PyQt6.QtWidgets import QMenu
        names = self._playlist_store.names()
        if not names:
            self._new_playlist()
            return
        already = self._playlist_store.playlists_containing(track)
        menu = QMenu(self)
        for name in names:
            act = menu.addAction(f'{"✓ " if name in already else "    "}{name}')
            act.setEnabled(name not in already)
            act.setData(name)
        menu.addSeparator()
        act_new = menu.addAction('+ Nouvelle playlist…')
        chosen = menu.exec(self._btn_add_to_pl.mapToGlobal(
            self._btn_add_to_pl.rect().bottomLeft()
        ))
        if chosen == act_new:
            self._new_playlist()
        elif chosen and chosen.data():
            if self._playlist_store.add_track(chosen.data(), track):
                self._lbl_status.setText(f'✅ Ajouté à "{chosen.data()}"')

    def _on_volume(self, value: int):'''
print('6 methods:', old_vol in content)
content = content.replace(old_vol, new_methods)

# 7. Rendre btn_add_to_pl visible quand un titre joue
old_play_cur = "        self._lbl_status.setText('Chargement…')\n        self._play_current()"
new_play_cur = "        self._lbl_status.setText('Chargement…')\n        self._btn_add_to_pl.setVisible(True)\n        self._play_current()"
content = content.replace(old_play_cur, new_play_cur)

with open(path, 'w') as f:
    f.write(content)
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK ✅')
except py_compile.PyCompileError as e:
    print(f'ERROR: {e}')
