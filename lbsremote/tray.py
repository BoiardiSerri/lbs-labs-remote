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

COLORS = {
    "idle": (59, 130, 246),       # blu: in ascolto
    "connected": (34, 197, 94),   # verde: client connesso
    "warning": (245, 158, 11),    # arancio: permessi mancanti
    "error": (220, 38, 38),       # rosso: porta occupata o altro errore
}


def make_icon_image(state: str):
    from PIL import Image, ImageDraw
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = COLORS.get(state, COLORS["idle"]) + (255,)
    # monitor stilizzato
    d.rounded_rectangle((4, 8, 60, 46), radius=6, fill=color)
    d.rectangle((10, 14, 54, 40), fill=(255, 255, 255, 235))
    d.rectangle((28, 46, 36, 54), fill=color)
    d.rounded_rectangle((16, 53, 48, 59), radius=3, fill=color)
    if state == "connected":
        d.ellipse((24, 19, 40, 35), fill=color)
    return img


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
            return f"Client connesso da {st['client']}"
        return f"In ascolto sulla porta {st['port']}"

    def _ip_text(self) -> str:
        ips = local_ipv4_addresses()
        return "IP: " + (", ".join(ips) if ips else "nessuna rete")

    def _build_menu(self):
        Item, Menu = self.pystray.MenuItem, self.pystray.Menu
        noop = lambda icon, item: None  # noqa: E731
        missing = lambda word: (lambda item: any(word in p for p in self.server.permission_problems))  # noqa: E731
        items = []
        if self.open_viewer:
            # default=True: doppio clic sull'icona (Windows) apre la finestra di connessione
            items += [Item("Connetti a un PC remoto…", lambda icon, item: self.open_viewer(),
                           default=True), Menu.SEPARATOR]
        items += [
            Item(lambda item: "Questo PC: " + self._status_text().lower()
                 if not self.server.status()["error"] else self._status_text(), noop, enabled=False),
            Item(lambda item: self._ip_text(), noop, enabled=False),
        ]
        if pu.IS_MAC:
            items += [
                Item("⚠ Concedi \"Registrazione schermo\"…",
                     lambda icon, item: pu.mac_open_privacy_pane("ScreenCapture"),
                     visible=missing("Registrazione schermo")),
                Item("⚠ Concedi \"Accessibilità\"…",
                     lambda icon, item: pu.mac_open_privacy_pane("Accessibility"),
                     visible=missing("Accessibilità")),
            ]
        items.append(Menu.SEPARATOR)
        if autostart.is_supported():
            items.append(Item("Avvia al login", self._toggle_autostart,
                              checked=lambda item: autostart.is_enabled()))
        items.append(Item("Esci", self._quit))
        return Menu(*items)

    def _toggle_autostart(self, icon, item) -> None:
        try:
            msg = autostart.disable() if autostart.is_enabled() else autostart.enable()
            log.info(msg)
        except Exception as exc:
            log.exception("modifica avvio automatico fallita")
            self.notify(f"Impossibile modificare l'avvio automatico: {exc}")
        self._refresh()

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
            self.notify(f"Sessione di controllo remoto avviata da {client}")
        elif not client and self._last_client and self.server.settings.notify_on_connect:
            self.notify("Sessione di controllo remoto terminata")
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
            if start_error:
                self.notify(start_error)
            elif self.server.permission_problems:
                self.notify("Permessi macOS mancanti: apri il menu dell'icona per concederli.")

        self.icon.icon = make_icon_image(self._state())
        self.icon.run(setup=setup)
