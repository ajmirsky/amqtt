from typing import Self

from amqtt.errors import AMQTTError
from amqtt.mqtt.constants import PINGREQ
from amqtt.mqtt.packet import MQTTFixedHeader, MQTTPacket


class PingReqPacket(MQTTPacket[None, None, MQTTFixedHeader]):
    """PINGREQ packet."""

    VARIABLE_HEADER = None
    PAYLOAD = None

    def __init__(self, fixed: MQTTFixedHeader = None) -> None:
        if fixed is None:
            fixed = MQTTFixedHeader(PINGREQ, 0x00)
        else:
            if fixed.packet_type is not PINGREQ:
                msg = f"Invalid fixed packet type {fixed.packet_type} for PingReqPacket init"
                raise AMQTTError(msg)

        super().__init__(fixed, None, None)

    @classmethod
    def build(cls) -> Self:
        """Build a PINGREQ packet."""
        return cls()

    @classmethod
    def build_mqtt5(cls) -> Self:
        """Build a PINGREQ packet for MQTT5.
        
        Note: PINGREQ packets are identical in MQTT 3.1.1 and MQTT5.
        """
        return cls.build()
