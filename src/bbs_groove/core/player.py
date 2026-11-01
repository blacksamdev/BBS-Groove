import atexit
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
        # --command=mpv lance le binaire mpv directement (pas la commande du
        # .desktop io.mpv.Mpv).
        return ['flatpak-spawn', '--host', 'flatpak', 'run', '--command=mpv', 'io.mpv.Mpv']
    if shutil.which('mpv'):
        return ['mpv']
    raise FileNotFoundError("mpv introuvable.\n  flatpak install flathub io.mpv.Mpv")


class MPVPlayer:
    """Contrôle mpv via une instance IDLE persistante + socket IPC.

    mpv est lancé UNE SEULE fois en --idle (sans URL) ; chaque titre est
    ensuite chargé via `loadfile` sur le socket IPC. C'est volontaire :
    passer l'URL en argument à `flatpak run io.mpv.Mpv <url>` declenchait
    l'activation du .desktop mpv (via D-Bus/systemd --user), ouvrant une 2e
    instance mpv en pseudo-gui — la fameuse fenetre "No file - mpv" dans la
    barre des taches. En mode idle + IPC, aucune URL n'est jamais passee a
    `flatpak run`, donc plus aucune fenetre parasite. Bonus : l'instance est
    reutilisee d'un titre a l'autre (plus fluide, plus de kill/relance).

    Fin de titre : detectee via l'event mpv `end-file` (reason == "eof").
    """

    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.socket_path = MPV_SOCKET
        self._lock = threading.Lock()
        self.on_track_ended: Callable | None = None
        self._volume: int = 100
        self._stopped = False
        self._started = False        # mpv idle lancé et socket prêt
        self._playing = False        # un titre est chargé / en lecture
        self._expect_eof = False     # on attend la fin naturelle du titre courant
        self._event_thread: threading.Thread | None = None
        atexit.register(self.shutdown)

    # ------------------------------------------------------------------ #
    #  Contrôles publics                                                   #
    # ------------------------------------------------------------------ #

    def play(self, url: str):
        self._stopped = False
        if not self._ensure_mpv():
            log('mpv idle indisponible — lecture annulée', 'warning')
            return
        self._expect_eof = True
        self._playing = True
        if not self._ipc_loadfile(url):
            log('loadfile IPC échec', 'warning')
            self._playing = False
            return
        # (ré)appliquer le volume courant au nouveau titre
        self._cmd('set_property', 'volume', self._volume)
        log('loadfile OK — lecture démarrée', 'debug')

    def pause(self):        self._cmd('set_property', 'pause', True)
    def resume(self):       self._cmd('set_property', 'pause', False)
    def toggle_pause(self): self._cmd('cycle', 'pause')

    def stop(self):
        """Arrête la lecture courante — mpv reste en idle (réutilisable)."""
        self._stopped = True
        self._expect_eof = False
        self._playing = False
        self._cmd('stop')

    def get_time_pos(self) -> float:  return self._get('time-pos') or 0.0
    def get_duration(self) -> float:  return self._get('duration') or 0.0
    def get_paused(self) -> bool:     return self._get('pause') or False
    def seek(self, seconds: float):   self._cmd('seek', seconds, 'absolute')

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, int(vol)))
        self._cmd('set_property', 'volume', self._volume)

    def is_running(self) -> bool:
        return (self.process is not None
                and self.process.poll() is None
                and self._started and self._playing)

    def shutdown(self):
        """Ferme complètement mpv (à la fermeture de l'app)."""
        self._stopped = True
        self._playing = False
        try:
            self._cmd('quit')
        except Exception:
            pass
        time.sleep(0.1)
        with self._lock:
            self._kill_process_locked()
        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Lancement de l'instance idle                                        #
    # ------------------------------------------------------------------ #

    def _ensure_mpv(self) -> bool:
        """Lance mpv en idle s'il ne tourne pas déjà. True si prêt."""
        with self._lock:
            if self._started and self.process and self.process.poll() is None:
                return True
            self._kill_process_locked()
            try:
                if os.path.exists(self.socket_path):
                    os.remove(self.socket_path)
            except Exception:
                pass
            cmd = _mpv_cmd() + MPV_ARGS + ['--idle=yes']
            log(f'mpv idle launch cmd={cmd[0]} socket={self.socket_path}', 'debug')
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        if not self._wait_socket():
            log('mpv socket timeout — idle non prêt', 'warning')
            return False

        self._started = True
        self._cmd('set_property', 'volume', self._volume)
        self._start_event_thread()
        log('mpv idle prêt — socket OK', 'debug')
        return True

    # ------------------------------------------------------------------ #
    #  Écoute des events mpv (fin de titre)                                #
    # ------------------------------------------------------------------ #

    def _start_event_thread(self):
        if self._event_thread and self._event_thread.is_alive():
            return
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

    def _event_loop(self):
        """Connexion dédiée au socket : lit les events, détecte end-file(eof)."""
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(self.socket_path)
        except Exception:
            return
        buf = b''
        try:
            while True:
                if self.process is None or self.process.poll() is not None:
                    break
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    continue
                except Exception:
                    break
                if not chunk:
                    break
                buf += chunk
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except Exception:
                        continue
                    if msg.get('event') == 'end-file':
                        # reason == "eof" => titre terminé naturellement.
                        # (un changement manuel via loadfile donne reason
                        #  "redirect"/"stop", qu'on ignore volontairement.)
                        if (msg.get('reason') == 'eof'
                                and self._expect_eof
                                and not self._stopped):
                            self._expect_eof = False
                            self._playing = False
                            cb = self.on_track_ended
                            if cb:
                                cb()
        finally:
            try:
                s.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    #  IPC                                                                 #
    # ------------------------------------------------------------------ #

    def _ipc_loadfile(self, url: str) -> bool:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect(self.socket_path)
                msg = json.dumps({'command': ['loadfile', url, 'replace']}) + '\n'
                s.sendall(msg.encode())
                return True
        except Exception as e:
            log(f'loadfile error: {e}', 'warning')
            return False

    def _cmd(self, *args):
        self._send(json.dumps({'command': list(args)}) + '\n')

    def _get(self, prop: str):
        """get_property via IPC, en ignorant les events qui transitent."""
        if not os.path.exists(self.socket_path):
            return None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(self.socket_path)
                req = json.dumps({'command': ['get_property', prop],
                                  'request_id': 1}) + '\n'
                s.sendall(req.encode())
                buf = b''
                deadline = time.time() + 2.0
                while time.time() < deadline:
                    try:
                        chunk = s.recv(8192)
                    except socket.timeout:
                        break
                    if not chunk:
                        break
                    buf += chunk
                    for raw in buf.split(b'\n'):
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            d = json.loads(raw)
                        except Exception:
                            continue
                        if d.get('request_id') == 1 and 'error' in d:
                            return d.get('data')
        except Exception:
            pass
        return None

    def _send(self, msg: str):
        if not os.path.exists(self.socket_path):
            return
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(self.socket_path)
                s.sendall(msg.encode())
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Privé                                                               #
    # ------------------------------------------------------------------ #

    def _wait_socket(self, timeout: float = 15.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if os.path.exists(self.socket_path):
                time.sleep(0.2)   # laisser mpv accepter les connexions
                return True
            time.sleep(0.1)
        return False

    def _kill_process_locked(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        self._started = False
        self._playing = False
