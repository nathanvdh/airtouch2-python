from pprint import pprint
import unittest

from airtouch2.protocol.at2plus.messages.GroupNames import RequestGroupNamesMessage, group_names_from_subdata


class TestDeserialize(unittest.TestCase):
    def test_deserialize(self):
        data = bytearray(b'\x00Dining\x00\x00\x01Study\x00\x00\x00\x02Master\x00\x00\x03'
                         b'Theatre\x00\x04Kitchen\x00\x05Lounge\x00\x00\x06Bedrooms')
        expected: dict[int, str] = {
            0: 'Dining',
            1: 'Study',
            2: 'Master',
            3: 'Theatre',
            4: 'Kitchen',
            5: 'Lounge',
            6: 'Bedrooms'
        }
        self.assertEqual(group_names_from_subdata(data), expected)


class TestRequestGroupNamesMessage(unittest.TestCase):
    def test_serialize(self):
        msg = RequestGroupNamesMessage()
        expected = bytes([0x55, 0x55, 0x90, 0xb0, 0x01, 0x1f, 0x00, 0x02, 0xff, 0x12, 0x82, 0x0c])
        self.assertEqual(msg.to_bytes().hex(':'), expected.hex(':'))
