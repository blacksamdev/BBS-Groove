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

MPV_ARGS = [
    '--no-video',
    '--no-terminal',
    '--really-quiet',
    '--audio-display=no',
    f'--input-ipc-server={MPV_SOCKET}',
]

PREFETCH_COUNT = 2
SYNC_INTERVAL  = 300
