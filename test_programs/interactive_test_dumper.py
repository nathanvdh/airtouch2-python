from typing import Callable
from airtouch2.at2 import At2Client
from airtouch2.protocol.at2.messages.ac_commands import ToggleAc
import logging
import asyncio
import aioconsole
from airtouch2.common.interfaces import Callback, PublisherType
logging.basicConfig(filename='airtouch2.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s %(threadName)s %(levelname)s: %(message)s')
_LOGGER = logging.getLogger()
_LOGGER.addHandler(logging.StreamHandler())
logging.getLogger('asyncio').setLevel(logging.WARNING)


class PublishersLogger:
    """"Subscribe to a changing list of publishers, logging each one when its state updates."""

    def __init__(self, pubs_by_id: dict[int, PublisherType],
                 observe_new_publisher_added: Callable[[Callback],
                                                       Callback]):
        self.pubs_by_id = pubs_by_id
        self.subscribed_publisher_ids: list[int] = []
        self.cleanup_callbacks: list[Callback] = []
        self.cleanup_callbacks.append(observe_new_publisher_added(self.new_publisher))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        while len(self.cleanup_callbacks) > 0:
            self.cleanup_callbacks.pop()()
        return False

    def new_publisher(self):
        for id, pub in self.pubs_by_id.items():
            if id not in self.subscribed_publisher_ids:
                _LOGGER.info(f"New publisher: {pub}")
                self.cleanup_callbacks.append(pub.add_callback(lambda: _LOGGER.info(f"Publisher update: {pub}")))
                self.subscribed_publisher_ids.append(id)


async def main():
    inp: str = await aioconsole.ainput('Enter IP address: ')
    client = At2Client(inp, dump_responses=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._client._host_ip}")

    # RAII in Python sucks.
    # Here we subscribe to the client on entering the context and unsubscribe on exit.
    with PublishersLogger(client.aircons_by_id, client.add_new_ac_callback) as ac_logger, \
         PublishersLogger(client.groups_by_id, client.add_new_group_callback) as group_logger:
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
