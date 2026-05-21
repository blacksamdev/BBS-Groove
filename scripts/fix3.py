#!/usr/bin/env python3
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Fix 1 : artwork décalé — envelopper top dans un QWidget fixedHeight
old1 = """        # Ligne haute : artwork + versions
        top = QHBoxLayout()
        top.setSpacing(12)
        top.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Artwork
        self._artwork = QLabel()"""
new1 = """        # Ligne haute : artwork + versions — hauteur fixe 220px
        top_w = QWidget()
        top_w.setFixedHeight(220)
        top_w.setStyleSheet('background: transparent;')
        top_w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top = QHBoxLayout(top_w)
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)
        top.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Artwork
        self._artwork = QLabel()"""
print('1 top widget:', old1 in content)
content = content.replace(old1, new1)

# Remplacer v.addLayout(top) par v.addWidget(top_w)
old1b = "        v.addLayout(top)"
new1b = "        v.addWidget(top_w)"
print('1b addWidget:', old1b in content)
content = content.replace(old1b, new1b)

# Fix 2 : version jouée — fond vert sombre + texte accentué
old2 = """            if c['url'] == current_url:
                item.setForeground(QColor(ACCENT))"""
new2 = """            if c['url'] == current_url:
                item.setForeground(QColor(ACCENT))
                item.setBackground(QColor('#0d2a0d'))"""
print('2 highlight:', old2 in content)
content = content.replace(old2, new2)

# Fix 3 : stocker candidates pour re-affichage après gaming mode
# Dans _fetch_candidates, sauvegarder dans self._candidates
old3 = """        try:
            from bbs_groove.core.resolver import Resolver
            candidates = Resolver().resolve_candidates(track)
            if candidates and index == self._playlist.current_index:
                self._signals.candidates_ready.emit(candidates, current_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')"""
new3 = """        try:
            from bbs_groove.core.resolver import Resolver
            candidates = Resolver().resolve_candidates(track)
            if candidates and index == self._playlist.current_index:
                self._candidates = candidates
                self._signals.candidates_ready.emit(candidates, current_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')"""
print('3 store candidates:', old3 in content)
content = content.replace(old3, new3)

# Fix 4 : _on_return_from_gaming — re-afficher artwork + versions
old4 = """    def _on_return_from_gaming(self):
        self.show()
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        track = self._playlist.current_track()
        if track:
            self._update_track_display(track)
            # Forcer le rechargement de l artwork
            url = track.get('artwork_url')
            if url:
                import threading
                threading.Thread(target=self._fetch_artwork, args=(url,), daemon=True).start()"""
new4 = """    def _on_return_from_gaming(self):
        self.show()
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        track = self._playlist.current_track()
        if track:
            self._update_track_display(track)
            # Forcer le rechargement de l artwork
            url = track.get('artwork_url')
            if url:
                import threading
                threading.Thread(target=self._fetch_artwork, args=(url,), daemon=True).start()
            # Re-afficher les versions si déjà fetchées
            if self._candidates and self._current_playing_url:
                self._signals.candidates_ready.emit(self._candidates, self._current_playing_url)"""
print('4 return gaming:', old4 in content)
content = content.replace(old4, new4)

with open(path, 'w') as f:
    f.write(content)
print('Done')
