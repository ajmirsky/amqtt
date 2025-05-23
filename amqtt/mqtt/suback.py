from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, int_to_bytes, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import MQTT_5_0
from amqtt.mqtt.packet import SUBACK, MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class SubackVariableHeader(MQTTVariableHeader):
    """Variable header for SUBACK packet."""

    __slots__ = ("packet_id", "properties")

    def __init__(self, packet_id: int = 0) -> None:
        super().__init__()
        self.packet_id = packet_id
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"SubackVariableHeader(packet_id={self.packet_id}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        # Read packet ID (2 bytes)
        packet_id_bytes = await read_or_raise(reader, 2)
        packet_id = bytes_to_int(packet_id_bytes)
        var_header = cls(packet_id)
        
        # Read properties for MQTT5 packets
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

    @property
    def bytes_length(self) -> int:
        """Return the length of the variable header when encoded to bytes."""
        length = 2  # packet_id
        
        # Add properties length for MQTT5
        if hasattr(self, 'mqtt5') and self.mqtt5:
            props_bytes = self.properties.to_bytes()
            length += len(props_bytes)
        elif hasattr(self, '_parent') and hasattr(self._parent, 'fixed_header') and hasattr(self._parent.fixed_header, 'mqtt5') and self._parent.fixed_header.mqtt5:
            props_bytes = self.properties.to_bytes()
            length += len(props_bytes)
            
        return length


class SubackPayload(MQTTPayload[SubackVariableHeader]):
    """Payload for SUBACK packet."""

    __slots__ = ("return_codes",)

    def __init__(self, return_codes: list[int] = None) -> None:
        super().__init__()
        self.return_codes = return_codes or []

    def __repr__(self) -> str:
        return f"SubackPayload(return_codes={self.return_codes})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, variable_header: SubackVariableHeader, fixed_header: MQTTFixedHeader) -> Self:
        """Decode payload from stream."""
        return_codes = []
        payload_length = fixed_header.remaining_length - variable_header.bytes_length
        for _ in range(payload_length):
            return_code = await read_or_raise(reader, 1)
            return_codes.append(bytes_to_int(return_code))
        return cls(return_codes)

    def to_bytes(self, fixed_header=None, variable_header=None) -> bytearray:
        """Encode payload to bytes.
        
        :param fixed_header: Optional fixed header (not used but required for compatibility)
        :param variable_header: Optional variable header (not used but required for compatibility)
        :return: Encoded payload bytes
        """
        out = bytearray()
        for return_code in self.return_codes:
            out.extend(int_to_bytes(return_code, 1))
        return out


class SubackPacket(MQTTPacket[SubackVariableHeader, SubackPayload, MQTTFixedHeader]):
    """SUBACK packet."""

    VARIABLE_HEADER = SubackVariableHeader
    PAYLOAD = SubackPayload

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: SubackVariableHeader = None,
        payload: SubackPayload = None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(SUBACK, 0x00)

        super().__init__(fixed, variable_header, payload)

    @property
    def return_codes(self) -> list[int]:
        """Return the list of return codes."""
        if self.payload is not None:
            return self.payload.return_codes
        return []

    @return_codes.setter
    def return_codes(self, return_codes: list[int]) -> None:
        """Set the list of return codes."""
        if self.payload is None:
            self.payload = SubackPayload()
        self.payload.return_codes = return_codes

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
            self.variable_header = SubackVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, packet_id: int, return_codes: list[int]) -> Self:
        """Build a SUBACK packet for MQTT 3.1.1."""
        variable_header = SubackVariableHeader(packet_id)
        payload = SubackPayload(return_codes)
        return cls(variable_header=variable_header, payload=payload)

    @classmethod
    def build_mqtt5(cls, packet_id: int, return_codes: list[int], properties: Properties = None) -> Self:
        """Build a SUBACK packet for MQTT5."""
        fixed_header = MQTTFixedHeader(SUBACK, 0x00)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        variable_header = SubackVariableHeader(packet_id)
        
        if properties:
            variable_header.properties = properties
            
        payload = SubackPayload(return_codes)
        
        return cls(fixed=fixed_header, variable_header=variable_header, payload=payload)
