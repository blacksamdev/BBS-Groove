import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'bbs-groove'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_IS_FLATPAK = os.path.exists('/app')

# XDG_RUNTIME_DIR est partagé nativement entre le sandbox Flatpak et le host.
# C'est le seul chemin garanti accessible des deux côtés sans filesystem flag.
# Socket dans le data dir de mpv Flatpak — accessible nativement par mpv
# et exposé à BBS Groove via --filesystem=~/.var/app/io.mpv.Mpv:create dans le manifest
import pathlib as _pl
MPV_SOCKET = str(_pl.Path.home() / '.var' / 'app' / 'io.mpv.Mpv' / 'bbs-groove-mpv.sock')

# App-id partagé avec la fenêtre Groove (cf. groove.py setDesktopFileName).
# Donner à mpv le meme app-id que Groove fait que le gestionnaire de fenetres
# (KDE/Wayland comme X11) groupe la fenetre mpv SOUS l'icone Groove dans la
# barre des taches, au lieu d'afficher une entree 'mpv' separee.
APP_ID = 'io.github.blacksamdev.Groove'

MPV_ARGS = [
    # Forcer le mode lecteur (cplayer). Lancé sans terminal, mpv bascule sinon
    # en pseudo-gui et ouvre une fenêtre, meme pour de l'audio.
    '--player-operation-mode=cplayer',
    '--no-video',
    '--force-window=no',
    '--audio-display=no',
    # Groupement barre des taches sous l'icone Groove (Wayland + X11)
    f'--wayland-app-id={APP_ID}',
    f'--x11-name={APP_ID}',
    '--no-terminal',
    '--really-quiet',
    f'--input-ipc-server={MPV_SOCKET}',
]

PREFETCH_COUNT = 3
SYNC_INTERVAL  = 300
