"""Auto-discovery in LAN tramite broadcast UDP.

Il server (agente) invia ogni ~2 secondi un piccolo pacchetto JSON:
    {"app": "lbsremote", "v": 1, "name": "DEMO-PC1", "port": 5970, "busy": false}
sulla porta UDP DISCOVERY_PORT. Il client resta in ascolto su quella porta e
costruisce l'elenco dei PC trovati; l'indirizzo IP è quello del mittente.

Il broadcast non attraversa i router: su subnet diverse si usa il campo IP manuale.
"""

from __future__ import annotations

import json
import logging
import platform
import socket
import threading
import time

from .protocol import APP_ID, DISCOVERY_PORT, PROTOCOL_VERSION

log = logging.getLogger(__name__)


def machine_name() -> str:
    name = platform.node() or socket.gethostname() or "PC"
    if name.lower().endswith(".local"):
        name = name[:-6]
    return name


def local_ipv4_addresses() -> list[str]:
    """Indirizzi IPv4 locali (escluso loopback), senza dipendenze esterne."""
    ips: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    # Indirizzo dell'interfaccia della route di default: connect() su UDP non
    # invia nulla, serve solo a far scegliere al sistema l'interfaccia.
    for probe in ("10.255.255.255", "192.168.255.255", "8.8.8.8"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((probe, 1))
                ips.add(s.getsockname()[0])
        except OSError:
            pass
    return sorted(ip for ip in ips if not ip.startswith("127.") and ip != "0.0.0.0")


class Announcer(threading.Thread):
    """Thread del server che annuncia periodicamente la propria presenza."""

    def __init__(self, tcp_port: int, discovery_port: int = DISCOVERY_PORT,
                 interval: float = 2.0, is_busy=lambda: False):
        super().__init__(name="discovery-announcer", daemon=True)
        self.tcp_port = tcp_port
        self.discovery_port = discovery_port
        self.interval = interval
        self.is_busy = is_busy
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self.announce_once()
            except Exception:  # non deve mai fermare l'agente
                log.debug("annuncio discovery fallito", exc_info=True)
            self._stop.wait(self.interval)

    def _targets(self) -> set[tuple[str, str | None]]:
        """Coppie (destinazione, ip_sorgente). Si invia sia al broadcast globale
        sia al broadcast /24 di ogni interfaccia, legando il socket all'IP
        locale: su Windows con più schede di rete 255.255.255.255 esce
        altrimenti da una sola interfaccia. I duplicati lato client sono innocui."""
        targets: set[tuple[str, str | None]] = {("255.255.255.255", None)}
        for ip in local_ipv4_addresses():
            parts = ip.split(".")
            targets.add(("255.255.255.255", ip))
            targets.add((".".join(parts[:3] + ["255"]), ip))
        return targets

    def announce_once(self) -> None:
        payload = json.dumps({
            "app": APP_ID,
            "v": PROTOCOL_VERSION,
            "name": machine_name(),
            "port": self.tcp_port,
            "busy": bool(self.is_busy()),
        }).encode("utf-8")
        for dest, source_ip in self._targets():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                if source_ip:
                    s.bind((source_ip, 0))
                s.sendto(payload, (dest, self.discovery_port))
            except OSError:
                pass
            finally:
                s.close()


class DiscoveryListener(threading.Thread):
    """Thread del client che raccoglie gli annunci dei server."""

    def __init__(self, discovery_port: int = DISCOVERY_PORT, max_age: float = 7.0):
        super().__init__(name="discovery-listener", daemon=True)
        self.discovery_port = discovery_port
        self.max_age = max_age
        self._servers: dict[tuple[str, int], dict] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.error: str | None = None

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except OSError:
                    pass
            s.bind(("", self.discovery_port))
        except OSError as exc:
            self.error = f"auto-discovery non disponibile ({exc})"
            log.warning(self.error)
            s.close()
            return
        s.settimeout(0.5)
        with s:
            while not self._stop.is_set():
                try:
                    data, (ip, _port) = s.recvfrom(2048)
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop.is_set():
                        break
                    time.sleep(0.5)
                    continue
                self._handle(data, ip)

    def _handle(self, data: bytes, ip: str) -> None:
        try:
            info = json.loads(data.decode("utf-8"))
            if info.get("app") != APP_ID:
                return
            port = int(info.get("port"))
            name = str(info.get("name") or ip)[:64]
        except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
            return
        with self._lock:
            self._servers[(ip, port)] = {
                "ip": ip, "port": port, "name": name,
                "busy": bool(info.get("busy")), "seen": time.monotonic(),
            }

    def servers(self) -> list[dict]:
        """Server visti negli ultimi `max_age` secondi, ordinati per nome."""
        now = time.monotonic()
        with self._lock:
            for key in [k for k, v in self._servers.items() if now - v["seen"] > self.max_age]:
                del self._servers[key]
            items = [dict(v) for v in self._servers.values()]
        return sorted(items, key=lambda v: (v["name"].lower(), v["ip"]))
