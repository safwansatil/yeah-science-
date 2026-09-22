import unittest

from link.packets import decode, encode


class PacketTests(unittest.TestCase):
    def test_drive_roundtrip(self):
        packet = decode(encode("drive", 4, left=-0.5, right=1.0))
        self.assertEqual((packet["seq"], packet["left"], packet["right"]), (4, -0.5, 1))

    def test_bad_input_is_rejected(self):
        cases = [b"noise", b"{}", b"[]", b"null", b"x" * 2049,
                 b'{"v":1,"type":"drive","seq":1,"left":NaN,"right":0}',
                 b'{"v":1,"type":"drive","seq":1,"left":true,"right":0}']
        for raw in cases:
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                decode(raw)

    def test_out_of_range_commands_do_not_cross_wire(self):
        for value in (-1.1, 2, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                encode("drive", 0, left=value, right=0)

    def test_telemetry_requires_all_fields(self):
        with self.assertRaises(ValueError):
            encode("telemetry", 0, battery=12.5)


if __name__ == "__main__":
    unittest.main()
