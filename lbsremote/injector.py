"""Iniezione di mouse e tastiera sul PC controllato (lato server), via pynput.

Su macOS i pulsanti del mouse vengono inviati direttamente con Quartz (già
installato come dipendenza di pynput) per poter impostare il "click count":
senza, macOS non riconosce i doppi click sintetici e i trascinamenti.
"""

from __future__ import annotations

import logging
import sys

from .mainthread import post_to_main, run_on_main

log = logging.getLogger(__name__)


class _QuartzMouse:
    """Mouse per macOS con supporto a doppio click e trascinamento."""

    def __init__(self):
        import Quartz  # type: ignore
        self.Q = Quartz
        self.pressed: list[str] = []
        self.pos = (0.0, 0.0)

    def _post(self, event_type, button, pos, clicks=None):
        Q = self.Q
        ev = Q.CGEventCreateMouseEvent(None, event_type, pos, button)
        if clicks is not None:
            Q.CGEventSetIntegerValueField(ev, Q.kCGMouseEventClickState, int(clicks))
        Q.CGEventPost(Q.kCGHIDEventTap, ev)

    def move(self, x: float, y: float) -> None:
        Q = self.Q
        self.pos = (x, y)
        if "left" in self.pressed:
            self._post(Q.kCGEventLeftMouseDragged, Q.kCGMouseButtonLeft, self.pos)
        elif "right" in self.pressed:
            self._post(Q.kCGEventRightMouseDragged, Q.kCGMouseButtonRight, self.pos)
        elif "middle" in self.pressed:
            self._post(Q.kCGEventOtherMouseDragged, Q.kCGMouseButtonCenter, self.pos)
        else:
            self._post(Q.kCGEventMouseMoved, Q.kCGMouseButtonLeft, self.pos)

    def button(self, name: str, down: bool, clicks: int) -> None:
        Q = self.Q
        table = {
            "left": (Q.kCGEventLeftMouseDown, Q.kCGEventLeftMouseUp, Q.kCGMouseButtonLeft),
            "right": (Q.kCGEventRightMouseDown, Q.kCGEventRightMouseUp, Q.kCGMouseButtonRight),
            "middle": (Q.kCGEventOtherMouseDown, Q.kCGEventOtherMouseUp, Q.kCGMouseButtonCenter),
        }
        ev_down, ev_up, btn = table[name]
        if down:
            if name not in self.pressed:
                self.pressed.append(name)
        elif name in self.pressed:
            self.pressed.remove(name)
        self._post(ev_down if down else ev_up, btn, self.pos, clicks=max(1, clicks))

    def scroll(self, dx: int, dy: int) -> None:
        Q = self.Q
        ev = Q.CGEventCreateScrollWheelEvent(None, Q.kCGScrollEventUnitLine, 2, int(dy), int(dx))
        Q.CGEventPost(Q.kCGHIDEventTap, ev)


class InputInjector:
    """Applica gli eventi INPUT del protocollo al sistema locale."""

    def __init__(self, monitor: dict):
        # monitor: geometria dello schermo catturato, nel sistema di coordinate
        # usato dal mouse (pixel fisici su Windows DPI-aware, punti su macOS).
        from pynput import keyboard, mouse  # import qui: richiede display/permessi

        self.monitor = monitor
        self._Key = keyboard.Key
        self._Button = mouse.Button
        # macOS: la tastiera di pynput va creata e usata dal thread principale (vedi mainthread.py)
        self.kb = run_on_main(keyboard.Controller)
        self.mouse = mouse.Controller()
        self.quartz = None
        if sys.platform == "darwin":
            try:
                self.quartz = _QuartzMouse()
            except Exception:
                log.warning("Quartz non disponibile: uso pynput per il mouse", exc_info=True)
        self.keys_down: dict[str, object] = {}
        self.buttons_down: set[str] = set()

    # --- coordinate ---
    def _abs(self, fx: float, fy: float) -> tuple[float, float]:
        m = self.monitor
        fx = min(max(float(fx), 0.0), 1.0)
        fy = min(max(float(fy), 0.0), 1.0)
        x = m["left"] + fx * (m["width"] - 1)
        y = m["top"] + fy * (m["height"] - 1)
        if self.quartz is None:
            return int(round(x)), int(round(y))
        return x, y

    def _move(self, fx, fy) -> None:
        pos = self._abs(fx, fy)
        if self.quartz:
            self.quartz.move(*pos)
        else:
            self.mouse.position = pos

    # --- tastiera ---
    def _resolve_key(self, ev: dict):
        if "s" in ev:
            name = str(ev["s"])
            key = getattr(self._Key, name, None)
            if key is None and name.endswith(("_l", "_r")):
                key = getattr(self._Key, name[:-2], None)  # es. cmd_l non disponibile
            return key
        char = ev.get("c")
        if isinstance(char, str) and len(char) == 1:
            return char
        return None

    def _kb(self, fn, *args) -> None:
        post_to_main(fn, *args)

    # --- API ---
    def handle(self, ev: dict) -> None:
        kind = ev.get("t")
        if kind == "move":
            self._move(ev["x"], ev["y"])
        elif kind == "btn":
            name = ev.get("b")
            if name not in ("left", "right", "middle"):
                return
            down = bool(ev.get("d"))
            if "x" in ev and "y" in ev:
                self._move(ev["x"], ev["y"])
            if down:
                self.buttons_down.add(name)
            else:
                self.buttons_down.discard(name)
            if self.quartz:
                self.quartz.button(name, down, int(ev.get("n", 1)))
            else:
                button = getattr(self._Button, name)
                (self.mouse.press if down else self.mouse.release)(button)
        elif kind == "scroll":
            dx, dy = int(ev.get("dx", 0)), int(ev.get("dy", 0))
            if dx or dy:
                if self.quartz:
                    self.quartz.scroll(dx, dy)
                else:
                    self.mouse.scroll(dx, dy)
        elif kind == "key":
            key = self._resolve_key(ev)
            if key is None:
                return
            ident = ev.get("s") or ev.get("c")
            if ev.get("d"):
                self._kb(self.kb.press, key)
                self.keys_down[ident] = key
            else:
                self._kb(self.kb.release, key)
                self.keys_down.pop(ident, None)

    def release_all(self) -> None:
        """Rilascia tasti e pulsanti rimasti premuti (es. connessione caduta con Ctrl premuto)."""
        for ident, key in list(self.keys_down.items()):
            try:
                self._kb(self.kb.release, key)
            except Exception:
                pass
        self.keys_down.clear()
        for name in list(self.buttons_down):
            try:
                if self.quartz:
                    self.quartz.button(name, False, 1)
                else:
                    self.mouse.release(getattr(self._Button, name))
            except Exception:
                pass
        self.buttons_down.clear()
