"""Finestra di LBS Labs Remote (connessione + schermo remoto).

L'interfaccia è una pagina web (lbsremote/ui/) con lo stile grafico LBS
(LBS-Stile-Grafico/), mostrata in una finestra nativa con pywebview
(WebKit sul Mac, Edge WebView2 su Windows). Un piccolo server HTTP locale,
raggiungibile solo da questo computer, fornisce la pagina e i frame dello
schermo remoto; i comandi dell'interfaccia arrivano tramite l'oggetto Api.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import APP_NAME, __version__
from . import platform_utils as pu
from .client import NetSession
from .config import load_json, save_json
from .discovery import DiscoveryListener, local_ipv4_addresses
from .protocol import DEFAULT_PORT, DISCOVERY_PORT, LEGACY_DEFAULT_PORT, parse_host_port
from .resources import STYLE_DIR, UI_DIR, style_token

log = logging.getLogger("lbsremote.viewer")

CLIENT_CONFIG = "client.json"
CONNECT_SIZE = (600, 720)          # finestra di connessione (px logici)
STYLE_PARTS = ("tokens", "css", "font", "logo", "icone")

QUALITY_PRESETS = {
    "Automatic": {},                                   # default dell'agente, adattiva
    "Low": {"quality": 35, "adaptive": False},
    "Medium": {"quality": 55, "adaptive": False},
    "High": {"quality": 75, "adaptive": False},
    "Maximum": {"quality": 90, "adaptive": False},
}
FPS_CHOICES = ["Default", "5", "10", "15", "20", "25", "30"]
WIDTH_CHOICES = ["Default", "1280", "1600", "1920", "2560", "Original"]

DEFAULT_CONFIG = {
    "last_host": "",
    "port": DEFAULT_PORT,
    "discovery_port": DISCOVERY_PORT,
    "quality": "Automatic",
    "fps": "Default",
    "max_width": "Default",
}


# =============================================================================
# server HTTP locale: pagina, stile LBS e frame
# =============================================================================

class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "LBSLabsRemote"
    viewer: "ViewerApp" = None   # impostato da LocalServer

    def log_message(self, fmt, *args):   # niente log per ogni richiesta
        pass

    def _send(self, code: int, body: bytes = b"", ctype: str = "text/plain", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        parts = urlsplit(self.path)
        prefix = f"/{self.viewer.token}/"
        if not parts.path.startswith(prefix):
            return self._send(404)
        rel = parts.path[len(prefix):]
        try:
            if rel == "frame":
                return self._frame(parse_qs(parts.query))
            if rel in ("", "index.html"):
                return self._file(UI_DIR / "index.html")
            if rel.startswith("lbs/"):
                sub = rel[4:]
                if sub.split("/", 1)[0] not in STYLE_PARTS:
                    return self._send(404)
                return self._file(STYLE_DIR / sub, root=STYLE_DIR)
            return self._file(UI_DIR / rel, root=UI_DIR)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _file(self, path: Path, root: Path = UI_DIR):
        try:
            path = path.resolve()
            path.relative_to(root.resolve())          # niente percorsi fuori dalla cartella
            data = path.read_bytes()
        except (ValueError, OSError):
            return self._send(404)
        ctype = {".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml",
                 ".ttf": "font/ttf", ".html": "text/html; charset=utf-8"}.get(
            path.suffix.lower(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self._send(200, data, ctype)

    def _frame(self, query):
        """Long polling: risponde appena c'è un frame più recente di `after` (o 204 dopo 1 s)."""
        session = self.viewer.session
        if session is None:
            return self._send(404)
        try:
            after = int(query.get("after", ["0"])[0])
        except ValueError:
            after = 0
        if after > session.frame_seq:     # sessione nuova: si riparte da zero
            after = 0
        seq, jpeg = session.wait_frame(after, timeout=1.0)
        if jpeg is None or seq <= after or session is not self.viewer.session:
            return self._send(204)
        self._send(200, jpeg, "image/jpeg", {"X-Seq": str(seq)})


class LocalServer:
    def __init__(self, viewer: "ViewerApp"):
        handler = type("Handler", (_Handler,), {"viewer": viewer})
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, name="local-http", daemon=True).start()

    def stop(self):
        self.httpd.shutdown()


# =============================================================================
# comandi chiamati dall'interfaccia (window.pywebview.api.*)
# =============================================================================

class Api:
    def __init__(self, viewer: "ViewerApp"):
        self._viewer = viewer

    def get_state(self):
        return self._viewer.state()

    def connect(self, text, settings=None):
        return self._viewer.connect(str(text or ""), settings or {})

    def disconnect(self):
        self._viewer.disconnect()

    def send_input(self, events):
        session = self._viewer.session
        if session is not None and isinstance(events, list):
            for ev in events:
                if isinstance(ev, dict):
                    session.send_input(ev)

    def get_servers(self):
        return self._viewer.servers()

    def set_fullscreen(self, on):
        self._viewer.set_fullscreen(bool(on))

    def set_capture(self, active):
        self._viewer.capture_active = bool(active)

    # --- permessi di macOS (procedura guidata nella schermata iniziale) ---
    def get_permissions(self):
        return pu.mac_permission_status()

    def request_permission(self, kind):
        """Mostra la richiesta di sistema e apre la pagina giusta di Impostazioni di Sistema."""
        if kind == "screen":
            pu.mac_request_screen_recording()
            pu.mac_open_privacy_pane("ScreenCapture")
        elif kind == "accessibility":
            pu.mac_has_accessibility(prompt=True)
            pu.mac_open_privacy_pane("Accessibility")
        elif kind == "local_network":
            pu.mac_trigger_local_network()
            pu.mac_open_privacy_pane("LocalNetwork")

    def restart_app(self):
        return pu.mac_relaunch()


# =============================================================================
# applicazione
# =============================================================================

class ViewerApp:
    def __init__(self, initial_host: str | None = None, notice: str | None = None,
                 agent_port: int | None = None):
        self.initial_host = initial_host
        self.notice = notice
        if agent_port is None:   # porta dell'agente di questo computer (server.json)
            try:
                agent_port = int(load_json("server.json", {}).get("port") or DEFAULT_PORT)
            except (TypeError, ValueError):
                agent_port = DEFAULT_PORT
        self.agent_port = agent_port
        self.token = secrets.token_urlsafe(12)
        self.session: NetSession | None = None
        self.capture_active = False
        self.fullscreen = False
        self.window = None
        self.mac_cmd_monitor = False
        self._local_ips: set[str] = set()
        self._local_ips_at = -1e9
        self.agent_state = {"state": "checking"}

        self.cfg = load_json(CLIENT_CONFIG, DEFAULT_CONFIG)
        if str(self.cfg.get("port")) == str(LEGACY_DEFAULT_PORT):   # aggiornamento dalla 1.0.0
            self.cfg["port"] = DEFAULT_PORT
        if self.cfg.get("quality") not in QUALITY_PRESETS:
            self.cfg["quality"] = "Automatic"
        if str(self.cfg.get("fps")) not in FPS_CHOICES:
            self.cfg["fps"] = "Default"
        if str(self.cfg.get("max_width")) not in WIDTH_CHOICES:
            self.cfg["max_width"] = "Default"

        try:
            dport = int(self.cfg.get("discovery_port") or DISCOVERY_PORT)
        except (TypeError, ValueError):
            dport = DISCOVERY_PORT
        self.discovery = DiscoveryListener(dport)
        self.discovery.start()
        self.server = LocalServer(self)

    # --- verso l'interfaccia ---
    def push(self, event: dict) -> None:
        win = self.window
        if win is None:
            return
        try:
            win.evaluate_js(f"window.LBS && window.LBS.onEvent({json.dumps(event)})")
        except Exception:
            log.debug("evento non consegnato all'interfaccia", exc_info=True)

    def state(self) -> dict:
        s = self.session
        return {
            "version": __version__,
            "platform": sys.platform,
            "last_host": self.cfg.get("last_host") or "",
            "settings": {k: self.cfg.get(k) for k in ("port", "quality", "fps", "max_width")},
            "notice": self.notice and ("This computer cannot be controlled by other computers: "
                                       + self.notice),
            "agent": self.agent_state,
            "mac_cmd_monitor": self.mac_cmd_monitor,
            "permissions": pu.mac_permission_status(),
            "connect_now": self.initial_host or "",
            "session": ({"host": s.host, "hello": s.hello, "state": "connected"}
                        if s is not None and s.hello else None),
        }

    def servers(self) -> list[dict]:
        now = time.monotonic()
        if now - self._local_ips_at > 10:
            self._local_ips, self._local_ips_at = set(local_ipv4_addresses()), now
        out = []
        for s in self.discovery.servers():
            # questo stesso computer non si propone: ci si controllerebbe da soli
            if s["ip"] in self._local_ips or s["ip"].startswith("127."):
                continue
            target = s["ip"] if s["port"] == DEFAULT_PORT else f"{s['ip']}:{s['port']}"
            out.append({"name": s["name"], "target": target, "busy": s["busy"]})
        return out

    # --- connessione ---
    def _remote_config(self, settings: dict) -> dict:
        cfg = dict(QUALITY_PRESETS.get(settings.get("quality"), {}))
        fps = str(settings.get("fps", ""))
        if fps.isdigit():
            cfg["fps"] = int(fps)
        width = str(settings.get("max_width", ""))
        if width == "Original":
            cfg["max_width"] = 0
        elif width.isdigit():
            cfg["max_width"] = int(width)
        return cfg

    def connect(self, text: str, settings: dict) -> dict:
        if self.session is not None:
            return {"error": "Already connected."}
        try:
            port = int(settings.get("port") or DEFAULT_PORT)
            if not 0 < port < 65536:
                raise ValueError
        except (TypeError, ValueError):
            return {"error": "The port must be a number between 1 and 65535."}
        try:
            host, port = parse_host_port(text, port)
        except ValueError as exc:
            return {"error": f"Invalid address: {exc}."}
        for key in ("port", "quality", "fps", "max_width"):
            if key in settings:
                self.cfg[key] = settings[key]
        self.cfg["port"] = int(settings.get("port") or DEFAULT_PORT)
        save_json(CLIENT_CONFIG, self.cfg)
        self._connect_text = text
        self.session = NetSession(host, port, self._remote_config(settings), self._on_net_event)
        self.session.start()
        return {"host": host}

    def disconnect(self) -> None:
        session, self.session = self.session, None
        if session:
            session.stop()
        self.capture_active = False
        self._restore_window()

    def _on_net_event(self, session: NetSession, kind: str, data) -> None:
        if session is not self.session:
            return
        if kind == "connected":
            self.cfg["last_host"] = getattr(self, "_connect_text", session.host)
            save_json(CLIENT_CONFIG, self.cfg)
            self._fit_window_to_remote(data or {})
            self.push({"type": "connected", "host": session.host, "hello": data or {}})
        elif kind == "failed":
            self.session = None
            self.push({"type": "failed", "host": session.host, "message": str(data)})
        elif kind == "closed":
            self.session = None
            self.capture_active = False
            self._restore_window()
            self.push({"type": "closed", "message": str(data or "")})
        elif kind in ("reconnecting", "reconnected"):
            self.push({"type": kind})
        elif kind == "notice":
            notice = data if isinstance(data, dict) else {}
            self.push({"type": "notice", "level": notice.get("level", "warning"),
                       "text": str(notice.get("text", ""))})

    # --- finestra ---
    def _screen_size(self) -> tuple[int, int]:
        try:
            import webview
            scr = webview.screens[0]
            return int(scr.width), int(scr.height)
        except Exception:
            return 1440, 900

    def _fit_window_to_remote(self, hello: dict) -> None:
        win = self.window
        if win is None:
            return
        try:
            rw, rh = (int(v) for v in (hello.get("screen") or [16, 9]))
            sw, sh = self._screen_size()
            extra_w, extra_h = 16, 48 + 32 + 16        # margini, barra superiore, barra di stato
            scale = min((sw * 0.88 - extra_w) / rw, (sh * 0.85 - extra_h) / rh, 1.0)
            w, h = int(rw * scale) + extra_w, int(rh * scale) + extra_h
            win.resize(w, h)
            win.move(max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 20))
            name = hello.get("name") or ""
            win.set_title(f"{name} – {APP_NAME}" if name else APP_NAME)
        except Exception:
            log.debug("ridimensionamento finestra fallito", exc_info=True)

    def _restore_window(self) -> None:
        win = self.window
        if win is None:
            return
        try:
            if self.fullscreen:
                win.toggle_fullscreen()
                self.fullscreen = False
            sw, sh = self._screen_size()
            w, h = CONNECT_SIZE
            win.resize(w, h)
            win.move(max(0, (sw - w) // 2), max(0, (sh - h) // 3))
            win.set_title(APP_NAME)
        except Exception:
            log.debug("ripristino finestra fallito", exc_info=True)

    def set_fullscreen(self, on: bool) -> None:
        if on != self.fullscreen and self.window is not None:
            self.fullscreen = on
            try:
                self.window.toggle_fullscreen()
            except Exception:
                log.debug("schermo intero non disponibile", exc_info=True)

    # --- thread di supporto ---
    def _background(self) -> None:
        """Statistiche ogni mezzo secondo e stato dell'agente locale ogni 10 secondi."""
        from .server import probe_agent
        next_probe = 0.0
        while self.window is not None:
            now = time.monotonic()
            if now >= next_probe:
                next_probe = now + 10
                port = self.agent_port or DEFAULT_PORT
                state = probe_agent(port)
                if state == "agent":
                    self.agent_state = {"state": "ready"}
                else:
                    self.agent_state = {"state": "unavailable", "message": self.notice or
                                        "LBS Labs Remote is not running in the background on this "
                                        "computer, so it cannot be controlled from elsewhere."}
                self.push({"type": "agent", **self.agent_state})
            s = self.session
            if s is not None and s.hello:
                w, h = s.frame_size or (0, 0)
                self.push({"type": "stats", "rtt": s.rtt_ms, "fps": s.fps, "width": w, "height": h})
            time.sleep(0.5)

    def _install_mac_cmd_monitor(self) -> None:
        """Mac: le scorciatoie Cmd+tasto andrebbero ai menu dell'app (Cmd+A, Cmd+Q…).
        Mentre si controlla il computer remoto le intercettiamo e le inoltriamo noi."""
        if not pu.IS_MAC:
            return
        try:
            from AppKit import NSEvent  # type: ignore
            from PyObjCTools import AppHelper  # type: ignore
            mask_key_down = 1 << 10                     # NSEventMaskKeyDown
            flag_cmd = 1 << 20                          # NSEventModifierFlagCommand

            def handler(event):
                session = self.session
                if not self.capture_active or session is None:
                    return event
                if not (event.modifierFlags() & flag_cmd):
                    return event
                chars = event.charactersIgnoringModifiers() or ""
                if len(chars) != 1 or not chars.isprintable() or ord(chars) >= 0xF700:
                    return event                        # frecce, tasti funzione…: li gestisce la pagina
                c = chars.lower() if chars.isascii() and chars.isalpha() else chars
                session.send_input({"t": "key", "d": 1, "c": c})
                session.send_input({"t": "key", "d": 0, "c": c})   # macOS non invia il rilascio
                return None                             # non arriva ai menu

            def install():
                self._mac_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                    mask_key_down, handler)
            AppHelper.callAfter(install)
            self.mac_cmd_monitor = True
        except Exception:
            log.warning("intercettazione delle scorciatoie Cmd non disponibile", exc_info=True)

    # --- avvio ---
    def run(self) -> None:
        import webview
        url = f"http://127.0.0.1:{self.server.port}/{self.token}/"
        sw, sh = self._screen_size()
        w, h = CONNECT_SIZE
        self.window = webview.create_window(
            APP_NAME, url, js_api=Api(self), width=w, height=h,
            x=max(0, (sw - w) // 2), y=max(0, (sh - h) // 3),
            min_size=(520, 560),
            background_color=style_token("color", "bg-window", "#26282c"),
            text_select=False,
        )
        self.window.events.closed += self._on_closed

        def started():
            self._install_mac_cmd_monitor()
            threading.Thread(target=self._background, name="viewer-bg", daemon=True).start()

        gui = "edgechromium" if pu.IS_WINDOWS else None   # mai il vecchio motore di Internet Explorer
        webview.start(started, gui=gui, debug=False, private_mode=True)

    def _on_closed(self) -> None:
        self.window = None
        if self.session:
            self.session.stop()
            self.session = None
        self.discovery.stop()


def run(initial_host: str | None = None, notice: str | None = None,
        agent_port: int | None = None) -> None:
    ViewerApp(initial_host, notice, agent_port).run()
