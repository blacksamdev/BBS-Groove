#!/usr/bin/env python3
"""Applique le patch versions sur main_window.py."""
import sys

path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Import PrefStore
if 'from bbs_groove.core.pref_store import PrefStore' not in content:
    content = content.replace(
        'from bbs_groove.core.sources.spotify import SpotifySource',
        'from bbs_groove.core.sources.spotify import SpotifySource\nfrom bbs_groove.core.pref_store import PrefStore'
    )

# 2. Signal candidates_ready
content = content.replace(
    '    track_enriched   = pyqtSignal(dict)',
    '    track_enriched   = pyqtSignal(dict)\n    candidates_ready = pyqtSignal(list, str)'
)

# 3. Init state vars (after self._playing = False)
content = content.replace(
    '        self._playing             = False\n        self._waiting_for_resolution = False\n        self._play_lock              = __import__("threading").Lock()\n        self._seeking                = False',
    '        self._playing             = False\n        self._waiting_for_resolution = False\n        self._play_lock              = __import__("threading").Lock()\n        self._seeking                = False\n        self._pref_store             = PrefStore()\n        self._versions_expanded      = self._pref_store.get_ui_state("versions_expanded", True)\n        self._candidates: list       = []\n        self._current_spotify_id     = ""\n        self._current_playing_url    = ""'
)

# 4. Connect signal
content = content.replace(
    '        self._signals.track_enriched.connect(self._update_track_display)',
    '        self._signals.track_enriched.connect(self._update_track_display)\n        self._signals.candidates_ready.connect(self._update_versions_list)'
)

# 5. Replace _right_panel with new layout
old_right = '''    def _right_panel(self) -> QWidget:
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
        return w'''

new_right = '''    def _right_panel(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f'background: {BG_PANEL}; border-radius: 6px;')
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(8)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Ligne haute : artwork + versions
        top = QHBoxLayout()
        top.setSpacing(12)
        top.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        top.addWidget(vp)
        v.addLayout(top)

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

if old_right in content:
    content = content.replace(old_right, new_right)
    print('right_panel: OK')
else:
    print('right_panel: NOT FOUND')

# 6. Ajouter les méthodes versions + modifier _play_current pour fetch candidates
# Insérer avant _on_volume
old_volume = '    def _on_volume(self, value: int):'
new_versions_methods = '''    def _toggle_versions(self):
        self._versions_expanded = not self._versions_expanded
        self._versions_list.setVisible(self._versions_expanded)
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
            item = QListWidgetItem(f"{check}{channel}  {dur_str}")
            item.setData(Qt.ItemDataRole.UserRole, c['url'])
            if c['url'] == current_url:
                item.setForeground(QColor(ACCENT))
            self._versions_list.addItem(item)

    def _on_version_clicked(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        if not url or url == self._current_playing_url:
            return
        # Sauvegarder la préférence
        if self._current_spotify_id:
            self._pref_store.save(self._current_spotify_id, url)
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
                self._signals.candidates_ready.emit(candidates, current_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')

    def _on_volume(self, value: int):'''

if old_volume in content:
    content = content.replace(old_volume, new_versions_methods)
    print('versions_methods: OK')
else:
    print('versions_methods: NOT FOUND')

# 7. Dans _play_current, après play() : stocker spotify_id + url + lancer fetch candidates
old_play = '''        self._player.on_track_ended = self._signals.track_ended.emit
        self._player.play(url)
        self._playing = True
        # Enrichir les métadonnées en arrière-plan si nécessaire
        track = self._playlist.current_track()
        if track and track.get('needs_enrich'):
            import threading as _t
            _t.Thread(target=self._enrich_track, args=(self._playlist.current_index,), daemon=True).start()'''

new_play = '''        self._player.on_track_ended = self._signals.track_ended.emit
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
            ).start()'''

if old_play in content:
    content = content.replace(old_play, new_play)
    print('play_current: OK')
else:
    print('play_current: NOT FOUND')

with open(path, 'w') as f:
    f.write(content)
print('Done')
