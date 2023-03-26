from typing import Callable
from airtouch2.at2plus.AT2PlusAircon import At2PlusAircon
from airtouch2.at2plus.AT2PlusClient import At2PlusClient
import logging
import asyncio
import aioconsole

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


input_str: str = \
    """
Enter: 'q' to quit
       'r' to request AC0 ability
"""


async def main():
    addr = await aioconsole.ainput("Enter airtouch2plus IP address: ")
    client = At2PlusClient(addr, dump=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._host_ip}:{client._host_port}")
    status_logger = AcStatusLogger(client)
    await client.run()
    inp = await aioconsole.ainput(input_str)
    while inp != "q":
        if (inp == "r"):
            ability = await client._request_ac_ability(0)
            while not ability:
                ability = await client._request_ac_ability(0)
            client.aircons_by_id[0]._set_ability(ability)
        inp = await aioconsole.ainput(input_str)
    await client.stop()
    status_logger.cleanup()

asyncio.run(main())
