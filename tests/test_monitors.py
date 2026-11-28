"""Prove dei monitor multipli (senza display): elenco, scelta, aggiornamento del mouse, riconnessione."""
import socket
import sys
import time
import types
import unittest

import lbsremote.injector as injector_mod
from lbsremote.client import NetSession
from lbsremote.server import AgentServer, ServerSettings, enumerate_monitors


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# quattro monitor: il principale (is_primary) NON è il primo elencato; l'ultimo va escluso (max 3)
MONITORS = [
    {"left": 0, "top": 0, "width": 4600, "height": 1200},                       # 0: tutti insieme
    {"left": 1920, "top": 0, "width": 1280, "height": 1024},                    # secondario a destra
    {"left": 0, "top": 0, "width": 1920, "height": 1080, "is_primary": True},   # principale
    {"left": -1000, "top": 0, "width": 1000, "height": 800},                    # a sinistra
    {"left": 3200, "top": 0, "width": 800, "height": 600},                      # quarto: escluso
]


class FakeShot:
    def __init__(self, mon, n):
        self.size = (mon["width"], mon["height"])
        self.bgra = bytes([n % 251, 7, 9, 0]) * (mon["width"] * mon["height"])


class FakeMSS:
    calls = 0

    def __init__(self):
        self.monitors = MONITORS

    def grab(self, mon):
        FakeMSS.calls += 1
        return FakeShot(mon, FakeMSS.calls)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class StubInjector:
    instances = []

    def __init__(self, monitor):
        self.monitor = monitor
        StubInjector.instances.append(self)

    def handle(self, ev):
        pass

    def release_all(self):
        pass


def wait_for(cond, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


class MonitorTest(unittest.TestCase):
    def test_enumeration_primary_first_max_three(self):
        found = enumerate_monitors(FakeMSS())
        self.assertEqual([m["id"] for m in found], [1, 2, 3])
        self.assertEqual((found[0]["width"], found[0]["height"]), (1920, 1080), "il principale è il n. 1")
        self.assertEqual((found[1]["width"], found[2]["width"]), (1280, 1000), "gli altri nell'ordine di mss")

    def test_select_monitor_and_resume_after_reconnect(self):
        fake = types.ModuleType("mss")
        fake.mss = FakeMSS
        old_mss = sys.modules.get("mss")
        old_inj = injector_mod.InputInjector
        sys.modules["mss"] = fake
        injector_mod.InputInjector = StubInjector
        StubInjector.instances.clear()
        port = free_port()
        server = AgentServer(ServerSettings(port=port, announce=False, fps=25, adaptive=False))
        server.start()
        events = []
        sess = NetSession("127.0.0.1", port, {}, lambda s, kind, data: events.append((kind, data)))
        try:
            sess.start()
            self.assertTrue(wait_for(lambda: sess.hello and sess.frame_size), "connessione e primo frame")
            hello = sess.hello
            self.assertEqual([m["id"] for m in hello["monitors"]], [1, 2, 3], "al massimo 3 monitor")
            self.assertEqual(hello["monitor"], 1)
            self.assertEqual(hello["screen"], [1920, 1080])
            self.assertEqual(sess.frame_size, (1920, 1080))
            self.assertEqual(StubInjector.instances[0].monitor["left"], 0)

            sess.select_monitor(2)                                  # il secondo, a destra del principale
            self.assertTrue(wait_for(lambda: sess.frame_size == (1280, 1024)), "i frame arrivano dal monitor 2")
            confirm = [d for k, d in events if k == "monitors"]
            self.assertTrue(confirm and confirm[-1]["monitor"] == 2, "l'agente conferma la scelta")
            self.assertEqual(StubInjector.instances[0].monitor["left"], 1920, "il mouse segue il monitor scelto")

            sess.select_monitor(3)
            self.assertTrue(wait_for(lambda: sess.frame_size == (1000, 800)))
            self.assertEqual(StubInjector.instances[0].monitor["left"], -1000, "coordinate negative per un monitor a sinistra")

            sess.select_monitor(4)                                  # fuori dal massimo: ignorato
            time.sleep(0.8)
            self.assertEqual(sess.frame_size, (1000, 800))

            # dopo una riconnessione si torna da soli al monitor scelto
            sess._sock.close()
            self.assertTrue(wait_for(lambda: any(k == "reconnected" for k, _ in events), 12))
            self.assertTrue(wait_for(lambda: sess.frame_size == (1000, 800)), "il monitor scelto viene ripristinato")
        finally:
            sess.stop()
            server.stop()
            injector_mod.InputInjector = old_inj
            if old_mss is None:
                sys.modules.pop("mss", None)
            else:
                sys.modules["mss"] = old_mss


if __name__ == "__main__":
    unittest.main()
