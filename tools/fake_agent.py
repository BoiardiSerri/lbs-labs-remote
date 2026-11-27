#!/usr/bin/env python3
"""Agente di prova: parla il protocollo di LBS Labs Remote senza catturare lo schermo.

Invia un'immagine animata e scrive su stdout ogni evento di input ricevuto. Serve ai test
automatici delle app per tablet (emulatore Android, simulatore iPad) e a provare un viewer
senza un computer vero da controllare. Usa solo la libreria standard e Pillow.

    python tools/fake_agent.py --port 5970 --seconds 120
"""
from __future__ import annotations

import argparse
import io
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw  # noqa: E402

from lbsremote import protocol as P  # noqa: E402


def make_frame(size: tuple[int, int], n: int) -> bytes:
    w, h = size
    img = Image.new("RGB", (w, h), (38, 40, 44))
    d = ImageDraw.Draw(img)
    for i in range(0, w, 80):
        d.line([(i, 0), (i, h)], fill=(55, 58, 64))
    for i in range(0, h, 80):
        d.line([(0, i), (w, i)], fill=(55, 58, 64))
    x = (n * 12) % (w - 200)
    d.rectangle((x, h // 2 - 40, x + 200, h // 2 + 40), fill=(245, 168, 0))
    d.text((20, 20), f"FAKE AGENT  frame {n}", fill=(241, 241, 241))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=60)
    return buf.getvalue()


def serve(conn: socket.socket, addr, size: tuple[int, int], fps: int, deadline: float, flap: bool = False) -> None:
    print(f"CLIENT connected {addr[0]}", flush=True)
    P.configure_socket(conn, 15.0)
    lock = threading.Lock()
    alive = threading.Event()
    alive.set()

    def send(kind: int, payload: bytes) -> None:
        with lock:
            conn.sendall(P.pack_message(kind, payload))

    def video() -> None:
        n = 0
        try:
            while alive.is_set() and time.time() < deadline:
                send(P.MSG_FRAME, make_frame(size, n))
                n += 1
                time.sleep(1.0 / fps)
        except OSError:
            pass

    try:
        send(P.MSG_HELLO, P.encode_json({
            "app": P.APP_ID, "v": P.PROTOCOL_VERSION, "version": "test", "name": "FAKE-AGENT",
            "platform": "win32", "screen": list(size), "warnings": []}))
        if flap:        # prova della riconnessione: chiude subito dopo il saluto, come un agente che non riesce a lavorare
            send(P.MSG_NOTICE, P.encode_json({"level": "warning", "text": "test: screen capture failed"}))
            return
        threading.Thread(target=video, daemon=True).start()
        while True:
            kind, payload = P.recv_message(conn)
            if kind == P.MSG_PING:
                send(P.MSG_PONG, payload)
            elif kind == P.MSG_INPUT:
                ev = P.decode_json(payload)
                if ev.get("t") != "move":
                    print(f"INPUT {ev}", flush=True)
            elif kind == P.MSG_CONFIG:
                print(f"CONFIG {P.decode_json(payload)}", flush=True)
    except (OSError, P.ConnectionClosed, P.ProtocolError):
        pass
    finally:
        alive.clear()
        conn.close()
        print(f"CLIENT disconnected {addr[0]}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=P.DEFAULT_PORT)
    ap.add_argument("--seconds", type=float, default=300, help="si ferma da solo dopo questo tempo")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--size", default="1280x800")
    ap.add_argument("--flap", action="store_true", help="chiude ogni connessione subito dopo il saluto")
    args = ap.parse_args()
    size = tuple(int(v) for v in args.size.lower().split("x"))
    deadline = time.time() + args.seconds
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", args.port))
    srv.listen(4)
    srv.settimeout(1.0)
    print(f"READY port {args.port}", flush=True)
    while time.time() < deadline:
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        threading.Thread(target=serve, args=(conn, addr, size, args.fps, deadline, args.flap), daemon=True).start()


if __name__ == "__main__":
    main()
