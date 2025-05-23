from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, decode_string, encode_string, int_to_bytes, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import MQTT_5_0
from amqtt.mqtt.packet import SUBSCRIBE, MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class SubscribeVariableHeader(MQTTVariableHeader):
    """Variable header for SUBSCRIBE packet."""

    __slots__ = ("packet_id", "properties")

    def __init__(self, packet_id: int = 0) -> None:
        super().__init__()
        self.packet_id = packet_id
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"SubscribeVariableHeader(packet_id={self.packet_id}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        packet_id = await cls.read_packet_id(reader)
        var_header = cls(packet_id)
        
        # Read properties for MQTT5 packets
        if fixed_header.flags & 0x01 == 0x01:  # MQTT5 packet flag
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode variable header to bytes."""
        out = bytearray(2)  # packet_id
        out[0] = self.packet_id >> 8
        out[1] = self.packet_id & 0x00FF
        
        # Add properties for MQTT5
        if hasattr(self, 'mqtt5') and self.mqtt5:
            out.extend(self.properties.to_bytes())
            
        return out


class SubscribePayload(MQTTPayload[SubscribeVariableHeader]):
    """Payload for SUBSCRIBE packet."""

    __slots__ = ("topics", "subscription_options")

    def __init__(self, topics: list[tuple[str, int]] = None) -> None:
        super().__init__()
        self.topics = topics or []
        self.subscription_options = {}  # MQTT5 subscription options by topic

    def __repr__(self) -> str:
        return f"SubscribePayload(topics={self.topics})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, variable_header: SubscribeVariableHeader, fixed_header: MQTTFixedHeader) -> Self:
        """Decode payload from stream."""
        topics = []
        subscription_options = {}
        payload_length = fixed_header.remaining_length - variable_header.bytes_length
        bytes_read = 0
        
        # Check if this is an MQTT5 packet
        is_mqtt5 = fixed_header.flags & 0x01 == 0x01
        
        while bytes_read < payload_length:
            topic_start = bytes_read
            topic = await decode_string(reader)
            bytes_read += 2 + len(topic.encode('utf-8'))
            
            options_byte = await read_or_raise(reader, 1)
            bytes_read += 1
            qos = options_byte[0] & 0x03
            
            # For MQTT5, parse additional subscription options
            if is_mqtt5:
                no_local = bool(options_byte[0] & 0x04)
                retain_as_published = bool(options_byte[0] & 0x08)
                retain_handling = (options_byte[0] & 0x30) >> 4
                
                subscription_options[topic] = {
                    'no_local': no_local,
                    'retain_as_published': retain_as_published,
                    'retain_handling': retain_handling
                }
                
            topics.append((topic, qos))
            
        payload = cls(topics)
        payload.subscription_options = subscription_options
        return payload

    def to_bytes(self, is_mqtt5: bool = False) -> bytearray:
        """Encode payload to bytes."""
        out = bytearray()
        for index, (topic, qos) in enumerate(self.topics):
            out.extend(encode_string(topic))
            
            # For MQTT5, include additional subscription options
            if is_mqtt5 and topic in self.subscription_options:
                options = self.subscription_options[topic]
                options_byte = qos & 0x03
                
                if options.get('no_local', False):
                    options_byte |= 0x04
                if options.get('retain_as_published', False):
                    options_byte |= 0x08
                if 'retain_handling' in options:
                    options_byte |= (options['retain_handling'] & 0x03) << 4
                    
                out.append(options_byte)
            else:
                # For MQTT 3.1.1, only QoS
                out.append(qos)
                
        return out


class SubscribePacket(MQTTPacket[SubscribeVariableHeader, SubscribePayload, MQTTFixedHeader]):
    """SUBSCRIBE packet."""

    VARIABLE_HEADER = SubscribeVariableHeader
    PAYLOAD = SubscribePayload

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: SubscribeVariableHeader = None,
        payload: SubscribePayload = None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(SUBSCRIBE, 0x02)  # [MQTT-3.8.1-1]

        super().__init__(fixed, variable_header, payload)

    @property
    def topics(self) -> list[tuple[str, int]]:
        """Return the list of topics and their QoS."""
        if self.payload is not None:
            return self.payload.topics
        return []

    @topics.setter
    def topics(self, topics: list[tuple[str, int]]) -> None:
        """Set the list of topics and their QoS."""
        if self.payload is None:
            self.payload = SubscribePayload()
        self.payload.topics = topics

    @property
    def subscription_options(self) -> dict:
        """Return the subscription options for MQTT5."""
        if self.payload is not None:
            return self.payload.subscription_options
        return {}

    @subscription_options.setter
    def subscription_options(self, options: dict) -> None:
        """Set the subscription options for MQTT5."""
        if self.payload is None:
            self.payload = SubscribePayload()
        self.payload.subscription_options = options

    @property
    def properties(self) -> Properties:
        """Return the properties for MQTT5."""
        if self.variable_header is not None:
            return self.variable_header.properties
        return Properties()

    @properties.setter
    def properties(self, properties: Properties) -> None:
        """Set the properties for MQTT5."""
        if self.variable_header is None:
            self.variable_header = SubscribeVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, topics: list[tuple[str, int]], packet_id: int) -> Self:
        """Build a SUBSCRIBE packet for MQTT 3.1.1."""
        variable_header = SubscribeVariableHeader(packet_id)
        payload = SubscribePayload(topics)
        return cls(variable_header=variable_header, payload=payload)

    @classmethod
    def build_mqtt5(cls, topics: list[tuple[str, int]], packet_id: int, subscription_options: dict = None, properties: Properties = None) -> Self:
        """Build a SUBSCRIBE packet for MQTT5."""
        variable_header = SubscribeVariableHeader(packet_id)
        variable_header.mqtt5 = True  # Mark as MQTT5 packet
        
        if properties:
            variable_header.properties = properties
            
        payload = SubscribePayload(topics)
        
        if subscription_options:
            payload.subscription_options = subscription_options
            
        packet = cls(fixed=MQTTFixedHeader(SUBSCRIBE, 0x03), variable_header=variable_header, payload=payload)
        return packet
