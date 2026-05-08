# AGENTS.md — amqtt MQTT 5.0 Implementation

## Purpose

This file gives coding agents the project context and operating rules needed to work on **amqtt**, with a focus on the active MQTT 5.0 implementation effort.

**amqtt** is an asyncio-native Python MQTT broker and client. It currently implements MQTT 3.1.1. The active goal is to add MQTT 5.0 support for both broker and client while preserving full backwards compatibility with MQTT 3.1.1.

- Repo: https://github.com/Yakifo/amqtt
- MQTT 5.0 spec: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html
- Python target: 3.10–3.13
- Style: asyncio-native, type-annotated, plugin-extensible

## How Agents Should Work

Before making changes:

1. Read this file.
2. Read `CONVENTIONS.md` for the full coding style guide.
3. Read `ISSUES.md` for the MQTT 5.0 issue breakdown and acceptance criteria.
4. Identify the issue or phase being worked on.
5. Preserve MQTT 3.1.1 behavior unless the issue explicitly requires changing it.

When implementing work:

- Prefer small, reviewable changes tied to a single issue.
- Keep public API changes additive.
- Add tests with every feature or behavior change.
- Use spec section comments for non-obvious MQTT 5.0 behavior.
- Do not introduce new dependencies without discussion.
- Do not silently skip acceptance criteria.

When finishing work:

- Run the narrowest relevant test command first.
- Run broader tests before claiming completion.
- Report what changed, what was tested, and what remains incomplete.

## Project Overview

amqtt is organized around separate MQTT protocol implementations with shared broker, client, transport, session, and plugin infrastructure.

```text
amqtt/
  broker.py                        # Broker class — listeners, sessions, routing
  client.py                        # MQTTClient class — public client API
  session.py                       # Session / ApplicationMessage state
  adapters.py                      # ReaderAdapter / WriterAdapter for TCP + WebSocket
  codecs.py                        # Low-level byte encoding/decoding helpers
  events.py                        # BrokerEvents enum
  mqtt/                            # Deprecated shim: amqtt.mqtt.* → amqtt.mqtt3.*
    __init__.py
  mqtt3/                           # MQTT 3.1.1 implementation
    constants.py
    packet.py                      # Base MQTTPacket
    connect.py / connack.py
    publish.py
    puback.py / pubrec.py / pubrel.py / pubcomp.py
    subscribe.py / suback.py
    unsubscribe.py / unsuback.py
    pingreq.py / pingresp.py
    disconnect.py
    protocol/
      handler.py
      client_handler.py
      broker_handler.py
  mqtt5/                           # MQTT 5.0 implementation
    properties.py                  # Properties encode/decode (§2.2.2)
    property_ids.py                # MQTT 5.0 property IDs
    reason_codes.py                # ReasonCode IntEnum (§2.4)
    connect.py / connack.py
    publish.py
    puback.py / pubrec.py / pubrel.py / pubcomp.py
    subscribe.py / suback.py
    unsubscribe.py / unsuback.py
    disconnect.py
    auth.py                        # AUTH packet (§3.15)
    protocol/
      handler.py
      client_handler.py
      broker_handler.py
  plugins/
    manager.py
    authentication/
    sys/
    ...
tests/
  test_broker.py
  test_client.py
  mqtt5/
    ...
```

## Key Architectural Facts

- MQTT 3.1.1 currently uses protocol level `0x04`.
- MQTT 5.0 uses protocol level `0x05` in the CONNECT packet.
- The existing broker handler has hard-coded MQTT 3.1.1 assumptions that must become version-aware.
- Packet parsing follows one module per packet type, with `build()` for outgoing packets and `from_stream()` for incoming packets.
- `Session` objects hold connection/session state and are tracked by the broker.
- The plugin system fires async events through `PluginManager`.
- Transports are wrapped by `ReaderAdapter` and `WriterAdapter`, including TCP and WebSocket support.

## MQTT 5.0 Implementation Goals

MQTT 5.0 support must coexist with MQTT 3.1.1.

The broker must:

- Detect protocol version from CONNECT.
- Accept MQTT 3.1.1 and MQTT 5.0 clients simultaneously.
- Dispatch to version-appropriate packet parsing and protocol behavior.
- Preserve existing MQTT 3.1.1 behavior.
- Send MQTT 5.0 CONNACK/DISCONNECT reason codes where required.

The client must:

- Default to MQTT 3.1.1.
- Opt in to MQTT 5.0 via configuration or explicit parameter.
- Expose MQTT 5.0 features through additive API parameters.
- Preserve compatibility for existing callers.

## MQTT 5.0 Feature Areas

MQTT 5.0 adds or changes these major areas:

| Area | Change |
|---|---|
| Packet format | Packets carry a Properties section encoded with MQTT property IDs. |
| Reason codes | ACK packets use explicit reason codes. |
| Session expiry | `Session Expiry Interval` replaces the old Clean Session semantics. |
| Flow control | `Receive Maximum` limits in-flight QoS 1/2 messages. |
| Topic aliases | Topic strings can be replaced with per-session integer aliases. |
| Shared subscriptions | `$share/{ShareName}/{filter}` load-balances matching messages. |
| Subscription options | No Local, Retain As Published, and Retain Handling. |
| Subscription identifiers | SUBSCRIBE can attach an identifier echoed on matching PUBLISH deliveries. |
| Message expiry | PUBLISH can carry `Message Expiry Interval`. |
| Payload metadata | Payload Format Indicator and Content Type. |
| Request/response | Response Topic and Correlation Data. |
| User properties | Arbitrary UTF-8 key/value pairs on packets. |
| Will properties | Will Delay Interval and other Will-specific properties. |
| AUTH packet | New packet type for enhanced authentication. |
| Server DISCONNECT | Server may send DISCONNECT before closing. |
| Server reference | Broker can redirect clients to another server. |
| Maximum packet size | Client and broker may negotiate packet size limits. |

## Implementation Layering

Use this layering unless an issue explicitly says otherwise:

1. `amqtt/mqtt5/property_ids.py`
   - Defines all MQTT 5.0 property ID constants.
   - Includes property metadata needed for validation and encoding.

2. `amqtt/mqtt5/properties.py`
   - Encodes and decodes MQTT 5.0 Properties.
   - Handles Variable Byte Integer length prefix.
   - Supports all property wire types.
   - Rejects duplicate non-repeatable properties.
   - Preserves duplicate User Properties in order.

3. Shared Variable Byte Integer helpers
   - Move duplicated MQTT 3.1.1 VBI logic into a shared helper, preferably `amqtt/codecs.py` unless the issue directs otherwise.
   - Ensure existing MQTT 3 packet parsing behavior does not change.

4. `amqtt/mqtt5/reason_codes.py`
   - Defines `ReasonCode` as an `IntEnum`.
   - Includes `is_error()` and human-readable descriptions.

5. MQTT 5 packet modules
   - Add v5 packet modules under `amqtt/mqtt5/`.
   - Prefer subclassing or reusing MQTT 3 classes when the wire format overlaps.
   - Do not fork large blocks of MQTT 3 code unnecessarily.

6. MQTT 5 protocol handlers
   - Add version-aware protocol dispatch.
   - Keep MQTT 3.1.1 paths stable.

7. `session.py`
   - Add negotiated MQTT version and MQTT 5 session state.

8. `broker.py`
   - Add shared subscriptions, subscription options, session expiry, aliases, flow control, and v5 delivery semantics.

9. `client.py`
   - Expose MQTT 5 connect, publish, subscribe, receive, AUTH, and server-disconnect behavior.

## Backwards Compatibility Rules

- MQTT 3.1.1 remains the default behavior.
- MQTT 5.0 is opt-in for the client.
- The broker auto-detects the protocol version on CONNECT.
- Public API changes must be additive.
- Existing public symbols must not be removed or renamed without a deprecation cycle.
- Existing plugins must continue to work if they do not implement new MQTT 5 hooks.
- New MQTT 5-only parameters should default to `None`, omitted, or v3-equivalent behavior.

## Commands

Run tests:

```bash
pytest tests/ -v
pytest tests/ -k "broker" -v
pytest tests/ -k "client" -v
pytest tests/mqtt5/ -v
```

Run a local broker:

```bash
python samples/broker_start.py
```

Type check:

```bash
mypy amqtt/
```

Lint:

```bash
ruff check amqtt/
```

Build docs:

```bash
mkdocs build
```

Preview docs:

```bash
mkdocs serve
```

## Coding Conventions

Follow `CONVENTIONS.md`. Important rules:

- Python 3.10+.
- Use `from __future__ import annotations` in new files.
- Fully annotate all new code.
- Annotate touched existing code opportunistically.
- Use modern syntax such as `X | Y`, `match/case`, and `TypeAlias` where appropriate.
- Keep the code asyncio-native.
- Never perform blocking I/O inside `async def`.
- Do not call `time.sleep()` in async code.
- Do not add dependencies without discussion.
- Use module-level loggers, not `print()`.

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `properties.py` |
| Classes | `PascalCase` | `ConnectProperties` |
| Functions / methods | `snake_case` | `encode_variable_byte_int` |
| Constants | `UPPER_SNAKE` | `SESSION_EXPIRY_INTERVAL` |
| Private helpers | leading `_` | `_read_property` |
| Type aliases | `PascalCase` | `PropertyMap` |
| Packet classes | `{PacketName}Packet` | `AuthPacket`, `DisconnectV5Packet` |

## Packet Module Rules

MQTT 5 packet modules live in `amqtt/mqtt5/`.

Each packet module should follow the existing packet pattern:

- Packet constants at module level.
- Variable header class where needed.
- Payload class where needed.
- Packet class inheriting from the appropriate base.
- `build()` classmethod for outgoing packets.
- `from_stream()` classmethod for incoming packets.
- `to_bytes()` or equivalent serialization methods that round-trip cleanly.

Wire format behavior must be deterministic:

```text
encode(decode(bytes)) == bytes
```

Where MQTT 5 allows shorter encodings, parsers must accept both short and full forms.

## MQTT 5 Properties Rules

- All MQTT 5 properties must be encoded and decoded through `amqtt/mqtt5/properties.py`.
- Do not hand-roll property bytes inside packet modules.
- Property IDs belong in `amqtt/mqtt5/property_ids.py`.
- User Properties must be represented as an ordered list of `(key, value)` tuples because keys may repeat.
- Duplicate non-repeatable properties must raise `MQTTError`.
- Empty properties encode as a single `0x00` byte.

## Version Negotiation

The protocol version is determined from the CONNECT packet Protocol Level byte:

| Value | Protocol |
|---|---|
| `0x04` | MQTT 3.1.1 |
| `0x05` | MQTT 5.0 |

The broker should branch early in connection setup, in or near `BrokerProtocolHandler.mqtt_connect()`.

Store the negotiated version on the session:

```python
session.mqtt_version: int
```

Do not assume a fixed protocol version in shared code paths. Use explicit checks:

```python
if session.mqtt_version == 5:
    ...
```

Unknown protocol levels should be refused cleanly.

## MQTT 5 Session Fields

Add or use these session fields as MQTT 5 support is implemented:

```python
session.mqtt_version: int                       # 4 or 5
session.session_expiry_interval: int            # 0 = clean, 0xFFFF_FFFF = never
session.receive_maximum: int                    # default 65535
session.topic_alias_maximum: int                # default 0
session.topic_alias_map: dict[int, str]
session.subscription_identifiers: dict[str, int]
session.inflight_qos2_count: int
session.maximum_packet_size: int | None
```

Existing session construction must continue to work without explicitly passing these fields.

## Error Handling

Use the existing exception hierarchy:

- `MQTTError` for protocol-level errors.
- `AMQTTError` for library/application-level errors.
- `NoDataError` when the connection closes unexpectedly.

For MQTT 5.0 protocol violations after CONNECT:

1. Send DISCONNECT with the appropriate reason code when possible.
2. Then close the connection.
3. Then raise or propagate the appropriate error.

For errors during CONNECT, send CONNACK with the correct error reason code and close.

Do not silently close v5 connections when the spec calls for a reason code.

## Spec Cross-References

Every non-obvious MQTT 5 implementation decision must cite the spec section in a comment.

Use this format:

```python
# [MQTT-3.1.2.11.2] Session Expiry Interval: 0xFFFFFFFF means session never expires.
```

This makes later conformance auditing possible.

## Testing Requirements

Read the testing conventions in `ISSUES.md` before adding MQTT 5 tests.

General rules:

- Every new packet type needs round-trip tests.
- Every new packet type needs at least one malformed-packet test.
- Use `pytest.mark.parametrize` for multi-value behavior.
- Use Hypothesis for packet `from_stream()` fuzz tests.
- Include at least one known-good wire byte fixture from the spec or Mosquitto for each packet test module.
- Use `pytest-asyncio` for async tests.
- Preserve existing MQTT 3.1.1 tests.

MQTT 5 test layout should mirror `amqtt/mqtt5/`:

```text
tests/
  mqtt5/
    conftest.py
    test_properties.py
    test_reason_codes.py
    test_connect.py
    test_connack.py
    test_publish.py
    test_puback.py
    test_subscribe.py
    test_suback.py
    test_unsubscribe.py
    test_disconnect.py
    test_auth.py
    protocol/
      conftest.py
      test_handler.py
```

Shared fixtures should include:

- `make_reader(data: bytes) -> BufferReader`
- `v5_connect_packet`
- `mock_v5_session`
- `mock_broker_handler`
- `mock_client_handler`

Coverage expectations:

- `pytest-cov` uses branch coverage.
- The project expects at least 80% coverage.
- Do not use `# pragma: no cover` to skip production logic.
- Acceptable `# pragma: no cover` cases are exhaustive enum fallbacks, abstract stubs, and `TYPE_CHECKING` blocks.

## Documentation Requirements

Documentation uses:

- `mkdocs`
- `mkdocs-material`
- `mkdocstrings-python`
- `--8<--` snippets

Every public class and public method in `amqtt/mqtt5/` must have a Google-style docstring.

Minimum docstrings required:

- `Properties` and its public methods: `set`, `get`, `has`, `encode`, `decode`.
- `ReasonCode` and `is_error()`.
- Every MQTT 5 packet class, with a one-line class docstring citing the spec section.
- `AuthPacket` and its fields.
- New public fields added to `Session`, `ApplicationMessage`, `BrokerConfig`, or `ClientConfig`.

When implementing MQTT 5 documentation, create or update:

- `docs/references/mqtt5.md`
- `docs/mqtt5.md`
- `docs/references/broker_config.md`
- `docs/references/client_config.md`
- `docs/references/client.md`
- `docs/references/common.md`
- `docs/plugins/custom_plugins.md`
- `docs/quickstart.md`
- `mkdocs.yml`

If `mkdocs.yml` does not exist, create it before docs work. Use `mkdocs new .` as a starting point, then configure site name, Material theme, mkdocstrings, and navigation.

## Issue Workflow

MQTT 5.0 work is tracked in `ISSUES.md`.

Issue prefixes:

- `[MQTT5-CORE]` — packet format, properties, reason codes, core protocol structures.
- `[MQTT5-BROKER]` — broker-side behavior.
- `[MQTT5-CLIENT]` — client-side behavior.
- `[MQTT5-COMPAT]` — interoperability, backwards compatibility, conformance.

The minimum viable implementation path for a first working demo is:

```text
#001 → #002 → #003 → #004 → #005 → #006 → #013 → #014 → #026 → #027
```

That path gives a broker and client that can connect, publish, and subscribe over MQTT 5.0 with basic properties support.

## Phase Summary

### Phase 0 — Foundation

- Properties subsystem.
- ReasonCode enum.
- Session v5 fields.
- MQTT 5 test infrastructure.
- Broker/client config schema.

### Phase 1 — Packet Encoding / Decoding

- CONNECT
- CONNACK
- PUBLISH
- PUBACK / PUBREC / PUBREL / PUBCOMP
- SUBSCRIBE
- SUBACK
- UNSUBSCRIBE / UNSUBACK
- DISCONNECT
- AUTH

PINGREQ and PINGRESP are unchanged and can reuse MQTT 3 implementations.

### Phase 2 — Broker Protocol Handler

- Version negotiation.
- CONNACK v5 properties.
- Session expiry.
- Receive Maximum flow control.
- Topic aliases.
- Subscription options.
- Subscription identifiers.
- Shared subscriptions.
- Server-initiated DISCONNECT.
- Enhanced authentication.
- Will delay.
- Message expiry.
- Server redirection.

### Phase 3 — Client Protocol Handler

- MQTT 5 connect options.
- Publish with v5 properties.
- Subscribe with v5 options.
- Receive PUBLISH with v5 properties.
- Enhanced authentication.
- Server-initiated DISCONNECT handling.

### Phase 4 — Integration, Conformance, Housekeeping

- Mosquitto interoperability.
- MQTT 3 client against v5-capable broker.
- `$SYS` plugin updates.
- MQTT 5 docs.
- Appendix B conformance checklist.

## Git Commit Guidelines

Use this format:

```text
[scope] short description
```

Keep the subject under 72 characters.

Common scopes:

- `broker`
- `client`
- `packet`
- `props`
- `session`
- `auth`
- `test`
- `docs`
- `deps`
- `ci`

Examples:

```text
[packet] add AUTH packet encoding/decoding
[broker] negotiate MQTT version on CONNECT
[props] implement Variable Byte Integer encode/decode
[client] expose User Properties in publish API
```

Reference issues in commit bodies:

```text
Closes #42
See #38
```

## Session Logging and Analysis

This repository may include Claude Code-oriented session logging tools under `.claude/`. Agents other than Claude can still use the same workflow conceptually.

Relevant files:

- `.claude/scripts/log_turn.py` records per-turn prompts, responses, token usage, and detected issue metadata.
- `.claude/scripts/analyze_session.py` generates a session log scaffold.
- `.claude/session-logs/` stores generated session logs.

If asked to generate a session log:

1. Run the analyzer with the requested slug if provided.
2. Fill in any interpretive placeholders honestly.
3. Do not modify the mechanically generated token usage section.
4. Archive the current turn log if the workflow requires it.
5. Report the session log path and archive path.

Do not fabricate completed work in session summaries or status checklists.

## Non-Goals and Cautions

- Do not rewrite the whole protocol stack when a targeted change will do.
- Do not break the `amqtt.mqtt` compatibility shim.
- Do not change MQTT 3.1.1 defaults while adding MQTT 5.0.
- Do not add MQTT 5 features to the public API in a way that forces existing users to change code.
- Do not hand-roll property encoding in individual packet modules.
- Do not mark issue acceptance criteria complete unless tests and implementation support it.
- Do not introduce synchronous I/O into async paths.

## Source Files for Deeper Context

- `CONVENTIONS.md` — complete coding conventions.
- `ISSUES.md` — detailed MQTT 5 issue plan and acceptance criteria.
- `CLAUDE.md` — original Claude-specific project brief from which this file was adapted.
