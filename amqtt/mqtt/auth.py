"""MQTT5 AUTH packet implementation."""

from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import AUTH, SUCCESS
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class AuthVariableHeader(MQTTVariableHeader):
    """Variable header for AUTH packet."""

    __slots__ = ("reason_code", "properties")

    def __init__(self, reason_code: int = SUCCESS) -> None:
        super().__init__()
        self.reason_code = reason_code
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"AuthVariableHeader(reason_code={self.reason_code}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        # For empty AUTH packet (no reason code or properties)
        if fixed_header.remaining_length == 0:
            return cls()
            
        # Read reason code
        reason_code_bytes = await read_or_raise(reader, 1)
        reason_code = bytes_to_int(reason_code_bytes)
        var_header = cls(reason_code)
        
        # Read properties if there are more bytes
        if fixed_header.remaining_length > 1:
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode variable header to bytes."""
        # If reason code is SUCCESS (0) and no properties, return empty bytearray
        if self.reason_code == SUCCESS and not self.properties.properties:
            return bytearray()
            
        out = bytearray(1)  # reason code
        out[0] = self.reason_code
        
        # Add properties
        out.extend(self.properties.to_bytes())
        return out


class AuthPacket(MQTTPacket[AuthVariableHeader, None, MQTTFixedHeader]):
    """AUTH packet for MQTT5."""

    VARIABLE_HEADER = AuthVariableHeader
    PAYLOAD = None

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: AuthVariableHeader = None,
        payload=None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(AUTH, 0x00)

        super().__init__(fixed, variable_header, payload)

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
            self.variable_header = AuthVariableHeader()
        self.variable_header.reason_code = reason_code

    @property
    def properties(self) -> Properties:
        """Return the properties."""
        if self.variable_header is not None:
            return self.variable_header.properties
        return Properties()

    @properties.setter
    def properties(self, properties: Properties) -> None:
        """Set the properties."""
        if self.variable_header is None:
            self.variable_header = AuthVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, reason_code: int = SUCCESS, properties: Properties = None) -> Self:
        """Build an AUTH packet."""
        variable_header = AuthVariableHeader(reason_code)
        
        if properties:
            variable_header.properties = properties
            
        return cls(variable_header=variable_header)
