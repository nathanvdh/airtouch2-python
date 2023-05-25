import unittest
from airtouch2.protocol.at2plus.crc16_modbus import crc16


class CrcTest(unittest.TestCase):
    def test_crc16(self):
        self.assertEqual(crc16(b"helloworld"),
                         (0xCAA3).to_bytes(2, byteorder='big'))
        self.assertEqual(crc16(b"abcdefghijklmnop"),
                         (0x768D).to_bytes(2, byteorder='big'))
