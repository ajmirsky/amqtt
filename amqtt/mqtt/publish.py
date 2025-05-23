from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, decode_string, encode_string, int_to_bytes, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import MQTT_5_0
from amqtt.mqtt.packet import PUBLISH, MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class PublishVariableHeader(MQTTVariableHeader):
    """Variable header for PUBLISH packet."""

    __slots__ = ("topic_name", "packet_id", "properties")

    def __init__(self, topic_name: str = "", packet_id: int = None) -> None:
        super().__init__()
        self.topic_name = topic_name
        self.packet_id = packet_id
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"PublishVariableHeader(topic_name={self.topic_name}, packet_id={self.packet_id}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        topic_name = await decode_string(reader)
        
        # Read packet_id if QoS > 0
        packet_id = None
        qos = (fixed_header.flags & 0x06) >> 1
        if qos > 0:
            packet_id_bytes = await read_or_raise(reader, 2)
            packet_id = bytes_to_int(packet_id_bytes)
            
        var_header = cls(topic_name, packet_id)
        
        # Read properties for MQTT5 packets
        if fixed_header.flags & 0x01 == 0x01:  # MQTT5 packet flag
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode variable header to bytes."""
        out = bytearray()
        out.extend(encode_string(self.topic_name))
        
        if self.packet_id is not None:
            out.extend(int_to_bytes(self.packet_id, 2))
            
        # Add properties for MQTT5
        if hasattr(self.properties, 'to_bytes') and hasattr(self, 'mqtt5') and self.mqtt5:
            out.extend(self.properties.to_bytes())
        elif hasattr(self.properties, 'to_bytes') and hasattr(self, '_parent') and hasattr(self._parent, 'fixed_header') and hasattr(self._parent.fixed_header, 'mqtt5') and self._parent.fixed_header.mqtt5:
            out.extend(self.properties.to_bytes())
            
        return out

    @property
    def bytes_length(self) -> int:
        """Return the length of the variable header when encoded to bytes."""
        length = 2 + len(self.topic_name.encode('utf-8'))  # 2 for topic length prefix
        
        if self.packet_id is not None:
            length += 2  # 2 for packet_id
            
        # Add properties length for MQTT5
        if hasattr(self, 'mqtt5') and self.mqtt5:
            props_bytes = self.properties.to_bytes()
            length += len(props_bytes)
        elif hasattr(self, '_parent') and hasattr(self._parent, 'fixed_header') and hasattr(self._parent.fixed_header, 'mqtt5') and self._parent.fixed_header.mqtt5:
            props_bytes = self.properties.to_bytes()
            length += len(props_bytes)
            
        return length


class PublishPayload(MQTTPayload[PublishVariableHeader]):
    """Payload for PUBLISH packet."""

    __slots__ = ("data",)

    def __init__(self, data: bytes = None) -> None:
        super().__init__()
        self.data = data or b""

    def __repr__(self) -> str:
        return f"PublishPayload(data={self.data!r})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, variable_header: PublishVariableHeader, fixed_header: MQTTFixedHeader) -> Self:
        """Decode payload from stream."""
        data = bytearray()
        bytes_to_read = fixed_header.remaining_length - variable_header.bytes_length
        
        if bytes_to_read > 0:
            data = await read_or_raise(reader, bytes_to_read)
            
        return cls(data)

    def to_bytes(self, fixed_header=None, variable_header=None) -> bytearray:
        """Encode payload to bytes."""
        return bytearray(self.data)


class PublishPacket(MQTTPacket[PublishVariableHeader, PublishPayload, MQTTFixedHeader]):
    """PUBLISH packet."""

    VARIABLE_HEADER = PublishVariableHeader
    PAYLOAD = PublishPayload

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: PublishVariableHeader = None,
        payload: PublishPayload = None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(PUBLISH, 0x00)

        super().__init__(fixed, variable_header, payload)

    @property
    def packet_id(self) -> int:
        """Return the packet ID."""
        if self.variable_header is not None and self.variable_header.packet_id is not None:
            return self.variable_header.packet_id
        return 0

    @packet_id.setter
    def packet_id(self, packet_id: int) -> None:
        """Set the packet ID."""
        if self.variable_header is None:
            self.variable_header = PublishVariableHeader()
        self.variable_header.packet_id = packet_id

    @property
    def topic_name(self) -> str:
        """Return the topic name."""
        if self.variable_header is not None:
            return self.variable_header.topic_name
        return ""

    @topic_name.setter
    def topic_name(self, topic_name: str) -> None:
        """Set the topic name."""
        if self.variable_header is None:
            self.variable_header = PublishVariableHeader()
        self.variable_header.topic_name = topic_name

    @property
    def data(self) -> bytes:
        """Return the payload data."""
        if self.payload is not None:
            return self.payload.data
        return b""

    @data.setter
    def data(self, data: bytes) -> None:
        """Set the payload data."""
        if self.payload is None:
            self.payload = PublishPayload()
        self.payload.data = data

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
            self.variable_header = PublishVariableHeader()
        self.variable_header.properties = properties

    @property
    def qos(self) -> int:
        """Return the QoS level."""
        if self.fixed_header is not None:
            return (self.fixed_header.flags & 0x06) >> 1
        return 0

    @qos.setter
    def qos(self, qos: int) -> None:
        """Set the QoS level."""
        if self.fixed_header is None:
            self.fixed_header = MQTTFixedHeader(PUBLISH, 0x00)
        self.fixed_header.flags &= 0xF9  # Clear QoS bits
        self.fixed_header.flags |= (qos << 1) & 0x06  # Set QoS bits

    @property
    def retain(self) -> bool:
        """Return the retain flag."""
        if self.fixed_header is not None:
            return bool(self.fixed_header.flags & 0x01)
        return False

    @retain.setter
    def retain(self, retain: bool) -> None:
        """Set the retain flag."""
        if self.fixed_header is None:
            self.fixed_header = MQTTFixedHeader(PUBLISH, 0x00)
        if retain:
            self.fixed_header.flags |= 0x01
        else:
            self.fixed_header.flags &= 0xFE

    @property
    def dup(self) -> bool:
        """Return the DUP flag."""
        if self.fixed_header is not None:
            return bool(self.fixed_header.flags & 0x08)
        return False

    @dup.setter
    def dup(self, dup: bool) -> None:
        """Set the DUP flag."""
        if self.fixed_header is None:
            self.fixed_header = MQTTFixedHeader(PUBLISH, 0x00)
        if dup:
            self.fixed_header.flags |= 0x08
        else:
            self.fixed_header.flags &= 0xF7

    @classmethod
    def build(cls, topic_name: str, data: bytes, packet_id: int = None, qos: int = 0, retain: bool = False, dup: bool = False) -> Self:
        """Build a PUBLISH packet for MQTT 3.1.1."""
        flags = 0x00
        if qos:
            flags |= (qos << 1) & 0x06
        if retain:
            flags |= 0x01
        if dup:
            flags |= 0x08
            
        fixed_header = MQTTFixedHeader(PUBLISH, flags)
        variable_header = PublishVariableHeader(topic_name, packet_id)
        payload = PublishPayload(data)
        return cls(fixed=fixed_header, variable_header=variable_header, payload=payload)

    @classmethod
    def build_mqtt5(cls, topic_name: str, data: bytes, packet_id: int = None, qos: int = 0, retain: bool = False, dup: bool = False, properties: Properties = None) -> Self:
        """Build a PUBLISH packet for MQTT5."""
        flags = 0x00  # Don't set MQTT5 flag in fixed header
        if qos:
            flags |= (qos << 1) & 0x06
        if retain:
            flags |= 0x01
        if dup:
            flags |= 0x08
            
        fixed_header = MQTTFixedHeader(PUBLISH, flags)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        variable_header = PublishVariableHeader(topic_name, packet_id)
        
        if properties:
            variable_header.properties = properties
            
        payload = PublishPayload(data)
        return cls(fixed=fixed_header, variable_header=variable_header, payload=payload)
