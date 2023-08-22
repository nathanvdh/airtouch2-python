from typing import Callable
from airtouch2.at2 import At2Client
from airtouch2.protocol.at2.enums import ACMode
from airtouch2.protocol.at2.messages.ac_commands import SetMode, ToggleAc
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


input_str: str = \
    f"""
Enter:  'q' to quit
        't' to toggle power
        'm' to set mode

        <command> <ac> [value]
        e.g. m 0 1 (set mode of AC0 to 1 ({ACMode(1)}))
             t 1   (toggle AC1)
        Modes: {ACMode._member_names_}
"""


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

        inp = await aioconsole.ainput(input_str)
        while inp != 'q':
            split = inp.split()
            while len(split) < 2:
                print("Enter command followed by ac number followed by optional args")
                inp = await aioconsole.ainput(input_str)
                split = inp.split()

            cmd = split[0]
            ac = int(split[1])

            if ac not in [0, 1]:
                raise ValueError("AC must be 0 or 1")

            if cmd == 't':
                _LOGGER.info(f"Toggling AC{ac}")
                await client.send(ToggleAc(ac))
            elif cmd == 'm':
                mode = ACMode.AUTO
                if len(split) > 2:
                    mode = ACMode(int(split[2]))
                else:
                    mode = ACMode(int(await aioconsole.ainput('Enter mode: ')))
                _LOGGER.info(f"Changing AC{ac} mode to {mode}")

                await client.send(SetMode(ac, ACMode(mode)))

            inp = await aioconsole.ainput(input_str)

    await client.stop()

asyncio.run(main())
