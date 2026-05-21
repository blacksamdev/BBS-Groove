#!/usr/bin/env python3
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Panel versions AlignTop — setSizePolicy Minimum pour que ca shrink
old1 = """        vp = QFrame()
        vp.setStyleSheet(f'background: {BG_ITEM}; border-radius: 6px;')
        vp.setFixedWidth(220)
        vpl = QVBoxLayout(vp)"""
new1 = """        vp = QFrame()
        vp.setStyleSheet(f'background: {BG_ITEM}; border-radius: 6px;')
        vp.setFixedWidth(220)
        vp.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        vpl = QVBoxLayout(vp)"""
print('1:', old1 in content)
content = content.replace(old1, new1)

# 2. Vider la liste au changement de piste
old2 = "    def _update_track_display(self, track: dict):\n        self._lbl_title.setText(track.get('title', ''))"
new2 = "    def _update_track_display(self, track: dict):\n        self._versions_list.clear()\n        self._lbl_title.setText(track.get('title', ''))"
print('2:', old2 in content)
content = content.replace(old2, new2)

# 3. Tooltip sur chaque item de la liste
old3 = """            item = QListWidgetItem(f"{check}{channel}  {dur_str}")
            item.setData(Qt.ItemDataRole.UserRole, c['url'])"""
new3 = """            full_title = c.get('title', '')
            item = QListWidgetItem(f"{check}{channel}  {dur_str}")
            item.setData(Qt.ItemDataRole.UserRole, c['url'])
            item.setToolTip(full_title)"""
print('3:', old3 in content)
content = content.replace(old3, new3)

with open(path, 'w') as f:
    f.write(content)
print('Done')
