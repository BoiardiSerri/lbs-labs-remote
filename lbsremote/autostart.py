"""Avvio automatico dell'agente al login dell'utente (Windows e macOS).

Windows: valore nel registro HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
         (eseguito con pythonw.exe, quindi senza finestra console).
macOS:   LaunchAgent ~/Library/LaunchAgents/com.lbslabs.remote.agent.plist
         (riavvia l'agente se termina in modo anomalo).
"""

from __future__ import annotations

import logging
import plistlib
import sys
from pathlib import Path

from .config import config_dir

log = logging.getLogger(__name__)

WIN_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WIN_VALUE_NAME = "LBS Labs Remote"
MAC_LABEL = "com.lbslabs.remote.agent"
MAC_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{MAC_LABEL}.plist"


def is_supported() -> bool:
    return sys.platform == "darwin" or sys.platform.startswith("win")


def _program_arguments() -> list[str]:
    """Comando che avvia l'agente: python lbs_labs_remote.py --agent (o l'eseguibile impacchettato)."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--agent"]
    exe = Path(sys.executable)
    if sys.platform.startswith("win"):
        pythonw = exe.with_name("pythonw.exe")
        if pythonw.exists():
            exe = pythonw
    script = Path(__file__).resolve().parent.parent / "lbs_labs_remote.py"
    return [str(exe), str(script), "--agent"]


def is_enabled() -> bool:
    if sys.platform == "darwin":
        return MAC_PLIST.exists()
    if sys.platform.startswith("win"):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY) as key:
                winreg.QueryValueEx(key, WIN_VALUE_NAME)
            return True
        except OSError:
            return False
    return False


def enable() -> str:
    """Attiva l'avvio automatico. Restituisce una descrizione di quanto fatto."""
    args = _program_arguments()
    if sys.platform == "darwin":
        MAC_PLIST.parent.mkdir(parents=True, exist_ok=True)
        log_path = str(config_dir() / "launchd.log")
        plist = {
            "Label": MAC_LABEL,
            "ProgramArguments": args,
            "RunAtLoad": True,
            "KeepAlive": {"SuccessfulExit": False},   # riavvia solo dopo un crash
            "ProcessType": "Interactive",
            "LimitLoadToSessionType": "Aqua",
            "StandardOutPath": log_path,
            "StandardErrorPath": log_path,
        }
        with open(MAC_PLIST, "wb") as fh:
            plistlib.dump(plist, fh)
        return f"LaunchAgent creato: {MAC_PLIST}"
    if sys.platform.startswith("win"):
        import winreg
        command = " ".join(f'"{a}"' for a in args)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY) as key:
            winreg.SetValueEx(key, WIN_VALUE_NAME, 0, winreg.REG_SZ, command)
        return f"Avvio automatico registrato: {command}"
    raise OSError("avvio automatico supportato solo su Windows e macOS")


def disable() -> str:
    if sys.platform == "darwin":
        if MAC_PLIST.exists():
            MAC_PLIST.unlink()
        return "LaunchAgent rimosso (effettivo dal prossimo login)"
    if sys.platform.startswith("win"):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0,
                                winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, WIN_VALUE_NAME)
        except FileNotFoundError:
            pass
        return "Avvio automatico rimosso"
    raise OSError("avvio automatico supportato solo su Windows e macOS")
