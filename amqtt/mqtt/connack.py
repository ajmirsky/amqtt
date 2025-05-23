from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import bytes_to_int, read_or_raise
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import MQTT_5_0
from amqtt.mqtt.packet import CONNACK, MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties

CONNECTION_ACCEPTED = 0x00
UNACCEPTABLE_PROTOCOL_VERSION = 0x01
IDENTIFIER_REJECTED = 0x02
SERVER_UNAVAILABLE = 0x03
BAD_USERNAME_PASSWORD = 0x04
NOT_AUTHORIZED = 0x05


class ConnackVariableHeader(MQTTVariableHeader):
    __slots__ = ("session_parent", "return_code", "properties")

    def __init__(self, session_parent: int = None, return_code: int = None) -> None:
        super().__init__()
        self.session_parent = session_parent
        self.return_code = return_code
        self.properties = Properties()

    def __repr__(self) -> str:
        """Return a string representation of the ConnackVariableHeader object."""
        return (
            f"ConnackVariableHeader(session_parent={self.session_parent}, "
            f"return_code={self.return_code}, properties={self.properties})"
        )

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> Self:
        """Decode the CONNACK variable header from a stream."""
        data = await read_or_raise(reader, 2)
        session_parent = bytes_to_int(data[0:1])
        return_code = bytes_to_int(data[1:2])
        var_header = cls(session_parent, return_code)
        
        # Read properties for MQTT5 packets
        if fixed_header.flags & 0x01 == 0x01:  # MQTT5 packet flag
            var_header.properties = await Properties.from_stream(reader)
            
        return var_header

    def to_bytes(self) -> bytearray:
        """Encode the CONNACK variable header to bytes."""
        out = bytearray(2)
        # Session present
        if self.session_parent:
            out[0] = 0x01
        else:
            out[0] = 0x00

        # Return code
        out[1] = self.return_code
        
        # Add properties for MQTT5
        if hasattr(self, 'mqtt5') and self.mqtt5:
            out.extend(self.properties.to_bytes())
            
        return out


class ConnackPacket(MQTTPacket[ConnackVariableHeader, None, MQTTFixedHeader]):
    VARIABLE_HEADER = ConnackVariableHeader
    PAYLOAD = None

    def __init__(
        self,
        fixed: MQTTFixedHeader = None,
        variable_header: ConnackVariableHeader = None,
        payload=None,
    ) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(CONNACK, 0x00)

        super().__init__(fixed, variable_header, payload)

    @property
    def return_code(self) -> int:
        if self.variable_header is not None:
            return self.variable_header.return_code
        return 0

    @return_code.setter
    def return_code(self, return_code: int) -> None:
        if self.variable_header is None:
            self.variable_header = ConnackVariableHeader()
        self.variable_header.return_code = return_code

    @property
    def session_parent(self) -> int:
        if self.variable_header is not None:
            return self.variable_header.session_parent
        return 0

    @session_parent.setter
    def session_parent(self, session_parent: int) -> None:
        if self.variable_header is None:
            self.variable_header = ConnackVariableHeader()
        self.variable_header.session_parent = session_parent
        
    @property
    def properties(self) -> Properties:
        if self.variable_header is not None:
            return self.variable_header.properties
        return Properties()

    @properties.setter
    def properties(self, properties: Properties) -> None:
        if self.variable_header is None:
            self.variable_header = ConnackVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, session_parent: int = 0, return_code: int = 0) -> Self:
        """Build a CONNACK packet."""
        variable_header = ConnackVariableHeader(session_parent, return_code)
        return cls(variable_header=variable_header)
        
    @classmethod
    def build_mqtt5(cls, session_parent: int = 0, return_code: int = 0, properties: Properties = None) -> Self:
        """Build an MQTT5 CONNACK packet."""
        fixed_header = MQTTFixedHeader(CONNACK, 0x00)
        fixed_header.mqtt5 = True  # Mark as MQTT5 packet
        
        variable_header = ConnackVariableHeader(session_parent, return_code)
        
        if properties:
            variable_header.properties = properties
            
        return cls(fixed=fixed_header, variable_header=variable_header)
