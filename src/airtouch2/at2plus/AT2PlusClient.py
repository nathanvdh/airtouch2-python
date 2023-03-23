
import asyncio
from datetime import datetime
import errno
import logging
from socket import gaierror
from typing import Callable

from airtouch2.at2plus.AT2PlusAircon import At2PlusAircon
from airtouch2.protocol.at2plus.message_common import HEADER_LENGTH
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubType, ControlStatusSubHeader
from airtouch2.protocol.at2plus.extended_common import ExtendedMessageSubType, ExtendedSubHeader
from airtouch2.protocol.at2plus.message_common import Header, Message, MessageType
from airtouch2.protocol.at2plus.messages.AcAbilityMessage import AcAbility, AcAbilityMessage, RequestAcAbilityMessage
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatusMessage
from airtouch2.protocol.bits_n_bytes.buffer import Buffer
from airtouch2.protocol.bits_n_bytes.crc16_modbus import crc16
from airtouch2.protocol.interfaces import Serializable

_LOGGER = logging.getLogger(__name__)


NetworkOrHostDownErrors = (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT,
                           errno.ENETDOWN, errno.ENETUNREACH, errno.ENETRESET, errno.ECONNABORTED)


class At2PlusClient:

    def __init__(self, host: str, port: int = 9200, dump: bool = False):
        self.aircons_by_id: dict[int, At2PlusAircon] = {}
        self._host_ip: str = host
        self._host_port: int = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._dump: bool = dump
        self._main_loop: asyncio.Task[None] | None = None
        self._stop: bool = False
        self._ability_message_queue: asyncio.Queue[AcAbilityMessage] = asyncio.Queue(
        )
        self._new_ac_callbacks: list[Callable] = []

    async def connect(self) -> bool:
        """Opens connection to the server, returns True/False if successful/unsuccessful"""
        _LOGGER.debug(
            f'Connecting to {self._host_ip} on port {self._host_port}')
        try:
            self._reader, self._writer = await asyncio.open_connection(self._host_ip, self._host_port)
        except OSError as e:
            _LOGGER.warning(f"Could not connect to host {self._host_ip}")
            if isinstance(e, gaierror):
                # provided ip or port is rubbish/invalid
                pass
            elif e.errno not in NetworkOrHostDownErrors:
                raise e
            return False
        else:
            print(">> Connected to AC")
            return True

    async def run(self, create_task: Callable = asyncio.create_task) -> None:
        """Starts the processing of incoming information from the server, using the provided create_task function"""
        _LOGGER.debug("Starting listener task")
        self._main_loop = create_task(self._main())
        await self.send(AcStatusMessage([]))  # request status

    async def stop(self) -> None:
        if not self._main_loop:
            raise RuntimeError("Client task is not running")
        self._stop = True
        self._main_loop.cancel()
        try:
            await self._main_loop
        except asyncio.CancelledError as e:
            # Eat the expected exception
            pass

    async def send(self, message: Serializable):
        if not self._writer:
            raise RuntimeError("Client is not connected - call run() first")
        else:
            _LOGGER.debug(f"Sending {message.__class__.__name__}")
            bytes_to_write = message.to_bytes()
            _LOGGER.debug(f"Sending BINARY %s", [bin(b)[2:] for b in bytes_to_write])
            _LOGGER.debug(f"Sending HEX %s", [hex(b) for b in bytes_to_write])
            self._writer.write(bytes_to_write)
            await self._writer.drain()
            _LOGGER.debug("Message sent, now lets wait...")

    async def _request_ac_ability(self, number: int) -> AcAbility | None:
        _LOGGER.debug("Requesting ability of AC %i", number)
        ability_bytes_to_send = RequestAcAbilityMessage(number)
        _LOGGER.debug("Sending ability request %s", ability_bytes_to_send)
        await self.send(ability_bytes_to_send)
        _LOGGER.debug("Waiting for ability message response...")
        test = await self._read_bytes(38)
        # _LOGGER.debug("Got %s", [hex(b) for b in test])
        _LOGGER.debug("Got %s", test.hex(":"))
        # return
        ac_ability = await self._ability_message_queue.get()
        _LOGGER.debug("Got ability message response")
        if len(ac_ability.abilities) != 1:
            _LOGGER.warning(
                f"Expected ability of single requested AC but got {len(ac_ability.abilities)}")
            return None
        if ac_ability.abilities[0].number != number:
            _LOGGER.warning(
                f"Requested ability of AC{number} but got AC{ac_ability.abilities[0].number}")
            return None
        return ac_ability.abilities[0]

    async def _handle_status_message(self, message: AcStatusMessage):
        _LOGGER.debug(
            f"Received status message with {len(message.statuses)} statuses")
        for status in message.statuses:
            _LOGGER.debug(f"Status: {status}")
            _LOGGER.debug("Looking through aircon list for id %i: %s", status.id, self.aircons_by_id)
            if status.id in self.aircons_by_id.keys():
                self.aircons_by_id[status.id].update_status(status)
                _LOGGER.debug("Updated AC %s with value ", status.id, status)
            else:
                _LOGGER.debug("AC %s not found, requesting ability...", status.id)
                ability = await self._request_ac_ability(status.id)
                _LOGGER.debug("Got ability %s", ability)
                while not ability:
                    ability = await self._request_ac_ability(status.id)
                self.aircons_by_id[status.id] = At2PlusAircon(ability, status)

    async def _try_reconnect(self) -> None:
        retries = 0
        while not await self.connect():
            await asyncio.sleep(0.001 * (10**retries) if retries < 4 else 10)
            retries += 1
            if not retries % 60 or retries == 4:
                _LOGGER.info(
                    "Server is not responding, will continue trying to reconnect every 10s")
        await self.send(AcStatusMessage([]))

    async def _read_bytes(self, size: int) -> bytes | None:
        if not self._reader:
            raise RuntimeError("Need reader")
        try:
            data = await self._reader.readexactly(size)
            # _LOGGER.debug("<<< Read data from bytes", data)
        except asyncio.IncompleteReadError as e:
            _LOGGER.debug(
                f"IncompleteReadError - partial bytes: {e.partial.hex(':')}")
            data = None
        if not data:
            _LOGGER.warning("Connection lost, reconnecting")
            await self._try_reconnect()
            return None
        _LOGGER.debug("Returning read bytes of size " +
                      str(size) + ": " + str([hex(b) for b in data]))
        return data

    async def _read_header(self) -> Header:
        header_bytes = await self._read_bytes(HEADER_LENGTH)
        while not header_bytes:
            header_bytes = await self._read_bytes(HEADER_LENGTH)
        try:
            header = Header.from_bytes(header_bytes)
        except ValueError as e:
            _LOGGER.debug(f"ValueError: {e}")
            _LOGGER.debug("Failed reading header, trying again")
            header = await self._read_header()
        _LOGGER.debug("Header read successfully.")
        return header

    async def _read_message(self) -> Message | None:
        header = await self._read_header()
        header_minus_start_bytes = header.to_bytes()[2:]
        _LOGGER.debug("!!! Header read successfully: " +
                      str(header_minus_start_bytes.hex(":")))
        buffer = Buffer(header.data_length)
        data_bytes = await self._read_bytes(header.data_length)
        # _LOGGER.debug("!!! Data bytes: " + str([hex(b) for b in data_bytes]))
        _LOGGER.debug("!!! Data bytes: " + str(data_bytes.hex(":")))

        if not data_bytes:
            # interrupted during data reading
            return None
        buffer.append_bytes(data_bytes)
        checksum = await self._read_bytes(2)
        if not checksum:
            # interrupted during checksum reading
            return None
        calculated_checksum = crc16(header_minus_start_bytes + buffer.data)
        _LOGGER.debug("!!! Calculated checksum is " + str(
            [hex(b) for b in calculated_checksum]) + " and expected checksum is " + str([hex(b) for b in checksum]))
        if (checksum != calculated_checksum):
            _LOGGER.warning(
                f"Checksum mismatch, ignoring message: Got {checksum.hex(':')} but expected {calculated_checksum.hex(':')}")
            return None
        if self._dump:
            # blocks but is only used for dev and debugging
            with open('message_' + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + '.dump', 'wb') as f:
                f.write(header.to_bytes() + buffer.to_bytes() + checksum)

        message = Message(header, buffer.finalise())
        return message

    async def _main(self) -> None:
        while not self._stop:
            if not (self._reader and self._writer):
                raise RuntimeError(
                    "Client is not connected - call connect() first")
            message = await self._read_message()
            if not message:
                # something went wrong
                _LOGGER.warning("Reading message failed")
                continue

            if message.header.type == MessageType.CONTROL_STATUS:
                _LOGGER.debug("Parsing a Control status message")
                subheader = ControlStatusSubHeader.from_buffer(
                    message.data_buffer)
                if subheader.sub_type == ControlStatusSubType.AC_STATUS:
                    _LOGGER.debug("Subheader is AC_STATUS")
                    status_message = AcStatusMessage.from_bytes(
                        message.data_buffer.read_bytes(subheader.subdata_length.total()))
                    await self._handle_status_message(status_message)
                else:
                    _LOGGER.warning(
                        f"Unhandled message type: {subheader.sub_type}")

            elif message.header.type == MessageType.EXTENDED:
                _LOGGER.debug("Parsing an extended message")
                subheader = ExtendedSubHeader.from_buffer(message.data_buffer)
                if subheader.sub_type == ExtendedMessageSubType.ABILITY:
                    await self._ability_message_queue.put(AcAbilityMessage.from_bytes(message.data_buffer.read_remaining()))
                else:
                    _LOGGER.warning(
                        f"Unhandled message type: {subheader.sub_type}")
            _LOGGER.debug("Does this execute?")

    def add_new_ac_callback(self, callback: Callable):
        self._new_ac_callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._new_ac_callbacks:
                self._new_ac_callbacks.remove(callback)

        return remove_callback
