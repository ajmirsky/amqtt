import asyncio
import logging
import logging.config

from typing import Any

from amqtt.broker import Broker


MIN_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'amqtt.broker': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    },
}

logging.config.dictConfig(MIN_LOGGING_CONFIG)
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
    },
    "plugins": {
        'amqtt.plugins.authentication.AnonymousAuthPlugin': {'allow_anonymous': True}
    }
}

async def main_loop() -> None:
    broker = Broker(config)
    try:
        print("Starting broker...")
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    task = loop.create_task(main())

    try:
       loop.run_until_complete(task)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Stopping server...")
    finally:
        print("Server stopped.")
        loop.close()

if __name__ == "__main__":
    __main__()
