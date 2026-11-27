"""Prove di robustezza (senza display): cattura che fallisce e riconnessioni in ciclo.

    python -m unittest discover -s tests
"""
import socket
import sys
import threading
import time
import types
import unittest

from lbsremote import client as client_mod
from lbsremote import protocol as P
from lbsremote.client import NetSession
from lbsremote.server import AgentServer, ServerSettings


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeShot:
    def __init__(self, n: int):
        self.size = (64, 48)
        self.bgra = bytes([n % 251, 10, 20, 0]) * (64 * 48)


class FakeMSS:
    """Finto "mss": la cattura fallisce per alcune chiamate, come BitBlt su un PC bloccato."""
    calls = 0
    created = 0
    fail_from, fail_to = 4, 9

    def __init__(self):
        FakeMSS.created += 1
        self.monitors = [{}, {"left": 0, "top": 0, "width": 64, "height": 48}]

    def grab(self, mon):
        FakeMSS.calls += 1
        if FakeMSS.fail_from <= FakeMSS.calls <= FakeMSS.fail_to:
            raise RuntimeError("Windows graphics function failed (no error provided): BitBlt")
        return FakeShot(FakeMSS.calls)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class CaptureFailureTest(unittest.TestCase):
    def test_session_survives_capture_failure(self):
        fake = types.ModuleType("mss")
        fake.mss = FakeMSS
        old = sys.modules.get("mss")
        sys.modules["mss"] = fake
        FakeMSS.calls = FakeMSS.created = 0
        port = free_port()
        server = AgentServer(ServerSettings(port=port, announce=False, fps=20, adaptive=False))
        server.start()
        events = []
        sess = NetSession("127.0.0.1", port, {}, lambda s, kind, data: events.append((kind, data)))
        try:
            sess.start()
            deadline = time.time() + 15
            while time.time() < deadline:
                kinds = [k for k, _ in events]
                if "notice" in kinds and sess.frame_seq > 8 and sum(1 for k, d in events if k == "notice") >= 2:
                    break
                time.sleep(0.1)
            kinds = [k for k, _ in events]
            self.assertIn("connected", kinds)
            self.assertNotIn("reconnecting", kinds, "la sessione non deve cadere quando la cattura fallisce")
            self.assertNotIn("closed", kinds)
            notices = [d for k, d in events if k == "notice"]
            warn = [n for n in notices if n.get("level") == "warning" and n.get("id") == "capture"]
            self.assertEqual(len(warn), 1, "un solo avviso per episodio, non uno per tentativo")
            self.assertTrue(any(n.get("level") == "info" for n in notices), "avviso di cattura ripristinata")
            self.assertGreater(sess.frame_seq, 8, "dopo il ripristino i frame riprendono")
            self.assertGreaterEqual(FakeMSS.created, 3, "l'oggetto di cattura viene ricreato dopo l'errore")
        finally:
            sess.stop()
            server.stop()
            if old is None:
                sys.modules.pop("mss", None)
            else:
                sys.modules["mss"] = old


class FlappingAgentTest(unittest.TestCase):
    def test_client_gives_up_instead_of_reconnecting_forever(self):
        port = free_port()
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(8)
        srv.settimeout(0.2)
        accepted = []
        stop = threading.Event()

        def serve():
            while not stop.is_set():
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                accepted.append(time.time())
                try:
                    P.send_json(conn, P.MSG_HELLO, {"app": P.APP_ID, "v": 1, "name": "FLAP", "platform": "win32",
                                                    "screen": [64, 48], "warnings": []})
                    P.send_json(conn, P.MSG_NOTICE, {"level": "warning", "text": "capture failed"})
                finally:
                    conn.close()

        threading.Thread(target=serve, daemon=True).start()
        old_delay = client_mod.RECONNECT_DELAY
        client_mod.RECONNECT_DELAY = 0.4
        events = []
        sess = NetSession("127.0.0.1", port, {}, lambda s, kind, data: events.append((kind, data)))
        try:
            t0 = time.time()
            sess.start()
            while time.time() - t0 < 20 and not any(k == "closed" for k, _ in events):
                time.sleep(0.1)
            closed = [d for k, d in events if k == "closed"]
            self.assertTrue(closed, "il client deve smettere di riprovare")
            self.assertIn("keeps closing the connection", closed[0])
            self.assertIn("capture failed", closed[0], "il messaggio riporta l'ultimo avviso dell'agente")
            self.assertLessEqual(len(accepted), 4, f"troppi tentativi: {len(accepted)}")
            gaps = [b - a for a, b in zip(accepted, accepted[1:])]
            self.assertTrue(all(g >= 0.3 for g in gaps), f"pausa tra i tentativi mancante: {gaps}")
        finally:
            sess.stop()
            stop.set()
            srv.close()
            client_mod.RECONNECT_DELAY = old_delay


if __name__ == "__main__":
    unittest.main()
