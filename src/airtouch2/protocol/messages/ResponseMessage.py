from airtouch2.protocol.messages.Message import Message
from airtouch2.protocol.constants import MessageLength, ResponseMessageConstants, ResponseMessageOffsets
from airtouch2.protocol.enums import ACBrand, ACMode

class ResponseMessage(Message):
    """ The airtouch 2 response message (there is only one) that contains all the information about the current state of the system"""
    length: MessageLength = MessageLength.RESPONSE

    # only getting things for AC1 for now
    def __init__(self, raw_response: bytes):
        super().__init__()

        status = raw_response[ResponseMessageOffsets.AC1_STATUS]
        # MS bit is on/off
        self.ac_active = [(status & 0x80 > 0)]
        # Bit 7 is whether AC is errored
        self.ac_error = [(status & 0x40 > 0)]
        self.ac_error_code = [raw_response[ResponseMessageOffsets.AC1_ERROR_CODE]]
        # bit 4 is whether or not 'thermistor on AC' is checked (0 = checked)
        self.ac_thermistor = [(status & 0x04 == 0)]
        # lowest 3 bits are AC program number
        #self.ac_program = [(status & 0x07)]

        status2 = raw_response[ResponseMessageOffsets.ACs_STATUS]
        self.ac_turbo = [(status2 & 0x20 > 0)]
        self.ac_safety = [(status2 & 0x04 > 0)]
        self.ac_spill = [(status2 & 0x02) > 0]

        # simply 0-4, see ACMode enum
        self.ac_mode = [ACMode(raw_response[ResponseMessageOffsets.AC1_MODE])]
        # most signficant byte is # of speeds, least significant byte is speed (the meaning of which depends), see AT2Aircon::_set_true_and_supported_fan_speed()
        self.ac_num_fan_speeds = [(raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0xF0) >> 4]
        self.ac_fan_speed = [raw_response[ResponseMessageOffsets.AC1_FAN_SPEED] & 0x0F]

        self.ac_set_temp = [raw_response[ResponseMessageOffsets.AC1_SET_TEMP]]
        self.ac_measured_temp = [raw_response[ResponseMessageOffsets.AC1_MEASURED_TEMP]]
        self.touchpad_temp = raw_response[ResponseMessageOffsets.TOUCHPAD_TEMP]

        self.ac_brand = [ACBrand(raw_response[ResponseMessageOffsets.AC1_BRAND])]
        self.ac_gateway_id = [raw_response[ResponseMessageOffsets.AC1_GATEWAY_ID]]

        self.ac_name = [raw_response[ResponseMessageOffsets.AC1_NAME_START:ResponseMessageOffsets.AC1_NAME_START+ResponseMessageConstants.SHORT_STRING_LENGTH].decode().split("\0")[0]]
        self.system_name = raw_response[ResponseMessageOffsets.SYSTEM_NAME:ResponseMessageOffsets.SYSTEM_NAME+ResponseMessageConstants.LONG_STRING_LENGTH].decode().split("\0")[0]

        # Group stuff
        self.num_groups = raw_response[ResponseMessageOffsets.NUM_GROUPS]
        # list of tuples: (start_zone, num_zones)
        self.group_zones = [((raw_response[offset] & 0xF0) >> 4, raw_response[offset] & 0x0F) for offset in range(ResponseMessageOffsets.GROUP_ZONES_START, ResponseMessageOffsets.GROUP_ZONES_START + 16)]
        self.zone_damps = [raw_response[offset] for offset in range(ResponseMessageOffsets.ZONE_DAMPS_START, ResponseMessageOffsets.ZONE_DAMPS_START+16)]
        self.group_names = [raw_response[offset:offset+ResponseMessageConstants.SHORT_STRING_LENGTH].decode().split("\0")[0] for offset in range(ResponseMessageOffsets.GROUP_NAMES_START, ResponseMessageOffsets.GROUP_NAMES_START+16*ResponseMessageConstants.SHORT_STRING_LENGTH, ResponseMessageConstants.SHORT_STRING_LENGTH)]
        zone_statuses = [raw_response[offset] for offset in range(ResponseMessageOffsets.ZONE_STATUSES_START, ResponseMessageOffsets.ZONE_STATUSES_START+16)]
        self.zone_ons = [(status & 0x80 > 0) for status in zone_statuses]
        self.zone_spills = [(status & 0x40 > 0) for status in zone_statuses]
        self.turbo_group = raw_response[ResponseMessageOffsets.TURBO_GROUP]
