"""Viewer (client): schermata di connessione minimale + finestra che mostra lo schermo remoto.

Avvio:  python lbs_labs_remote.py (vedi app.py)
"""

from __future__ import annotations

import io
import logging
import queue
import re
import socket
import sys
import threading
import time

try:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import ttk
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "tkinter non è disponibile in questa installazione di Python.\n"
        "  macOS con Homebrew:  brew install python-tk\n"
        "  Windows / python.org: reinstalla Python includendo 'tcl/tk and IDLE'.\n")
    raise

from PIL import Image, ImageTk

from . import APP_NAME
from . import platform_utils as pu
from .config import load_json, save_json
from .discovery import DiscoveryListener, local_ipv4_addresses
from .keymap import tk_key_to_wire
from .protocol import (APP_ID, DEFAULT_PORT, LEGACY_DEFAULT_PORT, describe_foreign_service, DISCOVERY_PORT, MSG_BYE, MSG_CONFIG, MSG_FRAME,
                       MSG_HELLO, MSG_INPUT, MSG_NOTICE, MSG_PING, MSG_PONG, ConnectionClosed,
                       ProtocolError, configure_socket, decode_json, encode_json,
                       parse_host_port, recv_message, send_json, send_message)

log = logging.getLogger("lbsremote.client")

CLIENT_CONFIG = "client.json"
CONNECT_TIMEOUT = 4.0
RECV_TIMEOUT = 6.0          # nessun dato (frame o pong) per 6 s => connessione persa
RECONNECT_WINDOW = 15.0     # per quanto tempo si tenta di riconnettersi
RECONNECT_DELAY = 2.5
PING_INTERVAL = 1.0
MOVE_INTERVAL_MS = 10       # massimo ~100 movimenti mouse/s inoltrati
CLICK_SWALLOW_S = 0.3       # il clic che "attiva" la finestra non viene inoltrato
DOUBLE_CLICK_S = 0.45

QUALITY_PRESETS = {
    "Automatica": {},                                   # default dell'agente, adattiva
    "Bassa": {"quality": 35, "adaptive": False},
    "Media": {"quality": 55, "adaptive": False},
    "Alta": {"quality": 75, "adaptive": False},
    "Massima": {"quality": 90, "adaptive": False},
}
FPS_CHOICES = ["Predefiniti", "5", "10", "15", "20", "25", "30"]
WIDTH_CHOICES = ["Predefinita", "1280", "1600", "1920", "2560", "Originale"]

DEFAULT_CONFIG = {
    "last_host": "",
    "port": DEFAULT_PORT,
    "discovery_port": DISCOVERY_PORT,
    "quality": "Automatica",
    "fps": "Predefiniti",
    "max_width": "Predefinita",
}

COLOR_OK = "#22c55e"
COLOR_WARN = "#f59e0b"
COLOR_ERR = "#b91c1c"
COLOR_MUTED = "#6b7280"
COLOR_LINK = "#2563eb"
TOOLBAR_BG = "#1f2937"
TOOLBAR_FG = "#e5e7eb"


# =============================================================================
# Rete
# =============================================================================

class NetSession:
    """Connessione al server, con riconnessione automatica. Gira in thread propri;
    comunica con l'interfaccia solo tramite la coda `events` e `take_frame()`."""

    def __init__(self, host: str, port: int, remote_config: dict, events: queue.Queue):
        self.host = host
        self.port = port
        self.remote_config = remote_config
        self.events = events
        self.hello: dict = {}
        self.rtt_ms: float | None = None
        self.target_size = (1280, 720)     # dimensione dell'area di disegno (aggiornata dalla UI)
        self.last_jpeg: bytes | None = None
        self._sock: socket.socket | None = None
        self._stop = threading.Event()
        self._send_q: queue.Queue = queue.Queue()
        self._frame_lock = threading.Lock()
        self._frame: Image.Image | None = None

    # --- API per la UI ---
    def start(self) -> None:
        threading.Thread(target=self._run, name="net-session", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()
        sock = self._sock
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def send_input(self, event: dict) -> None:
        self._send_q.put((MSG_INPUT, encode_json(event)))

    def take_frame(self) -> Image.Image | None:
        with self._frame_lock:
            frame, self._frame = self._frame, None
        return frame

    @staticmethod
    def render(jpeg: bytes, target: tuple[int, int]) -> Image.Image:
        """Decodifica il JPEG e lo adatta all'area (mantenendo le proporzioni)."""
        img = Image.open(io.BytesIO(jpeg))
        iw, ih = img.size
        tw, th = target
        scale = min(tw / iw, th / ih) if tw > 1 and th > 1 else 1.0
        size = (max(1, round(iw * scale)), max(1, round(ih * scale)))
        if scale < 1.0:
            img.draft("RGB", size)  # decodifica JPEG ridotta: molto più veloce
        img = img.convert("RGB")
        if img.size != size:
            img = img.resize(size, Image.BILINEAR)
        return img

    # --- interno ---
    def _post(self, kind: str, data=None) -> None:
        self.events.put((self, kind, data))

    def _connect(self) -> str | None:
        """Una connessione + handshake. Restituisce None se ok, altrimenti il motivo."""
        sock = None
        try:
            sock = socket.create_connection((self.host, self.port), timeout=CONNECT_TIMEOUT)
            configure_socket(sock, RECV_TIMEOUT)
            first = sock.recv(8, socket.MSG_PEEK)
            if not first:
                raise ConnectionClosed("il computer remoto ha chiuso subito la connessione")
            if first.startswith(b"RFB") or first[:4] in (b"HTTP", b"SSH-"):
                raise ProtocolError(describe_foreign_service(first, self.port))
            try:
                msg_type, payload = recv_message(sock)
            except ProtocolError:
                raise ProtocolError(describe_foreign_service(first, self.port))
            hello = decode_json(payload) if msg_type == MSG_HELLO else {}
            if hello.get("app") != APP_ID:
                raise ProtocolError(describe_foreign_service(b"", self.port))
            if self.remote_config:
                send_json(sock, MSG_CONFIG, self.remote_config)
        except socket.timeout:
            err = ("nessuna risposta. Il PC è acceso e in rete? L'agente è avviato? "
                   "Il firewall blocca la porta?")
        except ConnectionRefusedError:
            err = f"connessione rifiutata: l'agente non è in ascolto sulla porta {self.port}."
        except socket.gaierror:
            err = "indirizzo non valido o nome non risolvibile."
        except (OSError, ProtocolError, ConnectionClosed) as exc:
            err = str(exc) or exc.__class__.__name__
        else:
            self._sock = sock
            self.hello = hello
            return None
        if sock:
            sock.close()
        return err

    def _run(self) -> None:
        err = self._connect()
        if err:
            self._post("failed", err)
            return
        self._post("connected", self.hello)
        while not self._stop.is_set():
            kind, reason = self._serve()
            if self._stop.is_set():
                return
            if kind == "bye":
                self._post("closed", reason)
                return
            log.info("connessione persa (%s): riconnessione", reason)
            self._post("reconnecting", reason)
            deadline = time.monotonic() + RECONNECT_WINDOW
            err = reason
            while not self._stop.is_set() and time.monotonic() < deadline:
                err = self._connect()
                if err is None:
                    break
                self._stop.wait(RECONNECT_DELAY)
            if self._stop.is_set():
                return
            if err is not None:
                self._post("closed", f"Connessione persa con {self.host}: {err}")
                return
            self._post("reconnected", self.hello)

    def _serve(self) -> tuple[str, str]:
        sock = self._sock
        conn_done = threading.Event()
        while True:  # gli input accodati durante la disconnessione sono ormai obsoleti
            try:
                self._send_q.get_nowait()
            except queue.Empty:
                break
        sender = threading.Thread(target=self._sender, args=(sock, conn_done),
                                  name="net-sender", daemon=True)
        sender.start()
        try:
            while not self._stop.is_set():
                msg_type, payload = recv_message(sock)
                if msg_type == MSG_FRAME:
                    self.last_jpeg = payload
                    img = self.render(payload, self.target_size)
                    with self._frame_lock:
                        self._frame = img
                elif msg_type == MSG_PONG:
                    rtt = (time.perf_counter() - float(decode_json(payload)["ts"])) * 1000.0
                    self.rtt_ms = rtt if self.rtt_ms is None else self.rtt_ms * 0.7 + rtt * 0.3
                elif msg_type == MSG_NOTICE:
                    self._post("notice", decode_json(payload))
                elif msg_type == MSG_BYE:
                    return "bye", str(decode_json(payload).get("reason") or "Sessione chiusa dal server.")
            return "stopped", ""
        except socket.timeout:
            return "lost", "nessun dato dal PC remoto da alcuni secondi"
        except (OSError, ConnectionClosed, ProtocolError, ValueError, KeyError) as exc:
            return "lost", str(exc) or exc.__class__.__name__
        finally:
            conn_done.set()
            try:
                sock.close()
            except OSError:
                pass

    def _sender(self, sock: socket.socket, conn_done: threading.Event) -> None:
        next_ping = 0.0
        try:
            while not conn_done.is_set() and not self._stop.is_set():
                now = time.perf_counter()
                if now >= next_ping:
                    send_json(sock, MSG_PING, {"ts": now})
                    next_ping = now + PING_INTERVAL
                try:
                    msg_type, payload = self._send_q.get(timeout=max(0.01, next_ping - time.perf_counter()))
                except queue.Empty:
                    continue
                send_message(sock, msg_type, payload)
        except OSError:
            try:
                sock.shutdown(socket.SHUT_RDWR)  # sblocca il thread di ricezione
            except OSError:
                pass


# =============================================================================
# Finestra del viewer
# =============================================================================

def _tk_version(root: tk.Tk) -> tuple[int, int]:
    try:
        nums = re.findall(r"\d+", str(root.tk.call("info", "patchlevel")))
        return int(nums[0]), int(nums[1])
    except (IndexError, ValueError, tk.TclError):
        return 8, 6


def _button_map(root: tk.Tk) -> dict[int, str]:
    # In Tk 8.6 su macOS il tasto destro è il pulsante 2 e il centrale il 3.
    if pu.IS_MAC and _tk_version(root) < (8, 7):
        return {1: "left", 2: "right", 3: "middle"}
    return {1: "left", 2: "middle", 3: "right"}


class Viewer:
    def __init__(self, app: "ClientApp", hello: dict, host: str):
        self.app = app
        self.buttons = _button_map(app.root)
        self.focused = False
        self.fullscreen = False
        self.swallow_until = 0.0
        self.keys_down: dict[int, dict] = {}     # keycode -> {"key": wire, "sym": keysym}
        self.buttons_down: set[str] = set()
        self.button_clicks: dict[str, int] = {}
        self.swallowed: set[int] = set()
        self.pending_move = None
        self.last_sent_move = None
        self.move_job = None
        self.last_click = (None, 0.0, 0, 0, 0)
        self.wheel_acc = [0.0, 0.0]
        self.photo: ImageTk.PhotoImage | None = None
        self.img_geom = (0, 0, 0, 0)
        self.state = "connected"
        self._status_text = None
        self._resize_job = None
        self._hint_job = None

        name = hello.get("name") or host
        win = self.win = tk.Toplevel(app.root)
        win.title(f"{name} ({host}) – {APP_NAME}")
        win.configure(bg="black")
        win.protocol("WM_DELETE_WINDOW", app.disconnect)

        # --- barra superiore sottile (nascosta in schermo intero) ---
        small = tkfont.nametofont("TkDefaultFont").copy()
        self.toolbar = tk.Frame(win, bg=TOOLBAR_BG, padx=6, pady=3)
        self.btn_fs = self._toolbar_button("⛶  Schermo intero", self.toggle_fullscreen, small)
        self.btn_disc = self._toolbar_button("✕  Disconnetti", app.disconnect, small)
        self.status = tk.Label(self.toolbar, text="", bg=TOOLBAR_BG, fg=COLOR_OK, font=small)
        self.status.pack(side="right", padx=4)
        self.toolbar.pack(side="top", fill="x")

        # --- avvisi dal server (es. permessi macOS mancanti) ---
        self.banner = tk.Label(win, text="", bg="#fef3c7", fg="#78350f", anchor="w",
                               justify="left", padx=8, pady=4, cursor="hand2")
        self.banner.bind("<Button-1>", lambda e: self.banner.pack_forget())

        # --- immagine remota ---
        self.canvas = tk.Canvas(win, bg="black", highlightthickness=0, bd=0, takefocus=1)
        self.canvas.pack(side="top", fill="both", expand=True)
        self.img_item = self.canvas.create_image(0, 0, anchor="nw")
        self.overlay_bg = self.canvas.create_rectangle(0, 0, 0, 0, fill="#111827",
                                                       outline="#374151", state="hidden")
        self.overlay_text = self.canvas.create_text(0, 0, text="", fill="#f9fafb",
                                                    font=small, state="hidden")

        c = self.canvas
        c.bind("<Motion>", self.on_motion)
        c.bind("<ButtonPress>", self.on_press)
        c.bind("<ButtonRelease>", self.on_release)
        c.bind("<MouseWheel>", self.on_wheel)
        c.bind("<Configure>", self.on_resize)
        win.bind("<KeyPress>", self.on_key_press)
        win.bind("<KeyRelease>", self.on_key_release)
        win.bind("<FocusIn>", self.on_focus_in)
        win.bind("<FocusOut>", self.on_focus_out)

        self._initial_geometry(hello.get("screen") or [1920, 1080])
        win.after(50, self._grab_focus)

    # --- costruzione ---
    def _toolbar_button(self, text, command, font):
        lbl = tk.Label(self.toolbar, text=text, bg=TOOLBAR_BG, fg=TOOLBAR_FG, font=font,
                       padx=8, pady=1, cursor="hand2")
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.configure(bg="#374151"))
        lbl.bind("<Leave>", lambda e: lbl.configure(bg=TOOLBAR_BG))
        lbl.pack(side="left", padx=(0, 4))
        return lbl

    def _initial_geometry(self, screen) -> None:
        rw, rh = max(1, int(screen[0])), max(1, int(screen[1]))
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        bar = 30
        scale = min(sw * 0.85 / rw, (sh * 0.85 - bar) / rh, 1.0)
        w, h = int(rw * scale), int(rh * scale)
        x, y = max(0, (sw - w) // 2), max(0, (sh - h - bar) // 2 - 20)
        self.win.geometry(f"{w}x{h + bar}+{x}+{y}")
        self.app.session.target_size = (w, h)

    def _grab_focus(self) -> None:
        try:
            self.win.lift()
            self.win.focus_force()
            self.canvas.focus_set()
        except tk.TclError:
            pass

    def destroy(self) -> None:
        try:
            self.win.destroy()
        except tk.TclError:
            pass

    # --- disegno ---
    def show_frame(self, img: Image.Image) -> None:
        if self.photo is None or (self.photo.width(), self.photo.height()) != img.size:
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfigure(self.img_item, image=self.photo)
        else:
            self.photo.paste(img)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        ox, oy = max(0, (cw - img.width) // 2), max(0, (ch - img.height) // 2)
        self.canvas.coords(self.img_item, ox, oy)
        self.img_geom = (ox, oy, img.width, img.height)

    def on_resize(self, event) -> None:
        session = self.app.session
        if session is not None:
            session.target_size = (event.width, event.height)
        self._place_overlay()
        if self._resize_job:
            self.win.after_cancel(self._resize_job)
        self._resize_job = self.win.after(120, self._rerender)

    def _rerender(self) -> None:
        """Ridisegna l'ultimo frame alla nuova dimensione (utile se lo schermo remoto è statico)."""
        self._resize_job = None
        session = self.app.session
        if session is None or not session.last_jpeg:
            return
        try:
            self.show_frame(NetSession.render(session.last_jpeg, session.target_size))
        except Exception:
            log.debug("ridisegno fallito", exc_info=True)

    def _place_overlay(self) -> None:
        cw = self.canvas.winfo_width()
        self.canvas.coords(self.overlay_text, cw // 2, 34)
        x1, y1, x2, y2 = self.canvas.bbox(self.overlay_text) or (0, 0, 0, 0)
        self.canvas.coords(self.overlay_bg, x1 - 14, y1 - 8, x2 + 14, y2 + 8)
        self.canvas.tag_raise(self.overlay_bg)
        self.canvas.tag_raise(self.overlay_text)

    def show_overlay(self, text: str | None, duration_ms: int | None = None) -> None:
        if self._hint_job:
            self.win.after_cancel(self._hint_job)
            self._hint_job = None
        state = "normal" if text else "hidden"
        self.canvas.itemconfigure(self.overlay_text, text=text or "", state=state)
        self.canvas.itemconfigure(self.overlay_bg, state=state)
        self._place_overlay()
        if text and duration_ms:
            self._hint_job = self.win.after(duration_ms, lambda: self.show_overlay(None))

    def show_notice(self, notice: dict) -> None:
        text = str(notice.get("text", ""))
        if not text:
            return
        prefix = "⚠ " if notice.get("level") in ("warning", "error") else ""
        self.banner.configure(text=f"{prefix}{text}   (clic per chiudere)",
                              wraplength=max(300, self.win.winfo_width() - 30))
        self.banner.pack(side="top", fill="x", before=self.canvas)

    def set_state(self, state: str) -> None:
        self.state = state
        if state == "reconnecting":
            self.release_all(send=False)
            self.show_overlay("Connessione persa – riconnessione in corso…")
        else:
            self.show_overlay(None)
        self.update_status()

    def update_status(self) -> None:
        session = self.app.session
        if self.state == "reconnecting":
            text, color = "● Riconnessione…", COLOR_WARN
        else:
            text, color = "● Connesso", COLOR_OK
            if session and session.rtt_ms is not None:
                text += f" · {session.rtt_ms:.0f} ms"
            if not self.focused:
                text += "  ·  clic sull'immagine per controllare"
        if text != self._status_text:
            self._status_text = text
            self.status.configure(text=text, fg=color)

    # --- schermo intero ---
    def toggle_fullscreen(self) -> None:
        self.set_fullscreen(not self.fullscreen)

    def set_fullscreen(self, on: bool) -> None:
        if on == self.fullscreen:
            return
        self.fullscreen = on
        if on:
            self.toolbar.pack_forget()
            self.win.attributes("-fullscreen", True)
            self.show_overlay("Premi ESC per uscire dallo schermo intero", duration_ms=2500)
        else:
            self.win.attributes("-fullscreen", False)
            self.toolbar.pack(side="top", fill="x", before=self.banner if self.banner.winfo_ismapped()
                              else self.canvas)
            if self.state != "reconnecting":
                self.show_overlay(None)
        self.win.after(50, self._grab_focus)

    # --- focus: la cattura dell'input è attiva solo con la finestra a fuoco ---
    def on_focus_in(self, event) -> None:
        if not self.focused:
            self.focused = True
            self.swallow_until = time.monotonic() + CLICK_SWALLOW_S
            self.update_status()

    def on_focus_out(self, event) -> None:
        # FocusOut arriva anche quando il focus passa da un widget all'altro
        # della stessa finestra: si verifica poco dopo dove è finito davvero.
        self.win.after(30, self._verify_focus)

    def _verify_focus(self) -> None:
        try:
            widget = self.win.focus_get()
            inside = widget is not None and str(widget.winfo_toplevel()) == str(self.win)
        except (KeyError, tk.TclError):
            inside = False
        if not inside and self.focused:
            self.focused = False
            self.release_all()
            self.update_status()

    def release_all(self, send: bool = True) -> None:
        """Rilascia sul PC remoto tutto ciò che risulta premuto (niente tasti 'incollati')."""
        session = self.app.session
        if send and session:
            for entry in self.keys_down.values():
                session.send_input({"t": "key", "d": 0, **entry["key"]})
            for btn in self.buttons_down:
                session.send_input({"t": "btn", "b": btn, "d": 0, "n": 1})
        self.keys_down.clear()
        self.buttons_down.clear()
        self.swallowed.clear()
        self.wheel_acc = [0.0, 0.0]

    # --- mouse ---
    def _to_remote(self, x: int, y: int, clamp: bool):
        ox, oy, w, h = self.img_geom
        if w <= 1 or h <= 1:
            return None
        fx, fy = (x - ox) / w, (y - oy) / h
        if not clamp and not (0.0 <= fx <= 1.0 and 0.0 <= fy <= 1.0):
            return None
        return round(min(max(fx, 0.0), 1.0), 5), round(min(max(fy, 0.0), 1.0), 5)

    def _send(self, event: dict) -> None:
        session = self.app.session
        if session and self.state == "connected":
            session.send_input(event)

    def on_motion(self, event) -> None:
        if not self.focused:
            return
        pos = self._to_remote(event.x, event.y, clamp=True)
        if pos is None:
            return
        self.pending_move = pos
        if self.move_job is None:
            self.move_job = self.win.after(MOVE_INTERVAL_MS, self._flush_move)

    def _flush_move(self) -> None:
        if self.move_job is not None:
            self.win.after_cancel(self.move_job)
            self.move_job = None
        pos, self.pending_move = self.pending_move, None
        if pos and pos != self.last_sent_move:
            self.last_sent_move = pos
            self._send({"t": "move", "x": pos[0], "y": pos[1]})

    def _click_count(self, btn: str, x: int, y: int) -> int:
        now = time.monotonic()
        last_btn, last_t, lx, ly, last_n = self.last_click
        if btn == last_btn and now - last_t < DOUBLE_CLICK_S and abs(x - lx) < 6 and abs(y - ly) < 6:
            n = min(last_n + 1, 3)
        else:
            n = 1
        self.last_click = (btn, now, x, y, n)
        return n

    def on_press(self, event):
        if event.num in (4, 5, 6, 7):   # rotella su X11
            if self.focused:
                vertical = event.num in (4, 5)
                self._scroll(1 if event.num in (4, 6) else -1, horizontal=not vertical)
            return "break"
        btn = self.buttons.get(event.num)
        if btn is None:
            return None
        self.canvas.focus_set()
        if not self.focused or time.monotonic() < self.swallow_until:
            self.swallowed.add(event.num)   # clic di attivazione: non inoltrato
            return "break"
        pos = self._to_remote(event.x, event.y, clamp=False)
        if pos is None:                     # clic sulle bande nere
            self.swallowed.add(event.num)
            return "break"
        self._flush_move()
        n = self._click_count(btn, event.x, event.y)
        self.buttons_down.add(btn)
        self.button_clicks[btn] = n
        self.last_sent_move = pos
        self._send({"t": "btn", "b": btn, "d": 1, "x": pos[0], "y": pos[1], "n": n})
        return "break"

    def on_release(self, event):
        if event.num in self.swallowed:
            self.swallowed.discard(event.num)
            return "break"
        btn = self.buttons.get(event.num)
        if btn is None or btn not in self.buttons_down:
            return "break"
        pos = self._to_remote(event.x, event.y, clamp=True) or self.last_sent_move or (0.5, 0.5)
        self._flush_move()
        self.buttons_down.discard(btn)
        self.last_sent_move = pos
        self._send({"t": "btn", "b": btn, "d": 0, "x": pos[0], "y": pos[1],
                    "n": self.button_clicks.pop(btn, 1)})
        return "break"

    def on_wheel(self, event):
        if not self.focused:
            return "break"
        delta = event.delta
        if pu.IS_MAC and not (abs(delta) >= 120 and delta % 120 == 0):
            steps = float(delta)            # Tk 8.6 su macOS: delta già in "righe"
        else:
            steps = delta / 120.0           # Windows (e Tk recenti): multipli di 120
        shift_by_user = any(e["key"].get("s", "").startswith("shift") for e in self.keys_down.values())
        # Su macOS lo scorrimento orizzontale del trackpad arriva come Shift+rotella
        # anche senza Shift premuto: lo distinguiamo così.
        horizontal = bool(event.state & 0x0001) and not shift_by_user
        self._scroll(steps, horizontal)
        return "break"

    def _scroll(self, steps: float, horizontal: bool) -> None:
        i = 0 if horizontal else 1
        self.wheel_acc[i] += steps
        whole = int(self.wheel_acc[i])
        if whole == 0:
            return
        self.wheel_acc[i] -= whole
        self._flush_move()
        if horizontal:
            self._send({"t": "scroll", "dx": -whole, "dy": 0})
        else:
            self._send({"t": "scroll", "dx": 0, "dy": whole})

    # --- tastiera ---
    def on_key_press(self, event):
        if event.keysym == "Escape":        # riservato al client: mai inoltrato
            if self.fullscreen:
                self.set_fullscreen(False)
            return "break"
        if not self.focused:
            return "break"
        entry = self.keys_down.get(event.keycode)
        if entry is None:
            mods = {e["key"]["s"] for e in self.keys_down.values() if "s" in e["key"]}
            key = tk_key_to_wire(event.keysym, event.char, mods)
            if key is None:
                log.debug("tasto non inoltrabile: keysym=%r char=%r", event.keysym, event.char)
                return "break"
            entry = {"key": key, "sym": event.keysym}
            self.keys_down[event.keycode] = entry
        self._send({"t": "key", "d": 1, **entry["key"]})   # anche l'autorepeat
        return "break"

    def on_key_release(self, event):
        if event.keysym == "Escape":
            return "break"
        entry = self.keys_down.pop(event.keycode, None)
        if entry is None:
            # keycode diverso fra pressione e rilascio (succede su macOS): cerca per keysym
            for code, e in list(self.keys_down.items()):
                if e["sym"].lower() == event.keysym.lower():
                    entry = self.keys_down.pop(code)
                    break
        if entry is None:
            return "break"
        self._send({"t": "key", "d": 0, **entry["key"]})
        return "break"


# =============================================================================
# Applicazione / schermata iniziale
# =============================================================================

class ClientApp:
    def __init__(self, initial_host: str | None = None, notice: str | None = None):
        # "system aware": Tk 8.6 non gestisce il cambio di DPI fra monitor
        pu.enable_windows_dpi_awareness(per_monitor=False)
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.resizable(False, False)
        self.cfg = load_json(CLIENT_CONFIG, DEFAULT_CONFIG)
        if str(self.cfg.get("port")) == str(LEGACY_DEFAULT_PORT):   # aggiornamento dalla 1.0.0
            self.cfg["port"] = DEFAULT_PORT
        self.events: queue.Queue = queue.Queue()
        self.session: NetSession | None = None
        self.viewer: Viewer | None = None
        self.connecting_text = ""
        self._servers_sig = None
        self._local_ips: set[str] = set()
        self._local_ips_at = -1e9
        self._last_status = 0.0

        try:
            port = int(self.cfg.get("discovery_port") or DISCOVERY_PORT)
        except (TypeError, ValueError):
            port = DISCOVERY_PORT
        self.discovery = DiscoveryListener(port)
        self.discovery.start()

        self._build_launcher()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        if pu.IS_MAC:
            # Cmd+Q mentre si controlla il PC remoto non deve chiudere il viewer.
            self.root.createcommand("::tk::mac::Quit", self._mac_quit)
        self.root.after(15, self._poll)
        self.root.after(300, self._refresh_servers)
        if notice:
            self.show_message("⚠ Questo computer non può essere controllato da altri PC: " + notice)
        if initial_host:
            self.ip_var.set(initial_host)
            self.root.after(100, self.connect_from_entry)

    # --- interfaccia iniziale ---
    def _build_launcher(self) -> None:
        root = self.root
        base = tkfont.nametofont("TkDefaultFont")
        title_font = base.copy()
        title_font.configure(size=base.cget("size") + 3 if base.cget("size") > 0 else base.cget("size") - 3,
                             weight="bold")
        small = base.copy()
        small.configure(size=base.cget("size") - 1 if base.cget("size") > 0 else base.cget("size") + 1)
        entry_font = base.copy()
        entry_font.configure(size=base.cget("size") + 2 if base.cget("size") > 0 else base.cget("size") - 2)
        self._fonts = (title_font, small, entry_font)

        frm = ttk.Frame(root, padding=(22, 18, 22, 14))
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)
        self.frm = frm

        ttk.Label(frm, text="Connetti a un PC remoto", font=title_font).grid(
            row=0, column=0, columnspan=2, sticky="w")

        self.ip_var = tk.StringVar(value=str(self.cfg.get("last_host") or ""))
        self.entry = ttk.Entry(frm, textvariable=self.ip_var, width=26, font=entry_font)
        self.entry.grid(row=1, column=0, sticky="ew", pady=(12, 6), ipady=3)
        self.btn = ttk.Button(frm, text="Connetti", command=self.connect_from_entry)
        self.btn.grid(row=1, column=1, sticky="ns", padx=(8, 0), pady=(12, 6))

        self.msg = ttk.Label(frm, text="", wraplength=340, justify="left")
        self.msg.grid(row=2, column=0, columnspan=2, sticky="w")
        self.msg.grid_remove()

        self.found = ttk.Frame(frm)
        self.found.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.found.grid_remove()

        self.adv_link = ttk.Label(frm, text="Impostazioni avanzate ▸", foreground=COLOR_MUTED,
                                  cursor="hand2", font=small)
        self.adv_link.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.adv_link.bind("<Button-1>", lambda e: self._toggle_advanced())
        self.adv = self._build_advanced(frm)

        root.bind("<Return>", lambda e: self.connect_from_entry())
        root.bind("<KP_Enter>", lambda e: self.connect_from_entry())

        root.update_idletasks()
        w, h = root.winfo_reqwidth(), root.winfo_reqheight()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"+{(sw - w) // 2}+{max(0, (sh - h) // 3)}")
        self.entry.focus_set()
        self.entry.icursor("end")
        self.entry.select_range(0, "end")

    def _build_advanced(self, parent) -> ttk.Frame:
        adv = ttk.Frame(parent)
        self.port_var = tk.StringVar(value=str(self.cfg.get("port") or DEFAULT_PORT))
        self.quality_var = tk.StringVar(value=self.cfg.get("quality") if self.cfg.get("quality")
                                        in QUALITY_PRESETS else "Automatica")
        self.fps_var = tk.StringVar(value=str(self.cfg.get("fps")) if str(self.cfg.get("fps"))
                                    in FPS_CHOICES else "Predefiniti")
        self.width_var = tk.StringVar(value=str(self.cfg.get("max_width")) if str(self.cfg.get("max_width"))
                                      in WIDTH_CHOICES else "Predefinita")
        rows = [
            ("Porta", ttk.Entry(adv, textvariable=self.port_var, width=8)),
            ("Qualità immagine", ttk.Combobox(adv, textvariable=self.quality_var, state="readonly",
                                              values=list(QUALITY_PRESETS), width=12)),
            ("Fotogrammi/s", ttk.Combobox(adv, textvariable=self.fps_var, state="readonly",
                                          values=FPS_CHOICES, width=12)),
            ("Larghezza max (px)", ttk.Combobox(adv, textvariable=self.width_var, state="readonly",
                                                values=WIDTH_CHOICES, width=12)),
        ]
        for i, (label, widget) in enumerate(rows):
            ttk.Label(adv, text=label).grid(row=i, column=0, sticky="w", pady=2, padx=(0, 10))
            widget.grid(row=i, column=1, sticky="w", pady=2)
        return adv

    def _toggle_advanced(self) -> None:
        if self.adv.winfo_ismapped():
            self.adv.grid_remove()
            self.adv_link.configure(text="Impostazioni avanzate ▸")
        else:
            self.adv.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
            self.adv_link.configure(text="Impostazioni avanzate ▾")

    def show_message(self, text: str | None, color: str = COLOR_ERR) -> None:
        if text:
            self.msg.configure(text=text, foreground=color)
            self.msg.grid()
        else:
            self.msg.grid_remove()

    def _refresh_servers(self) -> None:
        try:
            now = time.monotonic()
            if now - self._local_ips_at > 10:
                self._local_ips, self._local_ips_at = set(local_ipv4_addresses()), now
            # Questo stesso PC (se l'agente è attivo) non va proposto: ci si
            # controllerebbe da soli, con un effetto "specchio" infinito.
            servers = [s for s in self.discovery.servers()
                       if s["ip"] not in self._local_ips and not s["ip"].startswith("127.")]
            sig = tuple((s["name"], s["ip"], s["port"], s["busy"]) for s in servers)
            if sig != self._servers_sig:
                self._servers_sig = sig
                for child in self.found.winfo_children():
                    child.destroy()
                if servers:
                    ttk.Label(self.found, text="PC trovati in rete:", foreground=COLOR_MUTED,
                              font=self._fonts[1]).pack(anchor="w")
                    for s in servers:
                        target = s["ip"] if s["port"] == DEFAULT_PORT else f"{s['ip']}:{s['port']}"
                        text = f"{s['name']}  ({target})" + ("  · in uso" if s["busy"] else "")
                        link = ttk.Label(self.found, text=text, foreground=COLOR_LINK, cursor="hand2")
                        link.pack(anchor="w", padx=(10, 0), pady=1)
                        link.bind("<Button-1>", lambda e, t=target: self._connect_to(t))
                    self.found.grid()
                else:
                    self.found.grid_remove()
        finally:
            self.root.after(1000, self._refresh_servers)

    # --- connessione ---
    def _adv_port(self) -> int:
        try:
            port = int(self.port_var.get())
            return port if 0 < port < 65536 else DEFAULT_PORT
        except ValueError:
            return DEFAULT_PORT

    def _remote_config(self) -> dict:
        cfg = dict(QUALITY_PRESETS.get(self.quality_var.get(), {}))
        if self.fps_var.get().isdigit():
            cfg["fps"] = int(self.fps_var.get())
        width = self.width_var.get()
        if width == "Originale":
            cfg["max_width"] = 0
        elif width.isdigit():
            cfg["max_width"] = int(width)
        return cfg

    def _save_config(self) -> None:
        self.cfg.update({"port": self._adv_port(), "quality": self.quality_var.get(),
                         "fps": self.fps_var.get(), "max_width": self.width_var.get()})
        save_json(CLIENT_CONFIG, self.cfg)

    def _connect_to(self, target: str) -> None:
        self.ip_var.set(target)
        self.connect_from_entry()

    def connect_from_entry(self) -> None:
        if self.session is not None:
            return
        text = self.ip_var.get().strip()
        if not text:
            self.show_message("Inserisci l'indirizzo IP del PC remoto.")
            self.entry.focus_set()
            return
        try:
            host, port = parse_host_port(text, self._adv_port())
        except ValueError as exc:
            self.show_message(f"Indirizzo non valido: {exc}")
            return
        self._save_config()
        self.connecting_text = text
        self.show_message(f"Connessione a {host}…", COLOR_MUTED)
        self.btn.state(["disabled"])
        self.session = NetSession(host, port, self._remote_config(), self.events)
        self.session.start()

    def disconnect(self) -> None:
        self._end_session(None)

    def _end_session(self, message: str | None) -> None:
        session, self.session = self.session, None
        if session:
            session.stop()
        if self.viewer:
            self.viewer.destroy()
            self.viewer = None
        self.btn.state(["!disabled"])
        self.root.deiconify()
        self.root.lift()
        self.show_message(message)
        self.entry.focus_force()
        self.entry.select_range(0, "end")

    # --- ciclo principale: eventi di rete e frame ---
    def _poll(self) -> None:
        try:
            while True:
                try:
                    session, kind, data = self.events.get_nowait()
                except queue.Empty:
                    break
                if session is not self.session:
                    continue   # evento di una sessione già chiusa
                self._handle_event(kind, data)
            if self.viewer and self.session:
                frame = self.session.take_frame()
                if frame is not None:
                    self.viewer.show_frame(frame)
                now = time.monotonic()
                if now - self._last_status > 0.5:
                    self._last_status = now
                    self.viewer.update_status()
        except Exception:
            log.exception("errore nell'interfaccia")
        finally:
            self.root.after(15, self._poll)

    def _handle_event(self, kind: str, data) -> None:
        if kind == "connected":
            self.cfg["last_host"] = self.connecting_text   # salvato solo se la connessione riesce
            save_json(CLIENT_CONFIG, self.cfg)
            self.show_message(None)
            self.root.withdraw()
            self.viewer = Viewer(self, data or {}, self.session.host)
        elif kind == "failed":
            host = self.session.host
            self.session = None
            self.btn.state(["!disabled"])
            self.show_message(f"Impossibile connettersi a {host}: {data}")
            self.entry.focus_set()
        elif kind == "reconnecting" and self.viewer:
            self.viewer.set_state("reconnecting")
        elif kind == "reconnected" and self.viewer:
            self.viewer.set_state("connected")
        elif kind == "notice" and self.viewer:
            self.viewer.show_notice(data or {})
        elif kind == "closed":
            self._end_session(str(data))

    def _mac_quit(self) -> None:
        if self.viewer and self.viewer.focused:
            return
        self.quit()

    def quit(self) -> None:
        if self.session:
            self.session.stop()
        self.discovery.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
