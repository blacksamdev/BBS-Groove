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

# Arguments mpv — lecteur AUDIO sans aucune fenetre.
# player.py lance mpv UNE fois en --idle (ajoute --idle=yes) puis charge les
# titres via loadfile sur le socket IPC : aucune URL n'est passee a
# `flatpak run`, donc pas de fenetre pseudo-gui parasite.
# NE PAS ajouter --wayland-app-id / --x11-name / --player-operation-mode :
# ces options forcent mpv a creer une surface graphique (fenetre + entree
# dans la barre des taches), meme en --no-video. La config ci-dessous ne
# cree aucune fenetre.
MPV_ARGS = [
    '--no-video',
    '--force-window=no',
    '--audio-display=no',
    '--no-terminal',
    '--really-quiet',
    f'--input-ipc-server={MPV_SOCKET}',
]

PREFETCH_COUNT = 3
SYNC_INTERVAL  = 300
