"""Parte di rete del viewer: connessione all'agente remoto, con riconnessione automatica.

Nessuna interfaccia grafica qui: la finestra è in viewer.py (pywebview + ui/).
I frame JPEG ricevuti non vengono decodificati: li mostra direttamente il motore web
(flusso MJPEG servito dal server locale del viewer).
"""

from __future__ import annotations

import logging
import queue
import socket
import threading
import time

from .protocol import (APP_ID, MSG_BYE, MSG_CONFIG, MSG_FRAME, MSG_HELLO, MSG_INPUT, MSG_NOTICE,
                       MSG_PING, MSG_PONG, ConnectionClosed, ProtocolError, configure_socket,
                       decode_json, describe_foreign_service, encode_json, recv_message,
                       send_json, send_message)

log = logging.getLogger("lbsremote.client")

CONNECT_TIMEOUT = 4.0
RECV_TIMEOUT = 6.0          # nessun dato (frame o pong) per 6 s => connessione persa
RECONNECT_WINDOW = 15.0     # per quanto tempo si tenta di riconnettersi
RECONNECT_DELAY = 2.5
PING_INTERVAL = 1.0


class NetSession:
    """Connessione al server. Gira in thread propri.

    on_event(session, kind, data) viene chiamata (da un thread di rete) con kind in:
    connected, failed, reconnecting, reconnected, notice, closed.
    """

    def __init__(self, host: str, port: int, remote_config: dict, on_event):
        self.host = host
        self.port = port
        self.remote_config = remote_config
        self.on_event = on_event
        self.hello: dict = {}
        self.rtt_ms: float | None = None
        self.fps = 0.0
        self.frame_size: tuple[int, int] | None = None
        self._sock: socket.socket | None = None
        self._stop = threading.Event()
        self._send_q: queue.Queue = queue.Queue()
        # ultimo frame JPEG ricevuto, con contatore: chi lo mostra attende il successivo
        self.frame_cond = threading.Condition()
        self.frame: bytes | None = None
        self.frame_seq = 0
        self._fps_count = 0
        self._fps_t0 = time.monotonic()

    # --- API per l'interfaccia ---
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
        with self.frame_cond:
            self.frame_cond.notify_all()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def send_input(self, event: dict) -> None:
        self._send_q.put((MSG_INPUT, encode_json(event)))

    def wait_frame(self, after_seq: int, timeout: float = 1.0) -> tuple[int, bytes | None]:
        """Attende un frame più recente di `after_seq`. Restituisce (seq, jpeg)."""
        with self.frame_cond:
            if self.frame_seq <= after_seq and not self._stop.is_set():
                self.frame_cond.wait(timeout)
            return self.frame_seq, self.frame

    # --- interno ---
    def _post(self, kind: str, data=None) -> None:
        try:
            self.on_event(self, kind, data)
        except Exception:
            log.exception("gestione evento %s fallita", kind)

    def _connect(self) -> str | None:
        """Una connessione + handshake. Restituisce None se ok, altrimenti il motivo."""
        sock = None
        try:
            sock = socket.create_connection((self.host, self.port), timeout=CONNECT_TIMEOUT)
            configure_socket(sock, RECV_TIMEOUT)
            first = sock.recv(8, socket.MSG_PEEK)
            if not first:
                raise ConnectionClosed("the remote computer closed the connection immediately")
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
            err = ("no response. Is the computer on and connected to the network? Is LBS Labs "
                   "Remote installed on it? Is a firewall blocking the connection?")
        except ConnectionRefusedError:
            err = f"connection refused: LBS Labs Remote is not running on that computer (port {self.port})."
        except socket.gaierror:
            err = "invalid address or unknown computer name."
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
                self._post("closed", f"Connection to {self.host} lost: {err}")
                return
            self._post("reconnected", self.hello)

    def _on_frame(self, jpeg: bytes) -> None:
        size = _jpeg_size(jpeg)   # può cambiare (qualità adattiva): costa pochi byte letti
        if size:
            self.frame_size = size
        with self.frame_cond:
            self.frame = jpeg
            self.frame_seq += 1
            self.frame_cond.notify_all()
        self._fps_count += 1
        now = time.monotonic()
        if now - self._fps_t0 >= 1.0:
            self.fps = self._fps_count / (now - self._fps_t0)
            self._fps_count, self._fps_t0 = 0, now

    def _serve(self) -> tuple[str, str]:
        sock = self._sock
        conn_done = threading.Event()
        while True:  # gli input accodati durante la disconnessione sono ormai obsoleti
            try:
                self._send_q.get_nowait()
            except queue.Empty:
                break
        threading.Thread(target=self._sender, args=(sock, conn_done),
                         name="net-sender", daemon=True).start()
        try:
            while not self._stop.is_set():
                msg_type, payload = recv_message(sock)
                if msg_type == MSG_FRAME:
                    self._on_frame(payload)
                elif msg_type == MSG_PONG:
                    rtt = (time.perf_counter() - float(decode_json(payload)["ts"])) * 1000.0
                    self.rtt_ms = rtt if self.rtt_ms is None else self.rtt_ms * 0.7 + rtt * 0.3
                elif msg_type == MSG_NOTICE:
                    self._post("notice", decode_json(payload))
                elif msg_type == MSG_BYE:
                    return "bye", str(decode_json(payload).get("reason")
                                      or "Session closed by the remote computer.")
            return "stopped", ""
        except socket.timeout:
            return "lost", "no data from the remote computer for several seconds"
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
                    msg_type, payload = self._send_q.get(
                        timeout=max(0.01, next_ping - time.perf_counter()))
                except queue.Empty:
                    continue
                send_message(sock, msg_type, payload)
        except OSError:
            try:
                sock.shutdown(socket.SHUT_RDWR)  # sblocca il thread di ricezione
            except OSError:
                pass


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    """Larghezza e altezza di un JPEG leggendo l'intestazione (senza decodificarlo)."""
    i = 2
    n = len(data)
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    return None
