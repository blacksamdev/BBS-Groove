PREFIX ?= /usr/local
BINDIR  = $(PREFIX)/bin
LIBDIR  = $(PREFIX)/lib/bbs-groove
DATADIR = $(PREFIX)/share
APPDIR  = $(DATADIR)/applications
ICONDIR = $(DATADIR)/icons/hicolor/scalable/apps

PYTHON = python3
PIP    = pip3
APP_ID = io.github.blacksamdev.Groove

.PHONY: all install install-user install-deps uninstall check dev clean

all:
	@echo "BBS grOOve — cibles disponibles :"
	@echo "  make install       Installe dans $(PREFIX)"
	@echo "  make install-user  Installe dans ~/.local"
	@echo "  make install-deps  Installe les dépendances Python"
	@echo "  make uninstall     Désinstalle"
	@echo "  make dev           Lance directement depuis les sources"
	@echo "  make check         Vérifie les dépendances"

# ─────────────────────────────
# Dépendances système
# ─────────────────────────────
install-deps:
	@echo ">>> Vérification des dépendances système..."
	@which $(PYTHON) > /dev/null || (echo "ERREUR : python3 manquant" && exit 1)
	@which mpv > /dev/null || echo "ATTENTION : mpv non trouvé — installez mpv"
	@$(PIP) install --break-system-packages \
		PyQt6 spotifyscraper yt-dlp pystray Pillow python-dotenv requests
	@echo ">>> Dépendances OK."

check:
	@echo ">>> Vérification de l'environnement..."
	@$(PYTHON) -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')" 2>/dev/null || echo "MANQUANT : PyQt6"
	@$(PYTHON) -c "from spotify_scraper import SpotifyClient; print('spotifyscraper OK')" 2>/dev/null || echo "MANQUANT : spotifyscraper"
	@$(PYTHON) -c "import yt_dlp; print('yt-dlp OK')" 2>/dev/null || echo "MANQUANT : yt-dlp"
	@$(PYTHON) -c "import pystray; print('pystray OK')" 2>/dev/null || echo "MANQUANT : pystray"
	@which mpv > /dev/null && echo "mpv OK ($(shell which mpv))" || echo "MANQUANT : mpv"

# ─────────────────────────────
# Installation système (sudo)
# ─────────────────────────────
install:
	@echo ">>> Installation dans $(PREFIX)..."
	install -Dm755 wrapper-native.sh $(BINDIR)/bbs-groove
	install -d $(LIBDIR)/src/bbs_groove/core/sources
	install -d $(LIBDIR)/src/bbs_groove/ui
	install -d $(LIBDIR)/src/bbs_groove/config
	install -Dm644 src/bbs_groove/__init__.py                    $(LIBDIR)/src/bbs_groove/__init__.py
	install -Dm644 src/bbs_groove/groove.py                      $(LIBDIR)/src/bbs_groove/groove.py
	install -Dm644 src/bbs_groove/core/__init__.py               $(LIBDIR)/src/bbs_groove/core/__init__.py
	install -Dm644 src/bbs_groove/core/player.py                 $(LIBDIR)/src/bbs_groove/core/player.py
	install -Dm644 src/bbs_groove/core/playlist.py               $(LIBDIR)/src/bbs_groove/core/playlist.py
	install -Dm644 src/bbs_groove/core/resolver.py               $(LIBDIR)/src/bbs_groove/core/resolver.py
	install -Dm644 src/bbs_groove/core/sources/__init__.py       $(LIBDIR)/src/bbs_groove/core/sources/__init__.py
	install -Dm644 src/bbs_groove/core/sources/spotify.py        $(LIBDIR)/src/bbs_groove/core/sources/spotify.py
	install -Dm644 src/bbs_groove/ui/__init__.py                 $(LIBDIR)/src/bbs_groove/ui/__init__.py
	install -Dm644 src/bbs_groove/ui/main_window.py              $(LIBDIR)/src/bbs_groove/ui/main_window.py
	install -Dm644 src/bbs_groove/ui/tray.py                     $(LIBDIR)/src/bbs_groove/ui/tray.py
	install -Dm644 src/bbs_groove/config/__init__.py             $(LIBDIR)/src/bbs_groove/config/__init__.py
	install -Dm644 src/bbs_groove/config/settings.py             $(LIBDIR)/src/bbs_groove/config/settings.py
	install -Dm644 data/$(APP_ID).desktop $(APPDIR)/$(APP_ID).desktop
	install -Dm644 data/$(APP_ID).svg     $(ICONDIR)/$(APP_ID).svg
	@echo ">>> Installation terminée. Lancez : bbs-groove"

install-user:
	PREFIX=$$HOME/.local $(MAKE) install
	@echo ">>> Assurez-vous que $$HOME/.local/bin est dans votre PATH."

# ─────────────────────────────
# Désinstallation
# ─────────────────────────────
uninstall:
	@echo ">>> Désinstallation..."
	rm -f  $(BINDIR)/bbs-groove
	rm -rf $(LIBDIR)
	rm -f  $(APPDIR)/$(APP_ID).desktop
	rm -f  $(ICONDIR)/$(APP_ID).svg
	@echo ">>> Désinstallation terminée."

# ─────────────────────────────
# Développement (sans install)
# ─────────────────────────────
dev:
	PYTHONPATH=src $(PYTHON) -m bbs_groove.groove

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
