from airtouch2 import At2Client
from airtouch2.at2.At2Aircon import At2Aircon
from airtouch2.protocol.at2.messages.ac_commands import ToggleAc
import logging
import asyncio
import aioconsole
from airtouch2.common.interfaces import Callback
logging.basicConfig(filename='airtouch2.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s %(threadName)s %(levelname)s: %(message)s')
_LOGGER = logging.getLogger()
_LOGGER.addHandler(logging.StreamHandler())
logging.getLogger('asyncio').setLevel(logging.WARNING)


class AcStatusLogger:
    client: At2Client
    acs: list[At2Aircon]
    cleanup_callbacks: list[Callback]

    def __init__(self, client: At2Client):
        self.client = client
        self.acs = []
        self.cleanup_callbacks = []
        self.cleanup_callbacks.append(client.add_new_ac_callback(self.new_ac))

    def __del__(self):
        self.cleanup()

    def new_ac(self):
        for ac in self.client.aircons:
            if ac not in self.acs:
                self.acs.append(ac)
                _LOGGER.info(ac)
                self.cleanup_callbacks.append(ac.add_callback(lambda: _LOGGER.info(ac)))

    def cleanup(self):
        while len(self.cleanup_callbacks) > 0:
            self.cleanup_callbacks.pop()()


async def main():
    inp : str = await aioconsole.ainput('Enter IP address: ')
    client = At2Client(inp, dump_responses=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._client._host_ip}")

    # Register callbacks
    status_logger = AcStatusLogger(client)

    client.run()
    _LOGGER.debug("Waiting for AC to be ready")
    await client.wait_for_ac()
    _LOGGER.debug("AC is ready")

    inp = await aioconsole.ainput('quit (q), toggleAC (t): ')
    while inp != 'q':
        if inp == 't':
            _LOGGER.info("Sending toggle")
            await client.send(ToggleAc(0))
        inp = await aioconsole.ainput()

    await client.stop()

asyncio.run(main())
