from airtouch2.common.interfaces import Serializable
from airtouch2.protocol.at2plus.extended_common import EXTENDED_SUBHEADER_LENGTH, ExtendedMessageSubType, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import AddressMsgType, Header, MessageType, add_checksum_message_buffer, prime_message_buffer


def group_names_from_subdata(subdata: bytes) -> dict[int, str]:
    return {subdata[i]: subdata[i+1:i+9].decode('ascii').split("\x00")[0] for i in range(0, len(subdata), 9)}


class RequestGroupNamesMessage(Serializable):

    def to_bytes(self) -> bytes:
        buffer = prime_message_buffer(
            Header(AddressMsgType.EXTENDED, MessageType.EXTENDED, EXTENDED_SUBHEADER_LENGTH))
        buffer.append(ExtendedSubHeader(ExtendedMessageSubType.GROUP_NAME))
        add_checksum_message_buffer(buffer)
        return buffer.to_bytes()
