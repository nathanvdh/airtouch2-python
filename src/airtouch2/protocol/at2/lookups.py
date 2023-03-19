from airtouch2.protocol.at2.enums import ACBrand

# I cannot find documentation of what these values actually mean
# The app prioritises this 'brand' (based on gateway id) over the other one in the message
# GATEWAY_BRAND2_LOOKUP = {
#     0x5  : 0x5,
#     0xFF : 0x5,
#     # 0x8: TETZUO (Daikin)
#     0x8  : 0x1,
#     # 0xD: me, gogreen, noirelec (fujitsu)
#     0xD  : 0x2,
#     0x22 : 0x2,
#     # 0xF: ruaandeysel (mitsubishi electric)
#     0xF  : 0x6,
#     0x10 : 0x4,
#     # 0x12 dmitry - (samsung)
#     0x12 : 0xE,
#     0x14 : 0xC,
#     0x15 : 0x7,
#     0x1F : 0xA,
#     0xE0 : 0xB,
#     0xE1 : 0xD
# }

# Lookup between the gateway ID and what brand I think it is
GATEWAYID_BRAND_LOOKUP = {
    0x8  : ACBrand.DAIKIN,
    0xD  : ACBrand.FUJITSU,
    0x22 : ACBrand.FUJITSU,
    0xF  : ACBrand.MITSUBISHI_ELECTRIC,
    0x12  : ACBrand.SAMSUNG
}