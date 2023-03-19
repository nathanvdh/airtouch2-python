import unittest

from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcMode
from airtouch2.protocol.at2plus.extended_common import SUBHEADER_LENGTH, SUBHEADER_MAGIC, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import Address, Header, MessageType, add_checksum_message_bytes
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AC_ABILITY_LENGTH, AcAbility, AcAbilityMessage, ExtendedMessageSubType, RequestAcAbilityMessage


class TestAcAbility(unittest.TestCase):
    def test(self):
        number: int = 1
        name: str = "helloworld"
        start_group: int = 3
        group_count: int = 2
        supported_modes: list[AcMode] = [AcMode.HEAT, AcMode.FAN, AcMode.COOL]
        supported_fan_speeds: list[AcFanSpeed] = [
            AcFanSpeed.AUTO, AcFanSpeed.LOW, AcFanSpeed.HIGH]
        min_setpoint: int = 17
        max_setpoint: int = 30
        raw = bytes([number, 22]) + name.encode("ascii") + \
            bytes(16-len(name)) + bytes([start_group, group_count])
        supported_modes_val: int = 0
        for mode in supported_modes:
            supported_modes_val |= 1 << mode
        supported_speeds_val: int = 0
        for speed in supported_fan_speeds:
            supported_speeds_val |= 1 << speed
        raw += bytes([supported_modes_val, supported_speeds_val,
                     min_setpoint, max_setpoint])
        ability = AcAbility.from_bytes(raw)
        self.assertEqual(number, ability.number)
        self.assertEqual(name, ability.name)
        self.assertEqual(start_group, ability.start_group)
        self.assertEqual(group_count, ability.group_count)
        self.assertEqual(supported_modes, ability.supported_modes)
        self.assertEqual(supported_fan_speeds, ability.supported_fan_speeds)
        self.assertEqual(min_setpoint, ability.min_setpoint)
        self.assertEqual(max_setpoint, ability.max_setpoint)
        self.assertEqual(raw, ability.to_bytes())


class TestAcAbilityMessage(unittest.TestCase):
    def test_response(self):
        ability = AcAbility(1, "helloworld", 3, 2, [AcMode.HEAT, AcMode.FAN, AcMode.COOL], [
                            AcFanSpeed.AUTO, AcFanSpeed.LOW, AcFanSpeed.HIGH], 17, 30)
        subdata = ability.to_bytes()
        msg = AcAbilityMessage.from_bytes(subdata)
        serialized = msg.to_bytes()
        expected_serial_msg = bytearray(Header(Address.EXTENDED, MessageType.EXTENDED,
                                        SUBHEADER_LENGTH + AC_ABILITY_LENGTH).to_bytes() + ExtendedSubHeader(ExtendedMessageSubType.ABILITY).to_bytes() + subdata + bytes([0, 0]))
        add_checksum_message_bytes(expected_serial_msg)
        self.assertEqual(serialized.hex(':'), expected_serial_msg.hex(':'))

    def test_request(self):
        msg = RequestAcAbilityMessage(3)
        serialized = msg.to_bytes()
        expected = bytearray(Header(Address.EXTENDED, MessageType.EXTENDED, SUBHEADER_LENGTH +
                                    1).to_bytes() + bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY, 3, 0, 0]))
        add_checksum_message_bytes(expected)
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

        msg = RequestAcAbilityMessage()
        serialized = msg.to_bytes()
        expected = bytearray(Header(Address.EXTENDED, MessageType.EXTENDED, SUBHEADER_LENGTH +
                                    1).to_bytes() + bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY, 0, 0]))
        add_checksum_message_bytes(expected)
