#!/usr/bin/env python3
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Fix 1 : stocker référence au panel versions pour resize au collapse
old1 = "        top.addWidget(vp)"
new1 = "        self._versions_panel = vp\n        top.addWidget(vp)"
print('1 panel ref:', old1 in content)
content = content.replace(old1, new1)

# Fix 2 : _toggle_versions — fixer la hauteur selon état
old2 = '''    def _toggle_versions(self):
        self._versions_expanded = not self._versions_expanded
        self._versions_list.setVisible(self._versions_expanded)
        self._btn_versions.setText('▼' if self._versions_expanded else '▶')
        self._pref_store.save_ui_state('versions_expanded', self._versions_expanded)'''
new2 = '''    def _toggle_versions(self):
        self._versions_expanded = not self._versions_expanded
        self._versions_list.setVisible(self._versions_expanded)
        self._btn_versions.setText('▼' if self._versions_expanded else '▶')
        if self._versions_expanded:
            self._versions_panel.setMaximumHeight(16777215)
            self._versions_panel.setMinimumHeight(0)
        else:
            self._versions_panel.setFixedHeight(32)
        self._pref_store.save_ui_state('versions_expanded', self._versions_expanded)'''
print('2 toggle:', old2 in content)
content = content.replace(old2, new2)

# Init hauteur au démarrage selon état sauvegardé (dans _right_panel après création vp)
old3 = "        self._versions_panel = vp\n        top.addWidget(vp)"
new3 = "        self._versions_panel = vp\n        if not self._versions_expanded:\n            vp.setFixedHeight(32)\n        top.addWidget(vp)"
print('3 init height:', old3 in content)
content = content.replace(old3, new3)

# Fix 4 : double-clic liste — stopper l ancien avant de jouer
old4 = "    def _on_list_dclick(self, item):\n        row = self._list.row(item)\n        track = self._playlist.go_to(row)\n        if track:\n            self._update_track_display(track)\n            self._play_current()"
new4 = "    def _on_list_dclick(self, item):\n        row = self._list.row(item)\n        self._player.stop()\n        self._playing = False\n        track = self._playlist.go_to(row)\n        if track:\n            self._update_track_display(track)\n            self._play_current()"
print('4 dclick:', old4 in content)
content = content.replace(old4, new4)

with open(path, 'w') as f:
    f.write(content)
print('Done')
