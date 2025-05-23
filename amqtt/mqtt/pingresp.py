from typing import Self

from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import PINGRESP
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket


class PingRespPacket(MQTTPacket[None, None, MQTTFixedHeader]):
    """PINGRESP packet."""

    VARIABLE_HEADER = None
    PAYLOAD = None

    def __init__(self, fixed: MQTTFixedHeader = None) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(PINGRESP, 0x00)
        else:
            if fixed.packet_type is not PINGRESP:
                msg = f"Invalid fixed packet type {fixed.packet_type} for PingRespPacket init"
                raise AMQTTError(msg)

        super().__init__(fixed, None, None)

    @classmethod
    def build(cls) -> Self:
        """Build a PINGRESP packet."""
        return cls()

    @classmethod
    def build_mqtt5(cls) -> Self:
        """Build a PINGRESP packet for MQTT5.
        
        Note: PINGRESP packets are identical in MQTT 3.1.1 and MQTT5.
        """
        return cls.build()
