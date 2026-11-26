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
        description=f"{APP_NAME} – controllo remoto in LAN. La stessa app su tutti i PC: "
                    "rende controllabile questo PC (icona nella tray/menu bar) e permette "
                    "di controllarne altri.")
    p.add_argument("host", nargs="?", help="PC a cui connettersi subito (es. 192.168.1.50 o 192.168.1.50:5900)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--agent", action="store_true",
                      help="solo agente in background (icona), nessuna finestra: per il PC da controllare")
    mode.add_argument("--viewer", action="store_true",
                      help="solo finestra di connessione: questo PC NON diventa controllabile")
    mode.add_argument("--install-autostart", action="store_true", help="avvia l'agente al login ed esci")
    mode.add_argument("--uninstall-autostart", action="store_true", help="rimuovi l'avvio al login ed esci")

    g = p.add_argument_group("opzioni dell'agente")
    g.add_argument("--port", type=int, help="porta TCP di ascolto (predefinita 5900)")
    g.add_argument("--discovery-port", type=int, help="porta UDP degli annunci (predefinita 5901)")
    g.add_argument("--fps", type=int, help="frame al secondo (predefinito 12)")
    g.add_argument("--quality", type=int, help="qualità JPEG 10-95 (predefinita 50)")
    g.add_argument("--max-width", type=int, help="larghezza massima dei frame in pixel, 0 = originale")
    g.add_argument("--monitor", type=int, help="schermo da catturare (1 = principale)")
    g.add_argument("--no-adaptive", action="store_true", help="disattiva qualità adattiva")
    g.add_argument("--no-discovery", action="store_true", help="non annunciare il PC in rete")
    g.add_argument("--no-notify", action="store_true", help="nessuna notifica alla connessione")
    g.add_argument("--no-tray", action="store_true", help="niente icona: agente in console (Ctrl+C per uscire)")
    g.add_argument("--save", action="store_true", help="salva queste opzioni in ~/.lbslabs-remote/server.json")
    p.add_argument("-v", "--verbose", action="store_true", help="log dettagliato")
    p.add_argument("--selftest", metavar="FILE", help=argparse.SUPPRESS)
    # parse_known_args: macOS può passare argomenti propri (es. -psn_0_123) alle app
    args, _unknown = p.parse_known_args(argv)
    return args


def viewer_command(host: str | None = None) -> list[str]:
    if getattr(sys, "frozen", False):          # eseguibile impacchettato (es. PyInstaller)
        cmd = [sys.executable, "--viewer"]
    else:
        cmd = [sys.executable, str(APP_SCRIPT), "--viewer"]
    if host:
        cmd.append(host)
    return cmd


def spawn_viewer(host: str | None = None) -> None:
    """Apre la finestra "Connetti" in un nuovo processo."""
    try:
        cwd = None if getattr(sys, "frozen", False) else str(APP_SCRIPT.parent)
        subprocess.Popen(viewer_command(host), cwd=cwd, close_fds=True)
    except OSError:
        log.exception("impossibile aprire la finestra di connessione")


def run_viewer(host: str | None) -> None:
    from .client import ClientApp
    ClientApp(host).run()


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

    def tk_window():
        import tkinter
        root = tkinter.Tk()
        root.update()
        root.destroy()

    check("tkinter", tk_window)
    check("PIL.ImageTk", lambda: __import__("PIL.ImageTk"))
    check("mss", grab)
    check("pynput", lambda: (__import__("pynput.keyboard"), __import__("pynput.mouse")))
    check("pystray", lambda: __import__("pystray").Icon)
    if pu.IS_MAC:
        check("Quartz", lambda: __import__("Quartz").CGEventCreateMouseEvent)
        check("AppKit", lambda: __import__("AppKit").NSApplication)
        check("PyObjCTools.AppHelper", lambda: __import__("PyObjCTools.AppHelper"))
    check("lbsremote.client", lambda: __import__("lbsremote.client"))
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


def _show_message(title: str, text: str) -> None:
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showwarning(title, text)
        root.destroy()
    except Exception:
        log.warning("%s: %s", title, text)


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.selftest:
        selftest(args.selftest)
        return
    from .server_main import build_settings, create_agent, run_agent_ui, setup_logging

    if _mac_wrong_location():
        _show_message(APP_NAME,
                      "Per funzionare correttamente LBS Labs Remote va copiata nella cartella "
                      "Applicazioni.\n\nTrascina l'icona di LBS Labs Remote sulla cartella "
                      "\"Applicazioni\" nella finestra del disco, poi aprila da lì.")
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
        run_viewer(args.host)
        return

    setup_logging(args.verbose, "agent.log")
    pu.enable_windows_dpi_awareness()          # prima di qualunque cattura dello schermo
    server, start_error = create_agent(build_settings(args))

    if not args.agent:
        if start_error and server.port_in_use:
            # Probabilmente l'agente è già attivo (es. avviato al login):
            # basta aprire la finestra di connessione.
            log.info("agente già attivo: apro solo la finestra di connessione")
            run_viewer(args.host)
            return
        spawn_viewer(args.host)

    run_agent_ui(server, start_error, use_tray=not args.no_tray, open_viewer=spawn_viewer)
