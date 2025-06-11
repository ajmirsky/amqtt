import asyncio
import logging
import unittest
from asyncio import CancelledError, Event

import pytest

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0


@pytest.mark.asyncio
async def test_async_with_interface(broker_fixture):

    has_received = Event()

    async def client_task_coro():

        client1 = MQTTClient(client_id="CLIENT_1")
        await client1.connect("mqtt://127.0.0.1/")
        await client1.subscribe([
            ("test/topic", QOS_0)
        ])

        try:
            async for message in client1.messages:
                assert message.topic == "test/topic"
                assert message.data == b'my data from mqtt'
                has_received.set()
        except CancelledError:
            await client1.disconnect()

    loop = asyncio.get_running_loop()

    client_task = loop.create_task(client_task_coro())
    await asyncio.sleep(1)

    client2 = MQTTClient(client_id="CLIENT_2")
    await client2.connect("mqtt://127.0.0.1/")
    await client2.publish("test/topic", b'my data from mqtt')
    await asyncio.sleep(1)
    await client2.disconnect()

    assert has_received.is_set(), "Should have received a message"

    await asyncio.sleep(0.5)

    client_task.cancel()
