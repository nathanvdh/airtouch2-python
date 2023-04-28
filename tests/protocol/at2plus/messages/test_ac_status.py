import unittest
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubType, SubDataLength, ControlStatusSubHeader
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_bytes

from airtouch2.protocol.at2plus.messages.AcStatus import AC_STATUS_LENGTH, AcStatus, AcPower, AcMode, AcFanSpeed, AcStatusMessage


class TestAcStatus(unittest.TestCase):
    def test_serialize(self):
        status = AcStatus(1, AcPower.AWAY_OFF, AcMode.AUTO_COOL,
                          AcFanSpeed.MEDIUM, 23, 25, False, False, True, True, 15)
        expected = bytes([(2 << 4 | 1), (9 << 4 | 3), 130, 3]) + \
            (750).to_bytes(2, 'big') + (15).to_bytes(2, 'big') + bytes([0, 0])
        self.assertEqual(status.to_bytes().hex(':'), expected.hex(':'))

        status2 = AcStatus(2, AcPower.ON, AcMode.HEAT,
                           AcFanSpeed.QUIET, 23, 17, False, True, False, True, 0)
        expected2 = bytes([(1 << 4 | 2), (1 << 4 | 1), 130, 5]) + \
            (670).to_bytes(2, 'big') + bytes([0, 0, 0, 0])
        self.assertEqual(status2.to_bytes().hex(':'), expected2.hex(':'))

    def test_deserialize(self):
        raw1 = bytes([(2 << 4 | 1), (9 << 4 | 3), 130, 3]) + \
            (750).to_bytes(2, 'big') + (15).to_bytes(2, 'big') + bytes([0, 0])
        status1 = AcStatus.from_bytes(raw1)
        self.assertEqual(status1.to_bytes().hex(':'), raw1.hex(':'))

        raw2 = bytes([(1 << 4 | 2), (1 << 4 | 1), 130, 5]) + \
            (670).to_bytes(2, 'big') + bytes([0, 0, 0, 0])
        status2 = AcStatus.from_bytes(raw2)
        self.assertEqual(status2.to_bytes().hex(':'), raw2.hex(':'))


class TestAcStatusMessage(unittest.TestCase):
    def test_serialize(self):
        status1 = AcStatus(1, AcPower.AWAY_OFF, AcMode.AUTO_COOL,
                           AcFanSpeed.MEDIUM, 23, 25, False, False, True, True, 15)
        expected1 = bytes([(2 << 4 | 1), (9 << 4 | 3), 130, 3]) + \
            (750).to_bytes(2, 'big') + (15).to_bytes(2, 'big') + bytes([0, 0])

        status2 = AcStatus(2, AcPower.ON, AcMode.HEAT,
                           AcFanSpeed.QUIET, 23, 17, False, True, False, True, 0)
        expected2 = bytes([(1 << 4 | 2), (1 << 4 | 1), 130, 5]) + \
            (670).to_bytes(2, 'big') + bytes([0, 0, 0, 0])

        msg = AcStatusMessage([status1, status2])
        expected_serial_msg = bytearray(Header(AddressMsgType.NORMAL,
                                               MessageType.CONTROL_STATUS,
                                               CONTROL_STATUS_SUBHEADER_LENGTH + 2*AC_STATUS_LENGTH).to_bytes() +
                                        ControlStatusSubHeader(ControlStatusSubType.AC_STATUS, SubDataLength(0, 2, AC_STATUS_LENGTH)).to_bytes() +
                                        expected1 + expected2 + bytes([0, 0]))
        add_checksum_message_bytes(expected_serial_msg)
        self.assertEqual(msg.to_bytes().hex(':'), expected_serial_msg.hex(':'))

    def test_deserialize(self):
        status1 = AcStatus(1, AcPower.AWAY_OFF, AcMode.AUTO_COOL,
                           AcFanSpeed.MEDIUM, 23, 25, False, False, True, True, 15)
        status2 = AcStatus(2, AcPower.ON, AcMode.HEAT,
                           AcFanSpeed.QUIET, 23, 17, False, True, False, True, 0)
        subdata = status1.to_bytes() + status2.to_bytes()
        msg = AcStatusMessage.from_bytes(subdata)
        expected_serial_msg = bytearray(Header(AddressMsgType.NORMAL,
                                               MessageType.CONTROL_STATUS,
                                               CONTROL_STATUS_SUBHEADER_LENGTH + 2*AC_STATUS_LENGTH).to_bytes() +
                                        ControlStatusSubHeader(ControlStatusSubType.AC_STATUS, SubDataLength(0, 2, AC_STATUS_LENGTH)).to_bytes() +
                                        subdata[0:10] + subdata[10:] + bytes([0, 0]))
        add_checksum_message_bytes(expected_serial_msg)
        self.assertEqual(msg.to_bytes().hex(':'), expected_serial_msg.hex(':'))

    class RequestAcStatusMessage(unittest.TestCase):
        def test_request(self):
            msg = AcStatusMessage([])
            serialization = msg.to_bytes()
            expected_serial_msg = bytearray(Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, CONTROL_STATUS_SUBHEADER_LENGTH).to_bytes() +
                                            ControlStatusSubHeader(ControlStatusSubType.AC_STATUS, SubDataLength(
                                                0, 0, 0)).to_bytes() + bytes([0, 0])
                                            )
            add_checksum_message_bytes(expected_serial_msg)

            self.assertEqual(serialization, expected_serial_msg)
