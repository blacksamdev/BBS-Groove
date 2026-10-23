#!/usr/bin/env python3
"""BBS Groove — Lecteur audio sans pub, sans compte. Suite BBS."""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='BBS Groove')
    parser.add_argument('--gaming', action='store_true',
                        help='Démarrer directement en mode gaming (tray)')
    parser.add_argument('--debug', action='store_true',
                        help='Activer les logs de debug')
    args = parser.parse_args()

    from bbs_groove.logging_utils import setup_logging
    setup_logging(debug=args.debug)

    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setApplicationName('BBS Groove')
    # App-id Wayland/X11 déterministe : la fenetre Groove s'annonce comme
    # io.github.blacksamdev.Groove (et non 'python3'), pour que la fenetre mpv,
    # lancee avec le meme app-id (cf. settings.MPV_ARGS), se groupe sous l'icone
    # Groove dans la barre des taches au lieu d'une entree 'mpv' separee.
    app.setDesktopFileName('io.github.blacksamdev.Groove')
    app.setStyle('Fusion')
    if args.gaming:
        from bbs_groove.ui.tray import GrooveTray
        window = GrooveTray()
        window.show()
    else:
        from bbs_groove.ui.main_window import BBSGrooveWindow
        window = BBSGrooveWindow()
        window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
