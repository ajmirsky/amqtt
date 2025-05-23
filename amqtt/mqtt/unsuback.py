from typing import List, Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import UNSUBACK, SUCCESS
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class UnsubackVariableHeader(MQTTVariableHeader):
    """Variable header for UNSUBACK packet."""

    __slots__ = ("packet_id", "properties")

    def __init__(self, packet_id: int = 0) -> None:
        super().__init__()
        self.packet_id = packet_id
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"UnsubackVariableHeader(packet_id={self.packet_id}, properties={self.properties})"

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


class UnsubackPayload(MQTTPayload):
    """Payload for UNSUBACK packet."""

    __slots__ = ("reason_codes",)

    def __init__(self, reason_codes: List[int] = None) -> None:
        super().__init__()
        self.reason_codes = reason_codes or []

    def __repr__(self) -> str:
        return f"UnsubackPayload(reason_codes={self.reason_codes})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader, variable_header: UnsubackVariableHeader) -> Self:
        """Decode payload from stream."""
        reason_codes = []
        remaining_bytes = fixed_header.remaining_length - variable_header.bytes_length
        
        # For MQTT5, account for properties length
        if hasattr(fixed_header, 'mqtt5') and fixed_header.mqtt5:
            remaining_bytes -= len(variable_header.properties.to_bytes())
        
        # For MQTT 3.1.1, there is no payload
        if not hasattr(fixed_header, 'mqtt5') or not fixed_header.mqtt5:
            return cls()
            
        # For MQTT5, read reason codes
        while remaining_bytes > 0:
            reason_code_bytes = await read_or_raise(reader, 1)
            reason_code = bytes_to_int(reason_code_bytes)
            reason_codes.append(reason_code)
            remaining_bytes -= 1
            
        return cls(reason_codes)

    def to_bytes(self) -> bytearray:
        """Encode payload to bytes."""
        out = bytearray()
        for reason_code in self.reason_codes:
            out.append(reason_code)
        return out


class UnsubackPacket(MQTTPacket[UnsubackVariableHeader, UnsubackPayload, MQTTFixedHeader]):
    """UNSUBACK packet."""

    VARIABLE_HEADER = UnsubackVariableHeader
    PAYLOAD = UnsubackPayload

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: UnsubackVariableHeader = None,
        payload: UnsubackPayload = None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(UNSUBACK, 0x00)

        if variable_header is None:
            variable_header = UnsubackVariableHeader()

        if payload is None:
            payload = UnsubackPayload()

        super().__init__(fixed, variable_header, payload)

    @property
    def reason_codes(self) -> List[int]:
        """Return the reason codes."""
        return self.payload.reason_codes

    @reason_codes.setter
    def reason_codes(self, reason_codes: List[int]) -> None:
        """Set the reason codes."""
        if not self.payload:
            self.payload = UnsubackPayload()
        self.payload.reason_codes = reason_codes

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
            self.variable_header = UnsubackVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, packet_id: int) -> Self:
        """Build an UNSUBACK packet for MQTT 3.1.1."""
        variable_header = UnsubackVariableHeader(packet_id)
        return cls(variable_header=variable_header)

    @classmethod
    def build_mqtt5(cls, packet_id: int, reason_codes: List[int] = None, properties: Properties = None) -> Self:
        """Build an UNSUBACK packet for MQTT5."""
        variable_header = UnsubackVariableHeader(packet_id)
        variable_header.mqtt5 = True  # Mark as MQTT5 packet
        
        if properties:
            variable_header.properties = properties
            
        payload = UnsubackPayload(reason_codes or [SUCCESS])
        fixed_header = MQTTFixedHeader(UNSUBACK, 0x00)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        return cls(fixed=fixed_header, variable_header=variable_header, payload=payload)
