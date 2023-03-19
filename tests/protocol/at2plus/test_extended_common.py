import unittest

from airtouch2.protocol.at2plus.extended_common import SUBHEADER_MAGIC, ExtendedMessageSubType, ExtendedSubHeader

class TestExtendedSubHeader(unittest.TestCase):
    def test_serialize(self):
        subheader = ExtendedSubHeader(ExtendedMessageSubType.ABILITY)
        serialized = subheader.to_bytes()
        expected = bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY])
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

    def test_deserialize(self):
        raw = bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY])
        subheader = ExtendedSubHeader.from_bytes(raw)
        serialized = subheader.to_bytes()
        self.assertEqual(raw.hex(':'), serialized.hex(':'))