

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.common.interfaces import Callback
from airtouch2.protocol.at2plus.enums import GroupPower
from airtouch2.protocol.at2plus.messages.GroupStatus import GroupStatus


class At2PlusGroup:
    """
    A class that represents a single airtouch2+ group.

    """

    def __init__(self, status: GroupStatus, client: At2PlusClient):
        self.status = status
        self._client = client
        self._callbacks: list[Callback] = []


    def is_on(self) -> bool:
        return self.status.power != GroupPower.OFF
    
    def add_callback(self, callback: Callback) -> Callback:
        self._callbacks.append(callback)

        def remove_callback() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return remove_callback
    
    def _update_status(self, status: GroupStatus):
        self.status = status
        for callback in self._callbacks:
            callback()