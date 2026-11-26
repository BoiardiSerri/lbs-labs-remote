"""Avvio dell'agente (parte "controllabile" dell'app): logging, impostazioni, tray o console."""

from __future__ import annotations

import logging
import logging.handlers
import sys
import threading

from . import APP_NAME, __version__
from .config import config_dir, load_json, save_json
from .server import AgentServer, ServerSettings

log = logging.getLogger("remotelan")

SERVER_CONFIG = "server.json"


def setup_logging(verbose: bool, filename: str) -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        fh = logging.handlers.RotatingFileHandler(config_dir() / filename, maxBytes=1_000_000,
                                                  backupCount=2, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        pass
    if sys.stderr is not None:  # con pythonw.exe stderr non esiste
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        root.addHandler(sh)


def build_settings(args) -> ServerSettings:
    """Impostazioni dell'agente: ~/.remotelan/server.json + opzioni da riga di comando."""
    stored = load_json(SERVER_CONFIG, ServerSettings().to_dict())
    settings = ServerSettings.from_dict(stored)
    for attr in ("port", "discovery_port", "fps", "quality", "max_width", "monitor"):
        value = getattr(args, attr, None)
        if value is not None:
            setattr(settings, attr, value)
    if getattr(args, "no_adaptive", False):
        settings.adaptive = False
    if getattr(args, "no_discovery", False):
        settings.announce = False
    if getattr(args, "no_notify", False):
        settings.notify_on_connect = False
    if getattr(args, "save", False):
        save_json(SERVER_CONFIG, settings.to_dict())
    return settings


def create_agent(settings: ServerSettings) -> tuple[AgentServer, str | None]:
    """Crea e avvia l'agente. Restituisce (agente, errore di avvio o None)."""
    log.info("%s %s – agente avviato (%s)", APP_NAME, __version__, sys.platform)
    server = AgentServer(settings)
    server.check_permissions(prompt=True)
    try:
        server.start()
        return server, None
    except OSError as exc:
        log.error("%s", exc)
        return server, str(exc)


def run_agent_ui(server: AgentServer, start_error: str | None, use_tray: bool,
                 open_viewer=None) -> None:
    """Blocca finché l'utente non esce: icona nella tray/menu bar, oppure console."""
    if use_tray:
        try:
            from .tray import TrayApp
            tray = TrayApp(server, open_viewer=open_viewer)
        except Exception as exc:
            log.error("icona nella tray non disponibile (%s): continuo in modalità console", exc)
        else:
            tray.run(start_error)
            return
    if start_error:
        sys.exit(1)
    run_console(server)


def run_console(server: AgentServer) -> None:
    def on_status(st):
        if st["client"]:
            log.info("STATO: client connesso da %s", st["client"])
        else:
            log.info("STATO: in ascolto sulla porta %s", st["port"])
    server.on_status = on_status
    stop = threading.Event()
    try:
        while not stop.wait(1.0):
            pass
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
