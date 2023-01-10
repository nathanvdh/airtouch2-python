from airtouch2 import AT2Client
from airtouch2.protocol.messages.ac_commands import ToggleAC
import logging
import asyncio
import aioconsole
logging.basicConfig(filename='airtouch2.log',filemode='a', level=logging.DEBUG, format='%(asctime)s %(threadName)s %(levelname)s: %(message)s')
_LOGGER = logging.getLogger()
_LOGGER.addHandler(logging.StreamHandler())
logging.getLogger('asyncio').setLevel(logging.WARNING)

async def main():
    client = AT2Client("192.168.1.21", dump=True)
    if not await client.connect():
        raise RuntimeError(f"Could not connect to {client._host_ip}")
    await client.run()
    inp = await aioconsole.ainput('quit (q), toggleAC (t): ')
    while inp != 'q':
        if inp == 't':
            _LOGGER.info("Sending toggle")
            await client.send_command(ToggleAC(0))
        inp = await aioconsole.ainput()

    await client.stop()

asyncio.run(main())