from enum import IntEnum

class ACMode(IntEnum):
    AUTO = 0
    HEAT = 1
    DRY = 2
    FAN = 3
    COOL = 4

    def __str__(self):
        return self._name_

class ACFanSpeed(IntEnum):
    AUTO = 0
    QUIET = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4

    def __str__(self):
        return self._name_

#Daikin and Panasonic from Luke's images
class ACManufacturer(IntEnum):
    NONE = 0
    DAIKIN = 1
    FUJITSU = 2
    PANASONIC = 7
    # NO IDEA ABOUT THESE, just going by the order listed in the installation manual
    HITACHI = 3
    LG = 4
    MITSUBISHI_ELECTRIC = 5
    # from the manual I would expect panasonic to be 6, not 7
    #PANASONIC = 6
    # added 1 to these as they come after panasonic, which is 7 now, not 6
    SAMSUNG = 8
    TOSHIBA = 9
    MITSUBISHI_HEAVY_IND = 10
        
    def __str__(self):
        return self._name_