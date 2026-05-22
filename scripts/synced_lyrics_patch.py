#!/usr/bin/env python3
"""Ajoute les lyrics synchronisées à BBS Groove."""
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Changer signal lyrics_ready pour passer aussi les synced lyrics
old1 = '    lyrics_ready     = pyqtSignal(str)'
new1 = '    lyrics_ready     = pyqtSignal(str, list)'
print('1 signal:', old1 in content)
content = content.replace(old1, new1)

# 2. Init state pour synced lyrics
old2 = "        self._sleep_secs         = 0"
new2 = "        self._sleep_secs         = 0\n        self._lyrics_synced: list  = []\n        self._lyrics_line: int     = -1"
print('2 state:', old2 in content)
content = content.replace(old2, new2)

# 3. _fetch_lyrics émet aussi synced
old3 = """        try:
            result = LyricsFetcher().fetch(artist, title, dur_ms)
            text = ''
            if result:
                if result.get('plain'):
                    text = result['plain']
            self._signals.lyrics_ready.emit(text)"""
new3 = """        try:
            result = LyricsFetcher().fetch(artist, title, dur_ms)
            text   = ''
            synced = []
            if result:
                text   = result.get('plain', '') or ''
                synced = result.get('synced', []) or []
            self._signals.lyrics_ready.emit(text, synced)"""
print('3 fetch:', old3 in content)
content = content.replace(old3, new3)

# 4. emit vide avec liste vide
old4 = "            self._signals.lyrics_ready.emit('')"
new4 = "            self._signals.lyrics_ready.emit('', [])"
print('4 emit empty:', old4 in content)
content = content.replace(old4, new4)

# 5. _on_lyrics_ready stocke synced + construit HTML
old5 = """    def _on_lyrics_ready(self, text: str):
        \"\"\"Affiche les lyrics dans le widget.\"\"\"
        if text:
            self._lyrics_widget.setPlainText(text)
            self._lyrics_widget.setVisible(True)
        else:
            self._lyrics_widget.clear()
            self._lyrics_widget.setVisible(False)"""
new5 = """    def _on_lyrics_ready(self, text: str, synced: list):
        \"\"\"Affiche les lyrics dans le widget.\"\"\"
        self._lyrics_synced = synced
        self._lyrics_line   = -1
        if synced:
            # Afficher les synced lyrics comme texte plain pour départ
            lines = [line for _, line in synced if line]
            self._lyrics_widget.setPlainText('\\n'.join(lines))
            self._lyrics_widget.setVisible(True)
        elif text:
            self._lyrics_synced = []
            self._lyrics_widget.setPlainText(text)
            self._lyrics_widget.setVisible(True)
        else:
            self._lyrics_synced = []
            self._lyrics_widget.clear()
            self._lyrics_widget.setVisible(False)"""
print('5 on_ready:', old5 in content)
content = content.replace(old5, new5)

# 6. Effacer synced lyrics au changement de piste
old6 = "        self._lyrics_widget.clear()\n        self._lyrics_widget.setVisible(False)"
new6 = "        self._lyrics_widget.clear()\n        self._lyrics_widget.setVisible(False)\n        self._lyrics_synced = []\n        self._lyrics_line   = -1"
print('6 clear:', old6 in content)
content = content.replace(old6, new6)

# 7. Mettre à jour la ligne courante dans _update_progress
old7 = """    def _update_progress(self):
        if not self._player.is_running():
            return
        pos = self._player.get_time_pos()
        dur = self._player.get_duration()
        if dur and dur > 0:
            self._slider.setValue(int(pos / dur * 1000))
        self._lbl_time.setText(self._fmt(pos))
        self._lbl_duration.setText(self._fmt(dur))"""
new7 = """    def _update_progress(self):
        if not self._player.is_running():
            return
        pos = self._player.get_time_pos()
        dur = self._player.get_duration()
        if dur and dur > 0:
            self._slider.setValue(int(pos / dur * 1000))
        self._lbl_time.setText(self._fmt(pos))
        self._lbl_duration.setText(self._fmt(dur))
        if self._lyrics_synced and pos > 0:
            self._sync_lyrics_line(pos)

    def _sync_lyrics_line(self, pos: float):
        \"\"\"Surligne la ligne courante dans les synced lyrics.\"\"\"
        synced = self._lyrics_synced
        # Trouver l'index de la ligne courante
        idx = 0
        for i, (t, _) in enumerate(synced):
            if t <= pos:
                idx = i
            else:
                break
        if idx == self._lyrics_line:
            return  # Pas de changement
        self._lyrics_line = idx
        # Surligner la ligne courante via QTextCursor
        from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
        doc = self._lyrics_widget.document()
        # Reset toutes les lignes
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        fmt_reset = QTextCharFormat()
        fmt_reset.setForeground(QColor('#888888'))
        cursor.setCharFormat(fmt_reset)
        # Surligner la ligne courante
        block = doc.findBlockByLineNumber(idx)
        if block.isValid():
            cursor = QTextCursor(block)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            fmt_cur = QTextCharFormat()
            fmt_cur.setForeground(QColor('#33cc66'))
            fmt_cur.setFontWeight(700)
            cursor.setCharFormat(fmt_cur)
            # Scroller pour voir la ligne
            self._lyrics_widget.setTextCursor(cursor)
            self._lyrics_widget.ensureCursorVisible()"""
print('7 progress:', old7 in content)
content = content.replace(old7, new7)

with open(path, 'w') as f:
    f.write(content)
print('Done')
