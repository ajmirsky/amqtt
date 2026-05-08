# CONVENTIONS.md — amqtt Coding Conventions

## Language & Runtime

- **Python 3.10+** minimum. Use modern syntax: `match/case`, `X | Y` unions, `TypeAlias`.
- **asyncio-native**: every I/O operation must be a coroutine. Never call `time.sleep()`, blocking socket ops, or any synchronous I/O inside an `async def`.
- **No new dependencies** without a PR discussion. The goal is a lean install.

---

## Type Annotations

All new code must be fully annotated. Existing code being touched should be annotated opportunistically.

```python
# Good
async def handle_publish(self, packet: PublishPacket) -> None: ...

# Bad — missing return type and param type
async def handle_publish(self, packet):
    pass
```

Use `from __future__ import annotations` at the top of every new file to enable forward references cheaply.

Prefer `TypeAlias` for complex types:
```python
PropertyMap: TypeAlias = dict[int, int | str | bytes | list[tuple[str, str]]]
```

Use `TYPE_CHECKING` guards for imports only needed at type-check time:
```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from amqtt.broker import BrokerContext
```

---

## Naming

| Thing | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `mqtt/properties.py` |
| Classes | `PascalCase` | `ConnectProperties` |
| Functions / methods | `snake_case` | `encode_variable_byte_int` |
| Constants | `UPPER_SNAKE` | `SESSION_EXPIRY_INTERVAL = 0x11` |
| Private helpers | leading `_` | `_read_property` |
| Type aliases | `PascalCase` | `ReasonCode` |

Packet classes must follow the pattern `{PacketName}Packet`, e.g. `AuthPacket`, `DisconnectV5Packet`.

---

## Packet Module Layout

MQTT 3.1.1 packet modules live under `amqtt/mqtt3/`. MQTT 5.0 packet modules live under `amqtt/mqtt5/`. New v5 modules must follow this template:

```python
"""MQTT AUTH packet (MQTT 5.0 §3.15)."""
from __future__ import annotations

from amqtt.mqtt3.packet import MQTTPacket, MQTTFixedHeader, PacketIdVariableHeader
from amqtt.mqtt5.properties import Properties
from amqtt.mqtt5.reason_codes import ReasonCode
from amqtt.adapters import ReaderAdapter

AUTH_PACKET = 0x0F


class AuthVariableHeader:
    def __init__(self, reason_code: ReasonCode, properties: Properties) -> None:
        self.reason_code = reason_code
        self.properties = properties

    def to_bytes(self) -> bytes: ...

    @classmethod
    async def from_stream(cls, reader: ReaderAdapter, fixed_header: MQTTFixedHeader) -> AuthVariableHeader: ...


class AuthPacket(MQTTPacket):
    VARIABLE_HEADER = AuthVariableHeader
    PAYLOAD = None

    @classmethod
    def build(cls, reason_code: ReasonCode, properties: Properties | None = None) -> AuthPacket: ...

    @classmethod
    async def from_stream(cls, fixed_header: MQTTFixedHeader, reader: ReaderAdapter) -> AuthPacket: ...
```

Key rules:
- `build()` is a classmethod factory for **outgoing** packets.
- `from_stream()` is a classmethod for **incoming** packets parsed off the wire.
- Wire format methods must be deterministic and round-trip clean (`encode(decode(x)) == x`).

---

## Properties Encoding (MQTT 5.0)

All MQTT 5.0 properties are encoded/decoded via `amqtt/mqtt5/properties.py`. Never hand-roll property bytes inline in packet modules.

Property IDs are defined as constants in `amqtt/mqtt5/property_ids.py`:
```python
PAYLOAD_FORMAT_INDICATOR     = 0x01
MESSAGE_EXPIRY_INTERVAL      = 0x02
CONTENT_TYPE                 = 0x03
RESPONSE_TOPIC               = 0x08
# ... etc
```

The `Properties` class handles the variable-byte-integer length prefix and the full encode/decode cycle. Packet modules just call:
```python
props = Properties()
props.set(CONTENT_TYPE, "application/json")
wire_bytes = props.encode()
```

---

## Spec Cross-References

Every non-obvious implementation decision must cite the relevant spec section in a comment. Use the MQTT 5.0 section number format:

```python
# [MQTT-3.1.2.11.2] Session Expiry Interval: if 0xFFFFFFFF, session never expires
if session_expiry_interval == 0xFFFF_FFFF:
    session.never_expire = True
```

The bracket prefix `[MQTT-X.Y.Z]` matches the normative statement numbering used throughout the spec. This makes auditing conformance tractable.

---

## Error Handling

Use the existing exception hierarchy:
- `MQTTError` — protocol-level errors (malformed packets, violations)
- `AMQTTError` — library/application-level errors
- `NoDataError` — connection closed unexpectedly

For MQTT 5.0: when a protocol violation is detected, send a DISCONNECT with the appropriate reason code *before* closing, unless the error occurred during CONNECT (in which case send CONNACK with error code and close).

```python
# Good — reason code + disconnect before close
await handler.send_disconnect(ReasonCode.PROTOCOL_ERROR, reason_string="Duplicate property")
raise MQTTError("Duplicate property received")

# Bad — silent close
raise MQTTError("Duplicate property received")
```

---

## Version Negotiation

The protocol version is determined from byte 9 of the CONNECT packet (the Protocol Level byte):

| Value | Version |
|---|---|
| `0x04` | MQTT 3.1.1 |
| `0x05` | MQTT 5.0 |

The broker and protocol handler must branch on this value early in connection setup. The canonical place is `BrokerProtocolHandler.mqtt_connect()`. Store the negotiated version on the `Session` object as `session.mqtt_version: int`.

Never assume a fixed version anywhere in shared code paths. Use:
```python
if session.mqtt_version == 5:
    # v5-specific logic
```

---

## Tests

- Every new packet type needs a test that:
  1. Builds a packet, encodes it to bytes, decodes it back, and asserts round-trip equality.
  2. Tests at least one malformed-packet case (wrong remaining length, duplicate property, etc.).
- Broker behavior tests go in `tests/test_broker.py`.
- Client behavior tests go in `tests/test_client.py`.
- Use `pytest-asyncio` for async test functions. Mark with `@pytest.mark.asyncio`.
- Use the existing `mqtt_server` / `client_connect` fixtures for integration tests.

Test naming: `test_{what}_{condition}`, e.g. `test_connect_v5_session_expiry_zero`, `test_publish_v5_topic_alias_invalid`.

---

## Logging

Use the module-level logger, never `print()`:
```python
import logging
logger = logging.getLogger(__name__)
```

Log levels:
- `DEBUG`: packet-level detail, useful during development.
- `INFO`: connection lifecycle events (client connected/disconnected).
- `WARNING`: recoverable protocol violations or unexpected conditions.
- `ERROR`: unrecoverable errors; connection will be closed.

---

## Git Commits

Format: `[scope] short description` — keep under 72 chars.

Scopes: `broker`, `client`, `packet`, `props`, `session`, `auth`, `test`, `docs`, `deps`, `ci`.

Examples:
```
[packet] add AUTH packet encoding/decoding (MQTT 5.0 §3.15)
[broker] negotiate MQTT version on CONNECT
[props] implement Variable Byte Integer encode/decode
[client] expose User Properties in publish() API
```

Reference issues in commit bodies:
```
Closes #42
See #38
```

---

## Backwards Compatibility

- Never remove or rename a public symbol without a deprecation cycle.
- Never change the default behaviour of `Broker` or `MQTTClient` in a way that breaks MQTT 3.1.1 operation.
- New v5-only parameters must have sensible defaults that are `None` or omitted, so callers that don't supply them get v3-equivalent behaviour.
- Plugin API: new plugin events for v5 features must be **additive**. Existing plugins that don't handle them must continue to work.
