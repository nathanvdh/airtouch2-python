import unittest

from airtouch2.protocol.at2plus.enums import AcFanSpeed, AcMode
from airtouch2.protocol.at2plus.extended_common import EXTENDED_SUBHEADER_LENGTH, SUBHEADER_MAGIC, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import Address, Header, MessageType, add_checksum_message_bytes
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbilitySubDataLength, AcAbility, AcAbilityMessage, DualSetpointLimits, ExtendedMessageSubType, RequestAcAbilityMessage, SetpointLimits


class TestAcAbility(unittest.TestCase):
    def test_v1(self):
        number: int = 1
        name: str = "helloworld"
        start_group: int = 3
        group_count: int = 2
        supported_modes: list[AcMode] = [AcMode.HEAT, AcMode.FAN, AcMode.COOL]
        supported_fan_speeds: list[AcFanSpeed] = [
            AcFanSpeed.AUTO, AcFanSpeed.LOW, AcFanSpeed.HIGH]
        min_setpoint: int = 17
        max_setpoint: int = 30
        raw = bytes([number, AcAbilitySubDataLength.V1 - 2]) + name.encode("ascii") + \
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
        self.assertEqual(number, ability.ac_number)
        self.assertEqual(name, ability.name)
        self.assertEqual(start_group, ability.start_group)
        self.assertEqual(group_count, ability.group_count)
        self.assertEqual(supported_modes, ability.supported_modes)
        self.assertEqual(supported_fan_speeds, ability.supported_fan_speeds)
        self.assertTrue(isinstance(ability.setpoint_limits, SetpointLimits))
        assert(isinstance(ability.setpoint_limits, SetpointLimits)) # for type checking
        self.assertEqual(min_setpoint, ability.setpoint_limits.min)
        self.assertEqual(max_setpoint, ability.setpoint_limits.max)
        self.assertEqual(raw, ability.to_bytes())

    def test_v1_1(self):
        number: int = 1
        name: str = "helloworld"
        start_group: int = 3
        group_count: int = 2
        supported_modes: list[AcMode] = [AcMode.HEAT, AcMode.FAN, AcMode.COOL]
        supported_fan_speeds: list[AcFanSpeed] = [
            AcFanSpeed.AUTO, AcFanSpeed.LOW, AcFanSpeed.HIGH]
        min_setpoint_cool: int = 17
        max_setpoint_cool: int = 25
        min_setpoint_heat: int = 22
        max_setpoint_heat: int = 30
        raw = bytes([number, AcAbilitySubDataLength.V1_1 - 2]) + name.encode("ascii") + \
            bytes(16-len(name)) + bytes([start_group, group_count])
        supported_modes_val: int = 0
        for mode in supported_modes:
            supported_modes_val |= 1 << mode
        supported_speeds_val: int = 0
        for speed in supported_fan_speeds:
            supported_speeds_val |= 1 << speed
        raw += bytes([supported_modes_val, supported_speeds_val,
                     min_setpoint_cool, max_setpoint_cool, min_setpoint_heat, max_setpoint_heat])
        ability = AcAbility.from_bytes(raw)
        self.assertEqual(number, ability.ac_number)
        self.assertEqual(name, ability.name)
        self.assertEqual(start_group, ability.start_group)
        self.assertEqual(group_count, ability.group_count)
        self.assertEqual(supported_modes, ability.supported_modes)
        self.assertEqual(supported_fan_speeds, ability.supported_fan_speeds)
        self.assertTrue(isinstance(ability.setpoint_limits, DualSetpointLimits))
        assert(isinstance(ability.setpoint_limits, DualSetpointLimits)) # for type checking
        self.assertEqual(min_setpoint_cool, ability.setpoint_limits.cool.min)
        self.assertEqual(max_setpoint_cool, ability.setpoint_limits.cool.max)
        self.assertEqual(min_setpoint_heat, ability.setpoint_limits.heat.min)
        self.assertEqual(max_setpoint_heat, ability.setpoint_limits.heat.max)
        self.assertEqual(raw.hex(':'), ability.to_bytes().hex(':'))


class TestAcAbilityMessage(unittest.TestCase):
    def test_response(self):
        ability = AcAbility(1, "helloworld", 3, 2, [AcMode.HEAT, AcMode.FAN, AcMode.COOL], [
                            AcFanSpeed.AUTO, AcFanSpeed.LOW, AcFanSpeed.HIGH], SetpointLimits(17, 30))
        subdata = ability.to_bytes()
        msg = AcAbilityMessage.from_bytes(subdata)
        serialized = msg.to_bytes()
        expected_serial_msg = bytearray(
            Header(
                Address.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH +
                AcAbilitySubDataLength.V1).to_bytes() +
            ExtendedSubHeader(ExtendedMessageSubType.ABILITY).to_bytes() + subdata +
            bytes([0, 0]))
        add_checksum_message_bytes(expected_serial_msg)
        self.assertEqual(serialized.hex(':'), expected_serial_msg.hex(':'))

    def test_request(self):
        msg = RequestAcAbilityMessage(3)
        serialized = msg.to_bytes()
        expected = bytearray(Header(Address.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH +
                                    1).to_bytes() + bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY, 3, 0, 0]))
        add_checksum_message_bytes(expected)
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

        msg = RequestAcAbilityMessage()
        serialized = msg.to_bytes()
        expected = bytearray(Header(Address.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH +
                                    1).to_bytes() + bytes([SUBHEADER_MAGIC, ExtendedMessageSubType.ABILITY, 0, 0]))
        add_checksum_message_bytes(expected)
