import asyncio
from airtouch2.protocol.messages import RequestState, ChangeSetTemperature
from airtouch2.protocol.constants import MessageLength

async def main():
    reader, writer = await asyncio.open_connection("192.168.1.21", 8899)

    writer.write(RequestState().serialize())
    await writer.drain()

    resp = await reader.read(MessageLength.RESPONSE)
    print(resp)

    writer.write(ChangeSetTemperature(0, True).serialize())
    await writer.drain()

    resp = await reader.read(MessageLength.RESPONSE)
    print(resp)

asyncio.run(main())