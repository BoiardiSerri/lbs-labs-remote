"""Test senza display: python -m unittest discover -s tests"""
import socket
import threading
import unittest

from lbsremote import protocol as p


class ProtocolTest(unittest.TestCase):
    def test_roundtrip(self):
        a, b = socket.socketpair()
        with a, b:
            jpeg = bytes(range(256)) * 1000
            t = threading.Thread(target=lambda: (p.send_message(a, p.MSG_FRAME, jpeg),
                                                 p.send_json(a, p.MSG_INPUT, {"t": "move", "x": 0.5})))
            t.start()
            self.assertEqual(p.recv_message(b), (p.MSG_FRAME, jpeg))
            kind, payload = p.recv_message(b)
            self.assertEqual((kind, p.decode_json(payload)), (p.MSG_INPUT, {"t": "move", "x": 0.5}))
            t.join()

    def test_frame_header_is_big_endian_length(self):
        data = p.pack_message(p.MSG_FRAME, b"\xff\xd8abc")
        self.assertEqual(data[:4], (5).to_bytes(4, "big"))
        self.assertEqual(data[4], p.MSG_FRAME)

    def test_closed(self):
        a, b = socket.socketpair()
        a.close()
        with b, self.assertRaises(p.ConnectionClosed):
            p.recv_message(b)

    def test_parse_host_port(self):
        self.assertEqual(p.parse_host_port("192.168.1.5"), ("192.168.1.5", 5970))
        self.assertEqual(p.parse_host_port(" 10.0.0.2:6000 "), ("10.0.0.2", 6000))
        self.assertEqual(p.parse_host_port("demo-pc", 7000), ("demo-pc", 7000))
        with self.assertRaises(ValueError):
            p.parse_host_port("1.2.3.4:abc")


class JpegSizeTest(unittest.TestCase):
    def test_size(self):
        import io
        from PIL import Image
        from lbsremote.client import _jpeg_size
        buf = io.BytesIO()
        Image.new("RGB", (1234, 567)).save(buf, "JPEG")
        self.assertEqual(_jpeg_size(buf.getvalue()), (1234, 567))


if __name__ == "__main__":
    unittest.main()
