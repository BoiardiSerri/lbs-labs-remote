"""Funzioni specifiche di piattaforma (DPI su Windows, permessi e notifiche su macOS).

Tutte le funzioni sono sicure da chiamare su qualunque sistema operativo.
"""

from __future__ import annotations

import ctypes
import logging
import subprocess
import sys

log = logging.getLogger(__name__)

IS_MAC = sys.platform == "darwin"
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
    """pane: "ScreenCapture" oppure "Accessibility"."""
    if not IS_MAC:
        return
    url = f"x-apple.systempreferences:com.apple.preference.security?Privacy_{pane}"
    try:
        subprocess.Popen(["open", url])
    except OSError:
        log.warning("impossibile aprire Impostazioni di Sistema")


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
            "Security > Screen Recording, then quit and reopen LBS Labs Remote.")
    if mac_has_accessibility(prompt=prompt) is False:
        problems.append(
            "\"Accessibility\" permission missing on the remote Mac: mouse and keyboard "
            "will have no effect. Grant it in System Settings > Privacy & Security > "
            "Accessibility, then quit and reopen LBS Labs Remote.")
    return problems


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
