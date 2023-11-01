import unittest

from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.protocol.at2plus.enums import GroupPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_bytes

from airtouch2.protocol.at2plus.messages.GroupStatus import GROUP_STATUS_LENGTH, GroupStatus, GroupStatusMessage


class TestGroupStatus(unittest.TestCase):
    def test_serialize(self):
        status = GroupStatus(1, GroupPower.ON, 80, True, False)
        expected = bytes([1 << 6 | 1, 80, 0, 0, 0, 0, 1 << 7, 0])
        self.assertEqual(status.to_bytes().hex(':'), expected.hex(':'))

    def test_deserialize(self):
        raw = bytes([1 << 6 | 1, 80, 0, 0, 0, 0, 1 << 7, 0])
        status = GroupStatus.from_bytes(raw)
        self.assertEqual(status.to_bytes().hex(':'), raw.hex(':'))


class TestGroupStatusMessage(unittest.TestCase):
    def test_serialize(self):
        status1 = GroupStatus(1, GroupPower.ON, 80, True, False)
        status2 = GroupStatus(2, GroupPower.TURBO, 75, True, True)

        msg = GroupStatusMessage([status1, status2])
        expected = bytearray(
            Header(
                AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, CONTROL_STATUS_SUBHEADER_LENGTH + 2 *
                GROUP_STATUS_LENGTH).to_bytes() +
            ControlStatusSubHeader(
                ControlStatusSubType.GROUP_STATUS, SubDataLength(0, 2, GROUP_STATUS_LENGTH)).to_bytes()
            + status1.to_bytes() + status2.to_bytes() + bytes([0, 0]))
        add_checksum_message_bytes(expected)

        self.assertEqual(msg.to_bytes().hex(':'), expected.hex(':'))

    def test_deserialize(self):
        status1 = GroupStatus(1, GroupPower.ON, 80, True, False)
        status2 = GroupStatus(2, GroupPower.TURBO, 75, True, True)
        subdata = status1.to_bytes() + status2.to_bytes()

        msg = GroupStatusMessage.from_bytes(subdata)
        expected = bytearray(
            Header(
                AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, CONTROL_STATUS_SUBHEADER_LENGTH + 2 *
                GROUP_STATUS_LENGTH).to_bytes() +
            ControlStatusSubHeader(
                ControlStatusSubType.GROUP_STATUS, SubDataLength(0, 2, GROUP_STATUS_LENGTH)).to_bytes() +
            subdata[0: GROUP_STATUS_LENGTH] + subdata[GROUP_STATUS_LENGTH:] + bytes([0, 0]))
        add_checksum_message_bytes(expected)

        self.assertEqual(msg.to_bytes().hex(':'), expected.hex(':'))
