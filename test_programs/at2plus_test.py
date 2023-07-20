from typing import Callable
import logging
import asyncio
import aioconsole

from airtouch2.at2plus import At2PlusAircon
from airtouch2.at2plus import At2PlusClient

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
        self.acs = []
        self.cleanup_callbacks = []
        self.cleanup_callbacks.append(client.add_new_ac_callback(self.new_ac))

    def __del__(self):
        self.cleanup()

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
    client = At2PlusClient(addr, dump_responses=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._client._host_ip}:{client._client._host_port}")

    # Register callbacks
    status_logger = AcStatusLogger(client)

    client.run()

    _LOGGER.debug("Waiting for AC0 to be ready")
    await client.wait_for_ac()
    _LOGGER.debug("Found at least 1 AC")
    ac0 = client.aircons_by_id[0]
    await ac0.wait_until_ready()
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
