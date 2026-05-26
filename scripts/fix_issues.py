import py_compile, re
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Fix 3+4 : icônes grandes + texte petit + 🎵 au lieu de 🏠
# Remplacer _nb pour avoir emoji grand et texte petit
old_nb = """        def _nb(icon, label, checkable=False):
            b = QPushButton(f'{icon}\\n{label}')
            b.setCheckable(checkable)
            b.setFixedSize(65, 72)
            b.setStyleSheet(f\"\"\"
                QPushButton {{
                    background: transparent; color: {TEXT_SEC};
                    border: none; font-size: 12px; padding: 4px 2px;
                }}
                QPushButton:hover {{ background: {BG_ITEM}; color: {TEXT_PRI}; }}
                QPushButton:checked {{
                    background: {BG_ITEM}; color: {ACCENT};
                    border-left: 3px solid {ACCENT};
                }}
            \"\"\")
            return b"""
new_nb = """        def _nb(icon, label, checkable=False):
            w = QFrame()
            w.setFixedSize(72, 72)
            w.setProperty('checkable_nav', checkable)
            w.setStyleSheet(f'background: transparent; border: none;')
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 6, 0, 4)
            wl.setSpacing(2)
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            lbl_icon.setStyleSheet(f'font-size: 24px; background: transparent; color: {TEXT_SEC};')
            lbl_text = QLabel(label)
            lbl_text.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            lbl_text.setStyleSheet(f'font-size: 9px; background: transparent; color: {TEXT_SEC};')
            wl.addWidget(lbl_icon)
            wl.addWidget(lbl_text)
            w._icon_lbl = lbl_icon
            w._text_lbl = lbl_text
            w._checked = False
            w._checkable = checkable
            def set_checked(val):
                w._checked = val
                col = ACCENT if val else TEXT_SEC
                lbl_icon.setStyleSheet(f'font-size: 24px; background: transparent; color: {col};')
                lbl_text.setStyleSheet(f'font-size: 9px; background: transparent; color: {col};')
                w.setStyleSheet(
                    f'background: {BG_ITEM}; border-left: 3px solid {ACCENT};'
                    if val else 'background: transparent; border: none;'
                )
            w.setChecked = set_checked
            w.isChecked = lambda: w._checked
            def enter(e): 
                if not w._checked:
                    w.setStyleSheet(f'background: {BG_ITEM}; border: none;')
            def leave(e):
                if not w._checked:
                    w.setStyleSheet('background: transparent; border: none;')
            w.enterEvent = enter
            w.leaveEvent = leave
            b = QPushButton('', w)
            b.setFixedSize(72, 72)
            b.setFlat(True)
            b.setStyleSheet('background: transparent; border: none;')
            w.clicked = b.clicked
            return w"""
print('1 _nb:', old_nb in content)
content = content.replace(old_nb, new_nb)

# Fix 4 : 🏠 → 🎵
content = content.replace("_nb('🏠', 'Lecture'", "_nb('🎵', 'Lecture'")
print('2 note icon:', "'🎵'" in content)

# Fix 7 : _switch_view reset detail view
old_switch = """    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)
        if index == 1:
            self._refresh_pl_list()"""
new_switch = """    def _switch_view(self, index: int):
        self._nav_queue.setChecked(index == 0)
        self._nav_playlists.setChecked(index == 1)
        self._center_stack.setCurrentIndex(index)
        if index == 1:
            # Toujours revenir à la liste principale
            if hasattr(self, '_pl_detail') and self._pl_detail.isVisible():
                self._pl_detail.setVisible(False)
                if hasattr(self, '_pl_list'):
                    self._pl_list.setVisible(True)
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
