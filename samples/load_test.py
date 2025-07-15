import asyncio
import time
from asyncio import CancelledError
from math import floor
from random import randint

from amqtt.client import MQTTClient
from lorem_text import lorem

from amqtt.mqtt.constants import QOS_0


class Counter:
    def __init__(self):
        self.running_clients = 0
        self.messages_sent = 0
        self.max_clients = randint(20, 40)


def get_topic():

    t = ['a', 'b', 'c']
    q = ['a/b', 'c/d', 'e/f', 'g/h']

    # return f"{t[randint(0, len(t) - 1)]}/{t[randint(0, len(t) - 1)]}"
    return f"{q[randint(0, len(t) - 1)]}"


async def run_client(counter: Counter) -> None:
    start_time = time.time()
    counter.running_clients += 1
    topic = get_topic()
    client = MQTTClient()
    await client.connect("mqtt://test.amqtt.io:1883/")
    await client.subscribe([
        # ('$SYS/#', QOS_0),
        (topic, QOS_0),
    ])
    try:
        msg_count = randint(10, 100)
        for _ in range(msg_count):
            msg = lorem.words(randint(2, 10))
            await client.publish(topic, msg.encode())
            await asyncio.sleep(randint(1, 10)/30)
            # print("sending message")

            rcv_count = 0
            try:
                while True:
                    _ = await client.deliver_message(timeout_duration=0.5)
                    rcv_count += 1
            except asyncio.TimeoutError:
                # print(f"received {rcv_count} messages")
                pass

            # await asyncio.sleep(randint(1, 3))

    except CancelledError as e:
        await client.disconnect()
        print("client cancelled")
        raise

    await client.disconnect()
    print(f"client exiting after {floor(time.time() - start_time)} seconds")
    counter.running_clients -= 1

async def running_client_max(counter:Counter) -> None:
    while True:
        if counter.max_clients < 60:
            counter.max_clients += randint(-10, 20)
        elif counter.max_clients > 60:
            counter.max_clients += randint(-20, 10)
        elif counter.max_clients < 0:
            counter.max_clients = randint(20, 40)

        print(f"max clients now >>>>>> {counter.max_clients}")
        await asyncio.sleep(45)


async def main() -> None:
    tasks = []
    counter = Counter()
    tasks.append(asyncio.create_task(running_client_max(counter)))
    try:
        while True:
            if counter.running_clients < counter.max_clients:
                print(f"launching new client: current running {counter.running_clients}")
                tasks.append(asyncio.create_task(run_client(counter)))
            await asyncio.sleep(0.25)
    except KeyboardInterrupt:
        for task in tasks:
            if not task.done():
                task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
