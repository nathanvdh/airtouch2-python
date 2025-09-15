import unittest
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubType
from airtouch2.protocol.at2plus.messages.Ack import Ack


class TestAck(unittest.TestCase):
    def _test_common(self, message_type: ControlStatusSubType):
        ack = Ack(message_type)
        serialised = ack.to_bytes()
        expected = bytes([
            0x55, 0x55, 0x80, 0xb0, 0x01, 0xc0, 0x00, 0x09,
            # ControlStatusSubheader with matching sub message type
            # Static, 1-byte, zero payload.
            int(message_type), 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        self.assertEqual(serialised[:-2].hex(':'), expected.hex(':'))

    def test_ac_status2(self):
        # aramshaw says this requires an extra payload byte
        self._test_common(ControlStatusSubType.AC_STATUS2)

    def test_system_status(self):
        self._test_common(ControlStatusSubType.SYSTEM_STATUS)

    def test_system_id(self):
        self._test_common(ControlStatusSubType.SYSTEM_ID)

    def test_zone_status(self):
        self._test_common(ControlStatusSubType.ZONE_STATUS)
