import asyncio
from datetime import datetime
import errno
import logging
from airtouch2.common.NetClient import NetClient

from airtouch2.protocol.at2.constants import MessageLength
from airtouch2.protocol.at2.messages import RequestState, ResponseMessage
from airtouch2.at2.At2Aircon import At2Aircon
from airtouch2.at2.At2Group import At2Group
from airtouch2.common.interfaces import Callback, Serializable, TaskCreator

_LOGGER = logging.getLogger(__name__)

NetworkOrHostDownErrors = (errno.EHOSTUNREACH, errno.ECONNREFUSED,  errno.ETIMEDOUT,
                           errno.ENETDOWN, errno.ENETUNREACH, errno.ENETRESET, errno.ECONNABORTED)


class At2Client:
    def __init__(self, host: str, dump_responses: bool = False, task_creator: TaskCreator = asyncio.create_task):
        # public
        self.aircons: list[At2Aircon] = []
        self.groups: list[At2Group] = []
        self.system_name: str = "UNKNOWN"

        # private
        self._client = NetClient(host, 8899, self._on_connect, self._handle_one_message, task_creator)
        self._dump_responses: bool = dump_responses
        self._new_ac_callbacks: list[Callback] = []
        self._found_ac = asyncio.Event()

        self.add_new_ac_callback(lambda: self._found_ac.set())

    async def connect(self) -> bool:
        return await self._client.connect()

    def run(self) -> None:
        self._client.run()

    async def wait_for_ac(self, timeout: int = 5) -> None:
        try:
            await asyncio.wait_for(self._found_ac.wait(), timeout)
        except TimeoutError:
            pass

    async def stop(self) -> None:
        await self._client.stop()

    def add_new_ac_callback(self, callback: Callback):
        self._new_ac_callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._new_ac_callbacks:
                self._new_ac_callbacks.remove(callback)

        return remove_callback

    async def send(self, msg: Serializable):
        await self._client.send(msg)

    async def _on_connect(self):
        await self._client.send(RequestState())

    async def _read_response(self) -> ResponseMessage | None:
        _LOGGER.debug("Waiting for response")
        resp = await self._client.read_bytes(MessageLength.RESPONSE)
        _LOGGER.debug("Got response")
        if not resp:
            return None

        if self._dump_responses:
            # blocks but is only used for dev and debugging
            with open('response_' + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + '.dump', 'wb') as f:
                f.write(resp)

        return ResponseMessage.from_bytes(resp)

    async def _handle_one_message(self) -> None:
        resp = await self._read_response()
        if not resp:
            # something went wrong
            _LOGGER.info("Reading message failed")
            return

        # ACs
        if not self.aircons:
            # TODO: Support multiple aircons
            self.aircons.append(At2Aircon(0, self, resp))
            _LOGGER.debug(self.aircons[0])
            for callback in self._new_ac_callbacks:
                callback()
        else:
            for aircon in self.aircons:
                aircon.update(resp)
                _LOGGER.debug(aircon)
        # Groups
        if not self.groups or len(self.groups) != resp.num_groups:
            # this clear will cause problems for anything using the groups
            self.groups.clear()
            for i in range(resp.num_groups):
                self.groups.append(At2Group(self, i, resp))
                _LOGGER.debug(self.groups[i])
        else:
            for group in self.groups:
                group.update(resp)
                _LOGGER.debug(group)
