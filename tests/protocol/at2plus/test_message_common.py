import unittest
from airtouch2.protocol.at2plus.message_common import AddressMsgType, AddressSource, HEADER_MAGIC, MESSAGE_ID, Header, MessageType

class TestHeader(unittest.TestCase):
    def test_serialize(self):
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, 15)
        serialized = header.to_bytes()
        
        expected = bytes([HEADER_MAGIC, HEADER_MAGIC, AddressMsgType.NORMAL, AddressSource.SELF]) + bytes([MESSAGE_ID, MessageType.CONTROL_STATUS]) + (15).to_bytes(2, 'big')
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

    def test_deserialize(self):
        raw = bytes([HEADER_MAGIC, HEADER_MAGIC, AddressSource.SELF, AddressMsgType.NORMAL]) + bytes([MESSAGE_ID, MessageType.CONTROL_STATUS]) + (15).to_bytes(2, 'big')
        header = Header.from_bytes(raw)

        self.assertEqual(raw.hex(':'), header.to_bytes().hex(':'))
