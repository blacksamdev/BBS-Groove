#!/usr/bin/env python3
"""Ajoute le sleep timer à BBS Groove."""
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# 1. Import QTimer
old1 = 'from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QSize'
new1 = 'from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QSize, QTimer'
print('1 QTimer import:', old1 in content)
content = content.replace(old1, new1)

# 2. Init sleep timer dans __init__
old2 = '        self._pref_store         = PrefStore()\n        self._versions_expanded  = self._pref_store.get_ui_state("versions_expanded", True)'
new2 = '        self._pref_store         = PrefStore()\n        self._versions_expanded  = self._pref_store.get_ui_state("versions_expanded", True)\n        self._sleep_timer        = QTimer()\n        self._sleep_timer.setSingleShot(True)\n        self._sleep_timer.timeout.connect(self._on_sleep_timer)\n        self._sleep_remaining    = QTimer()\n        self._sleep_remaining.setInterval(1000)\n        self._sleep_remaining.timeout.connect(self._update_sleep_btn)\n        self._sleep_secs         = 0'
print('2 init sleep:', old2 in content)
content = content.replace(old2, new2)

# 3. Ajouter bouton sleep après btn_repeat dans la barre de contrôles
old3 = '''        for b in (self._btn_shuffle, self._btn_prev, self._btn_play,
                  self._btn_next, self._btn_repeat):
            ctrl.addWidget(b)
        ctrl.addStretch()'''
new3 = '''        self._btn_sleep = self._ctrl_btn('💤')
        for b in (self._btn_shuffle, self._btn_prev, self._btn_play,
                  self._btn_next, self._btn_repeat):
            ctrl.addWidget(b)
        ctrl.addStretch()
        ctrl.addWidget(self._btn_sleep)'''
print('3 sleep btn:', old3 in content)
content = content.replace(old3, new3)

# 4. Connecter le bouton dans les connexions
old4 = '        self._btn_repeat.toggled.connect(self._on_repeat)'
new4 = '        self._btn_repeat.toggled.connect(self._on_repeat)\n        self._btn_sleep.clicked.connect(self._on_sleep_click)'
print('4 connect:', old4 in content)
content = content.replace(old4, new4)

# 5. Ajouter les méthodes sleep avant _on_volume
old5 = '    def _on_volume(self, value: int):'
new5 = '''    def _on_sleep_click(self):
        """Cycle : off → 15 → 30 → 45 → 60 → off."""
        options = [0, 15, 30, 45, 60]
        if self._sleep_timer.isActive():
            current = self._sleep_secs // 60
            try:
                idx = options.index(current)
            except ValueError:
                idx = 0
            nxt = options[(idx + 1) % len(options)]
        else:
            nxt = options[1]  # 15 min par défaut

        if nxt == 0:
            self._sleep_timer.stop()
            self._sleep_remaining.stop()
            self._btn_sleep.setText('💤')
            self._btn_sleep.setStyleSheet(self._btn_sleep.styleSheet().replace(
                f'border-color: {ACCENT}', 'border-color: #333'))
        else:
            self._sleep_secs = nxt * 60
            self._sleep_timer.start(self._sleep_secs * 1000)
            self._sleep_remaining.start()
            self._update_sleep_btn()

    def _update_sleep_btn(self):
        remaining = self._sleep_timer.remainingTime() // 1000
        if remaining <= 0:
            return
        mins, secs = divmod(remaining, 60)
        self._btn_sleep.setText(f'💤{mins}:{secs:02d}')

    def _on_sleep_timer(self):
        self._sleep_remaining.stop()
        self._btn_sleep.setText('💤')
        self._player.stop()
        self._playing = False
        self._btn_play.setText('▶')
        self._lbl_status.setText('Sleep timer — lecture terminée')

    def _on_volume(self, value: int):'''
print('5 methods:', old5 in content)
content = content.replace(old5, new5)

with open(path, 'w') as f:
    f.write(content)
print('Done')
