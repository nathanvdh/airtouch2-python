import asyncio
from datetime import datetime
import errno
import logging
from socket import gaierror
from typing import Callable

from airtouch2.protocol.constants import MessageLength
from airtouch2.protocol.messages import RequestState, ResponseMessage
from airtouch2.AT2Aircon import AT2Aircon
from airtouch2.AT2Group import AT2Group
from airtouch2.protocol.messages.CommandMessage import CommandMessage

_LOGGER = logging.getLogger(__name__)

NetworkOrHostDownErrors = (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT,
                           errno.ENETDOWN, errno.ENETUNREACH, errno.ENETRESET, errno.ECONNABORTED)


class AT2Client:
    def __init__(self, host: str, dump: bool = False) -> None:
        self._host_ip: str = host
        self._host_port: int = 8899
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._dump: bool = dump
        self._stop: bool = True
        self._read_task: asyncio.Task[None] | None = None
        self._got_response: asyncio.Event = asyncio.Event()
        self.aircons: list[AT2Aircon] = []
        self.groups: list[AT2Group] = []
        self.system_name: str = "UNKNOWN"
        self.active: bool = False

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
            return True

    async def run(self, create_task: Callable = asyncio.create_task) -> None:
        """Starts the processing of incoming information from the server, using the provided create_task function"""
        _LOGGER.debug("Starting listener task")
        self._stop = False
        self._read_task = create_task(self._listen_for_updates())
        await self.send_command(RequestState())
        await asyncio.wait_for(self._got_response.wait(), timeout=5)

    async def stop(self) -> None:
        if not self._read_task:
            raise RuntimeError("Client task is not running")
        self._stop = True
        self._read_task.cancel()
        try:
            await self._read_task
        except asyncio.CancelledError as e:
            # Eat the expected exception
            pass
        self._got_response.clear()

    async def send_command(self, command: CommandMessage, await_response=True) -> None:
        if not self._writer:
            raise RuntimeError("Client is not connected - call run() first")
        else:
            _LOGGER.debug(f"Sending {command.__class__.__name__}")
            self._writer.write(command.serialize())
            self._got_response.clear()
            await self._writer.drain()
            if await_response:
                await self._got_response.wait()

    async def _read_response(self) -> ResponseMessage:
        if not (self._reader and self._writer):
            raise RuntimeError(
                "Client is not connected - call connect() first")
        _LOGGER.debug("Waiting for response")
        resp = await self._reader.read(MessageLength.RESPONSE)
        # handle socket exceptions?
        _LOGGER.debug("Got response")
        while len(resp) != MessageLength.RESPONSE:
            if not resp:
                _LOGGER.debug("Connection lost, reconnecting")
                self._got_response.clear()
                await self._try_reconnect()
            else:
                _LOGGER.debug(
                    f"Invalid length message received ({len(resp)}) - ignoring")
            resp = await self._reader.read(MessageLength.RESPONSE)
        if self._dump:
            # blocks but is only used for dev and debugging
            with open('response_' + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + '.dump', 'wb') as f:
                f.write(resp)

        return ResponseMessage(resp)

    async def _try_reconnect(self) -> None:
        retries = 0
        while not await self.connect():
            await asyncio.sleep(0.001 * (10**retries) if retries < 4 else 10)
            retries += 1
            if not retries % 50 or retries == 4:
                _LOGGER.debug(
                    "Server is not responding, will continue trying to reconnect every 10s")
        await self.send_command(RequestState(), await_response=False)

    async def _listen_for_updates(self) -> None:
        while not self._stop:
            resp = await self._read_response()
            # ACs
            if not self.aircons:
                self.aircons.append(AT2Aircon(0, self, resp))
                _LOGGER.debug(self.aircons[0])
            else:
                for aircon in self.aircons:
                    aircon.update(resp)
                    _LOGGER.debug(aircon)
            # Groups
            if not self.groups or len(self.groups) != resp.num_groups:
                # this clear will cause problems for anything using the groups
                self.groups.clear()
                for i in range(resp.num_groups):
                    await asyncio.sleep(0)
                    self.groups.append(AT2Group(self, i, resp))
                    _LOGGER.debug(self.groups[i])
            else:
                for group in self.groups:
                    await asyncio.sleep(0)
                    group.update(resp)
                    _LOGGER.debug(group)
            self._got_response.set()
