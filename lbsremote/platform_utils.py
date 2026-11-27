"""Funzioni specifiche di piattaforma (DPI su Windows, permessi e notifiche su macOS).

Tutte le funzioni sono sicure da chiamare su qualunque sistema operativo.
"""

from __future__ import annotations

import ctypes
import logging
import os
import shlex
import signal
import socket
import subprocess
import sys

log = logging.getLogger(__name__)

IS_MAC = sys.platform == "darwin"
MAC_BUNDLE_ID = "com.lbslabs.remote"       # identificativo dell'app (packaging/lbs_labs_remote.spec)
IS_WINDOWS = sys.platform.startswith("win")


# --- Windows -----------------------------------------------------------------

def enable_windows_dpi_awareness(per_monitor: bool = True) -> None:
    """Rende il processo "DPI aware": coordinate e catture in pixel fisici.

    Senza questa chiamata, con lo scaling di Windows (125%, 150%...) mss,
    pynput e tkinter userebbero sistemi di coordinate diversi fra loro.
    Va chiamata il prima possibile, prima di creare finestre o catture.
    """
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2 if per_monitor else 1)
        return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def windows_desktop_locked() -> bool | None:
    """True se il computer è bloccato o mostra una richiesta di sicurezza (desktop protetto): in questi
    casi nessun programma può catturare lo schermo. None se non verificabile (non Windows)."""
    if not IS_WINDOWS:
        return None
    try:
        user32 = ctypes.windll.user32
        h = user32.OpenInputDesktop(0, False, 0x0100)     # DESKTOP_SWITCHDESKTOP
        if not h:
            return True
        user32.CloseDesktop(h)
        return False
    except (AttributeError, OSError):
        return None


def windows_capture_diagnostics() -> str:
    """Dati utili a capire perché la cattura fallisce (finiscono in agent.log)."""
    if not IS_WINDOWS:
        return ""
    try:
        k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
        sid = ctypes.c_uint32(0)
        k32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid))
        return (f"sessione={sid.value} sessione_console={k32.WTSGetActiveConsoleSessionId()} "
                f"remota={bool(u32.GetSystemMetrics(0x1000))} bloccato={windows_desktop_locked()} "
                f"schermo={u32.GetSystemMetrics(0)}x{u32.GetSystemMetrics(1)}")
    except Exception as exc:  # noqa: BLE001
        return f"diagnostica non disponibile: {exc}"


def capture_failure_text(exc: Exception) -> str:
    """Spiega a chi controlla perché lo schermo non arriva, con parole semplici."""
    if windows_desktop_locked():
        return ("This computer is locked or showing a secure Windows prompt, so its screen cannot be "
                "captured. Unlock it: the picture comes back by itself.")
    if IS_MAC:
        return ("This Mac's screen cannot be captured right now. Check the Screen Recording permission, "
                "or the display may be off. Retrying…")
    return ("The screen of this computer cannot be captured right now: it may be locked or its display "
            f"turned off. Retrying… ({exc})")


# --- macOS: permessi -----------------------------------------------------------

_CG_PATH = "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
_AS_PATH = "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"


def _mac_bool_call(lib_path: str, func_name: str) -> bool | None:
    try:
        lib = ctypes.cdll.LoadLibrary(lib_path)
        func = getattr(lib, func_name)
    except (OSError, AttributeError):
        return None
    func.restype = ctypes.c_bool
    func.argtypes = []
    try:
        return bool(func())
    except Exception:
        return None


def mac_has_screen_recording() -> bool | None:
    """True/False se il permesso "Registrazione schermo" è concesso; None se non verificabile."""
    if not IS_MAC:
        return True
    return _mac_bool_call(_CG_PATH, "CGPreflightScreenCaptureAccess")


def mac_request_screen_recording() -> None:
    """Fa comparire il processo nell'elenco "Registrazione schermo" (e l'avviso di sistema)."""
    if IS_MAC:
        _mac_bool_call(_CG_PATH, "CGRequestScreenCaptureAccess")


def mac_has_accessibility(prompt: bool = False) -> bool | None:
    """True/False se il permesso "Accessibilità" è concesso; None se non verificabile.

    Con prompt=True macOS mostra la richiesta di sistema e aggiunge il processo
    all'elenco in Impostazioni di Sistema (va comunque abilitato a mano).
    """
    if not IS_MAC:
        return True
    if prompt:
        try:
            from ApplicationServices import (  # type: ignore  # pyobjc, installato con pynput
                AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt)
            return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))
        except Exception:
            log.debug("AXIsProcessTrustedWithOptions non disponibile", exc_info=True)
    return _mac_bool_call(_AS_PATH, "AXIsProcessTrusted")


def mac_open_privacy_pane(pane: str) -> None:
    """pane: "ScreenCapture", "Accessibility" oppure "LocalNetwork"."""
    if not IS_MAC:
        return
    url = f"x-apple.systempreferences:com.apple.preference.security?Privacy_{pane}"
    try:
        subprocess.Popen(["open", url])
    except OSError:
        log.warning("impossibile aprire Impostazioni di Sistema")


def mac_permission_status() -> dict:
    """Stato dei permessi per la procedura guidata dell'interfaccia (True/False, None se non verificabile)."""
    if not IS_MAC:
        return {"supported": False}
    return {"supported": True, "screen": mac_has_screen_recording(), "accessibility": mac_has_accessibility()}


def mac_trigger_local_network() -> None:
    """Fa comparire la richiesta "Rete locale" di macOS 15+, che scatta alla prima comunicazione in LAN."""
    if not IS_MAC:
        return
    targets = {"255.255.255.255"}
    try:
        from .discovery import local_ipv4_addresses
        for ip in local_ipv4_addresses():
            targets.add(".".join(ip.split(".")[:3] + ["255"]))
    except Exception:
        log.debug("indirizzi locali non disponibili", exc_info=True)
    for dest in targets:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(b"lbs-local-network", (dest, 5901))
        except OSError:
            pass


def mac_app_bundle() -> str | None:
    """Percorso di "LBS Labs Remote.app" quando l'app gira impacchettata."""
    exe = sys.executable
    i = exe.find(".app/Contents/MacOS/")
    return exe[:i + 4] if IS_MAC and getattr(sys, "frozen", False) and i > 0 else None


def mac_relaunch() -> bool:
    """Chiude tutti i processi dell'app (agente e finestre) e la riapre: serve dopo aver concesso
    "Registrazione schermo", che macOS applica solo ai processi avviati dopo."""
    app = mac_app_bundle()
    if app is None:
        return False
    subprocess.Popen(["/bin/sh", "-c", f"sleep 2; /usr/bin/open -n {shlex.quote(app)}"],
                     start_new_session=True, close_fds=True)
    me = os.getpid()
    try:
        out = subprocess.run(["/usr/bin/pgrep", "-x", "LBSLabsRemote"], capture_output=True,
                             text=True, timeout=5).stdout.split()
        for pid in out:
            if pid.isdigit() and int(pid) != me:
                os.kill(int(pid), signal.SIGTERM)
    except (OSError, subprocess.SubprocessError):
        log.debug("chiusura degli altri processi fallita", exc_info=True)
    os._exit(0)


def permission_problems(prompt: bool = False) -> list[str]:
    """Elenco (in italiano) dei permessi macOS mancanti. Vuoto su Windows/Linux."""
    if not IS_MAC:
        return []
    problems = []
    if mac_has_screen_recording() is False:
        if prompt:
            mac_request_screen_recording()
        problems.append(
            "\"Screen Recording\" permission missing on the remote Mac: the screen will look "
            "empty or show only the wallpaper. Grant it in System Settings > Privacy & "
            "Security > Screen Recording, then quit and reopen LBS Labs Remote. If it already shows "
            "ON (it can go stale after an update), use the menu bar icon > Reset permissions.")
    if mac_has_accessibility(prompt=prompt) is False:
        problems.append(
            "\"Accessibility\" permission missing on the remote Mac: mouse and keyboard "
            "will have no effect. Grant it in System Settings > Privacy & Security > "
            "Accessibility, then quit and reopen LBS Labs Remote. If it already shows ON (it can go "
            "stale after an update), use the menu bar icon > Reset permissions.")
    return problems


def mac_reset_permissions() -> None:
    """Cancella i permessi "Registrazione schermo" e "Accessibilità" di questa app e li richiede di nuovo.

    Serve quando l'interruttore in Impostazioni di Sistema è attivo ma macOS non lo considera più
    valido: succede dopo un aggiornamento dell'app con una firma diversa.
    """
    if not IS_MAC:
        return
    for service in ("ScreenCapture", "Accessibility"):
        try:
            subprocess.run(["/usr/bin/tccutil", "reset", service, MAC_BUNDLE_ID],
                           check=False, timeout=20, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            log.warning("tccutil reset %s fallito", service, exc_info=True)
    mac_request_screen_recording()
    mac_has_accessibility(prompt=True)
    mac_trigger_local_network()


# --- notifiche ---------------------------------------------------------------

def mac_notify(title: str, text: str) -> None:
    if not IS_MAC:
        return

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    try:
        subprocess.Popen(["osascript", "-e",
                          f'display notification "{esc(text)}" with title "{esc(title)}"'])
    except OSError:
        pass
