import asyncio
from datetime import datetime
import logging

from airtouch2.common.NetClient import NetClient
from airtouch2.protocol.at2.constants import MessageLength
from airtouch2.protocol.at2.messages import RequestState, SystemInfo
from airtouch2.at2.At2Aircon import At2Aircon
from airtouch2.at2.At2Group import At2Group
from airtouch2.common.interfaces import add_callback, Callback, Serializable, TaskCreator

_LOGGER = logging.getLogger(__name__)


class At2Client:
    aircons_by_id: dict[int, At2Aircon]
    groups_by_id: dict[int, At2Group]
    system_name: str

    def __init__(self, host: str, dump_responses: bool = False, task_creator: TaskCreator = asyncio.create_task):
        self.aircons_by_id = {}
        self.groups_by_id = {}
        self.system_name: str = "UNKNOWN"

        self._client = NetClient(host, 8899, self._on_connect, self._handle_one_message, task_creator)
        self._dump_responses: bool = dump_responses
        self._new_ac_callbacks: list[Callback] = []
        self._new_group_callbacks: list[Callback] = []
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

    def add_new_ac_callback(self, callback: Callback) -> Callback:
        """
        Subscribe 'callback' to new AC discoveries.
        Return a callback to unsubscribe.
        """
        return add_callback(callback, self._new_ac_callbacks)

    def add_new_group_callback(self, callback: Callback):
        """
        Subscribe 'callback' to new group discoveries.
        Return a callback to unsubscribe.
        """
        return add_callback(callback, self._new_group_callbacks)

    async def send(self, msg: Serializable):
        await self._client.send(msg)

    async def _on_connect(self):
        await self._client.send(RequestState())

    async def _read_response(self) -> SystemInfo | None:
        _LOGGER.debug("Waiting for response")
        resp = await self._client.read_bytes(MessageLength.RESPONSE)
        _LOGGER.debug("Got response")
        if not resp:
            return None

        if self._dump_responses:
            # blocks but is only used for dev and debugging
            with open('response_' + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + '.dump', 'wb') as f:
                f.write(resp)

        return SystemInfo.from_bytes(resp)

    async def _handle_one_message(self) -> None:
        system_info = await self._read_response()
        if not system_info:
            # something went wrong
            _LOGGER.info("Reading response message failed")
            return

        _LOGGER.debug(f"SystemInfo: {system_info}")
        # ACs
        for id, ac_info in system_info.aircons_by_id.items():
            if id not in self.aircons_by_id:
                self.aircons_by_id[id] = At2Aircon(self, ac_info)
                for callback in self._new_ac_callbacks:
                    callback()
            else:
                self.aircons_by_id[id].update(ac_info)

        # Groups
        for id, group_info in system_info.groups_by_id.items():
            if id not in self.groups_by_id:
                self.groups_by_id[id] = At2Group(self, group_info)
                for callback in self._new_group_callbacks:
                    callback()
            else:
                self.groups_by_id[id].update(group_info)
