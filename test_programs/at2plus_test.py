from typing import Callable
from airtouch2.at2plus.AT2PlusAircon import At2PlusAircon
from airtouch2.at2plus.AT2PlusClient import At2PlusClient
import logging
import asyncio
import aioconsole

from airtouch2.protocol.at2plus.enums import AcFanSpeed

logging.basicConfig(filename='airtouch2plus.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s %(threadName)s %(levelname)s: %(message)s')
_LOGGER = logging.getLogger()
_LOGGER.addHandler(logging.StreamHandler())
logging.getLogger('asyncio').setLevel(logging.WARNING)


class AcStatusLogger:
    client: At2PlusClient
    acs: list[At2PlusAircon]
    cleanup_callbacks: list[Callable]

    def __init__(self, client: At2PlusClient):
        self.client = client
        self.cleanup_callbacks = []
        self.acs = []
        self.cleanup_callbacks.append(client.add_new_ac_callback(self.new_ac))

    def new_ac(self):
        for ac in self.client.aircons_by_id.values():
            if ac not in self.acs:
                self.acs.append(ac)
                _LOGGER.info(ac.status)

                def log_ac_info():
                    _LOGGER.info(ac.status)
                    if (ac.ability is not None):
                        _LOGGER.info(ac.ability)

                self.cleanup_callbacks.append(ac.add_callback(log_ac_info))

    def cleanup(self):
        while len(self.cleanup_callbacks) > 0:
            self.cleanup_callbacks.pop()()


class Ac0Waiter:
    client: At2PlusClient
    cleanup_callbacks: list[Callable]
    ac0: At2PlusAircon | None
    found_ac0: asyncio.Event

    def __init__(self, client: At2PlusClient):
        self.client = client
        self.ac0 = None
        self.cleanup_callbacks = []
        self.cleanup_callbacks.append(client.add_new_ac_callback(self.new_ac))

    def new_ac(self):
        if self.ac0 is None:
            for ac in self.client.aircons_by_id.values():
                if ac.status.id == 0:
                    self.ac0 = ac
                    self.found_ac0.set()

    def cleanup(self):
        while len(self.cleanup_callbacks) > 0:
            self.cleanup_callbacks.pop()()

    async def wait(self):
        await self.found_ac0.wait()
        assert self.ac0 is not None
        await self.ac0.wait_until_ready()
        # once we've waited for it, we're finished
        self.cleanup()


input_str: str = \
    """
Enter: 'q' to quit
       'r' to request AC0 ability
       't' to toggle AC0
       's' to set AC0 temperature setpoint
       'f' to set AC0 fan speed
       'm' to set AC0 mode
"""


async def main():
    addr = await aioconsole.ainput("Enter airtouch2plus IP address: ")
    client = At2PlusClient(addr, dump=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._host_ip}:{client._host_port}")

    # Register callbacks
    status_logger = AcStatusLogger(client)
    ac0_waiter = Ac0Waiter(client)

    await client.run()

    _LOGGER.debug("Waiting for AC0 to be ready")
    await ac0_waiter.wait()
    _LOGGER.debug("AC0 is ready")
    ac0 = client.aircons_by_id[0]
    assert ac0.ability is not None

    inp = await aioconsole.ainput(input_str)
    while inp != "q":
        if (inp == "r"):
            ability = await client._request_ac_ability(0)
            while not ability:
                ability = await client._request_ac_ability(0)
            ac0._set_ability(ability)

        if (inp == "t"):
            await client.aircons_by_id[0].toggle()

        if (inp == "s"):
            inp = await aioconsole.ainput("Enter setpoint: ")
            await ac0.set_setpoint(float(inp))

        if (inp == "f"):
            inp = await aioconsole.ainput(f"Enter supported fan speed index [0-{len(ac0.ability.supported_fan_speeds) - 1}]: ")
            await ac0.set_fan_speed(ac0.ability.supported_fan_speeds[int(inp)])

        if (inp == "m"):
            inp = await aioconsole.ainput(f"Enter supported mode index [0-{len(ac0.ability.supported_modes) - 1}]: ")
            await ac0.set_mode(ac0.ability.supported_modes[int(inp)])

        inp = await aioconsole.ainput(input_str)

    # Cleanup
    await client.stop()
    status_logger.cleanup()

asyncio.run(main())
