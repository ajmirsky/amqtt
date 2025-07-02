import asyncio
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

    await client.disconnect()
    print("client exiting")

async def main() -> None:

    while True:
        print("launching new client")
        asyncio.ensure_future(run_client())
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    asyncio.run(main())
