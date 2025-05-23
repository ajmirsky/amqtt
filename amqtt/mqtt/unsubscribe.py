from typing import List, Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, encode_string, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import UNSUBSCRIBE
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class UnsubscribeVariableHeader(MQTTVariableHeader):
    """Variable header for UNSUBSCRIBE packet."""

    __slots__ = ("packet_id", "properties")

    def __init__(self, packet_id: int = 0) -> None:
        super().__init__()
        self.packet_id = packet_id
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"UnsubscribeVariableHeader(packet_id={self.packet_id}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        packet_id_bytes = await read_or_raise(reader, 2)
        packet_id = bytes_to_int(packet_id_bytes)
        var_header = cls(packet_id)
        
        # Read properties for MQTT5
        if hasattr(fixed_header, 'mqtt5') and fixed_header.mqtt5:
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


class UnsubscribePayload(MQTTPayload):
    """Payload for UNSUBSCRIBE packet."""

    __slots__ = ("topics",)

    def __init__(self, topics: List[str] = None) -> None:
        super().__init__()
        self.topics = topics or []

    def __repr__(self) -> str:
        return f"UnsubscribePayload(topics={self.topics})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader, variable_header: UnsubscribeVariableHeader) -> Self:
        """Decode payload from stream."""
        topics = []
        remaining_bytes = fixed_header.remaining_length - variable_header.bytes_length
        
        # For MQTT5, account for properties length
        if hasattr(fixed_header, 'mqtt5') and fixed_header.mqtt5:
            remaining_bytes -= len(variable_header.properties.to_bytes())
            
        while remaining_bytes > 0:
            topic_len_bytes = await read_or_raise(reader, 2)
            topic_len = bytes_to_int(topic_len_bytes)
            topic = await read_or_raise(reader, topic_len)
            topics.append(topic.decode())
            remaining_bytes -= topic_len + 2
            
        return cls(topics)

    def to_bytes(self) -> bytearray:
        """Encode payload to bytes."""
        out = bytearray()
        for topic in self.topics:
            out.extend(encode_string(topic))
        return out


class UnsubscribePacket(MQTTPacket[UnsubscribeVariableHeader, UnsubscribePayload, MQTTFixedHeader]):
    """UNSUBSCRIBE packet."""

    VARIABLE_HEADER = UnsubscribeVariableHeader
    PAYLOAD = UnsubscribePayload

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: UnsubscribeVariableHeader = None,
        payload: UnsubscribePayload = None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(UNSUBSCRIBE, 0x02)  # [0 0 1 0] (flags fixed to 2)

        if variable_header is None:
            variable_header = UnsubscribeVariableHeader()

        if payload is None:
            payload = UnsubscribePayload()

        super().__init__(fixed, variable_header, payload)

    @property
    def topics(self) -> List[str]:
        """Return the topics."""
        return self.payload.topics

    @topics.setter
    def topics(self, topics: List[str]) -> None:
        """Set the topics."""
        if not self.payload:
            self.payload = UnsubscribePayload()
        self.payload.topics = topics

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
            self.variable_header = UnsubscribeVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, topics: List[str], packet_id: int) -> Self:
        """Build an UNSUBSCRIBE packet for MQTT 3.1.1."""
        variable_header = UnsubscribeVariableHeader(packet_id)
        payload = UnsubscribePayload(topics)
        return cls(variable_header=variable_header, payload=payload)

    @classmethod
    def build_mqtt5(cls, topics: List[str], packet_id: int, properties: Properties = None) -> Self:
        """Build an UNSUBSCRIBE packet for MQTT5."""
        variable_header = UnsubscribeVariableHeader(packet_id)
        variable_header.mqtt5 = True  # Mark as MQTT5 packet
        
        if properties:
            variable_header.properties = properties
            
        payload = UnsubscribePayload(topics)
        fixed_header = MQTTFixedHeader(UNSUBSCRIBE, 0x02)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        return cls(fixed=fixed_header, variable_header=variable_header, payload=payload)
