from __future__ import annotations
from itertools import compress
from typing import TYPE_CHECKING, Callable
from airtouch2.protocol.at2.messages import ResponseMessage

from airtouch2.protocol.at2.messages import ChangeDamper, ToggleGroup
if TYPE_CHECKING:
    from airtouch2.at2.At2Client import At2Client
import logging


_LOGGER = logging.getLogger(__name__)


class At2Group:
    def __init__(self, client: At2Client, number: int, response: ResponseMessage):
        self._client = client
        self.number = number
        self._callbacks: list[Callable] = []
        self.update(response)

    def update(self, response: ResponseMessage):
        self.name = response.group_names[self.number]
        [start_zone, num_zones] = response.group_zones[self.number]
        # 0 to 10 steps of 10%
        self.damp = response.zone_damps[start_zone]
        self.spill = response.zone_spills[start_zone]
        self.on = response.zone_ons[start_zone]
        mismatches: set[str] = set()
        for i in range(start_zone+1, start_zone + num_zones):
            # this group is spilling if any of its zones are
            self.spill = response.zone_spills[i]
            # these should match for all zones that comprise this group
            if (self.damp != response.zone_damps[i]):
                mismatches.add("open percents")
            if (self.on != response.zone_ons[i]):
                mismatches.add("on/offs")
            if mismatches:
                _LOGGER.warning(f"Zones of group '{self.name}' have mismatching {', '.join(mismatches)}")

        self.turbo = True if response.turbo_group == self.number else False

        for func in self._callbacks:
            func()

    def add_callback(self, func: Callable) -> Callable:
        self._callbacks.append(func)

        def remove_callback() -> None:
            if func in self._callbacks:
                self._callbacks.remove(func)

        return remove_callback

    async def inc_dec_damp(self, inc: bool):
        await self._client.send(ChangeDamper(self.number, inc))

    async def set_damp(self, new_damp: int):
        if new_damp < 0 or new_damp > 10:
            raise ValueError("Dampers can only be set from 0 to 10")
        # Set to 0 is equivalent to turning off
        if new_damp == 0:
            await self.turn_off()
        else:
            await self.turn_on()
            damp_diff = new_damp - self.damp
            inc = damp_diff > 0
            for i in range(abs(damp_diff)):
                await self.inc_dec_damp(inc)

    async def _turn_on_off(self, on: bool):
        if self.on != on:
            await self._client.send(ToggleGroup(self.number))

    async def turn_off(self):
        await self._turn_on_off(False)

    async def turn_on(self):
        await self._turn_on_off(True)

    def get_status_strings(self):
        flags = [self.spill, self.turbo]
        flag_names = ['SPILL', 'TURBO']
        statuses = list(compress(flag_names, flags))
        if not statuses:
            statuses.append('NORMAL')
        return statuses

    def __str__(self):
        return f"""
        Group Name:\t{self.name}
        Group Number:\t{self.number}
        On:\t\t{self.on}
        Status:\t\t{self.get_status_strings()}
        Damper:\t\t{f'{self.damp*10}%'}
        """
