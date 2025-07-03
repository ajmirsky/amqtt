import logging
import asyncio
from amqtt.client import MQTTClient, ConnectError
logger = logging.getLogger(__name__)

async def t_coro():
    try:
        while True:
            ss = "CLIENT_ID_"
            for i in range(0, 500):
                C = MQTTClient(client_id=ss + str(i))
                await C.connect("mqtt://localhost:1883/")
                await C.publish("a/b", b"TEST MESSAGE WITH QOS_0", qos=0x00)
                await C.publish("a/b", b"TEST MESSAGE WITH QOS_1", qos=0x01)
                await C.publish("a/b", b"TEST MESSAGE WITH QOS_2", qos=0x02)
                await C.disconnect()
    except ConnectError as ce:
        logger.error("Connection failed: %s" % ce)


if __name__ == "__main__":
    formatter = ("[%(asctime)s] %(name)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
    logging.basicConfig(level=logging.ERROR, format=formatter)
    asyncio.run(t_coro())
