from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import PUBCOMP, SUCCESS
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class PubcompVariableHeader(MQTTVariableHeader):
    """Variable header for PUBCOMP packet."""

    __slots__ = ("packet_id", "reason_code", "properties")

    def __init__(self, packet_id: int = 0, reason_code: int = SUCCESS) -> None:
        super().__init__()
        self.packet_id = packet_id
        self.reason_code = reason_code
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"PubcompVariableHeader(packet_id={self.packet_id}, reason_code={self.reason_code}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        packet_id_bytes = await read_or_raise(reader, 2)
        packet_id = bytes_to_int(packet_id_bytes)
        
        # For MQTT 3.1.1, only packet_id is present
        if fixed_header.remaining_length == 2:
            return cls(packet_id)
            
        # For MQTT5, read reason code if present
        reason_code = SUCCESS
        if fixed_header.remaining_length > 2:
            reason_code_bytes = await read_or_raise(reader, 1)
            reason_code = bytes_to_int(reason_code_bytes)
            
        var_header = cls(packet_id, reason_code)
        
        # Read properties if there are more bytes
        if fixed_header.remaining_length > 3:
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode variable header to bytes."""
        out = bytearray(2)  # packet_id
        out[0] = self.packet_id >> 8
        out[1] = self.packet_id & 0x00FF
        
        # For MQTT5, include reason code and properties
        if hasattr(self, 'mqtt5') and self.mqtt5:
            # Add reason code
            out.append(self.reason_code)
            
            # Add properties
            out.extend(self.properties.to_bytes())
            
        return out


class PubcompPacket(MQTTPacket[PubcompVariableHeader, None, MQTTFixedHeader]):
    """PUBCOMP packet."""

    VARIABLE_HEADER = PubcompVariableHeader
    PAYLOAD = None

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: PubcompVariableHeader = None,
        payload=None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(PUBCOMP, 0x00)

        super().__init__(fixed, variable_header, payload)

    @property
    def packet_id(self) -> int:
        """Return the packet ID."""
        if self.variable_header is not None:
            return self.variable_header.packet_id
        return 0

    @packet_id.setter
    def packet_id(self, packet_id: int) -> None:
        """Set the packet ID."""
        if self.variable_header is None:
            self.variable_header = PubcompVariableHeader()
        self.variable_header.packet_id = packet_id

    @property
    def reason_code(self) -> int:
        """Return the reason code."""
        if self.variable_header is not None:
            return self.variable_header.reason_code
        return SUCCESS

    @reason_code.setter
    def reason_code(self, reason_code: int) -> None:
        """Set the reason code."""
        if self.variable_header is None:
            self.variable_header = PubcompVariableHeader()
        self.variable_header.reason_code = reason_code

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
            self.variable_header = PubcompVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, packet_id: int) -> Self:
        """Build a PUBCOMP packet for MQTT 3.1.1."""
        variable_header = PubcompVariableHeader(packet_id)
        return cls(variable_header=variable_header)

    @classmethod
    def build_mqtt5(cls, packet_id: int, reason_code: int = SUCCESS, properties: Properties = None) -> Self:
        """Build a PUBCOMP packet for MQTT5."""
        variable_header = PubcompVariableHeader(packet_id, reason_code)
        variable_header.mqtt5 = True  # Mark as MQTT5 packet
        
        if properties:
            variable_header.properties = properties
            
        return cls(variable_header=variable_header)
