import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import newrelic.agent

from amqtt.broker import Broker

newrelic_ini = Path(__file__).parent.resolve() / "newrelic.ini"
if "NEWRELIC_CONFIG_INI" in os.environ:
    newrelic_ini = Path(os.environ["NEWRELIC_CONFIG_INI"])

newrelic.agent.initialize(newrelic_ini)

logger = logging.getLogger(__name__)

config: dict[str, Any] = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        },
        "ws-mqtt": {
            "bind": "127.0.0.1:8080",
            "type": "ws",
            "max_connections": 20,
        },
    },
    "sys_interval": 2
}

async def main_loop() -> None:
    broker = Broker(config)
    try:
        await broker.start()
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await broker.shutdown()

async def main() -> None:
    t = asyncio.create_task(main_loop())
    try:
        await t
    except asyncio.CancelledError:
        pass

def __main__() -> None:

    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    task = loop.create_task(main())

    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Stopping server...")
        task.cancel()
        loop.run_until_complete(task)  # Ensure task finishes cleanup
    finally:
        logger.info("Server stopped.")
        loop.close()

if __name__ == "__main__":
    __main__()
