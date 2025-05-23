"""MQTT5 Properties Implementation."""

from enum import IntEnum
from typing import Any, Dict, List, Optional, Self, Tuple, Union

from amqtt.adapters import ReaderAdapter
from amqtt.codecs_amqtt import (
    bytes_to_int,
    decode_binary_data,
    decode_data_with_length,
    decode_string,
    encode_binary_data,
    encode_data_with_length,
    encode_string,
    int_to_bytes,
    read_or_raise,
)
from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import (
    AUTHENTICATION_DATA,
    AUTHENTICATION_METHOD,
    ASSIGNED_CLIENT_IDENTIFIER,
    CONTENT_TYPE,
    CORRELATION_DATA,
    MAXIMUM_PACKET_SIZE,
    MAXIMUM_QOS,
    MESSAGE_EXPIRY_INTERVAL,
    PAYLOAD_FORMAT_INDICATOR,
    REASON_STRING,
    RECEIVE_MAXIMUM,
    REQUEST_PROBLEM_INFORMATION,
    REQUEST_RESPONSE_INFORMATION,
    RESPONSE_INFORMATION,
    RESPONSE_TOPIC,
    RETAIN_AVAILABLE,
    SERVER_KEEP_ALIVE,
    SERVER_REFERENCE,
    SESSION_EXPIRY_INTERVAL,
    SHARED_SUBSCRIPTION_AVAILABLE,
    SUBSCRIPTION_IDENTIFIER,
    SUBSCRIPTION_IDENTIFIER_AVAILABLE,
    TOPIC_ALIAS,
    TOPIC_ALIAS_MAXIMUM,
    USER_PROPERTY,
    WILDCARD_SUBSCRIPTION_AVAILABLE,
    WILL_DELAY_INTERVAL,
)


class PropertyType(IntEnum):
    """MQTT5 Property Types."""

    BYTE = 1
    TWO_BYTE_INTEGER = 2
    FOUR_BYTE_INTEGER = 3
    VARIABLE_BYTE_INTEGER = 4
    BINARY_DATA = 5
    UTF8_ENCODED_STRING = 6
    UTF8_STRING_PAIR = 7


# Property ID to Property Type mapping
PROPERTY_TYPES = {
    PAYLOAD_FORMAT_INDICATOR: PropertyType.BYTE,
    MESSAGE_EXPIRY_INTERVAL: PropertyType.FOUR_BYTE_INTEGER,
    CONTENT_TYPE: PropertyType.UTF8_ENCODED_STRING,
    RESPONSE_TOPIC: PropertyType.UTF8_ENCODED_STRING,
    CORRELATION_DATA: PropertyType.BINARY_DATA,
    SUBSCRIPTION_IDENTIFIER: PropertyType.VARIABLE_BYTE_INTEGER,
    SESSION_EXPIRY_INTERVAL: PropertyType.FOUR_BYTE_INTEGER,
    ASSIGNED_CLIENT_IDENTIFIER: PropertyType.UTF8_ENCODED_STRING,
    SERVER_KEEP_ALIVE: PropertyType.TWO_BYTE_INTEGER,
    AUTHENTICATION_METHOD: PropertyType.UTF8_ENCODED_STRING,
    AUTHENTICATION_DATA: PropertyType.BINARY_DATA,
    REQUEST_PROBLEM_INFORMATION: PropertyType.BYTE,
    WILL_DELAY_INTERVAL: PropertyType.FOUR_BYTE_INTEGER,
    REQUEST_RESPONSE_INFORMATION: PropertyType.BYTE,
    RESPONSE_INFORMATION: PropertyType.UTF8_ENCODED_STRING,
    SERVER_REFERENCE: PropertyType.UTF8_ENCODED_STRING,
    REASON_STRING: PropertyType.UTF8_ENCODED_STRING,
    RECEIVE_MAXIMUM: PropertyType.TWO_BYTE_INTEGER,
    TOPIC_ALIAS_MAXIMUM: PropertyType.TWO_BYTE_INTEGER,
    TOPIC_ALIAS: PropertyType.TWO_BYTE_INTEGER,
    MAXIMUM_QOS: PropertyType.BYTE,
    RETAIN_AVAILABLE: PropertyType.BYTE,
    USER_PROPERTY: PropertyType.UTF8_STRING_PAIR,
    MAXIMUM_PACKET_SIZE: PropertyType.FOUR_BYTE_INTEGER,
    WILDCARD_SUBSCRIPTION_AVAILABLE: PropertyType.BYTE,
    SUBSCRIPTION_IDENTIFIER_AVAILABLE: PropertyType.BYTE,
    SHARED_SUBSCRIPTION_AVAILABLE: PropertyType.BYTE,
}


class Properties:
    """MQTT5 Properties container."""

    def __init__(self) -> None:
        self._properties: Dict[int, Any] = {}
        self._user_properties: List[Tuple[str, str]] = []

    def __repr__(self) -> str:
        """Return a string representation of the Properties object."""
        return f"Properties(properties={self._properties}, user_properties={self._user_properties})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Properties):
            return False
        return (
            self._properties == other._properties
            and self._user_properties == other._user_properties
        )

    def __contains__(self, property_id: int) -> bool:
        return property_id in self._properties

    def __getitem__(self, property_id: int) -> Any:
        return self._properties.get(property_id)

    def __setitem__(self, property_id: int, value: Any) -> None:
        self._properties[property_id] = value

    def __delitem__(self, property_id: int) -> None:
        if property_id in self._properties:
            del self._properties[property_id]

    def get(self, property_id: int, default: Any = None) -> Any:
        """Get property value by ID."""
        return self._properties.get(property_id, default)

    def set(self, property_id: int, value: Any) -> None:
        """Set property value by ID."""
        if property_id not in PROPERTY_TYPES:
            raise AMQTTError(f"Invalid property ID: {property_id}")
        self._properties[property_id] = value

    def add_user_property(self, name: str, value: str) -> None:
        """Add a user property."""
        self._user_properties.append((name, value))

    def get_user_properties(self) -> List[Tuple[str, str]]:
        """Get all user properties."""
        return self._user_properties

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter) -> Self:
        """Decode properties from a stream."""
        properties = cls()
        property_length = await decode_data_with_length(reader)
        if property_length == 0:
            return properties

        # Read the property length bytes
        property_bytes = await read_or_raise(reader, property_length)
        property_reader = ReaderAdapter(property_bytes)

        while True:
            try:
                property_id_byte = await read_or_raise(property_reader, 1)
            except AMQTTError:
                # End of properties
                break

            property_id = bytes_to_int(property_id_byte)
            if property_id not in PROPERTY_TYPES:
                raise AMQTTError(f"Unknown property ID: {property_id}")

            property_type = PROPERTY_TYPES[property_id]

            if property_type == PropertyType.BYTE:
                value_bytes = await read_or_raise(property_reader, 1)
                value = bytes_to_int(value_bytes)
            elif property_type == PropertyType.TWO_BYTE_INTEGER:
                value_bytes = await read_or_raise(property_reader, 2)
                value = bytes_to_int(value_bytes)
            elif property_type == PropertyType.FOUR_BYTE_INTEGER:
                value_bytes = await read_or_raise(property_reader, 4)
                value = bytes_to_int(value_bytes)
            elif property_type == PropertyType.VARIABLE_BYTE_INTEGER:
                value = await decode_data_with_length(property_reader)
            elif property_type == PropertyType.BINARY_DATA:
                value = await decode_binary_data(property_reader)
            elif property_type == PropertyType.UTF8_ENCODED_STRING:
                value = await decode_string(property_reader)
            elif property_type == PropertyType.UTF8_STRING_PAIR:
                name = await decode_string(property_reader)
                value = await decode_string(property_reader)
                properties.add_user_property(name, value)
                continue
            else:
                raise AMQTTError(f"Unsupported property type: {property_type}")

            if property_id in properties._properties:
                # For properties that can appear multiple times, handle as a list
                if property_id == SUBSCRIPTION_IDENTIFIER:
                    if isinstance(properties._properties[property_id], list):
                        properties._properties[property_id].append(value)
                    else:
                        properties._properties[property_id] = [properties._properties[property_id], value]
                # For User Properties, they're already handled separately
                elif property_id == USER_PROPERTY:
                    pass
                else:
                    # For properties that should appear only once, this is a protocol error
                    raise AMQTTError(f"Duplicate property ID: {property_id}")
            else:
                properties._properties[property_id] = value

        return properties

    def to_bytes(self) -> bytearray:
        """Encode properties to bytes."""
        data = bytearray()

        # Encode each property
        for property_id, value in self._properties.items():
            property_type = PROPERTY_TYPES[property_id]

            # Handle subscription identifiers which can be a list
            if property_id == SUBSCRIPTION_IDENTIFIER and isinstance(value, list):
                for sub_id in value:
                    data.append(property_id)
                    data.extend(encode_data_with_length(sub_id))
                continue

            data.append(property_id)

            if property_type == PropertyType.BYTE:
                data.append(value)
            elif property_type == PropertyType.TWO_BYTE_INTEGER:
                data.extend(int_to_bytes(value, 2))
            elif property_type == PropertyType.FOUR_BYTE_INTEGER:
                data.extend(int_to_bytes(value, 4))
            elif property_type == PropertyType.VARIABLE_BYTE_INTEGER:
                data.extend(encode_data_with_length(value))
            elif property_type == PropertyType.BINARY_DATA:
                data.extend(encode_binary_data(value))
            elif property_type == PropertyType.UTF8_ENCODED_STRING:
                data.extend(encode_string(value))

        # Encode user properties
        for name, value in self._user_properties:
            data.append(USER_PROPERTY)
            data.extend(encode_string(name))
            data.extend(encode_string(value))

        # Encode the total length as a variable byte integer
        result = bytearray()
        result.extend(encode_data_with_length(len(data)))
        result.extend(data)

        return result
