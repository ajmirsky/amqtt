import asyncio
from asyncio import CancelledError
from random import randint

from amqtt.client import MQTTClient
from lorem_text import lorem

from amqtt.mqtt.constants import QOS_0


async def run_client() -> None:
    client = MQTTClient()
    await client.connect("mqtt://localhost:1883/")
    await client.subscribe([
        ('$SYS/#', QOS_0),
        ('a/b', QOS_0),
    ])
    try:
        msg_count = randint(10, 100)
        for _ in range(msg_count):
            msg = lorem.words(randint(2, 10))
            await client.publish("a/b", msg.encode())
            print("sending message")

            rcv_count = 0
            try:
                while True:
                    msg = await client.deliver_message(timeout_duration=0.5)
                    rcv_count += 1
            except asyncio.TimeoutError:
                print(f"received {rcv_count} messages")


            await asyncio.sleep(randint(1, 3))
    except CancelledError as e:
        await client.disconnect()
        print("client cancelled")
        raise

    await client.disconnect()
    print("client exiting")

async def main() -> None:
    tasks = []
    try:
        while True:
            print("launching new client")
            tasks.append(asyncio.create_task(run_client()))
            await asyncio.sleep(0.25)
    except KeyboardInterrupt:
        for task in tasks:
            if not task.done():
                task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
