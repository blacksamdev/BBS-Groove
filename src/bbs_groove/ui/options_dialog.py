"""Dialog Options — autoplay + clé Last.fm."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QLineEdit, QPushButton, QButtonGroup, QFrame, QWidget
)
from PyQt6.QtCore import Qt

# Couleurs cohérentes avec le reste de l'app
BG   = '#1a1a1a'
BG2  = '#252525'
ACC  = '#1DB954'
TXT  = '#ffffff'
SEC  = '#aaaaaa'
BTN  = f"""
    QPushButton {{
        background: {ACC}; color: #000; border: none;
        border-radius: 4px; font-size: 12px;
        padding: 6px 16px; font-weight: bold;
    }}
    QPushButton:hover {{ background: #1ed760; }}
"""
BTN2 = f"""
    QPushButton {{
        background: #333; color: {TXT}; border: none;
        border-radius: 4px; font-size: 12px; padding: 6px 16px;
    }}
    QPushButton:hover {{ background: #444; }}
"""


class OptionsDialog(QDialog):
    def __init__(self, settings_store, parent=None):
        super().__init__(parent)
        self._store = settings_store
        self.setWindowTitle('Options')
        self.setModal(True)
        self.setFixedSize(480, 300)
        self.setStyleSheet(f'background: {BG}; color: {TXT};')
        self._build()
        self._load()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(12)

        # Titre section
        lbl = QLabel('Continuer après la playlist')
        lbl.setStyleSheet(f'color: {TXT}; font-size: 13px; font-weight: bold;')
        v.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f'color: #333; background: #333;')
        sep.setFixedHeight(1)
        v.addWidget(sep)

        # Radio buttons
        self._grp = QButtonGroup(self)
        for val, txt, sub in [
            ('off',     'Désactivé',                         ''),
            ('youtube', 'YouTube Music',                     'Résultats automatiques, sans clé'),
            ('lastfm',  'Last.fm',                           'Recommandations précises — clé API requise'),
        ]:
            row = QWidget()
            row.setStyleSheet('background: transparent;')
            rl = QVBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(2)
            rb = QRadioButton(txt)
            rb.setProperty('value', val)
            rb.setStyleSheet(f'''
                QRadioButton {{ color: {TXT}; font-size: 12px; background: transparent; }}
                QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 7px;
                    border: 2px solid #666; background: transparent; }}
                QRadioButton::indicator:checked {{ border: 2px solid {ACC}; background: {ACC}; }}
            ''')
            self._grp.addButton(rb)
            rl.addWidget(rb)
            if sub:
                sub_lbl = QLabel(sub)
                sub_lbl.setStyleSheet(f'color: {SEC}; font-size: 10px; background: transparent; padding-left: 20px;')
                rl.addWidget(sub_lbl)
            v.addWidget(row)
            if val == 'lastfm':
                self._lastfm_row = QWidget()
                self._lastfm_row.setStyleSheet('background: transparent;')
                kl = QHBoxLayout(self._lastfm_row)
                kl.setContentsMargins(20, 0, 0, 0)
                kl.setSpacing(8)
                self._key_input = QLineEdit()
                self._key_input.setPlaceholderText('Clé API Last.fm (32 caractères)')
                self._key_input.setStyleSheet(f"""
                    QLineEdit {{
                        background: {BG2}; color: {TXT};
                        border: 1px solid #444; border-radius: 4px;
                        padding: 4px 8px; font-size: 11px;
                    }}
                    QLineEdit:focus {{ border-color: {ACC}; }}
                """)
                btn_save_key = QPushButton('💾')
                btn_save_key.setFixedSize(30, 28)
                btn_save_key.setStyleSheet(BTN)
                btn_save_key.clicked.connect(self._save_key)
                btn_save_key.setToolTip('Sauvegarder la clé')
                kl.addWidget(self._key_input)
                kl.addWidget(btn_save_key)
                link = QLabel('<a href="https://www.last.fm/api/account/create" style="color:#1DB954;">Obtenir une clé gratuite sur last.fm/api</a>')
                link.setOpenExternalLinks(True)
                link.setStyleSheet('background: transparent; font-size: 10px; padding-left: 20px;')
                v.addWidget(link)
                v.addWidget(self._lastfm_row)

        self._grp.buttonClicked.connect(self._on_mode_change)

        v.addStretch()

        # Boutons bas
        brow = QHBoxLayout()
        brow.addStretch()
        btn_close = QPushButton('Fermer')
        btn_close.setStyleSheet(BTN2)
        btn_close.clicked.connect(self.accept)
        brow.addWidget(btn_close)
        v.addLayout(brow)

    def _load(self):
        mode = self._store.get('autoplay_mode')
        key  = self._store.get('lastfm_api_key')
        for btn in self._grp.buttons():
            if btn.property('value') == mode:
                btn.setChecked(True)
        if key:
            self._key_input.setText(key)
        self._lastfm_row.setVisible(mode == 'lastfm')

    def _on_mode_change(self, btn):
        val = btn.property('value')
        self._store.set('autoplay_mode', val)
        self._lastfm_row.setVisible(val == 'lastfm')

    def _save_key(self):
        key = self._key_input.text().strip()
        self._store.set('lastfm_api_key', key)
        self._key_input.setStyleSheet(self._key_input.styleSheet().replace(
            'border: 1px solid #444', 'border: 1px solid #1DB954'
        ))
