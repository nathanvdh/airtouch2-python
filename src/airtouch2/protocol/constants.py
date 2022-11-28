
from enum import IntEnum

class MessageLength(IntEnum):
    UNDETERMINED = 0
    COMMAND = 13
    RESPONSE = 395

class CommandMessageConstants(IntEnum):
    BYTE_0 = 85                  # Byte 0 of command always fixed
    BYTE_2 = 12                  # Byte 2 of command always fixed
    TOGGLE = 128                 # Toggle on/off in byte 4
    BYTE_5_GRP_POS = 1           # In Position dec/inc command, byte 5 is fixed
    BYTE_4_GRP_POSDEC = 1        # Position decrement (5% down) in byte 4
    BYTE_4_GRP_POSINC = 2        # Position increment (5% up) in byte 4

# Go in byte 1 of command messages
class CommandMessageType(IntEnum):
    REQUEST_STATE = 1
    ZONE_CONROL = 129
    AC_CONTROL = 134

# Go in byte 4 of CommandMessageType.AC_CONTROL messages
class ACControlCommands(IntEnum):
    SET_MODE = 129
    SET_FAN_SPEED = 130
    TEMP_DEC = 147
    TEMP_INC = 163

class ResponseMessageConstants(IntEnum):
    LONG_STRING_LENGTH = 16
    SHORT_STRING_LENGTH = 8

# Thanks to home-assistant.io user Radebe2k
class ResponseMessageOffsets(IntEnum):
    # Header is 2 bytes
    HEADER = 0

    # There are 16 zones
    # zone names are 8 bytes (ResponseMessageConstants.SHORT_STRING_LENGTH)
    ZONE_NAMES_START = 100
    # zone statuses are 1 byte each
    ZONE_STATUSES_START = 228
    # Zone strengths are 1 byte each
    ZONE_STRENGTHS_START = 276

    # System name is 16 bytes (ResponseMessageConstants.LONG_STRING_LENGTH)
    SYSTEM_NAME = 324

    # Contains isTurbo, isSafety, isSpill bits of the 2 ACs
    ACs_STATUS = 299
    TOUCHPAD_TEMP = 323 # I think?? Idk what happens when there's 2 touchpads then...
    # On/Off, isError, 'Auto off' enabled, 'thermistor on AC', program number
    AC1_STATUS = 354
    #AC2_STATUS = 355
    AC1_MODE = 358
    #AC2_MODE = 359
    AC1_FAN_SPEED = 360
    #AC2_FAN_SPEED = 361
    AC1_SET_TEMP = 362
    #AC2_SET_TEMP = 363
    AC1_MEASURED_TEMP = 364
    #AC2_MEASURED_TEMP = 365
    AC1_BRAND = 356
    #AC2_BRAND = 357
    AC1_ERROR_CODE = 366
    #AC2_ERROR_CODE = 367
    AC1_GATEWAY_ID = 368
    #AC2_GATEWAY_ID = 369
    # AC names are 8 bytes (ResponseMessageConstants.SHORT_STRING_LENGTH)
    AC1_NAME_START = 370
    #AC2_NAME_START = 378
    HASH = 394
