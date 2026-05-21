#!/usr/bin/env python3
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Fix 1 : aligner vp en haut dans le HBoxLayout après addWidget
old1 = """        self._versions_panel = vp
        if not self._versions_expanded:
            vp.setFixedHeight(32)
        top.addWidget(vp)"""
new1 = """        self._versions_panel = vp
        if not self._versions_expanded:
            vp.setFixedHeight(32)
        top.addWidget(vp, 0, Qt.AlignmentFlag.AlignTop)"""
print('1 align top:', old1 in content)
content = content.replace(old1, new1)

# Fix 2 : version jouée — fond + gras + coche plus visible
old2 = """            if c['url'] == current_url:
                item.setForeground(QColor(ACCENT))
                item.setBackground(QColor('#0d2a0d'))"""
new2 = """            if c['url'] == current_url:
                from PyQt6.QtGui import QBrush, QFont
                item.setForeground(QColor(ACCENT))
                item.setBackground(QBrush(QColor('#0f2f0f')))
                f = item.font()
                f.setBold(True)
                item.setFont(f)"""
print('2 highlight:', old2 in content)
content = content.replace(old2, new2)

# Fix 3 : retour gaming mode — re-fetch candidates + artwork
old3 = """    def _on_return_from_gaming(self):
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
new3 = """    def _on_return_from_gaming(self):
        self.show()
        idx = self._playlist.current_index
        self._list.setCurrentRow(idx)
        track = self._playlist.current_track()
        if not track:
            return
        self._update_track_display(track)
        # Artwork
        art_url = track.get('artwork_url')
        if art_url:
            import threading
            threading.Thread(target=self._fetch_artwork, args=(art_url,), daemon=True).start()
        # URL courante depuis la playlist
        cur_url = self._playlist.current_url() or self._current_playing_url
        self._current_playing_url = cur_url or ''
        # Versions : re-afficher ou re-fetcher
        import threading
        if self._candidates and cur_url:
            self._signals.candidates_ready.emit(self._candidates, cur_url)
        elif track.get('spotify_id'):
            self._candidates = []
            threading.Thread(
                target=self._fetch_candidates,
                args=(idx, track.get('spotify_id', ''), cur_url or ''),
                daemon=True,
            ).start()"""
print('3 return gaming:', old3 in content)
content = content.replace(old3, new3)

with open(path, 'w') as f:
    f.write(content)
print('Done')
