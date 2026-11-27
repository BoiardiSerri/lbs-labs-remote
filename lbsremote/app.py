"""Punto di ingresso unico di LBS Labs Remote: la stessa app gira su tutti i PC.

    python lbs_labs_remote.py              agente (icona tray/menu bar) + finestra "Connetti"
    python lbs_labs_remote.py 10.0.0.5     come sopra, connettendosi subito a 10.0.0.5
    python lbs_labs_remote.py --agent      solo agente, nessuna finestra (avvio automatico, PC demo)
    python lbs_labs_remote.py --viewer     solo finestra "Connetti", senza rendere controllabile il PC

La finestra "Connetti" (tkinter) gira in un processo figlio della stessa app:
su macOS sia tkinter sia l'icona nella menu bar pretendono il thread principale.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from . import APP_NAME, autostart
from . import platform_utils as pu

log = logging.getLogger("lbsremote")

APP_SCRIPT = Path(__file__).resolve().parent.parent / "lbs_labs_remote.py"


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="lbs_labs_remote.py",
        description=f"{APP_NAME} – LAN remote control. The same app on every computer: "
                    "makes this computer controllable (tray / menu bar icon) and lets you "
                    "control others.")
    p.add_argument("host", nargs="?", help="computer to connect to right away (e.g. 192.168.1.50 or 192.168.1.50:5970)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--agent", action="store_true",
                      help="background agent only (icon), no window: for the computer to be controlled")
    mode.add_argument("--viewer", action="store_true",
                      help="connection window only: this computer does NOT become controllable")
    mode.add_argument("--quit", action="store_true",
                      help="quit the running agent and every window of this app, then exit (use it before updating)")
    mode.add_argument("--install-autostart", action="store_true", help="start the agent at login, then exit")
    mode.add_argument("--uninstall-autostart", action="store_true", help="remove start at login, then exit")

    g = p.add_argument_group("agent options")
    g.add_argument("--port", type=int, help="TCP listening port (default 5970)")
    g.add_argument("--discovery-port", type=int, help="UDP discovery port (default 5901)")
    g.add_argument("--fps", type=int, help="frames per second (default 12)")
    g.add_argument("--quality", type=int, help="JPEG quality 10-95 (default 50)")
    g.add_argument("--max-width", type=int, help="maximum frame width in pixels, 0 = original")
    g.add_argument("--monitor", type=int, help="screen to capture (1 = main)")
    g.add_argument("--no-adaptive", action="store_true", help="disable adaptive quality")
    g.add_argument("--no-discovery", action="store_true", help="do not announce this computer on the network")
    g.add_argument("--no-notify", action="store_true", help="no notification when someone connects")
    g.add_argument("--no-tray", action="store_true", help="no icon: run the agent in the console (Ctrl+C to quit)")
    g.add_argument("--save", action="store_true", help="save these options to ~/.lbslabs-remote/server.json")
    p.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    p.add_argument("--selftest", metavar="FILE", help=argparse.SUPPRESS)
    p.add_argument("--notice", help=argparse.SUPPRESS)   # avviso da mostrare nella finestra
    # parse_known_args: macOS può passare argomenti propri (es. -psn_0_123) alle app
    args, _unknown = p.parse_known_args(argv)
    return args


def viewer_command(host: str | None = None, notice: str | None = None) -> list[str]:
    if getattr(sys, "frozen", False):          # eseguibile impacchettato (es. PyInstaller)
        cmd = [sys.executable, "--viewer"]
    else:
        cmd = [sys.executable, str(APP_SCRIPT), "--viewer"]
    if notice:
        cmd += ["--notice", notice]
    if host:
        cmd.append(host)
    return cmd


def spawn_viewer(host: str | None = None, notice: str | None = None) -> None:
    """Apre la finestra "Connetti" in un nuovo processo."""
    try:
        cwd = None if getattr(sys, "frozen", False) else str(APP_SCRIPT.parent)
        subprocess.Popen(viewer_command(host, notice), cwd=cwd, close_fds=True)
    except OSError:
        log.exception("impossibile aprire la finestra di connessione")


def run_viewer(host: str | None, notice: str | None = None) -> None:
    from .viewer import run
    run(host, notice)


def refresh_autostart() -> None:
    """Se l'avvio automatico è attivo, ne riscrive la definizione con le impostazioni correnti
    (es. il percorso dell'app o le regole di riavvio cambiate da un aggiornamento)."""
    if not getattr(sys, "frozen", False) or not autostart.is_supported():
        return
    try:
        autostart.refresh()
    except OSError:
        log.debug("aggiornamento dell'avvio automatico fallito", exc_info=True)


def ensure_autostart_first_run() -> None:
    """App installata: al primo avvio si attiva da sola l'avvio automatico dell'agente,
    così il computer resta sempre controllabile senza fare altro. Se poi l'utente lo
    disattiva dal menu dell'icona, la scelta viene rispettata."""
    if not getattr(sys, "frozen", False) or not autostart.is_supported():
        return
    from .config import load_json, save_json
    state = load_json("app.json", {})
    if state.get("autostart_configured"):
        return
    try:
        if not autostart.is_enabled():
            log.info(autostart.enable())
        state["autostart_configured"] = True
        save_json("app.json", state)
    except OSError:
        log.exception("attivazione dell'avvio automatico fallita")


def selftest(path: str) -> None:
    """Verifica che l'app impacchettata contenga tutto (usata dalla build automatica)."""
    results = []

    def check(name, fn):
        try:
            fn()
            results.append(f"OK   {name}")
        except Exception as exc:  # noqa: BLE001
            results.append(f"FAIL {name}: {exc!r}")

    def grab():
        import mss
        with mss.mss() as sct:
            sct.grab(sct.monitors[1])

    def ui_files():
        from .resources import STYLE_DIR, UI_DIR
        for p in (UI_DIR / "index.html", UI_DIR / "app.js", UI_DIR / "app.css", UI_DIR / "icons.js",
                  STYLE_DIR / "tokens" / "lbs-tokens.css", STYLE_DIR / "css" / "lbs-base.css",
                  STYLE_DIR / "css" / "lbs-components.css", STYLE_DIR / "logo" / "lbs-logo.svg",
                  STYLE_DIR / "font" / "BarlowSemiCondensed-SemiBold.ttf",
                  STYLE_DIR / "icone" / "link.svg"):
            if not p.is_file():
                raise FileNotFoundError(str(p))

    def webview_backend():
        import importlib
        importlib.import_module("webview")
        if pu.IS_MAC:
            importlib.import_module("webview.platforms.cocoa")
        elif pu.IS_WINDOWS:
            importlib.import_module("webview.platforms.edgechromium")

    check("interfaccia (file)", ui_files)
    check("pywebview", webview_backend)
    check("PIL", lambda: __import__("PIL.Image"))
    check("mss", grab)
    check("pynput", lambda: (__import__("pynput.keyboard"), __import__("pynput.mouse")))
    check("pystray", lambda: __import__("pystray").Icon)
    if pu.IS_MAC:
        check("Quartz", lambda: __import__("Quartz").CGEventCreateMouseEvent)
        check("AppKit", lambda: __import__("AppKit").NSApplication)
        check("PyObjCTools.AppHelper", lambda: __import__("PyObjCTools.AppHelper"))
    check("lbsremote.viewer", lambda: __import__("lbsremote.viewer"))
    check("lbsremote.tray", lambda: __import__("lbsremote.tray"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(results) + "\n")
    sys.exit(1 if any(r.startswith("FAIL") for r in results) else 0)


def _mac_wrong_location() -> bool:
    """True se l'app per Mac viene eseguita dal DMG o da una posizione "temporanea"."""
    if not (pu.IS_MAC and getattr(sys, "frozen", False)):
        return False
    path = sys.executable
    return path.startswith("/Volumes/") or "/AppTranslocation/" in path


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.selftest:
        selftest(args.selftest)
        return
    from .server_main import build_settings, create_agent, run_agent_ui, setup_logging

    if _mac_wrong_location():
        setup_logging(args.verbose, "viewer.log")
        run_viewer(None, notice="LBS Labs Remote must be copied to the Applications folder. "
                                "Drag its icon onto the \"Applications\" folder in the disk "
                                "window, then open it from there.")
        return

    if args.quit:
        pu.quit_all_processes()
        return

    if args.install_autostart or args.uninstall_autostart:
        setup_logging(args.verbose, "app.log")
        try:
            print(autostart.enable() if args.install_autostart else autostart.disable())
        except OSError as exc:
            print(f"Errore: {exc}")
            sys.exit(1)
        return

    if args.viewer:
        setup_logging(args.verbose, "viewer.log")
        run_viewer(args.host, args.notice)
        return

    setup_logging(args.verbose, "agent.log")
    ensure_autostart_first_run()
    refresh_autostart()
    pu.enable_windows_dpi_awareness()          # prima di qualunque cattura dello schermo
    server, start_error = create_agent(build_settings(args))

    if not args.agent:
        if start_error and server.port_in_use and server.port_owner == "agent":
            # L'app è già attiva (es. avviata al login): basta aprire la finestra.
            log.info("agente già attivo: apro solo la finestra di connessione")
            run_viewer(args.host)
            return
        # se l'agente non è partito (porta occupata da un altro programma) lo si dice subito
        spawn_viewer(args.host, notice=start_error)

    run_agent_ui(server, start_error, use_tray=not args.no_tray, open_viewer=spawn_viewer)
