from asyncio import StreamReader
from typing import Self

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import (
    bytes_to_int,
    decode_data_with_length,
    decode_string,
    encode_data_with_length,
    encode_string,
    int_to_bytes,
    read_or_raise,
)
from amqtt.errors import AMQTTError, NoDataError
from amqtt.mqtt.constants import MQTT_3_1, MQTT_3_1_1, MQTT_5_0
from amqtt.mqtt.packet import CONNECT, MQTTFixedHeader, MQTTPacket, MQTTPayload, MQTTVariableHeader
from amqtt.mqtt.properties import Properties
from amqtt.utils import gen_client_id


class ConnectVariableHeader(MQTTVariableHeader):
    __slots__ = ("flags", "keep_alive", "proto_level", "proto_name", "properties")

    USERNAME_FLAG = 0x80
    PASSWORD_FLAG = 0x40
    WILL_RETAIN_FLAG = 0x20
    WILL_FLAG = 0x04
    WILL_QOS_MASK = 0x18
    CLEAN_SESSION_FLAG = 0x02
    RESERVED_FLAG = 0x01

    def __init__(self, connect_flags: int = 0x00, keep_alive: int = 0, proto_name: str = "MQTT", proto_level: int = MQTT_3_1_1) -> None:
        super().__init__()
        self.proto_name = proto_name
        self.proto_level = proto_level
        self.flags = connect_flags
        self.keep_alive = keep_alive
        self.properties = Properties()

    def __repr__(self) -> str:
        """Return a string representation of the ConnectVariableHeader object."""
        return (
            f"ConnectVariableHeader(proto_name={self.proto_name}, proto_level={self.proto_level},"
            f" flags={hex(self.flags)}, keepalive={self.keep_alive}, properties={self.properties})"
        )

    def _set_flag(self, val: bool, mask: int) -> None:
        if val:
            self.flags |= mask
        else:
            self.flags &= ~mask

    def _get_flag(self, mask: int) -> bool:
        return bool(self.flags & mask)

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, _: MQTTFixedHeader) -> Self:
        #  protocol name
        protocol_name = await decode_string(reader)

        # protocol level
        protocol_level_byte = await read_or_raise(reader, 1)
        protocol_level = bytes_to_int(protocol_level_byte)

        # flags
        flags_byte = await read_or_raise(reader, 1)
        flags = bytes_to_int(flags_byte)

        # keep-alive
        keep_alive_byte = await read_or_raise(reader, 2)
        keep_alive = bytes_to_int(keep_alive_byte)

        header = cls(flags, keep_alive, protocol_name, protocol_level)
        
        # Read properties for MQTT5
        if protocol_level == MQTT_5_0:
            header.properties = await Properties.from_stream(reader)

        return header

    def to_bytes(self) -> bytearray:
        out = bytearray()

        # Protocol name
        out.extend(encode_string(self.proto_name))
        # Protocol level
        out.append(self.proto_level)
        # flags
        out.append(self.flags)
        # keep alive
        out.extend(int_to_bytes(self.keep_alive, 2))
        
        # Add properties for MQTT5
        if self.proto_level == MQTT_5_0:
            out.extend(self.properties.to_bytes())

        return out

    @property
    def username_flag(self) -> bool:
        return self._get_flag(self.USERNAME_FLAG)

    @username_flag.setter
    def username_flag(self, val: bool) -> None:
        self._set_flag(val, self.USERNAME_FLAG)

    @property
    def password_flag(self) -> bool:
        return self._get_flag(self.PASSWORD_FLAG)

    @password_flag.setter
    def password_flag(self, val: bool) -> None:
        self._set_flag(val, self.PASSWORD_FLAG)

    @property
    def will_retain_flag(self) -> bool:
        return self._get_flag(self.WILL_RETAIN_FLAG)

    @will_retain_flag.setter
    def will_retain_flag(self, val: bool) -> None:
        self._set_flag(val, self.WILL_RETAIN_FLAG)

    @property
    def will_flag(self) -> bool:
        return self._get_flag(self.WILL_FLAG)

    @will_flag.setter
    def will_flag(self, val: bool) -> None:
        self._set_flag(val, self.WILL_FLAG)

    @property
    def clean_session_flag(self) -> bool:
        return self._get_flag(self.CLEAN_SESSION_FLAG)

    @clean_session_flag.setter
    def clean_session_flag(self, val: bool) -> None:
        self._set_flag(val, self.CLEAN_SESSION_FLAG)

    @property
    def reserved_flag(self) -> bool:
        return self._get_flag(self.RESERVED_FLAG)

    @reserved_flag.setter
    def reserved_flag(self, val: bool) -> None:
        self._set_flag(val, self.RESERVED_FLAG)

    @property
    def will_qos(self) -> int:
        return (self.flags & 0x18) >> 3

    @will_qos.setter
    def will_qos(self, val: int) -> None:
        self.flags &= 0xE7  # Reset QOS flags
        self.flags |= val << 3


class ConnectPayload(MQTTPayload[ConnectVariableHeader]):
    __slots__ = (
        "client_id",
        "client_id_is_random",
        "password",
        "username",
        "will_message",
        "will_topic",
        "will_properties",
    )

    def __init__(
        self,
        client_id: str | None = None,
        will_topic: str | None = None,
        will_message: bytes | bytearray | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__()
        self.client_id_is_random = False
        self.client_id = client_id
        self.will_topic = will_topic
        self.will_message = will_message
        self.username = username
        self.password = password
        self.will_properties = Properties()

    def __repr__(self) -> str:
        """Return a string representation of the ConnectPayload object."""
        return (
            f"ConnectPayload(client_id={self.client_id}, will_topic={self.will_topic}, "
            f"will_message={self.will_message}, username={self.username}, password={self.password}, "
            f"will_properties={self.will_properties})"
        )

    @classmethod
    async def from_stream(
        cls,
        reader: StreamReader | ReaderAdapter,
        _: MQTTFixedHeader | None,
        variable_header: ConnectVariableHeader | None,
    ) -> Self:
        payload = cls()
        if variable_header is None:
            msg = "Variable header is not initialized"
            raise AMQTTError(msg)

        # Read client_id
        try:
            payload.client_id = await decode_string(reader)
            if payload.client_id == "":
                if variable_header.proto_level == MQTT_5_0 or variable_header.clean_session_flag:
                    payload.client_id = gen_client_id()
                    payload.client_id_is_random = True
                else:
                    # Empty client id with persistent session not allowed in MQTT 3.1.1
                    msg = "Empty client id not allowed with persistent session"
                    raise AMQTTError(msg)
        except NoDataError as exc:
            msg = "Connection closed by peer when reading client ID"
            raise AMQTTError(msg) from exc

        # Read will topic, message, and properties for MQTT5
        if variable_header.will_flag:
            if variable_header.proto_level == MQTT_5_0:
                payload.will_properties = await Properties.from_stream(reader)
            try:
                payload.will_topic = await decode_string(reader)
                payload.will_message = await decode_data_with_length(reader)
            except NoDataError as exc:
                msg = "Connection closed by peer when reading will topic/message"
                raise AMQTTError(msg) from exc

        # Read username
        if variable_header.username_flag:
            try:
                payload.username = await decode_string(reader)
            except NoDataError as exc:
                msg = "Connection closed by peer when reading username"
                raise AMQTTError(msg) from exc

        # Read password
        if variable_header.password_flag:
            try:
                payload.password = await decode_string(reader)
            except NoDataError as exc:
                msg = "Connection closed by peer when reading password"
                raise AMQTTError(msg) from exc

        return payload

    def to_bytes(
        self,
        fixed_header: MQTTFixedHeader | None = None,
        variable_header: ConnectVariableHeader | None = None,
    ) -> bytearray:
        if variable_header is None:
            msg = "Variable header is not initialized"
            raise AMQTTError(msg)

        out = bytearray()
        # Client ID
        client_id = self.client_id or ""
        out.extend(encode_string(client_id))

        # Will topic, message, and properties for MQTT5
        if variable_header.will_flag:
            if variable_header.proto_level == MQTT_5_0:
                out.extend(self.will_properties.to_bytes())
            if self.will_topic:
                out.extend(encode_string(self.will_topic))
            if self.will_message:
                out.extend(encode_data_with_length(self.will_message))

        # Username
        if variable_header.username_flag and self.username:
            out.extend(encode_string(self.username))

        # Password
        if variable_header.password_flag and self.password:
            out.extend(encode_string(self.password))

        return out


class ConnectPacket(MQTTPacket[ConnectVariableHeader, ConnectPayload, MQTTFixedHeader]):  # type: ignore [type-var]
    VARIABLE_HEADER = ConnectVariableHeader
    PAYLOAD = ConnectPayload

    def __init__(
        self,
        fixed: MQTTFixedHeader | None = None,
        variable_header: ConnectVariableHeader | None = None,
        payload: ConnectPayload | None = None,
    ) -> None:
        if fixed is None:
            header = MQTTFixedHeader(CONNECT, 0x00)
        else:
            if fixed.packet_type is not CONNECT:
                msg = f"Invalid fixed packet type {fixed.packet_type} for ConnectPacket init"
                raise AMQTTError(msg)
            header = fixed
        super().__init__(header)
        self.variable_header = variable_header
        self.payload = payload

    @property
    def proto_name(self) -> str:
        if self.variable_header is not None:
            return self.variable_header.proto_name
        return ""

    @proto_name.setter
    def proto_name(self, name: str) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.proto_name = name

    @property
    def proto_level(self) -> int:
        if self.variable_header is not None:
            return self.variable_header.proto_level
        return 0

    @proto_level.setter
    def proto_level(self, level: int) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.proto_level = level

    @property
    def username_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header.username_flag
        return False

    @username_flag.setter
    def username_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.username_flag = flag

    @property
    def password_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header.password_flag
        return False

    @password_flag.setter
    def password_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.password_flag = flag

    @property
    def clean_session_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header._get_flag(self.variable_header.CLEAN_SESSION_FLAG)
        return False

    @clean_session_flag.setter
    def clean_session_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header._set_flag(flag, self.variable_header.CLEAN_SESSION_FLAG)

    @property
    def will_retain_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header._get_flag(self.variable_header.WILL_RETAIN_FLAG)
        return False

    @will_retain_flag.setter
    def will_retain_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header._set_flag(flag, self.variable_header.WILL_RETAIN_FLAG)

    @property
    def will_qos(self) -> int:
        if self.variable_header is not None:
            return (self.variable_header.flags & self.variable_header.WILL_QOS_MASK) >> 3
        return 0

    @will_qos.setter
    def will_qos(self, flag: int) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.flags &= ~self.variable_header.WILL_QOS_MASK
        self.variable_header.flags |= (flag << 3) & self.variable_header.WILL_QOS_MASK

    @property
    def will_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header._get_flag(self.variable_header.WILL_FLAG)
        return False

    @will_flag.setter
    def will_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header._set_flag(flag, self.variable_header.WILL_FLAG)

    @property
    def reserved_flag(self) -> bool:
        if self.variable_header is not None:
            return self.variable_header._get_flag(self.variable_header.RESERVED_FLAG)
        return False

    @reserved_flag.setter
    def reserved_flag(self, flag: bool) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header._set_flag(flag, self.variable_header.RESERVED_FLAG)

    @property
    def client_id(self) -> str:
        if self.payload is not None and self.payload.client_id is not None:
            return self.payload.client_id
        return ""

    @client_id.setter
    def client_id(self, client_id: str) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.client_id = client_id

    @property
    def client_id_is_random(self) -> bool:
        if self.payload is not None:
            return self.payload.client_id_is_random
        return False

    @client_id_is_random.setter
    def client_id_is_random(self, client_id_is_random: bool) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.client_id_is_random = client_id_is_random

    @property
    def will_topic(self) -> str:
        if self.payload is not None and self.payload.will_topic is not None:
            return self.payload.will_topic
        return ""

    @will_topic.setter
    def will_topic(self, will_topic: str) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.will_topic = will_topic
        self.will_flag = True

    @property
    def will_message(self) -> bytes | bytearray | None:
        if self.payload is not None:
            return self.payload.will_message
        return None

    @will_message.setter
    def will_message(self, will_message: bytes | bytearray) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.will_message = will_message
        self.will_flag = True

    @property
    def will_properties(self) -> Properties:
        if self.payload is not None:
            return self.payload.will_properties
        return Properties()

    @will_properties.setter
    def will_properties(self, properties: Properties) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.will_properties = properties

    @property
    def username(self) -> str:
        if self.payload is not None and self.payload.username is not None:
            return self.payload.username
        return ""

    @username.setter
    def username(self, username: str) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.username = username
        self.username_flag = True

    @property
    def password(self) -> str:
        if self.payload is not None and self.payload.password is not None:
            return self.payload.password
        return ""

    @password.setter
    def password(self, password: str) -> None:
        if self.payload is None:
            self.payload = ConnectPayload()
        self.payload.password = password
        self.password_flag = True

    @property
    def keep_alive(self) -> int:
        if self.variable_header is not None:
            return self.variable_header.keep_alive
        return 0

    @keep_alive.setter
    def keep_alive(self, keep_alive: int) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.keep_alive = keep_alive

    @property
    def properties(self) -> Properties:
        if self.variable_header is not None:
            return self.variable_header.properties
        return Properties()

    @properties.setter
    def properties(self, properties: Properties) -> None:
        if self.variable_header is None:
            self.variable_header = ConnectVariableHeader()
        self.variable_header.properties = properties

    @classmethod
    def build(cls, client_id: str | None = None, clean_session: bool = True, keep_alive: int = 0) -> Self:
        """Build a CONNECT packet."""
        if client_id is None:
            client_id = gen_client_id()

        variable_header = ConnectVariableHeader()
        variable_header.proto_level = MQTT_3_1_1  # Default to 3.1.1
        if clean_session:
            variable_header._set_flag(True, variable_header.CLEAN_SESSION_FLAG)

        payload = ConnectPayload()
        payload.client_id = client_id

        packet = cls(variable_header=variable_header, payload=payload)
        packet.keep_alive = keep_alive

        return packet

    @classmethod
    def build_mqtt5(cls, client_id: str | None = None, clean_session: bool = True, keep_alive: int = 0) -> Self:
        """Build an MQTT5 CONNECT packet."""
        if client_id is None:
            client_id = gen_client_id()

        variable_header = ConnectVariableHeader()
        variable_header.proto_level = MQTT_5_0  # Set to MQTT5
        if clean_session:
            variable_header._set_flag(True, variable_header.CLEAN_SESSION_FLAG)

        payload = ConnectPayload()
        payload.client_id = client_id

        packet = cls(variable_header=variable_header, payload=payload)
        packet.keep_alive = keep_alive

        return packet
