from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import DISCONNECT, NORMAL_DISCONNECTION
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties


class DisconnectVariableHeader(MQTTVariableHeader):
    """Variable header for DISCONNECT packet."""

    __slots__ = ("reason_code", "properties")

    def __init__(self, reason_code: int = NORMAL_DISCONNECTION) -> None:
        super().__init__()
        self.reason_code = reason_code
        self.properties = Properties()

    def __repr__(self) -> str:
        return f"DisconnectVariableHeader(reason_code={self.reason_code}, properties={self.properties})"

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode variable header from stream."""
        # For MQTT 3.1.1, there is no variable header
        if fixed_header.remaining_length == 0:
            return cls()
            
        # For MQTT5, read reason code
        reason_code_bytes = await read_or_raise(reader, 1)
        reason_code = bytes_to_int(reason_code_bytes)
        var_header = cls(reason_code)
        
        # Read properties if there are more bytes
        if fixed_header.remaining_length > 1:
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode variable header to bytes."""
        # For MQTT 3.1.1, return empty bytearray
        if not hasattr(self, 'mqtt5') or not self.mqtt5:
            return bytearray()
            
        # For MQTT5, include reason code and properties
        out = bytearray(1)  # reason code
        out[0] = self.reason_code
        
        # Add properties
        out.extend(self.properties.to_bytes())
        return out


class DisconnectPacket(MQTTPacket[DisconnectVariableHeader, None, MQTTFixedHeader]):
    """DISCONNECT packet."""

    VARIABLE_HEADER = DisconnectVariableHeader
    PAYLOAD = None

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: DisconnectVariableHeader = None,
        payload=None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(DISCONNECT, 0x00)

        super().__init__(fixed, variable_header, payload)

    @property
    def reason_code(self) -> int:
        """Return the reason code."""
        if self.variable_header is not None:
            return self.variable_header.reason_code
        return NORMAL_DISCONNECTION

    @reason_code.setter
    def reason_code(self, reason_code: int) -> None:
        """Set the reason code."""
        if self.variable_header is None:
            self.variable_header = DisconnectVariableHeader()
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
            self.variable_header = DisconnectVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls) -> Self:
        """Build a DISCONNECT packet for MQTT 3.1.1."""
        return cls()

    @classmethod
    def build_mqtt5(cls, reason_code: int = NORMAL_DISCONNECTION, properties: Properties = None) -> Self:
        """Build a DISCONNECT packet for MQTT5."""
        fixed_header = MQTTFixedHeader(DISCONNECT, 0x00)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        variable_header = DisconnectVariableHeader(reason_code)
        
        if properties:
            variable_header.properties = properties
            
        return cls(fixed=fixed_header, variable_header=variable_header)
