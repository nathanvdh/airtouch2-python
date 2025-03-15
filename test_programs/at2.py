from airtouch2.at2 import At2Client
import asyncio 

client = At2Client("192.168.0.100")


async def main():
    if not await client.connect():
        print("Connection failure")
        
    client.run()
    await client.wait_for_ac()
    print(client.touchpad_temp)
    
if __name__ == "__main__":
    asyncio.run(main())