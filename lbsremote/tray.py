"""Icona nella system tray (Windows) / menu bar (macOS) per l'agente, con pystray."""

from __future__ import annotations

import logging
import sys
import threading

from . import APP_NAME, autostart
from . import platform_utils as pu
from .discovery import local_ipv4_addresses
from .server import AgentServer

log = logging.getLogger(__name__)

# stato -> token di colore del LED (stile LBS: ok verde, accento ambra, warn arancio, error rosso)
STATE_TOKENS = {
    "idle": "ok",            # pronto: gli altri computer possono collegarsi
    "connected": "accent",   # qualcuno sta controllando questo computer
    "warning": "warn",       # permessi macOS mancanti
    "error": "error",        # porta occupata o altro errore
}


def _logo_disc(size: int):
    """Il marchio LBS (disco chiaro con le lettere) ritagliato dall'icona dell'app."""
    from PIL import Image, ImageDraw
    from .resources import STYLE_DIR
    src = Image.open(STYLE_DIR / "logo" / "lbs-icona-app-1024.png").convert("RGBA")
    disc = src.crop((214, 214, 810, 810))            # disco: centro 512, raggio ~298 (lbs-icona-app.svg)
    mask = Image.new("L", disc.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, disc.size[0] - 1, disc.size[1] - 1), fill=255)
    disc.putalpha(mask)
    return disc.resize((size, size), Image.LANCZOS)


def make_icon_image(state: str):
    """Icona 64×64: marchio LBS + LED di stato in basso a destra (alone al 27,5 % come i chip)."""
    from PIL import Image, ImageDraw
    from .resources import token_rgb
    size, ss = 64, 4                                  # disegno a 4× poi riduzione: bordi lisci
    big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    try:
        big.alpha_composite(_logo_disc(56 * ss), (0, 0))
    except Exception:                                 # risorsa mancante: disco semplice
        ImageDraw.Draw(big).ellipse((0, 0, 56 * ss, 56 * ss), fill=token_rgb("text") + (255,))
    d = ImageDraw.Draw(big)
    color = token_rgb(STATE_TOKENS.get(state, "ok"))
    cx, cy = 50 * ss, 50 * ss
    d.ellipse((cx - 14 * ss, cy - 14 * ss, cx + 14 * ss, cy + 14 * ss), fill=token_rgb("bg-0") + (255,))
    d.ellipse((cx - 12 * ss, cy - 12 * ss, cx + 12 * ss, cy + 12 * ss), fill=color + (70,))
    d.ellipse((cx - 8 * ss, cy - 8 * ss, cx + 8 * ss, cy + 8 * ss), fill=color + (255,))
    return big.resize((size, size), Image.LANCZOS)


def _on_main_thread(fn) -> None:
    """Su macOS AppKit va toccato solo dal thread principale."""
    if sys.platform == "darwin":
        try:
            from PyObjCTools import AppHelper  # type: ignore
            AppHelper.callAfter(fn)
            return
        except Exception:
            pass
    fn()


class TrayApp:
    def __init__(self, server: AgentServer, open_viewer=None):
        import pystray
        self.pystray = pystray
        self.server = server
        self.open_viewer = open_viewer
        self._last_client = None
        self.icon = pystray.Icon("lbsremote", make_icon_image("idle"), APP_NAME,
                                 self._build_menu())
        server.on_status = self._on_status

    # --- menu ---
    def _status_text(self) -> str:
        st = self.server.status()
        if st["error"]:
            return "⚠ " + st["error"][:80]
        if st["client"]:
            return f"Controlled from {st['client']}"
        return f"Ready, listening on port {st['port']}"

    def _ip_text(self) -> str:
        ips = local_ipv4_addresses()
        return "IP: " + (", ".join(ips) if ips else "no network")

    def _build_menu(self):
        Item, Menu = self.pystray.MenuItem, self.pystray.Menu
        noop = lambda icon, item: None  # noqa: E731
        missing = lambda word: (lambda item: any(word in p for p in self.server.permission_problems))  # noqa: E731
        items = []
        if self.open_viewer:
            # default=True: doppio clic sull'icona (Windows) apre la finestra di connessione
            items += [Item("Connect to a remote computer…", lambda icon, item: self.open_viewer(),
                           default=True), Menu.SEPARATOR]
        items += [
            Item(lambda item: "This computer: " + self._status_text()
                 if not self.server.status()["error"] else self._status_text(), noop, enabled=False),
            Item(lambda item: self._ip_text(), noop, enabled=False),
        ]
        if pu.IS_MAC:
            items += [
                Item("⚠ Grant \"Screen Recording\" permission…",
                     lambda icon, item: pu.mac_open_privacy_pane("ScreenCapture"),
                     visible=missing("Screen Recording")),
                Item("⚠ Grant \"Accessibility\" permission…",
                     lambda icon, item: pu.mac_open_privacy_pane("Accessibility"),
                     visible=missing("Accessibility")),
                Item("⚠ Reset permissions…", self._reset_permissions,
                     visible=lambda item: bool(self.server.permission_problems)),
            ]
        items.append(Menu.SEPARATOR)
        if autostart.is_supported():
            items.append(Item("Start at login", self._toggle_autostart,
                              checked=lambda item: autostart.is_enabled()))
        items.append(Item("Quit", self._quit))
        return Menu(*items)

    def _toggle_autostart(self, icon, item) -> None:
        try:
            msg = autostart.disable() if autostart.is_enabled() else autostart.enable()
            log.info(msg)
        except Exception as exc:
            log.exception("modifica avvio automatico fallita")
            self.notify(f"Unable to change the start-at-login setting: {exc}")
        self._refresh()

    def _reset_permissions(self, icon, item) -> None:
        def work():
            pu.mac_reset_permissions()
            self.notify("Permissions reset. Allow Screen Recording and Accessibility when macOS asks, "
                        "then choose Quit from this menu and open LBS Labs Remote again.")
            pu.mac_open_privacy_pane("ScreenCapture")
        threading.Thread(target=work, daemon=True).start()

    def _quit(self, icon, item) -> None:
        self.server.stop()
        icon.stop()

    # --- aggiornamenti ---
    def _state(self) -> str:
        st = self.server.status()
        if st["error"]:
            return "error"
        if st["client"]:
            return "connected"
        if st["permission_problems"]:
            return "warning"
        return "idle"

    def _refresh(self) -> None:
        def apply():
            try:
                self.icon.icon = make_icon_image(self._state())
                self.icon.title = f"{APP_NAME} – {self._status_text()}"
                self.icon.update_menu()
            except Exception:
                log.debug("aggiornamento icona fallito", exc_info=True)
        _on_main_thread(apply)

    def _on_status(self, status: dict) -> None:
        client = status.get("client")
        if client and client != self._last_client and self.server.settings.notify_on_connect:
            # Solo trasparenza verso chi è davanti al PC: non è un controllo di accesso.
            self.notify(f"Remote control session started from {client}")
        elif not client and self._last_client and self.server.settings.notify_on_connect:
            self.notify("Remote control session ended")
        self._last_client = client
        self._refresh()

    def notify(self, text: str) -> None:
        if pu.IS_MAC:
            pu.mac_notify(APP_NAME, text)
            return
        if getattr(self.icon, "HAS_NOTIFICATION", False):
            def show():
                try:
                    self.icon.notify(text, APP_NAME)
                except Exception:
                    log.debug("notifica non mostrata", exc_info=True)
            threading.Thread(target=show, daemon=True).start()

    # --- avvio ---
    def run(self, start_error: str | None = None) -> None:
        if pu.IS_MAC:
            try:  # niente icona nel Dock: solo menu bar
                import AppKit  # type: ignore
                AppKit.NSApplication.sharedApplication().setActivationPolicy_(
                    AppKit.NSApplicationActivationPolicyAccessory)
            except Exception:
                pass

        def setup(icon):
            icon.visible = True
            self._refresh()
            if pu.IS_MAC and self.open_viewer:
                _on_main_thread(lambda: _install_mac_reopen_handler(self.open_viewer))
            if start_error:
                self.notify(start_error)
            elif self.server.permission_problems:
                self.notify("macOS permissions missing: open the menu bar icon to grant them.")

        self.icon.icon = make_icon_image(self._state())
        self.icon.run(setup=setup)


_reopen_handler = None


def _install_mac_reopen_handler(callback) -> None:
    """Mac: doppio clic sull'app (Finder, Launchpad, Dock) mentre è già attiva in background
    = apri la finestra di connessione. macOS invia l'evento "reopen" all'app già in esecuzione."""
    global _reopen_handler
    try:
        import struct

        import objc  # type: ignore
        from Foundation import NSAppleEventManager, NSObject  # type: ignore

        class LBSReopenHandler(NSObject):
            @objc.typedSelector(b"v@:@@")
            def handleReopen_withReply_(self, event, reply):
                try:
                    callback()
                except Exception:
                    log.exception("apertura della finestra fallita")

        def four_cc(code: bytes) -> int:
            return struct.unpack(">I", code)[0]

        _reopen_handler = LBSReopenHandler.alloc().init()
        NSAppleEventManager.sharedAppleEventManager().setEventHandler_andSelector_forEventClass_andEventID_(
            _reopen_handler, b"handleReopen:withReply:", four_cc(b"aevt"), four_cc(b"rapp"))
    except Exception:
        log.warning("gestione della riapertura dell'app non disponibile", exc_info=True)
