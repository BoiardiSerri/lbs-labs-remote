"""Protocollo di rete condiviso fra server (agente) e client (viewer).

Ogni messaggio sul socket TCP ha questa forma:

    +---------------------------+-----------+---------------------+
    | lunghezza payload (4 byte |  tipo     |  payload            |
    | big-endian, unsigned)     |  (1 byte) |  (lunghezza byte)   |
    +---------------------------+-----------+---------------------+

Per i frame video il payload è direttamente il JPEG: quindi un frame è
"4 byte big-endian con la lunghezza del JPEG + 1 byte di tipo + i byte JPEG".
Il byte di tipo permette di far passare sullo stesso socket anche i pochi
messaggi di controllo (hello, ping/pong, avvisi, comandi di input), che
hanno un payload JSON UTF-8.

Messaggi server -> client
    HELLO   JSON  {"app", "v", "name", "platform", "screen": [w, h], "warnings": [...]}
    FRAME   JPEG
    PONG    JSON  eco del PING ricevuto
    NOTICE  JSON  {"level": "info"|"warning"|"error", "text": "..."}
    BYE     JSON  {"reason": "..."}  (il server chiude: il client NON deve riconnettersi)

Messaggi client -> server
    INPUT   JSON  un evento di input (vedi sotto)
    PING    JSON  {"ts": <float>}  (il server risponde con PONG identico)
    CONFIG  JSON  {"quality": int, "adaptive": bool, "fps": int, "max_width": int}
                  (tutte le chiavi sono opzionali)

Eventi INPUT (coordinate x/y sempre in frazione 0.0-1.0 dello schermo remoto)
    {"t": "move", "x": 0.5, "y": 0.5}
    {"t": "btn", "b": "left"|"right"|"middle", "d": 1|0, "x": .., "y": .., "n": <n. click>}
    {"t": "scroll", "dx": int, "dy": int}            (dy > 0 = rotella in su)
    {"t": "key", "d": 1|0, "c": "a"}                 (tasto carattere)
    {"t": "key", "d": 1|0, "s": "shift_l"}           (tasto speciale, nome come pynput.keyboard.Key)
"""

from __future__ import annotations

import json
import socket
import struct

APP_ID = "remotelan"
PROTOCOL_VERSION = 1

DEFAULT_PORT = 5900        # TCP: sessione di controllo remoto
DISCOVERY_PORT = 5901      # UDP: annunci broadcast per l'auto-discovery

MAX_MESSAGE_SIZE = 64 * 1024 * 1024

# --- tipi di messaggio -------------------------------------------------------
# server -> client
MSG_HELLO = 1
MSG_FRAME = 2
MSG_PONG = 3
MSG_NOTICE = 4
MSG_BYE = 5
# client -> server
MSG_INPUT = 10
MSG_PING = 11
MSG_CONFIG = 12

_HEADER = struct.Struct(">IB")
HEADER_SIZE = _HEADER.size


class ConnectionClosed(Exception):
    """Il peer ha chiuso la connessione."""


class ProtocolError(Exception):
    """Dati ricevuti non conformi al protocollo."""


def configure_socket(sock: socket.socket, timeout: float | None) -> None:
    """Imposta le opzioni consigliate per una connessione di controllo remoto."""
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except OSError:
        pass
    sock.settimeout(timeout)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray(n)
    view = memoryview(buf)
    pos = 0
    while pos < n:
        got = sock.recv_into(view[pos:], n - pos)
        if got == 0:
            raise ConnectionClosed("connessione chiusa dall'altro capo")
        pos += got
    return bytes(buf)


def pack_message(msg_type: int, payload: bytes) -> bytes:
    return _HEADER.pack(len(payload), msg_type) + payload


def send_message(sock: socket.socket, msg_type: int, payload: bytes = b"") -> None:
    sock.sendall(pack_message(msg_type, payload))


def encode_json(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_json(payload: bytes):
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProtocolError(f"JSON non valido: {exc}") from exc


def send_json(sock: socket.socket, msg_type: int, obj) -> None:
    send_message(sock, msg_type, encode_json(obj))


def recv_message(sock: socket.socket) -> tuple[int, bytes]:
    """Riceve un messaggio completo. Restituisce (tipo, payload)."""
    length, msg_type = _HEADER.unpack(recv_exact(sock, HEADER_SIZE))
    if length > MAX_MESSAGE_SIZE:
        raise ProtocolError(f"messaggio troppo grande ({length} byte)")
    payload = recv_exact(sock, length) if length else b""
    return msg_type, payload


def parse_host_port(text: str, default_port: int = DEFAULT_PORT) -> tuple[str, int]:
    """'192.168.1.5' -> ('192.168.1.5', default); '192.168.1.5:6000' -> (.., 6000)."""
    text = text.strip()
    if not text:
        raise ValueError("indirizzo vuoto")
    if text.startswith("["):  # IPv6 [::1]:5900
        host, _, rest = text[1:].partition("]")
        port = int(rest[1:]) if rest.startswith(":") else default_port
        return host, port
    if text.count(":") == 1:
        host, port_s = text.split(":")
        if not port_s.isdigit():
            raise ValueError("porta non valida")
        return host.strip(), int(port_s)
    return text, default_port
