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

    if args.gaming:
        from bbs_groove.ui.tray import GrooveTray
        tray = GrooveTray()
        tray.show()
    else:
        from PyQt6.QtWidgets import QApplication
        from bbs_groove.ui.main_window import BBSGrooveWindow
        app = QApplication(sys.argv)
        app.setApplicationName('BBS Groove')
        app.setStyle('Fusion')
        window = BBSGrooveWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
