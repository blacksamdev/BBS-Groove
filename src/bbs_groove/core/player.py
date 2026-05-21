import json
import os
import shutil
import socket
import subprocess
import threading
import time
from typing import Callable
from bbs_groove.config.settings import MPV_ARGS, MPV_SOCKET
from bbs_groove.logging_utils import log

_IS_FLATPAK = os.path.exists('/app')


def _mpv_cmd() -> list[str]:
    if _IS_FLATPAK:
        return ['flatpak-spawn', '--host', 'flatpak', 'run', 'io.mpv.Mpv']
    if shutil.which('mpv'):
        return ['mpv']
    raise FileNotFoundError("mpv introuvable.\n  flatpak install flathub io.mpv.Mpv")


def _kill_all_mpv():
    if _IS_FLATPAK:
        subprocess.run(['flatpak-spawn', '--host', 'pkill', '-x', 'mpv'],     capture_output=True)
        subprocess.run(['flatpak-spawn', '--host', 'pkill', '-x', 'mpv-bin'], capture_output=True)
    else:
        subprocess.run(['pkill', '-x', 'mpv'], capture_output=True)


class MPVPlayer:
    """Contrôle mpv via socket IPC Unix."""

    def __init__(self):
        self.process:        subprocess.Popen | None = None
        self.socket_path     = MPV_SOCKET
        self._stopped        = False
        self._started        = False
        self._transitioning  = False   # Empêche la cascade on_track_ended pendant play()
        self._lock           = threading.Lock()
        self._monitor_thread: threading.Thread | None = None
        self.on_track_ended: Callable | None = None
        self._volume: int = 100

    # ------------------------------------------------------------------ #
    #  Contrôles publics                                                   #
    # ------------------------------------------------------------------ #

    def play(self, url: str):
        # Lever le flag AVANT de tuer l'ancien mpv pour bloquer sa cascade
        self._transitioning = True
        self._stopped = False

        with self._lock:
            self._stop_process()
            cmd = _mpv_cmd() + MPV_ARGS + [url]
            log(f'play() cmd={cmd[0]} socket={self.socket_path}', 'debug')
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        socket_ok = self._wait_socket()
        self._transitioning = False   # Re-activer maintenant que le nouveau mpv tourne

        if not socket_ok:
            log('mpv socket timeout — lecture annulée', 'warning')
            self._stop_process()
            return

        self._started = True
        log('mpv socket OK — lecture démarrée', 'debug')
        if self._volume != 100:
            self.set_volume(self._volume)
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()

    def pause(self):        self._cmd('set_property', 'pause', True)
    def resume(self):       self._cmd('set_property', 'pause', False)
    def toggle_pause(self): self._cmd('cycle', 'pause')

    def stop(self):
        self._stopped = True
        self._stop_process()

    def get_time_pos(self) -> float:  return self._get('time-pos') or 0.0
    def get_duration(self) -> float:  return self._get('duration') or 0.0
    def get_paused(self) -> bool:     return self._get('pause') or False
    def seek(self, seconds: float):   self._cmd('seek', seconds, 'absolute')
    def set_volume(self, vol: int):
        self._volume = max(0, min(100, vol))
        self._cmd('set_property', 'volume', self._volume)

    def is_running(self) -> bool:
        return (self.process is not None
                and self.process.poll() is None
                and self._started)

    # ------------------------------------------------------------------ #
    #  Privé                                                               #
    # ------------------------------------------------------------------ #

    def _monitor(self):
        process = self.process  # capturer la référence au démarrage
        if process:
            process.wait()
        # Ne déclencher que si c'est le process actif (pas un ancien monitor)
        if (not self._stopped and self._started
                and not self._transitioning
                and process is self.process
                and self.on_track_ended):
            self.on_track_ended()

    def _stop_process(self):
        self._cmd('quit')
        time.sleep(0.1)
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                pass
            self.process = None
        _kill_all_mpv()
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass
        self._started = False

    def _wait_socket(self, timeout: float = 15.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if os.path.exists(self.socket_path):
                return True
            time.sleep(0.1)
        return False

    def _cmd(self, *args):
        self._send(json.dumps({'command': list(args)}) + '\n')

    def _get(self, prop: str):
        raw = self._send_recv(json.dumps({'command': ['get_property', prop]}) + '\n')
        if raw:
            try:
                return json.loads(raw).get('data')
            except Exception:
                pass
        return None

    def _send(self, msg: str):
        if not os.path.exists(self.socket_path):
            return
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(self.socket_path)
                s.sendall(msg.encode())
        except Exception:
            pass

    def _send_recv(self, msg: str) -> str | None:
        if not os.path.exists(self.socket_path):
            return None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(self.socket_path)
                s.sendall(msg.encode())
                return s.recv(4096).decode()
        except Exception:
            return None
