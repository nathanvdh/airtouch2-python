import unittest
from airtouch2.protocol.at2plus.constants import Limits

from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.protocol.at2plus.enums import GroupSetDamper, GroupSetPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_bytes
from airtouch2.protocol.at2plus.messages.GroupControl import GROUP_SETTINGS_LENGTH, GroupControlMessage, GroupSettings


class TestGroupSettings(unittest.TestCase):
    def setUp(self) -> None:
        # some values to reuse in all tests
        self.group = 3
        self.damp_mode = GroupSetDamper.SET
        self.power = GroupSetPower.ON
        self.damp = 85

    def test_errors(self):
        # Should not be constructable with values outside limits
        self.assertRaises(ValueError, GroupSettings, self.group, self.damp_mode, self.power, 101)
        self.assertRaises(ValueError, GroupSettings, self.group, self.damp_mode, self.power, -1)
        self.assertRaises(ValueError, GroupSettings, 16, self.damp_mode, self.power, self.damp)
        self.assertRaises(ValueError, GroupSettings, -1, self.damp_mode, self.power, self.damp)

    def test_serialize(self):
        settings = GroupSettings(self.group, self.damp_mode, self.power, self.damp)
        serialized = settings.to_bytes()
        expected = bytes([self.group, (self.damp_mode << 5) | (self.power), self.damp, 0])
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

        # test with different values, notably using GroupSetDamper.INC and providing no damp
        group = 10
        damp_mode = GroupSetDamper.INC
        power = GroupSetPower.UNCHANGED
        damp = None
        settings = GroupSettings(group, damp_mode, power, damp)
        serialized = settings.to_bytes()
        expected = bytes([group, (damp_mode << 5) | (power), 255, 0])

    def test_deserialize(self):
        raw = bytes([self.group, (self.damp_mode << 5) | (self.power), self.damp, 0])
        settings = GroupSettings(self.group, self.damp_mode, self.power, self.damp)
        serialized = settings.to_bytes()
        self.assertEqual(raw.hex(':'), serialized.hex(':'))


class TestGroupControlMessage(unittest.TestCase):
    def test_serialize(self):
        group1 = 3
        damp_mode1 = GroupSetDamper.SET
        power1 = GroupSetPower.ON
        damp1 = 85
        settings1 = GroupSettings(group1, damp_mode1, power1, damp1)
        expected1 = bytes([group1, (damp_mode1 << 5) | (power1), damp1, 0])
        group2 = 10
        damp_mode2 = GroupSetDamper.INC
        power2 = GroupSetPower.UNCHANGED
        damp2 = None
        settings2 = GroupSettings(group2, damp_mode2, power2, damp2)
        expected2 = bytes([group2, (damp_mode2 << 5) | (power2), 255, 0])
        settings = [settings1, settings2]
        msg = GroupControlMessage(settings)
        serialized = msg.to_bytes()
        expected = bytearray(
            Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, CONTROL_STATUS_SUBHEADER_LENGTH + 2*GROUP_SETTINGS_LENGTH).to_bytes() +
            ControlStatusSubHeader(ControlStatusSubType.GROUP_CONTROL, SubDataLength(0, 2, GROUP_SETTINGS_LENGTH)).to_bytes() +
            expected1 + expected2 + bytes([0, 0])
        )
        add_checksum_message_bytes(expected)
        self.assertEqual(serialized.hex(':'), expected.hex(':'))
