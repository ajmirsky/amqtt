import asyncio
from asyncio import AbstractEventLoop, Future, Queue
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from amqtt.adapters import ReaderAdapter, WriterAdapter
from amqtt.errors import MQTTError
from amqtt.mqtt.constants import MQTT_5_0
from amqtt.mqtt.connack import ConnackPacket
from amqtt.mqtt.connect import ConnectPacket
from amqtt.mqtt.disconnect import DisconnectPacket
from amqtt.mqtt.packet import MQTTPacket, MQTTPacketType
from amqtt.mqtt.pingreq import PingReqPacket
from amqtt.mqtt.pingresp import PingRespPacket
from amqtt.mqtt.protocol.handler import ProtocolHandler
from amqtt.mqtt.puback import PubackPacket
from amqtt.mqtt.pubcomp import PubcompPacket
from amqtt.mqtt.publish import PublishPacket
from amqtt.mqtt.pubrec import PubrecPacket
from amqtt.mqtt.pubrel import PubrelPacket
from amqtt.mqtt.suback import SubackPacket
from amqtt.mqtt.subscribe import SubscribePacket
from amqtt.mqtt.unsuback import UnsubackPacket
from amqtt.mqtt.unsubscribe import UnsubscribePacket
from amqtt.plugins.manager import PluginManager
from amqtt.session import Session

from .handler import EVENT_MQTT_PACKET_RECEIVED, EVENT_MQTT_PACKET_SENT


class ClientProtocolHandler(ProtocolHandler):
    """MQTT client protocol implementation."""

    def __init__(
        self,
        plugins_manager: PluginManager,
        session: Optional[Session] = None,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        super().__init__(plugins_manager, session, loop)
        self._ping_task: Optional[asyncio.Task] = None
        self._pingresp_queue: Queue = Queue()
        self._subscriptions_waiter: Dict[int, Future] = {}
        self._unsubscriptions_waiter: Dict[int, Future] = {}
        self._puback_waiters: Dict[int, Future] = {}
        self._pubrec_waiters: Dict[int, Future] = {}
        self._pubrel_waiters: Dict[int, Future] = {}
        self._pubcomp_waiters: Dict[int, Future] = {}

    async def start(self) -> None:
        await super().start()

    async def stop(self) -> None:
        if self._ping_task is not None:
            if not self._ping_task.done():
                self._ping_task.cancel()
            self._ping_task = None
        await super().stop()

    async def _disconnect(self, disconnect: DisconnectPacket) -> None:
        await self.mqtt_write(disconnect)
        await self.stop()

    async def disconnect(self, disconnect: Optional[DisconnectPacket] = None) -> None:
        """Send a DISCONNECT packet and stop the protocol."""
        if disconnect is None:
            disconnect = DisconnectPacket()
        await self._disconnect(disconnect)

    async def connect(
        self,
        host: str,
        port: int = 1883,
        cleansession: bool = True,
        keepalive: int = 60,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        will_message: Optional[Union[str, bytes]] = None,
        will_topic: Optional[str] = None,
        will_qos: Optional[int] = None,
        will_retain: Optional[bool] = None,
        version: int = 0x04,  # Default to MQTT 3.1.1
        properties: Optional[Dict] = None,
        will_properties: Optional[Dict] = None,
    ) -> ConnackPacket:
        """Connect to a remote broker."""
        reader = await self._connected_reader_cond.wait_for(self._connected_reader)
        writer = await self._connected_writer_cond.wait_for(self._connected_writer)

        # Build and send CONNECT packet
        if version == MQTT_5_0:  # MQTT 5.0
            connect = ConnectPacket.build_mqtt5(
                client_id=client_id,
                clean_session=cleansession,
                keep_alive=keepalive,
                username=username,
                password=password,
                will_flag=will_message is not None and will_topic is not None,
                will_retain=will_retain,
                will_qos=will_qos,
                will_topic=will_topic,
                will_message=will_message,
                properties=properties,
                will_properties=will_properties,
            )
        else:  # MQTT 3.1.1 or earlier
            connect = ConnectPacket.build(
                client_id=client_id,
                clean_session=cleansession,
                keep_alive=keepalive,
                username=username,
                password=password,
                will_flag=will_message is not None and will_topic is not None,
                will_retain=will_retain,
                will_qos=will_qos,
                will_topic=will_topic,
                will_message=will_message,
            )

        await self.mqtt_write(connect)

        # Wait for CONNACK
        connack = await ConnackPacket.from_stream(reader)
        await self.plugins_manager.fire_event(EVENT_MQTT_PACKET_RECEIVED, packet=connack)

        # Start keepalive task if needed
        if keepalive > 0:
            self._ping_task = asyncio.create_task(self._keep_alive(keepalive))

        return connack

    async def _keep_alive(self, keepalive: int) -> None:
        """Keep alive MQTT connection by sending periodic PINGREQ packets."""
        sleep_time = keepalive * 0.9  # Send ping before keep alive runs out
        while True:
            await asyncio.sleep(sleep_time)
            try:
                # Send PINGREQ and wait for PINGRESP
                pingreq = PingReqPacket()
                await self.mqtt_write(pingreq)
                resp = await asyncio.wait_for(self._pingresp_queue.get(), keepalive)
                if not isinstance(resp, PingRespPacket):
                    self.logger.warning(f"Received {resp} instead of PingRespPacket")
            except asyncio.TimeoutError:
                self.logger.warning("Timeout while waiting for PINGRESP")
                break
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.warning(f"Error in keep alive: {exc!r}")
                break

    async def mqtt_connect(self) -> int | None:
        connect_packet = self._build_connect_packet()
        await self._send_packet(connect_packet)

        if self.reader is None:
            msg = "Reader is not initialized."
            raise AMQTTError(msg)

        connack = await ConnackPacket.from_stream(self.reader)
        await self.plugins_manager.fire_event(EVENT_MQTT_PACKET_RECEIVED, packet=connack, session=self.session)
        return connack.return_code

    def _build_connect_packet(self) -> ConnectPacket:
        vh = ConnectVariableHeader()
        payload = ConnectPayload()

        if self.session is None:
            msg = "Session is not initialized."
            raise AMQTTError(msg)

        vh.keep_alive = self.session.keep_alive
        vh.clean_session_flag = self.session.clean_session if self.session.clean_session is not None else False
        vh.will_retain_flag = self.session.will_retain if self.session.will_retain is not None else False
        payload.client_id = self.session.client_id

        if self.session.username:
            vh.username_flag = True
            payload.username = self.session.username
        else:
            vh.username_flag = False

        if self.session.password:
            vh.password_flag = True
            payload.password = self.session.password
        else:
            vh.password_flag = False

        if self.session.will_flag:
            vh.will_flag = True
            if self.session.will_qos is not None:
                vh.will_qos = self.session.will_qos
            payload.will_message = self.session.will_message
            payload.will_topic = self.session.will_topic
        else:
            vh.will_flag = False

        return ConnectPacket(variable_header=vh, payload=payload)

    async def mqtt_subscribe(self, topics: list[tuple[str, int]], packet_id: int) -> list[int]:
        """Subscribe to the given topics.

        :param topics: List of tuples, e.g. [('filter', '/a/b', 'qos': 0x00)].
        :return: Return codes for the subscription.
        """
        subscribe = SubscribePacket.build(topics, packet_id)
        await self._send_packet(subscribe)

        if subscribe.variable_header is None:
            msg = f"Invalid variable header in SUBSCRIBE packet: {subscribe.variable_header}"
            raise AMQTTError(msg)

        waiter: asyncio.Future[list[int]] = asyncio.Future()
        self._subscriptions_waiter[subscribe.variable_header.packet_id] = waiter
        try:
            return_codes = await waiter
        finally:
            del self._subscriptions_waiter[subscribe.variable_header.packet_id]
        return return_codes

    async def handle_suback(self, suback: SubackPacket) -> None:
        if suback.variable_header is None:
            msg = "SUBACK packet: variable header not initialized."
            raise AMQTTError(msg)
        if suback.payload is None:
            msg = "SUBACK packet: payload not initialized."
            raise AMQTTError(msg)

        packet_id = suback.variable_header.packet_id

        waiter = self._subscriptions_waiter.get(packet_id)
        if waiter is not None:
            waiter.set_result(suback.payload.return_codes)
        else:
            self.logger.warning(f"Received SUBACK for unknown pending subscription with Id: {packet_id}")

    async def mqtt_unsubscribe(self, topics: list[str], packet_id: int) -> None:
        """Unsubscribe from the given topics.

        :param topics: List of topics ['/a/b', ...].
        """
        unsubscribe = UnsubscribePacket.build(topics, packet_id)

        if unsubscribe.variable_header is None:
            msg = "UNSUBSCRIBE packet: variable header not initialized."
            raise AMQTTError(msg)

        await self._send_packet(unsubscribe)
        waiter: asyncio.Future[Any] = asyncio.Future()
        self._unsubscriptions_waiter[unsubscribe.variable_header.packet_id] = waiter
        try:
            await waiter
        finally:
            del self._unsubscriptions_waiter[unsubscribe.variable_header.packet_id]

    async def handle_unsuback(self, unsuback: UnsubackPacket) -> None:
        if unsuback.variable_header is None:
            msg = "UNSUBACK packet: variable header not initialized."
            raise AMQTTError(msg)

        packet_id = unsuback.variable_header.packet_id
        waiter = self._unsubscriptions_waiter.get(packet_id)
        if waiter is not None:
            waiter.set_result(None)
        else:
            self.logger.warning(f"Received UNSUBACK for unknown pending unsubscription with Id: {packet_id}")

    async def mqtt_disconnect(self) -> None:
        disconnect_packet = DisconnectPacket()
        await self._send_packet(disconnect_packet)

    async def mqtt_ping(self) -> PingRespPacket:
        ping_packet = PingReqPacket()
        try:
            await self._send_packet(ping_packet)
            resp = await self._pingresp_queue.get()
        finally:
            self._ping_task = None  # Ensure the task is cleaned up
        return resp

    async def handle_pingresp(self, pingresp: PingRespPacket) -> None:
        await self._pingresp_queue.put(pingresp)

    async def handle_connection_closed(self) -> None:
        self.logger.debug("Broker closed connection")
        if self._disconnect_waiter is not None and not self._disconnect_waiter.done():
            self._disconnect_waiter.set_result(None)

    async def wait_disconnect(self) -> None:
        if self._disconnect_waiter is not None:
            await self._disconnect_waiter

    async def handle_write_timeout(self) -> None:
        try:
            if not self._ping_task:
                self.logger.debug("Scheduling Ping")
                self._ping_task = asyncio.create_task(self.mqtt_ping())
        except asyncio.InvalidStateError as e:
            self.logger.warning(f"Invalid state while scheduling ping task: {e!r}")
        except asyncio.CancelledError as e:
            self.logger.info(f"Ping task was cancelled: {e!r}")

    async def handle_read_timeout(self) -> None:
        pass
