"""Nucleo dell'agente (server): listener TCP, cattura schermo, iniezione input, discovery.

Non contiene interfaccia grafica: l'icona nella tray/menu bar è in tray.py,
l'avvio da riga di comando in server_main.py.
"""

from __future__ import annotations

import io
import logging
import socket
import sys
import threading
import time
from dataclasses import asdict, dataclass

from . import __version__
from . import platform_utils as pu
from .discovery import Announcer, machine_name
from .protocol import (APP_ID, DEFAULT_PORT, DISCOVERY_PORT, MSG_BYE, MSG_CONFIG, MSG_FRAME,
                       MSG_HELLO, MSG_INPUT, MSG_NOTICE, MSG_PING, MSG_PONG, PROTOCOL_VERSION,
                       ConnectionClosed, ProtocolError, configure_socket, decode_json,
                       encode_json, pack_message, recv_message)

log = logging.getLogger(__name__)

SOCKET_TIMEOUT = 15.0      # nessun dato dal client per 15 s => client considerato perso
Q_MIN = 20                 # qualità JPEG minima in modalità adattiva


@dataclass
class ServerSettings:
    port: int = DEFAULT_PORT
    discovery_port: int = DISCOVERY_PORT
    announce: bool = True
    fps: int = 12
    quality: int = 50          # JPEG 1-95: medio-bassa per privilegiare la fluidità
    adaptive: bool = True      # adatta qualità/risoluzione alla congestione
    max_width: int = 1920      # 0 = risoluzione originale (es. Retina 2880 px)
    monitor: int = 1           # 1 = schermo principale (indice mss)
    notify_on_connect: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "ServerSettings":
        fields = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in fields})

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


class ClientSession:
    """Una connessione client attiva: un thread invia i frame, uno riceve gli input."""

    def __init__(self, server: "AgentServer", sock: socket.socket, addr):
        self.server = server
        self.sock = sock
        self.addr = addr
        self.ip = addr[0]
        s = server.settings
        self.fps = s.fps
        self.quality = s.quality
        self.adaptive = s.adaptive
        self.max_width = s.max_width
        self._send_lock = threading.Lock()
        self._closed = threading.Event()
        self._close_lock = threading.Lock()
        self._settings_changed = threading.Event()
        self.injector = None
        self.monitor_geom = None

    # --- invio ---
    def send(self, msg_type: int, payload: bytes, timeout: float | None = None) -> bool:
        data = pack_message(msg_type, payload)
        if not self._send_lock.acquire(timeout=-1 if timeout is None else timeout):
            return False
        try:
            self.sock.sendall(data)
            return True
        finally:
            self._send_lock.release()

    def send_json(self, msg_type: int, obj, timeout: float | None = None) -> bool:
        return self.send(msg_type, encode_json(obj), timeout)

    # --- ciclo di vita ---
    def start(self) -> None:
        configure_socket(self.sock, SOCKET_TIMEOUT)
        try:  # buffer di invio contenuto: meno latenza accumulata, congestione più visibile
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512 * 1024)
        except OSError:
            pass
        threading.Thread(target=self._run_input, name=f"input-{self.ip}", daemon=True).start()

    def close(self, reason: str | None = None) -> None:
        with self._close_lock:
            if self._closed.is_set():
                return
            self._closed.set()
        if reason:
            try:
                self.send_json(MSG_BYE, {"reason": reason}, timeout=1.0)
            except OSError:
                pass
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    # --- thread input (e handshake) ---
    def _run_input(self) -> None:
        try:
            import mss
            with mss.mss() as sct:
                idx = self.server.settings.monitor
                if idx >= len(sct.monitors):
                    idx = 1
                self.monitor_geom = dict(sct.monitors[idx])

            warnings = list(self.server.permission_problems)
            try:
                from .injector import InputInjector
                self.injector = InputInjector(self.monitor_geom)
            except Exception as exc:
                log.exception("iniezione input non disponibile")
                warnings.append(f"Mouse/keyboard control is not available on the remote computer: {exc}")

            self.send_json(MSG_HELLO, {
                "app": APP_ID, "v": PROTOCOL_VERSION, "version": __version__,
                "name": machine_name(), "platform": sys.platform,
                "screen": [self.monitor_geom["width"], self.monitor_geom["height"]],
                "warnings": warnings,
            })
            for text in warnings:
                self.send_json(MSG_NOTICE, {"level": "warning", "text": text})

            activated = False
            while not self.closed:
                msg_type, payload = recv_message(self.sock)
                if not activated:
                    # Un vero client invia subito un messaggio (ping/config): solo allora
                    # diventa la sessione attiva. Chi legge solo l'HELLO e chiude (es. la
                    # verifica "l'agente è già avviato?") non disturba la sessione in corso.
                    activated = True
                    self.server._activate(self)
                    threading.Thread(target=self._run_video, name=f"video-{self.ip}",
                                     daemon=True).start()
                if msg_type == MSG_INPUT:
                    if self.injector is not None:
                        try:
                            event = decode_json(payload)
                            if event.get("t") != "move":
                                log.debug("input da %s: %s", self.ip, event)
                            self.injector.handle(event)
                        except Exception:
                            log.debug("evento di input non applicato", exc_info=True)
                elif msg_type == MSG_PING:
                    self.send(MSG_PONG, payload)
                elif msg_type == MSG_CONFIG:
                    self._apply_config(decode_json(payload))
        except (ConnectionClosed, ProtocolError, OSError) as exc:
            if not self.closed:
                log.info("client %s disconnesso (%s)", self.ip, exc)
        except Exception:
            log.exception("errore nella sessione con %s", self.ip)
        finally:
            if self.injector is not None:
                self.injector.release_all()
            self.close()
            self.server._session_ended(self)

    def _apply_config(self, cfg: dict) -> None:
        if not isinstance(cfg, dict):
            return
        if "fps" in cfg:
            self.fps = _clamp(cfg["fps"], 1, 30, self.fps)
        if "quality" in cfg:
            self.quality = _clamp(cfg["quality"], 10, 95, self.quality)
        if "adaptive" in cfg:
            self.adaptive = bool(cfg["adaptive"])
        if "max_width" in cfg:
            self.max_width = _clamp(cfg["max_width"], 0, 10000, self.max_width)
        self._settings_changed.set()
        log.info("impostazioni dal client: fps=%s qualità=%s adattiva=%s max_width=%s",
                 self.fps, self.quality, self.adaptive, self.max_width)

    # --- thread video ---
    def _run_video(self) -> None:
        import mss
        from PIL import Image

        q_current = self.quality
        scale = 1.0          # fattore di riduzione extra in caso di congestione
        good_streak = 0
        prev_raw = None
        last_sent_quality = None
        last_sent_scale = None
        unchanged_since = time.monotonic()
        try:
            with mss.mss() as sct:
                idx = self.server.settings.monitor
                mon = sct.monitors[idx if idx < len(sct.monitors) else 1]
                while not self.closed:
                    t0 = time.perf_counter()
                    interval = 1.0 / max(1, self.fps)
                    if self._settings_changed.is_set():
                        self._settings_changed.clear()
                        q_current, scale, prev_raw = self.quality, 1.0, None

                    shot = sct.grab(mon)
                    raw = shot.bgra
                    target_q = self.quality
                    if raw == prev_raw:
                        # Schermo invariato: non si invia nulla. Se l'ultimo frame era
                        # stato degradato per congestione, dopo 0.5 s se ne manda uno
                        # alla qualità piena per "rifinire" l'immagine statica.
                        needs_refine = (last_sent_quality is not None and
                                        (last_sent_quality < target_q or last_sent_scale < 1.0))
                        if not (needs_refine and time.monotonic() - unchanged_since > 0.5):
                            self._closed.wait(max(0.0, interval - (time.perf_counter() - t0)))
                            continue
                        q_send, scale_send = target_q, 1.0
                    else:
                        prev_raw = raw
                        unchanged_since = time.monotonic()
                        q_send = q_current if self.adaptive else target_q
                        scale_send = scale if self.adaptive else 1.0

                    img = Image.frombytes("RGB", shot.size, raw, "raw", "BGRX")
                    w, h = img.size
                    max_w = int((self.max_width or w) * scale_send)
                    if w > max_w > 0:
                        img = img.resize((max_w, max(1, round(h * max_w / w))), Image.BILINEAR)
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=int(q_send))
                    jpeg = buf.getvalue()

                    t_send = time.perf_counter()
                    self.send(MSG_FRAME, jpeg)
                    send_dt = time.perf_counter() - t_send
                    last_sent_quality, last_sent_scale = q_send, scale_send

                    if self.adaptive:
                        # Se l'invio blocca (buffer TCP pieno) il canale è congestionato:
                        # si scende di qualità e poi di risoluzione; si risale piano.
                        if send_dt > interval * 0.6:
                            good_streak = 0
                            if q_current > Q_MIN:
                                q_current = max(Q_MIN, q_current - 8)
                            else:
                                scale = max(0.5, scale - 0.1)
                        else:
                            good_streak += 1
                            if good_streak >= max(6, self.fps * 2):
                                good_streak = 0
                                if scale < 1.0:
                                    scale = min(1.0, scale + 0.1)
                                elif q_current < target_q:
                                    q_current = min(target_q, q_current + 5)
                        q_current = min(q_current, target_q)

                    self._closed.wait(max(0.0, interval - (time.perf_counter() - t0)))
        except OSError as exc:
            if not self.closed:
                log.info("invio frame a %s interrotto: %s", self.ip, exc)
        except Exception as exc:
            log.exception("errore nella cattura dello schermo")
            try:
                self.send_json(MSG_NOTICE, {"level": "error",
                                            "text": f"Screen capture failed on the remote computer: {exc}"},
                               timeout=1.0)
            except OSError:
                pass
        finally:
            self.close()


def probe_agent(port: int, timeout: float = 2.0) -> str:
    """Chi risponde su localhost:port? "agent" (LBS Labs Remote), "other" o "none"."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
            s.settimeout(timeout)
            first = s.recv(8, socket.MSG_PEEK)
            if not first or first.startswith(b"RFB"):
                return "other"
            msg_type, payload = recv_message(s)
            if msg_type == MSG_HELLO and decode_json(payload).get("app") == APP_ID:
                return "agent"
    except (OSError, ConnectionClosed, ProtocolError, ValueError, AttributeError):
        return "none"
    return "other"


class AgentServer:
    """Accetta un client alla volta e annuncia la propria presenza in LAN."""

    def __init__(self, settings: ServerSettings, on_status=None):
        self.settings = settings
        self.on_status = on_status or (lambda status: None)
        self.session: ClientSession | None = None
        self._lock = threading.Lock()
        self._listen_sock: socket.socket | None = None
        self._announcer: Announcer | None = None
        self._stopping = False
        self.error: str | None = None
        self.port_in_use = False
        self.port_owner = "none"     # dopo un errore di avvio: "agent", "other" o "none"
        self.permission_problems: list[str] = []

    # --- stato per la UI ---
    def status(self) -> dict:
        with self._lock:
            client = self.session.ip if self.session and not self.session.closed else None
        return {"port": self.settings.port, "client": client, "error": self.error,
                "permission_problems": list(self.permission_problems)}

    def _notify_status(self) -> None:
        try:
            self.on_status(self.status())
        except Exception:
            log.exception("callback di stato fallita")

    # --- avvio/arresto ---
    def check_permissions(self, prompt: bool = True) -> list[str]:
        self.permission_problems = pu.permission_problems(prompt=prompt)
        for p in self.permission_problems:
            log.warning(p)
        return self.permission_problems

    def start(self) -> None:
        """Apre il listener. Solleva OSError con messaggio chiaro se la porta è occupata."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not pu.IS_WINDOWS:  # su Windows SO_REUSEADDR permetterebbe doppi bind
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", self.settings.port))
        except OSError as exc:
            s.close()
            self.port_in_use = True
            self.port_owner = probe_agent(self.settings.port)
            if self.port_owner == "agent":
                self.error = "LBS Labs Remote is already running on this computer."
            else:
                self.error = (f"Port {self.settings.port} is already used by another program on "
                              "this computer, so other computers cannot control it. Close that "
                              "program or choose a different port.")
            self._notify_status()
            raise OSError(self.error) from exc
        s.listen(4)
        self._listen_sock = s
        self.error = None
        threading.Thread(target=self._accept_loop, name="accept", daemon=True).start()
        if self.settings.announce:
            self._announcer = Announcer(self.settings.port, self.settings.discovery_port,
                                        is_busy=lambda: self.status()["client"] is not None)
            self._announcer.start()
        log.info("in ascolto sulla porta TCP %d (discovery UDP %d)",
                 self.settings.port, self.settings.discovery_port)
        self._notify_status()

    def stop(self) -> None:
        self._stopping = True
        if self._announcer:
            self._announcer.stop()
        if self._listen_sock:
            try:
                self._listen_sock.close()
            except OSError:
                pass
        with self._lock:
            session = self.session
        if session:
            session.close("LBS Labs Remote was closed on the remote computer.")

    def _accept_loop(self) -> None:
        while not self._stopping:
            try:
                conn, addr = self._listen_sock.accept()
            except OSError:
                if self._stopping:
                    return
                time.sleep(0.5)
                continue
            ClientSession(self, conn, addr).start()

    def _activate(self, new: ClientSession) -> None:
        """La sessione `new` diventa quella attiva (un solo client alla volta)."""
        with self._lock:
            old, self.session = self.session, new
        if old and old is not new and not old.closed:
            # L'ultimo client che si connette prende il controllo: evita di restare
            # bloccati da una connessione "zombie".
            log.info("nuovo client %s: chiudo la sessione di %s", new.ip, old.ip)
            old.close(f"Another computer ({new.ip}) has taken control.")
        log.info("client connesso da %s", new.ip)
        self._notify_status()

    def _session_ended(self, session: ClientSession) -> None:
        with self._lock:
            if self.session is session:
                self.session = None
            else:
                return
        log.info("client %s disconnesso: di nuovo in ascolto", session.ip)
        self._notify_status()
