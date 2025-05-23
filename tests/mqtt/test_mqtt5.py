import asyncio
import unittest

from amqtt.adapters import BufferReader, BufferWriter
from amqtt.mqtt.auth import AuthPacket
from amqtt.mqtt.connect import ConnectPacket
from amqtt.mqtt.connack import ConnackPacket
from amqtt.mqtt.constants import (
    MQTT_5_0,
    SUCCESS,
    CONTINUE_AUTHENTICATION,
    AUTHENTICATION_METHOD,
    AUTHENTICATION_DATA,
    SESSION_EXPIRY_INTERVAL,
    RECEIVE_MAXIMUM,
    TOPIC_ALIAS_MAXIMUM,
    USER_PROPERTY,
)
from amqtt.mqtt.disconnect import DisconnectPacket
from amqtt.mqtt.mqtt5_helper import MQTT5Helper
from amqtt.mqtt.properties import Properties
from amqtt.mqtt.publish import PublishPacket
from amqtt.mqtt.puback import PubackPacket
from amqtt.mqtt.pubrec import PubrecPacket
from amqtt.mqtt.pubrel import PubrelPacket
from amqtt.mqtt.pubcomp import PubcompPacket
from amqtt.mqtt.subscribe import SubscribePacket
from amqtt.mqtt.suback import SubackPacket
from amqtt.mqtt.unsubscribe import UnsubscribePacket
from amqtt.mqtt.unsuback import UnsubackPacket


class TestMQTT5Packets(unittest.TestCase):
    """Test MQTT5 packet encoding and decoding."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_connect_mqtt5(self):
        """Test MQTT5 CONNECT packet."""
        # Create a CONNECT packet with MQTT5 properties
        properties = Properties()
        properties.set(SESSION_EXPIRY_INTERVAL, 3600)  # 1 hour
        properties.set(RECEIVE_MAXIMUM, 100)
        properties.set(TOPIC_ALIAS_MAXIMUM, 10)
        properties.add_user_property("client_type", "test")

        # For now, let's use the regular build method and manually set MQTT5 properties
        packet = ConnectPacket.build(
            client_id="test_client",
            clean_session=True,
            keep_alive=60,
        )
        packet.variable_header.proto_level = MQTT_5_0
        packet.variable_header.properties = properties

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(ConnectPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.variable_header.proto_level, MQTT_5_0)
        self.assertEqual(decoded.payload.client_id, "test_client")
        self.assertEqual(decoded.variable_header.keep_alive, 60)
        
        # Verify properties
        self.assertEqual(
            decoded.variable_header.properties.get(SESSION_EXPIRY_INTERVAL),
            3600,
        )
        self.assertEqual(
            decoded.variable_header.properties.get(RECEIVE_MAXIMUM),
            100,
        )
        self.assertEqual(
            decoded.variable_header.properties.get(TOPIC_ALIAS_MAXIMUM),
            10,
        )
        user_props = decoded.variable_header.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "client_type")
        self.assertEqual(user_props[0][1], "test")

    def test_connack_mqtt5(self):
        """Test MQTT5 CONNACK packet."""
        # Create a CONNACK packet with MQTT5 properties
        properties = Properties()
        properties.set(SESSION_EXPIRY_INTERVAL, 3600)  # 1 hour
        properties.set(RECEIVE_MAXIMUM, 100)
        properties.set(TOPIC_ALIAS_MAXIMUM, 10)
        properties.add_user_property("server_type", "test")

        # Use the MQTT5-specific build method
        packet = ConnackPacket.build_mqtt5(
            session_parent=True,  # Session present
            return_code=SUCCESS
        )
        packet.properties = properties

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(ConnackPacket.from_stream(reader))
        
        # Verify the packet
        self.assertTrue(decoded.session_parent)
        self.assertEqual(decoded.return_code, SUCCESS)
        
        # Verify properties
        self.assertEqual(
            decoded.properties.get(SESSION_EXPIRY_INTERVAL),
            3600,
        )
        self.assertEqual(
            decoded.properties.get(RECEIVE_MAXIMUM),
            100,
        )
        self.assertEqual(
            decoded.properties.get(TOPIC_ALIAS_MAXIMUM),
            10,
        )
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "server_type")
        self.assertEqual(user_props[0][1], "test")

    def test_publish_mqtt5(self):
        """Test MQTT5 PUBLISH packet."""
        # Create a PUBLISH packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("message_type", "test")

        # Use the MQTT5-specific build method
        packet = PublishPacket.build_mqtt5(
            topic_name="test/topic",
            data=b"test message",
            packet_id=1234,
            qos=1,
            retain=False,
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(PublishPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.variable_header.topic_name, "test/topic")
        self.assertEqual(decoded.payload.data, b"test message")
        self.assertEqual(decoded.variable_header.packet_id, 1234)
        self.assertEqual(decoded.qos, 1)
        self.assertFalse(decoded.retain)
        
        # Verify properties
        user_props = decoded.variable_header.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "message_type")
        self.assertEqual(user_props[0][1], "test")

    def test_puback_mqtt5(self):
        """Test MQTT5 PUBACK packet."""
        # Create a PUBACK packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("ack_type", "test")

        # For now, let's use the regular build method and manually set MQTT5 properties
        packet = PubackPacket.build(packet_id=1234)
        packet.reason_code = SUCCESS
        packet.properties = properties
        packet.variable_header.mqtt5 = True

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(PubackPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.packet_id, 1234)
        self.assertEqual(decoded.reason_code, SUCCESS)
        
        # Verify properties
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "ack_type")
        self.assertEqual(user_props[0][1], "test")

    def test_subscribe_mqtt5(self):
        """Test MQTT5 SUBSCRIBE packet."""
        # Create a SUBSCRIBE packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("subscription_type", "test")

        # Use the MQTT5-specific build method
        packet = SubscribePacket.build_mqtt5(
            packet_id=1234,
            topics=[("test/topic", 1)],  # QoS 1
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(SubscribePacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.packet_id, 1234)
        self.assertEqual(len(decoded.topics), 1)
        self.assertEqual(decoded.topics[0][0], "test/topic")
        self.assertEqual(decoded.topics[0][1], 1)  # QoS 1
        
        # Verify properties
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "subscription_type")
        self.assertEqual(user_props[0][1], "test")

    def test_suback_mqtt5(self):
        """Test MQTT5 SUBACK packet."""
        # Create a SUBACK packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("suback_type", "test")

        # Use the MQTT5-specific build method
        packet = SubackPacket.build_mqtt5(
            packet_id=1234,
            return_codes=[0],  # Success with QoS 0
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(SubackPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.packet_id, 1234)
        self.assertEqual(len(decoded.return_codes), 1)
        self.assertEqual(decoded.return_codes[0], 0)  # Success with QoS 0
        
        # Verify properties
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "suback_type")
        self.assertEqual(user_props[0][1], "test")

    def test_unsubscribe_mqtt5(self):
        """Test MQTT5 UNSUBSCRIBE packet."""
        # Create an UNSUBSCRIBE packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("unsubscribe_type", "test")

        # Use the MQTT5-specific build method
        packet = UnsubscribePacket.build_mqtt5(
            packet_id=1234,
            topics=["test/topic"],
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(UnsubscribePacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.packet_id, 1234)
        self.assertEqual(len(decoded.topics), 1)
        self.assertEqual(decoded.topics[0], "test/topic")
        
        # Verify properties
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "unsubscribe_type")
        self.assertEqual(user_props[0][1], "test")

    def test_unsuback_mqtt5(self):
        """Test MQTT5 UNSUBACK packet."""
        # Create an UNSUBACK packet with MQTT5 properties
        properties = Properties()
        properties.add_user_property("unsuback_type", "test")

        # Use the MQTT5-specific build method
        packet = UnsubackPacket.build_mqtt5(
            packet_id=1234,
            reason_codes=[SUCCESS],
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(UnsubackPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.packet_id, 1234)
        self.assertEqual(len(decoded.reason_codes), 1)
        self.assertEqual(decoded.reason_codes[0], SUCCESS)
        
        # Verify properties
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "unsuback_type")
        self.assertEqual(user_props[0][1], "test")

    def test_disconnect_mqtt5(self):
        """Test MQTT5 DISCONNECT packet."""
        # Create a DISCONNECT packet with MQTT5 properties
        properties = Properties()
        properties.set(SESSION_EXPIRY_INTERVAL, 0)  # Don't maintain session
        properties.add_user_property("disconnect_type", "test")

        # Use the MQTT5-specific build method
        packet = DisconnectPacket.build_mqtt5(
            reason_code=SUCCESS,
            properties=properties
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(DisconnectPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.reason_code, SUCCESS)
        
        # Verify properties
        self.assertEqual(
            decoded.properties.get(SESSION_EXPIRY_INTERVAL),
            0,
        )
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "disconnect_type")
        self.assertEqual(user_props[0][1], "test")

    def test_auth_mqtt5(self):
        """Test MQTT5 AUTH packet."""
        # Create an AUTH packet with MQTT5 properties
        properties = Properties()
        properties.set(AUTHENTICATION_METHOD, "oauth2")
        properties.set(AUTHENTICATION_DATA, b"token123")
        properties.add_user_property("auth_type", "test")

        packet = AuthPacket.build(
            reason_code=CONTINUE_AUTHENTICATION,
            properties=properties,
        )

        # Encode the packet
        out = packet.to_bytes()
        
        # Decode the packet
        reader = BufferReader(out)
        decoded = self.loop.run_until_complete(AuthPacket.from_stream(reader))
        
        # Verify the packet
        self.assertEqual(decoded.reason_code, CONTINUE_AUTHENTICATION)
        
        # Verify properties
        self.assertEqual(
            decoded.properties.get(AUTHENTICATION_METHOD),
            "oauth2",
        )
        self.assertEqual(
            decoded.properties.get(AUTHENTICATION_DATA),
            b"token123",
        )
        user_props = decoded.properties.get_user_properties()
        self.assertEqual(user_props[0][0], "auth_type")
        self.assertEqual(user_props[0][1], "test")


if __name__ == "__main__":
    unittest.main()
