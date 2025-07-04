import asyncio
import logging
import signal
import subprocess
from pathlib import Path

import pytest

from amqtt.broker import Broker
from samples.client_publish import __main__ as client_publish_main
from samples.client_subscribe import __main__ as client_subscribe_main
from samples.client_keepalive import __main__ as client_keepalive_main
from samples.broker_acl import config as broker_acl_config
from samples.broker_taboo import config as broker_taboo_config

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_broker_acl():
    broker_acl_script = Path(__file__).parent.parent / "samples/broker_acl.py"
    process = subprocess.Popen(["python", broker_acl_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Send the interrupt signal
    await asyncio.sleep(5)
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "Broker closed" in stderr.decode("utf-8")
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")


@pytest.mark.asyncio
async def test_broker_simple():
    broker_simple_script = Path(__file__).parent.parent / "samples/broker_simple.py"
    process = subprocess.Popen(["python", broker_simple_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(5)

    # Send the interrupt signal
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    has_broker_closed = "Broker closed" in stderr.decode("utf-8")
    has_loop_stopped = "Broadcast loop stopped by exception" in stderr.decode("utf-8")

    assert has_broker_closed or has_loop_stopped, "Broker didn't close correctly."


@pytest.mark.asyncio
async def test_broker_start():
    broker_start_script = Path(__file__).parent.parent / "samples/broker_start.py"
    process = subprocess.Popen(["python", broker_start_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(5)

    # Send the interrupt signal to stop broker
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "Broker closed" in stderr.decode("utf-8")
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")


@pytest.mark.asyncio
async def test_broker_taboo():
    broker_taboo_script = Path(__file__).parent.parent / "samples/broker_taboo.py"
    process = subprocess.Popen(["python", broker_taboo_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(5)

    # Send the interrupt signal to stop broker
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "INFO :: amqtt.broker :: Broker closed" in stderr.decode("utf-8")
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")


@pytest.mark.timeout(25)
@pytest.mark.asyncio
async def test_client_keepalive():

    broker = Broker()
    await broker.start()
    await asyncio.sleep(2)

    keep_alive_script = Path(__file__).parent.parent / "samples/client_keepalive.py"
    process = subprocess.Popen(["python", keep_alive_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2)

    stdout, stderr = process.communicate()
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()


@pytest.mark.asyncio
async def test_client_publish():
    broker = Broker()
    await broker.start()
    await asyncio.sleep(2)

    client_publish = Path(__file__).parent.parent / "samples/client_publish.py"
    process = subprocess.Popen(["python", client_publish], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2)

    stdout, stderr = process.communicate()
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()

broker_ssl_config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "0.0.0.0:8883",
            "ssl": True,
            "certfile": "cert.pem",
            "keyfile": "key.pem",
        }
    },
    "auth": {
        "allow-anonymous": True,
        "plugins": ["auth_anonymous"]
            }
}

@pytest.mark.asyncio
async def test_client_publish_ssl():

    # generate a self-signed certificate for this test
    cmd = 'openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=localhost"'
    subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # start a secure broker
    broker = Broker(config=broker_ssl_config)
    await broker.start()
    await asyncio.sleep(2)
    # run the sample
    client_publish_ssl_script = Path(__file__).parent.parent / "samples/client_publish_ssl.py"
    process = subprocess.Popen(["python", client_publish_ssl_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2)
    stdout, stderr = process.communicate()

    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()


@pytest.mark.asyncio
async def test_client_publish_acl():

    broker = Broker()
    await broker.start()
    await asyncio.sleep(2)

    broker_simple_script = Path(__file__).parent.parent / "samples/client_publish_acl.py"
    process = subprocess.Popen(["python", broker_simple_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Send the interrupt signal
    await asyncio.sleep(2)

    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()

broker_ws_config = {
    "listeners": {
        "default": {
            "type": "ws",
            "bind": "0.0.0.0:8080",
        }
    },
    "auth": {
        "allow-anonymous": True,
        "plugins": ["auth_anonymous"]
            }
}

@pytest.mark.asyncio
async def test_client_publish_ws():
    # start a secure broker
    broker = Broker(config=broker_ws_config)
    await broker.start()
    await asyncio.sleep(2)
    # run the sample

    client_publish_ssl_script = Path(__file__).parent.parent / "samples/client_publish_ws.py"
    process = subprocess.Popen(["python", client_publish_ssl_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await asyncio.sleep(2)
    stdout, stderr = process.communicate()

    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()


def test_client_subscribe():
    client_subscribe_main()


@pytest.mark.asyncio
async def test_client_subscribe_plugin_acl():
    broker = Broker(config=broker_acl_config)
    await broker.start()

    broker_simple_script = Path(__file__).parent.parent / "samples/client_subscribe_acl.py"
    process = subprocess.Popen(["python", broker_simple_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Send the interrupt signal
    await asyncio.sleep(5)
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "Subscribed results: [128, 1, 128, 1, 128, 1]" in stderr.decode("utf-8")
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()


@pytest.mark.asyncio
async def test_client_subscribe_plugin_taboo():
    broker = Broker(config=broker_taboo_config)
    await broker.start()

    broker_simple_script = Path(__file__).parent.parent / "samples/client_subscribe_acl.py"
    process = subprocess.Popen(["python", broker_simple_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Send the interrupt signal
    await asyncio.sleep(5)
    process.send_signal(signal.SIGINT)
    stdout, stderr = process.communicate()
    logger.debug(stderr.decode("utf-8"))
    assert "Subscribed results: [1, 1, 128, 1, 1, 1]" in stderr.decode("utf-8")
    assert "ERROR" not in stderr.decode("utf-8")
    assert "Exception" not in stderr.decode("utf-8")

    await broker.shutdown()