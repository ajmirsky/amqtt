import asyncio
from asyncio import AbstractEventLoop, Queue

from amqtt.adapters import ReaderAdapter, WriterAdapter
from amqtt.errors import MQTTError
from amqtt.mqtt.connack import (
    BAD_USERNAME_PASSWORD,
    CONNECTION_ACCEPTED,
    IDENTIFIER_REJECTED,
    NOT_AUTHORIZED,
    UNACCEPTABLE_PROTOCOL_VERSION,
    ConnackPacket,
)
from amqtt.mqtt.connect import ConnectPacket
from amqtt.mqtt.constants import MQTT_3_1, MQTT_3_1_1, MQTT_5_0, UNSUPPORTED_PROTOCOL_VERSION
from amqtt.mqtt.disconnect import DisconnectPacket
from amqtt.mqtt.pingreq import PingReqPacket
from amqtt.mqtt.pingresp import PingRespPacket
from amqtt.mqtt.protocol.handler import ProtocolHandler
from amqtt.mqtt.suback import SubackPacket
from amqtt.mqtt.subscribe import SubscribePacket
from amqtt.mqtt.unsuback import UnsubackPacket
from amqtt.mqtt.unsubscribe import UnsubscribePacket
from amqtt.plugins.manager import PluginManager
from amqtt.session import Session
from amqtt.utils import format_client_message

from .handler import EVENT_MQTT_PACKET_RECEIVED, EVENT_MQTT_PACKET_SENT

# MQTT protocol versions supported by this implementation
_MQTT_PROTOCOL_VERSIONS_SUPPORTED = [MQTT_3_1_1, MQTT_5_0]  # Support both 3.1.1 and 5.0


class Subscription:
    def __init__(self, packet_id: int, topics: list[tuple[str, int]]) -> None:
        self.packet_id = packet_id
        self.topics = topics


class UnSubscription:
    def __init__(self, packet_id: int, topics: list[str]) -> None:
        self.packet_id = packet_id
        self.topics = topics


class BrokerProtocolHandler(ProtocolHandler):
    def __init__(
        self,
        plugins_manager: PluginManager,
        session: Session | None = None,
        loop: AbstractEventLoop | None = None,
    ) -> None:
        super().__init__(plugins_manager, session, loop)
        self._disconnect_waiter: asyncio.Future[DisconnectPacket | None] | None = None
        self._pending_subscriptions: Queue[Subscription] = Queue()
        self._pending_unsubscriptions: Queue[UnSubscription] = Queue()

    async def start(self) -> None:
        await super().start()
        # Ensure the disconnect waiter is reset
        if self._disconnect_waiter and self._disconnect_waiter.done():
            self._disconnect_waiter = asyncio.Future()

    async def stop(self) -> None:
        """Stop the protocol handler and reset the disconnect waiter."""
        await super().stop()
        if self._disconnect_waiter is not None and not self._disconnect_waiter.done():
            self._disconnect_waiter.set_result(None)
        self._disconnect_waiter = None  # Reset the disconnect waiter
        # Clear pending subscriptions and unsubscriptions
        while not self._pending_subscriptions.empty():
            self._pending_subscriptions.get_nowait()
        while not self._pending_unsubscriptions.empty():
            self._pending_unsubscriptions.get_nowait()

    async def wait_disconnect(self) -> DisconnectPacket | None:
        """Wait for a disconnect packet or connection closure."""
        if self._disconnect_waiter is not None:
            return await self._disconnect_waiter
        return None

    def handle_write_timeout(self) -> None:
        pass

    def handle_read_timeout(self) -> None:
        pass

    async def handle_disconnect(self, disconnect: DisconnectPacket | None) -> None:
        """Handle a disconnect packet and notify the disconnect waiter."""
        self.logger.debug("Client disconnecting")
        if self._disconnect_waiter and not self._disconnect_waiter.done():
            self.logger.debug(f"Setting disconnect waiter result to {disconnect!r}")
            self._disconnect_waiter.set_result(disconnect)
        self._disconnect_waiter = None  # Reset the disconnect waiter to avoid reuse

    async def handle_connection_closed(self) -> None:
        """Handle connection closure and notify the disconnect waiter."""
        await self.handle_disconnect(None)

    async def handle_connect(self, connect: ConnectPacket) -> None:
        # Broker handler shouldn't receive CONNECT message during messages handling
        # as CONNECT messages are managed by the broker on client connection
        self.logger.error(
            f"{self.session.client_id if self.session else None} [MQTT-3.1.0-2] {format_client_message(self.session)} :"
            f" CONNECT message received during messages handling",
        )
        if self._disconnect_waiter is not None and not self._disconnect_waiter.done():
            self._disconnect_waiter.set_result(None)

    async def handle_pingreq(self, pingreq: PingReqPacket) -> None:
        await self._send_packet(PingRespPacket.build())

    async def handle_subscribe(self, subscribe: SubscribePacket) -> None:
        if subscribe.variable_header is None:
            msg = "SUBSCRIBE packet: variable header not initialized."
            raise MQTTError(msg)
        if subscribe.payload is None:
            msg = "SUBSCRIBE packet: payload not initialized."
            raise MQTTError(msg)

        subscription: Subscription = Subscription(subscribe.variable_header.packet_id, subscribe.payload.topics)
        await self._pending_subscriptions.put(subscription)

    async def handle_unsubscribe(self, unsubscribe: UnsubscribePacket) -> None:
        if unsubscribe.variable_header is None:
            msg = "UNSUBSCRIBE packet: variable header not initialized."
            raise MQTTError(msg)
        if unsubscribe.payload is None:
            msg = "UNSUBSCRIBE packet: payload not initialized."
            raise MQTTError(msg)
        unsubscription: UnSubscription = UnSubscription(unsubscribe.variable_header.packet_id, unsubscribe.payload.topics)
        await self._pending_unsubscriptions.put(unsubscription)

    async def get_next_pending_subscription(self) -> Subscription:
        return await self._pending_subscriptions.get()

    async def get_next_pending_unsubscription(self) -> UnSubscription:
        return await self._pending_unsubscriptions.get()

    async def mqtt_acknowledge_subscription(self, packet_id: int, return_codes: list[int]) -> None:
        suback = SubackPacket.build(packet_id, return_codes)
        await self._send_packet(suback)

    async def mqtt_acknowledge_unsubscription(self, packet_id: int) -> None:
        unsuback = UnsubackPacket.build(packet_id)
        await self._send_packet(unsuback)

    async def mqtt_connack_authorize(self, authorize: bool) -> None:
        if self.session is None:
            msg = "Session is not initialized!"
            raise MQTTError(msg)

        connack = ConnackPacket.build(self.session.parent, CONNECTION_ACCEPTED if authorize else NOT_AUTHORIZED)
        await self._send_packet(connack)

    @classmethod
    async def init_from_connect(
        cls,
        reader: ReaderAdapter,
        writer: WriterAdapter,
        plugins_manager: PluginManager,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> tuple["BrokerProtocolHandler", Session]:
        """Initialize from a CONNECT packet and validates the connection."""
        connect = await ConnectPacket.from_stream(reader)
        await plugins_manager.fire_event(EVENT_MQTT_PACKET_RECEIVED, packet=connect)

        if connect.variable_header is None:
            msg = "CONNECT packet: variable header not initialized."
            raise MQTTError(msg)

        # Check protocol version
        remote_address, remote_port = writer.get_peer_info()
        proto_level = connect.variable_header.proto_level

        if proto_level not in _MQTT_PROTOCOL_VERSIONS_SUPPORTED:
            if proto_level == MQTT_3_1:  # Handle MQTT 3.1 (not 3.1.1) specially
                connack = ConnackPacket.build(0, UNACCEPTABLE_PROTOCOL_VERSION)  # [MQTT-3.2.2-4] session_parent=0
            elif proto_level == MQTT_5_0:  # For MQTT 5.0, use the MQTT5 reason code
                connack = ConnackPacket.build_mqtt5(0, UNSUPPORTED_PROTOCOL_VERSION)
            else:  # For other unsupported versions
                connack = ConnackPacket.build(0, UNACCEPTABLE_PROTOCOL_VERSION)  # [MQTT-3.2.2-4] session_parent=0
                
            await plugins_manager.fire_event(EVENT_MQTT_PACKET_SENT, packet=connack)
            await connack.to_stream(writer)
            await writer.close()
            msg = f"Invalid protocol from {remote_address}:{remote_port}: 0x{proto_level:02x}"
            raise MQTTError(msg)

        if connect.payload is None:
            msg = "CONNECT packet: payload not initialized."
            raise MQTTError(msg)

        if connect.client_id == "":
            if not connect.clean_session_flag:
                connack = ConnackPacket.build(0, IDENTIFIER_REJECTED)
                await plugins_manager.fire_event(EVENT_MQTT_PACKET_SENT, packet=connack)
                await connack.to_stream(writer)
                await writer.close()
                msg = f"[MQTT-3.1.3-8] Invalid client_id with CleanSession=0: {connect.client_id}"
                raise MQTTError(msg)

        incoming_session = Session()
        incoming_session.client_id = connect.client_id
        incoming_session.clean_session = connect.clean_session_flag
        incoming_session.will_flag = connect.will_flag
        incoming_session.will_message = connect.will_message
        incoming_session.will_qos = connect.will_qos
        incoming_session.will_retain = connect.will_retain_flag
        incoming_session.will_topic = connect.will_topic
        incoming_session.username = connect.username
        incoming_session.password = connect.password
        incoming_session.remote_address = remote_address
        incoming_session.remote_port = remote_port
        
        # For MQTT5, store the protocol version and properties
        incoming_session.protocol_version = proto_level
        if proto_level == MQTT_5_0 and hasattr(connect, 'properties'):
            incoming_session.properties = connect.properties
            if hasattr(connect, 'will_properties'):
                incoming_session.will_properties = connect.will_properties

        incoming_session.keep_alive = max(connect.keep_alive, 0)

        if connect.keep_alive > 0:
            incoming_session.keep_alive = connect.keep_alive
        else:
            incoming_session.keep_alive = 0

        handler = cls(plugins_manager, loop=loop)
        return handler, incoming_session
