import asyncio
import logging
import logging.config

import os
from pathlib import Path
from typing import Any

from amqtt.broker import Broker

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': 'app.log',
            'mode': 'a',  # append mode
            'encoding': 'utf-8',
        },
    },

    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },

    'loggers': {
        'transitions': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

config: dict[str, Any] = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:1883",
        },
        "ws-mqtt": {
            "type": "ws",
            "bind": "0.0.0.0:8080",
        },
        # "tls-mqtt": {
        #     "type": "tcp",
        #     "bind": "0.0.0.0:8883",
        #     "ssl": True,
        #     "cafile": "/app/cert/live/test.amqtt.io/fullchain.pem",
        #     "certfile": "/app/cert/live/test.amqtt.io/fullchain.pem",
        #     "keyfile": "/app/cert/live/test.amqtt.io/privkey.pem"
        # },
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
