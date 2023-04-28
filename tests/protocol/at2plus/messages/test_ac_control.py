
import unittest
from airtouch2.protocol.at2plus.constants import Limits
from airtouch2.protocol.at2plus.control_status_common import CONTROL_STATUS_SUBHEADER_LENGTH, ControlStatusSubType, SubDataLength, ControlStatusSubHeader

from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcSetMode, AcSetPower
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_bytes
from airtouch2.protocol.at2plus.messages.AcControl import AC_SETTINGS_LENGTH, AcControlMessage, AcSettings


class TestAcSettings(unittest.TestCase):
    def test_serialize(self):
        ac = 3
        power = AcSetPower.ON
        mode = AcSetMode.HEAT
        speed = AcFanSpeed.MEDIUM
        setpoint = 22

        # Should not be constructable with values outside limits
        self.assertRaises(ValueError, AcSettings, ac, power,
                          mode, speed, Limits.SETPOINT_MAX + 10)
        self.assertRaises(ValueError, AcSettings, ac, power,
                          mode, speed, Limits.SETPOINT_MIN - 10)
        self.assertRaises(ValueError, AcSettings,
                          Limits.MAX_ACS+1, power, mode, speed)
        self.assertRaises(ValueError, AcSettings,
                          -1, power, mode, speed)

        # simple serialization test
        settings = AcSettings(ac, power, mode, speed, setpoint)
        serialized = settings.to_bytes()
        expected = bytes([(3 << 4) | 3, (1 << 4) | 3, 0x40, 120])

        self.assertEqual(serialized.hex(':'), expected.hex(':'))

        # test with different values, notably without setpoing
        ac = 2
        power = AcSetPower.OFF
        mode = AcSetMode.AUTO
        speed = AcFanSpeed.POWERFUL

        settings = AcSettings(ac, power, mode, speed)
        serialized = settings.to_bytes()
        expected = bytes([(2 << 4) | 2, (0 << 4) | 5, 0,
                         Limits.SETPOINT_MAX * 10 - 100 + 1])

        self.assertEqual(serialized.hex(":"), expected.hex(":"))

    def test_deserialize(self):
        raw = bytes([(3 << 4) | 3, (1 << 4) | 3, 0x40, 120])
        settings = AcSettings.from_bytes(raw)
        serialized = settings.to_bytes()
        self.assertEqual(raw.hex(':'), serialized.hex(':'))


class TestAcControlMessage(unittest.TestCase):
    def test_serialize(self):
        settings1 = AcSettings(
            3, AcSetPower.ON, AcSetMode.HEAT, AcFanSpeed.MEDIUM, 23)
        expected1 = bytes([(3 << 4) | 3, (1 << 4) | 3, 0x40, 130])
        settings2 = AcSettings(7, AcSetPower.SLEEP,
                               AcSetMode.FAN, AcFanSpeed.TURBO)
        expected2 = bytes([(5 << 4) | 7, (3 << 4) | 6, 0,
                          Limits.SETPOINT_MAX * 10 - 100 + 1])
        settings = [settings1, settings2]
        msg = AcControlMessage(settings)
        serialized = msg.to_bytes()
        expected = bytearray(Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS,
                             CONTROL_STATUS_SUBHEADER_LENGTH + 2*AC_SETTINGS_LENGTH).to_bytes() +
                             ControlStatusSubHeader(ControlStatusSubType.AC_CONTROL, SubDataLength(0, 2, AC_SETTINGS_LENGTH)).to_bytes() +
                             expected1 + expected2 + bytes([0, 0]))
        add_checksum_message_bytes(expected)
        self.assertEqual(serialized.hex(':'), expected.hex(':'))
