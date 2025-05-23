"""Helper module for MQTT5 specific functionality."""

from typing import Dict, List, Optional, Tuple, Union

from amqtt.mqtt.constants import (
    MQTT_5_0,
    PROPERTY_TYPE_BINARY_DATA,
    PROPERTY_TYPE_BYTE,
    PROPERTY_TYPE_FOUR_BYTE_INTEGER,
    PROPERTY_TYPE_TWO_BYTE_INTEGER,
    PROPERTY_TYPE_UTF8_ENCODED_STRING,
    PROPERTY_TYPE_UTF8_STRING_PAIR,
    PROPERTY_TYPE_VARIABLE_BYTE_INTEGER,
    PROPERTY_TYPES,
    USER_PROPERTY,
)
from amqtt.mqtt.properties import Properties


class MQTT5Helper:
    """Helper class for MQTT5 specific functionality."""

    @staticmethod
    def is_mqtt5_packet(flags: int) -> bool:
        """Check if a packet is an MQTT5 packet based on flags."""
        return bool(flags & 0x01)

    @staticmethod
    def create_user_property(name: str, value: str) -> Tuple[int, Tuple[str, str]]:
        """Create a user property tuple for MQTT5."""
        return (USER_PROPERTY, (name, value))

    @staticmethod
    def get_user_properties(properties: Properties) -> Dict[str, str]:
        """Extract user properties from Properties object."""
        user_properties = {}
        for prop_id, value in properties.properties:
            if prop_id == USER_PROPERTY and isinstance(value, tuple) and len(value) == 2:
                user_properties[value[0]] = value[1]
        return user_properties

    @staticmethod
    def add_user_properties(properties: Properties, user_props: Dict[str, str]) -> None:
        """Add user properties to a Properties object."""
        for name, value in user_props.items():
            properties.add_property(USER_PROPERTY, (name, value))

    @staticmethod
    def get_property_value(properties: Properties, property_id: int) -> Optional[Union[int, str, bytes, Tuple[str, str]]]:
        """Get a property value from Properties object by property ID."""
        for prop_id, value in properties.properties:
            if prop_id == property_id:
                return value
        return None

    @staticmethod
    def get_property_values(properties: Properties, property_id: int) -> List[Union[int, str, bytes, Tuple[str, str]]]:
        """Get all property values from Properties object by property ID."""
        values = []
        for prop_id, value in properties.properties:
            if prop_id == property_id:
                values.append(value)
        return values

    @staticmethod
    def get_property_type(property_id: int) -> int:
        """Get the type of a property by its ID."""
        return PROPERTY_TYPES.get(property_id, 0)

    @staticmethod
    def is_valid_property_type(property_id: int, value: Union[int, str, bytes, Tuple[str, str]]) -> bool:
        """Check if a property value matches its expected type."""
        prop_type = MQTT5Helper.get_property_type(property_id)
        
        if prop_type == PROPERTY_TYPE_BYTE:
            return isinstance(value, int) and 0 <= value <= 255
        elif prop_type == PROPERTY_TYPE_TWO_BYTE_INTEGER:
            return isinstance(value, int) and 0 <= value <= 65535
        elif prop_type == PROPERTY_TYPE_FOUR_BYTE_INTEGER:
            return isinstance(value, int) and 0 <= value <= 4294967295
        elif prop_type == PROPERTY_TYPE_VARIABLE_BYTE_INTEGER:
            return isinstance(value, int) and value >= 0
        elif prop_type == PROPERTY_TYPE_BINARY_DATA:
            return isinstance(value, bytes)
        elif prop_type == PROPERTY_TYPE_UTF8_ENCODED_STRING:
            return isinstance(value, str)
        elif prop_type == PROPERTY_TYPE_UTF8_STRING_PAIR:
            return (isinstance(value, tuple) and len(value) == 2 and 
                    isinstance(value[0], str) and isinstance(value[1], str))
        return False
