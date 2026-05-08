# MQTT 5.0 Implementation Issues

This file contains the full breakdown of work required to implement MQTT 5.0 support in amqtt. Each issue maps to a discrete, reviewable chunk of work. They are grouped by phase. Phases are roughly sequential; within a phase, issues can be worked in parallel.

Spec reference throughout: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html

---

## Testing Conventions

These rules apply to every issue in this file. Read them before writing any test.

### File layout

Mirror `amqtt/mqtt5/` under `tests/mqtt5/`:

```
tests/
  mqtt5/
    conftest.py          # shared fixtures for all mqtt5 packet tests
    test_properties.py   # Issue #001
    test_reason_codes.py # Issue #002
    test_connect.py      # Issue #004
    test_connack.py      # Issue #005
    test_publish.py      # Issue #006
    test_puback.py       # Issue #007  (covers puback/pubrec/pubrel/pubcomp)
    test_subscribe.py    # Issue #008
    test_suback.py       # Issue #009
    test_unsubscribe.py  # Issue #010
    test_disconnect.py   # Issue #011
    test_auth.py         # Issue #012
    protocol/
      conftest.py        # broker/client handler fixtures
      test_handler.py    # Issues #013–#025, #026–#031
```

### Shared fixtures (tests/mqtt5/conftest.py)

Define these once; every test file imports them:
- `make_reader(data: bytes) -> BufferReader` — wraps raw bytes in a `BufferReader` for `from_stream()` calls.
- `v5_connect_packet` — a fully-populated `ConnectV5Packet` fixture for use in broker handler tests.
- `mock_v5_session` — a `Session` with `mqtt_version=5` and spec-default v5 fields populated.
- `mock_broker_handler` / `mock_client_handler` — minimal async handler stubs wired to an in-memory stream pair.

### Use parametrize for multi-value cases

Any test covering multiple distinct inputs must use `@pytest.mark.parametrize`. Required uses:
- All MQTT 5.0 property IDs in encode/decode round-trip tests (Issue #001).
- All reason codes in `ReasonCode` enum (Issue #002).
- Short form vs. full form for PUBACK/PUBREC/PUBREL/PUBCOMP and DISCONNECT.
- All subscription option combinations (no_local × retain_as_published × retain_handling values).
- Every CONNACK Properties field (Issue #005).

### Use Hypothesis for wire format fuzz tests

Use `hypothesis` for all packet `from_stream()` implementations to verify that no arbitrary byte sequence causes an unhandled exception (only `MQTTError` or `AMQTTError` are acceptable raises):

```python
from hypothesis import given, strategies as st

@given(st.binary())
def test_properties_decode_never_crashes(data):
    try:
        Properties.decode(data)
    except (MQTTError, AMQTTError):
        pass
```

Add at least one Hypothesis test per packet type introduced in Phase 1.

### Coverage requirements

- `pytest-cov` runs automatically (`branch=True`, `fail_under=80`). All new code must contribute to passing this threshold — do not add `# pragma: no cover` to skip production logic.
- Use `# pragma: no cover` only for: unreachable `else` branches on exhaustive enums, abstract method stubs, and `if TYPE_CHECKING:` blocks.
- After completing each phase, run `pytest --cov-report=html` and inspect `htmlcov/` for uncovered branches before marking the issue done.

### Known-good wire bytes

Each packet test module must include at least one test decoding a hardcoded byte literal taken directly from a spec example or captured from Mosquitto. This catches silent off-by-one errors in field offsets. Label these tests `test_decode_spec_example` or `test_decode_mosquitto_capture`.

---

## Phase 0 — Foundation

These must land before any protocol work begins. They are pure infrastructure.

### Scaffolding already in place (commit `8fc6a94`)

The following was completed in the Phase 0 scaffolding commit and does **not** need to be re-implemented:
- `amqtt/mqtt5/` package created with `__init__.py`
- `amqtt/mqtt5/properties.py` stub
- `amqtt/mqtt5/property_ids.py` stub
- `amqtt/mqtt5/reason_codes.py` stub
- `amqtt/mqtt5/protocol/` directory created
- `amqtt/mqtt/` shim left intact pointing at `mqtt3/`

Before starting any Phase 0 issue, read the stubs to understand what scaffolding already exists so you don't create duplicate definitions.

---

### Issue #001 [MQTT5-CORE] — Properties subsystem: encoding and decoding

**Spec:** §2.2.2, Appendix B (property table)

**Summary:**
MQTT 5.0 adds a structured Properties section to every packet type. This issue implements the core encode/decode machinery used by all subsequent packet work.

**Scope:**
- [x] Create `amqtt/mqtt5/property_ids.py` — all MQTT 5.0 property ID constants with types and which packet types each is valid on.
- [x] Create `amqtt/mqtt5/properties.py`:
  - [x] `Properties` class with `set(id, value)`, `get(id)`, `has(id)`, `encode() -> bytes`, and `Properties.decode(data: bytes) -> Properties` methods.
  - [x] Support all wire types: one-byte integer, two-byte integer, four-byte integer, Variable Byte Integer, UTF-8 string, UTF-8 string pair (User Properties), binary data.
  - [x] A property ID appearing more than once in a packet (except User Property `0x26`) MUST raise `MQTTError`.
  - [x] User Properties are a list of `(key, value)` string tuples, not a dict, because keys can repeat.
- [x] Variable Byte Integer encode/decode (used for property length prefix): move to `amqtt/codecs.py` or a new `amqtt/mqtt5/varint.py`. This is a **refactor of existing code** — the same VBI logic already exists inline in `mqtt3/` packet parsing. Centralising it must not change the behavior of any existing `mqtt3/` packet. Add a regression test that exercises VBI through existing v3 packet parsing after the move.

**Acceptance criteria:**
- [x] Round-trip test: for every property type, `Properties.decode(p.encode()) == p`.
- [x] Test that duplicate non-repeatable properties raise `MQTTError`.
- [x] Test User Properties with duplicate keys are preserved in order.
- [x] Zero-property encoding produces a single `0x00` byte (empty properties length).
- [x] All existing `mqtt3/` packet encode/decode tests still pass after VBI is moved.

---

### Issue #002 [MQTT5-CORE] — Reason codes: enum and wire encoding

**Spec:** §2.4, Table 2-6

**Summary:**
MQTT 5.0 replaces the limited CONNACK return codes with a unified 1-byte Reason Code used across CONNACK, PUBACK, PUBREC, PUBREL, PUBCOMP, SUBACK, UNSUBACK, DISCONNECT, and AUTH.

**Scope:**
- [ ] Create `amqtt/mqtt5/reason_codes.py`:
  - [ ] `ReasonCode` `IntEnum` with all ~30 defined values and their byte representations.
  - [ ] Two categories: Success codes (0x00–0x9F, depending on packet) and Error codes (0x80+).
  - [ ] Helper: `ReasonCode.is_error() -> bool` (value >= 0x80).
  - [ ] Human-readable string descriptions for logging.
- [ ] Keep the old MQTT 3.1.1 CONNACK return code constants in `constants.py` — do not remove them.

**Acceptance criteria:**
- [ ] Every reason code in spec Table 2-6 is present.
- [ ] `ReasonCode(0x00).name == "SUCCESS"`.
- [ ] `ReasonCode(0x80).is_error() == True`.
- [ ] `ReasonCode(0x00).is_error() == False`.

---

### Issue #003 [MQTT5-CORE] — Session: add MQTT version and v5 state fields

**Spec:** §3.1.4, §4.1

**Summary:**
The `Session` class needs to carry the negotiated protocol version and v5-specific state.

**Scope:**
- [ ] Add `session.mqtt_version: int` (4 for MQTT 3.1.1, 5 for MQTT 5.0).
- [ ] Add `session.session_expiry_interval: int` (seconds; 0 = clean on disconnect; `0xFFFF_FFFF` = never).
- [ ] Add `session.receive_maximum: int` (default 65535 per spec §3.1.2.11.3).
- [ ] Add `session.topic_alias_maximum: int` (default 0 — no aliases by default).
- [ ] Add `session.topic_alias_map: dict[int, str]` — alias integer → topic string, per-session.
- [ ] Add `session.subscription_identifiers: dict[str, int]` — topic filter → subscription identifier.
- [ ] Add `session.inflight_qos2_count: int` for flow control tracking.
- [ ] Add `session.maximum_packet_size: int | None` (None = unlimited).

**Acceptance criteria:**
- [ ] Existing session construction (without new params) still works unchanged.
- [ ] New fields have documented defaults matching spec defaults.

---

### Issue #003b [MQTT5-CORE] — Test infrastructure for mqtt5

**Summary:**
Create the `tests/mqtt5/` directory structure and shared fixtures before any Phase 1 packet tests are written. This prevents each issue from independently inventing incompatible helpers.

**Scope:**
- [ ] Create `tests/mqtt5/__init__.py` and `tests/mqtt5/protocol/__init__.py`.
- [ ] Write `tests/mqtt5/conftest.py` with the fixtures listed in the Testing Conventions section above: `make_reader`, `v5_connect_packet`, `mock_v5_session`, `mock_broker_handler`, `mock_client_handler`.
- [ ] Verify that `pytest tests/mqtt5/` runs and collects zero tests (empty suite passes cleanly) — this confirms the directory structure and conftest are valid before any packet tests exist.
- [ ] Do **not** implement any packet-level tests here; leave that to the individual issues.

**Acceptance criteria:**
- [ ] `pytest tests/mqtt5/ -v` exits 0 with "no tests ran".
- [ ] `mock_v5_session` fixture produces a `Session` with `mqtt_version=5` and all spec-default v5 fields set correctly per Issue #003.
- [ ] `make_reader(b"")` returns a `BufferReader` that immediately raises on read (not silently succeeds).

---

### Issue #003a [MQTT5-CORE] — Config schema: broker and client v5 parameters

**Summary:**
Several Phase 2 and Phase 3 issues introduce new config keys (e.g. `receive_maximum`, `topic_alias_maximum`, `session_expiry_interval`, `mqtt_version`). This issue establishes where those keys live and validates them at startup, so later issues can reference a stable schema rather than each inventing their own parsing.

**Scope:**
- [ ] Define the new broker config keys under a `[mqtt5]` section (or flat alongside existing keys — decide and document the choice): `receive_maximum`, `topic_alias_maximum`, `maximum_packet_size`, `shared_subscriptions_available`, `subscription_identifiers_available`, `wildcard_subscriptions_available`.
- [ ] Define the new client config keys: `mqtt_version` (int, default 4), `session_expiry_interval`, `receive_maximum`, `maximum_packet_size`, `topic_alias_maximum`, `user_properties`, `authentication_method`, `authentication_data`.
- [ ] Add validation: unknown or out-of-range values raise a clear `ConfigurationError` at startup.
- [ ] Document each key with its default and the spec section that governs it.

**Acceptance criteria:**
- [ ] A broker started with no v5 config keys uses spec-default values for all new fields.
- [ ] A broker started with an out-of-range `receive_maximum` (e.g. 0 or > 65535) raises `ConfigurationError`.
- [ ] A client config with `mqtt_version=5` and no other v5 keys connects successfully with spec defaults.
- [ ] `docs/references/broker_config.md` and `docs/references/client_config.md` are updated with all new v5 keys; `mkdocs build` passes.

---

## Phase 1 — Packet Encoding / Decoding

One issue per packet type that changes in MQTT 5.0. All issues in this phase are independent of each other.

**PINGREQ / PINGRESP:** These packets are identical in MQTT 5.0 and 3.1.1 — no changes needed. The existing `mqtt3/` implementations are reused as-is for v5 connections.

---

### Issue #004 [MQTT5-CORE] — CONNECT packet v5 support

**Spec:** §3.1

**Changes from v3.1.1:**
- Protocol Level byte is `0x05` (was `0x04`).
- `Clean Start` flag replaces `Clean Session` (same wire position, new semantics — session expiry is now a property, not a flag).
- New CONNECT Properties section (§3.1.2.11): Session Expiry Interval, Receive Maximum, Maximum Packet Size, Topic Alias Maximum, Request Response Information, Request Problem Information, User Properties, Authentication Method, Authentication Data.
- Will message now has its own Will Properties section in the payload (§3.1.3.2): Will Delay Interval, Payload Format Indicator, Message Expiry Interval, Content Type, Response Topic, Correlation Data, User Property.
- Password field is now binary data (arbitrary bytes, not a string).

**Scope:**
- [ ] Extend existing `ConnectPacket` (or add `ConnectV5Packet`) to parse and produce v5 CONNECT packets.
- [ ] Implement Will Properties decode/encode.
- [ ] Implement CONNECT Properties decode/encode.

**Acceptance criteria:**
- [ ] Can parse raw bytes of a known-good v5 CONNECT packet (from spec example or captured traffic).
- [ ] Can encode a v5 CONNECT packet and decode it back with identical fields (round-trip).
- [ ] v3.1.1 CONNECT parsing is unaffected.

---

### Issue #005 [MQTT5-CORE] — CONNACK packet v5 support

**Spec:** §3.2

**Changes from v3.1.1:**
- Return code becomes Reason Code (1 byte, uses unified `ReasonCode` enum).
- New CONNACK Properties section (§3.2.2.3): Session Expiry Interval, Receive Maximum, Maximum QoS, Retain Available, Maximum Packet Size, Assigned Client Identifier, Topic Alias Maximum, Reason String, User Properties, Wildcard Subscription Available, Subscription Identifiers Available, Shared Subscription Available, Server Keep Alive, Response Information, Server Reference, Authentication Method, Authentication Data.

**Scope:**
- [ ] Extend `ConnackPacket` to produce and parse v5 CONNACK with Properties.
- [ ] `ConnackPacket.build()` must accept a `ReasonCode` and optional `Properties`.

**Acceptance criteria:**
- [ ] Round-trip test with at least: Reason Code, Assigned Client Identifier, Session Expiry Interval, Reason String.
- [ ] v3.1.1 CONNACK unaffected.

---

### Issue #006 [MQTT5-CORE] — PUBLISH packet v5 support

**Spec:** §3.3

**Changes from v3.1.1:**
- New PUBLISH Properties section (§3.3.2.3): Payload Format Indicator, Message Expiry Interval, Topic Alias, Response Topic, Correlation Data, User Properties, Subscription Identifier, Content Type.
- Topic Name may be zero-length when Topic Alias is used (§3.3.2.1).
- Subscription Identifier may appear multiple times (once per matched subscription).

**Scope:**
- [ ] Extend `PublishPacket` to encode/decode v5 Properties.
- [ ] Handle zero-length topic name (alias path).

**Acceptance criteria:**
- [ ] Round-trip test with: Payload Format Indicator, Message Expiry Interval, Response Topic, Content Type, User Properties.
- [ ] Zero-length topic with Topic Alias encodes correctly.

---

### Issue #007 [MQTT5-CORE] — PUBACK / PUBREC / PUBREL / PUBCOMP v5 support

**Spec:** §3.4, §3.5, §3.6, §3.7

**Changes from v3.1.1:**
- Each packet now optionally carries a Reason Code byte and a Properties section.
- When Reason Code is 0x00 (Success) and there are no properties, the variable header MAY be omitted (remaining length = 2, just packet ID). Parsers must handle both forms.

**Scope:**
- [ ] Extend `PubackPacket`, `PubrecPacket`, `PubrelPacket`, `PubcompPacket`.
- [ ] Each gains optional `reason_code: ReasonCode` and `properties: Properties | None`.
- [ ] Encode: omit reason code + properties when both would be default (success, no props) for wire efficiency.

**Acceptance criteria:**
- [ ] Round-trip test: full form (with reason code + properties) and short form (packet ID only).
- [ ] Parser handles both forms correctly.
- [ ] v3.1.1 packets unaffected.

---

### Issue #008 [MQTT5-CORE] — SUBSCRIBE packet v5 support

**Spec:** §3.8

**Changes from v3.1.1:**
- New SUBSCRIBE Properties section (§3.8.2.1): Subscription Identifier, User Properties.
- Each topic filter in the payload now has 3 extra option bits (§3.8.3.1): Maximum QoS (2 bits, existing), No Local (1 bit), Retain As Published (1 bit), Retain Handling (2 bits).

**Scope:**
- [ ] Extend `SubscribePacket` with Properties.
- [ ] Add `SubscriptionOptions` data class: `max_qos`, `no_local`, `retain_as_published`, `retain_handling`.
- [ ] Update subscription topic list to carry `(topic_filter, SubscriptionOptions)` pairs.

**Acceptance criteria:**
- [ ] Round-trip test with Subscription Identifier and all four option bits set.
- [ ] Default options match v3.1.1 semantics (retain_handling=0, no_local=False, retain_as_published=False).

---

### Issue #009 [MQTT5-CORE] — SUBACK packet v5 support

**Spec:** §3.9

**Changes from v3.1.1:**
- Payload reason codes now use full `ReasonCode` values (not just QoS grant bytes).
- New SUBACK Properties section: Reason String, User Properties.

**Scope:**
- [ ] Extend `SubackPacket` with Properties and `ReasonCode` per-topic payload.

**Acceptance criteria:**
- [ ] Round-trip test with mixed success/error reason codes and Reason String property.

---

### Issue #010 [MQTT5-CORE] — UNSUBSCRIBE / UNSUBACK v5 support

**Spec:** §3.10, §3.11

**Changes from v3.1.1:**
- UNSUBSCRIBE: new Properties section (User Properties only).
- UNSUBACK: new Properties section (Reason String, User Properties) + per-topic Reason Code payload (was empty in v3.1.1).

**Scope:**
- [ ] Extend `UnsubscribePacket` with Properties.
- [ ] Extend `UnsubackPacket` with Properties and per-topic `ReasonCode` payload.

**Acceptance criteria:**
- [ ] Round-trip test for both packets.
- [ ] UNSUBACK with mixed success/error reason codes per topic.

---

### Issue #011 [MQTT5-CORE] — DISCONNECT packet v5 support

**Spec:** §3.14

**Changes from v3.1.1:**
- DISCONNECT now carries a Reason Code byte and Properties section.
- **Server may now send DISCONNECT** (not just client). Reason codes differ depending on direction.
- Properties (§3.14.2.2): Session Expiry Interval (client can extend on DISCONNECT), Reason String, User Properties, Server Reference.

**Scope:**
- [ ] Extend `DisconnectPacket` with `reason_code: ReasonCode` and `properties: Properties | None`.
- [ ] Allow server-initiated disconnect path (currently not in the codebase).
- [ ] Short form: when reason code is 0x00 and no properties, remaining length = 0 (no variable header). Parser must handle both.

**Acceptance criteria:**
- [ ] Round-trip test for full and short forms.
- [ ] Server Reference property properly encodes/decodes.

---

### Issue #012 [MQTT5-CORE] — AUTH packet (new in MQTT 5.0)

**Spec:** §3.15

**Summary:**
AUTH is a new packet type (`0x0F`) used for extended authentication (challenge-response flows after CONNECT). There is no v3.1.1 equivalent.

**Scope:**
- [ ] Create `amqtt/mqtt5/auth.py` with `AuthPacket`.
- [ ] Fixed header: type `0x0F`, reserved flags `0x00`.
- [ ] Variable header: Reason Code (one of: `0x00` Success, `0x18` Continue Authentication, `0x19` Re-authenticate), then Properties section.
- [ ] Properties: Authentication Method, Authentication Data, Reason String, User Properties.

**Acceptance criteria:**
- [ ] Round-trip test with each valid reason code.
- [ ] AUTH packet with no properties encodes to 2 bytes of variable header.

---

## Phase 2 — Broker Protocol Handler

---

### Issue #013 [MQTT5-BROKER] — Version negotiation in BrokerProtocolHandler

**Spec:** §3.1.2.2, §3.1.4

**Summary:**
The broker's `mqtt_connect()` method currently hard-codes protocol level 4. It needs to detect v3 vs v5 and take the appropriate code path.

**Scope:**
- [ ] Read Protocol Level byte from CONNECT; if not 4 or 5, send CONNACK with reason code `0x84 Unsupported Protocol Version` and close.
- [ ] Store negotiated version on `session.mqtt_version`.
- [ ] All subsequent packet operations in the handler must be version-aware.
- [ ] v3.1.1 path must be unchanged in behavior.
- [ ] **Version-aware packet dispatch**: after CONNECT, every call to `read_packet()` (or equivalent) must produce the correct v3 or v5 packet class based on `session.mqtt_version`. The two options are: (a) a single dispatcher that checks the fixed-header type byte and delegates to the right module, or (b) two separate handler subclasses that each call their own packet factories. Decide and document the approach here; all Phase 1 packet classes must conform to it. The chosen approach also determines whether `from_stream()` classmethods are version-agnostic (option a) or each handler calls its own module directly (option b).

**Acceptance criteria:**
- [ ] A v5 client can complete a CONNECT/CONNACK handshake with the broker.
- [ ] A client sending an unknown protocol level (e.g. 3 or 6) is refused cleanly.
- [ ] Existing v3 integration tests still pass.
- [ ] A v5 PUBLISH received after CONNECT is decoded as a `mqtt5.PublishPacket`, not `mqtt3.PublishPacket`.

---

### Issue #014 [MQTT5-BROKER] — CONNACK v5 properties on successful connect

**Spec:** §3.2.2.3

**Summary:**
When accepting a v5 client, the broker should populate the CONNACK Properties that inform the client of broker capabilities and negotiated parameters.

**Scope:**
Send the following CONNACK Properties for v5 connections:
- [ ] `Receive Maximum` — broker's receive maximum (configurable, default 65535).
- [ ] `Maximum QoS` — if broker is configured to limit QoS.
- [ ] `Retain Available` — whether broker supports retained messages.
- [ ] `Maximum Packet Size` — if broker imposes a limit.
- [ ] `Topic Alias Maximum` — broker's limit on aliases (configurable, default 0 = no aliases).
- [ ] `Wildcard Subscription Available` — always true unless disabled.
- [ ] `Subscription Identifiers Available` — always true unless disabled.
- [ ] `Shared Subscription Available` — true if broker supports shared subscriptions.
- [ ] `Assigned Client Identifier` — if broker assigned the client ID.

**Acceptance criteria:**
- [ ] `Receive Maximum` is always sent for v5 connections.
- [ ] Client test that reads CONNACK Properties and verifies at least `Receive Maximum` and `Topic Alias Maximum`.

---

### Issue #015 [MQTT5-BROKER] — Session expiry semantics for MQTT 5.0

**Spec:** §3.1.2.11.2, §3.2.2.3.2, §3.14.2.2.2, §4.1

**Summary:**
MQTT 5.0 decouples session persistence from the connect call. Session Expiry Interval (property in CONNECT) replaces the old Clean Session flag. Session expiry can also be updated in DISCONNECT.

**Scope:**
- [ ] On v5 CONNECT: read `Session Expiry Interval` property (default 0 if absent = clean session).
- [ ] If `0`: delete session on disconnect (equivalent to clean session).
- [ ] If non-zero: persist session for that many seconds after disconnect.
- [ ] If `0xFFFF_FFFF`: persist session indefinitely.
- [ ] On v5 DISCONNECT from client: if `Session Expiry Interval` property is present, use it to update the session expiry (except: cannot change from 0 to non-zero — that's a protocol error).
- [ ] Broker sends CONNACK with Session Present flag correctly set.

**Acceptance criteria:**
- [ ] Client connecting with Session Expiry Interval = 0 gets a clean session.
- [ ] Client connecting with Session Expiry Interval = 300 has session preserved for 5 minutes after disconnect.
- [ ] Client attempting to set expiry from 0 to non-zero in DISCONNECT receives DISCONNECT with reason code `0x82 Protocol Error`.

---

### Issue #016 [MQTT5-BROKER] — Flow control: Receive Maximum

**Spec:** §4.9, §3.1.2.11.3, §3.2.2.3.3

**Summary:**
Either side can limit the number of in-flight QoS 1 and QoS 2 publishes using `Receive Maximum`. The broker must respect the client's limit when sending, and enforce its own limit when receiving.

**Scope:**
- [ ] Track per-session in-flight QoS 1/2 publish count.
- [ ] When sending to a v5 client: do not exceed the client's `Receive Maximum` from CONNECT Properties.
- [ ] When receiving from a v5 client: if the client exceeds the broker's `Receive Maximum` (from CONNACK), send DISCONNECT with reason code `0x93 Receive Maximum Exceeded`.
- [ ] Implement a flow-control gate: queue additional publishes until in-flight count drops below the limit when a PUBACK/PUBCOMP is received.

**Acceptance criteria:**
- [ ] Broker correctly limits outgoing QoS 1 publishes to client's declared Receive Maximum.
- [ ] Client exceeding broker's Receive Maximum triggers DISCONNECT `0x93`.
- [ ] QoS 0 messages are not counted (they are not flow-controlled).

---

### Issue #017 [MQTT5-BROKER] — Topic Aliases (broker-side)

**Spec:** §3.3.2.3.4, §3.1.2.11.5, §3.2.2.3.8

**Summary:**
Topic Aliases allow replacing the full topic string in PUBLISH with a short integer. The broker must handle aliases in both directions.

**Scope:**
- [ ] **Receiving from client**: maintain a per-session alias-to-topic mapping. A PUBLISH with a non-zero Topic Alias and a non-empty Topic Name establishes or updates the mapping. A PUBLISH with a non-zero alias and empty Topic Name uses the existing mapping. If no mapping exists for an alias, send DISCONNECT `0x82 Protocol Error`.
- [ ] **Sending to client**: optionally use topic aliases when sending PUBLISH to a v5 client, if `Topic Alias Maximum` in the CONNECT Properties is > 0. The broker assigns alias IDs; this is optional for this first iteration — mark as a stretch goal.
- [ ] Enforce: alias value 0 is invalid; disconnect with `0x82`.
- [ ] Enforce: alias value > client's `Topic Alias Maximum` from CONNACK; disconnect with `0x94 Topic Alias Invalid`.

**Acceptance criteria:**
- [ ] Client can establish a topic alias with a PUBLISH and then use it in subsequent publishes.
- [ ] Invalid alias (0 or out-of-range) triggers DISCONNECT with correct reason code.
- [ ] Broker → client alias sending is out of scope for this issue; track in a follow-up.

---

### Issue #018 [MQTT5-BROKER] — Subscription Options: No Local, Retain As Published, Retain Handling

**Spec:** §3.8.3.1, §4.8.1

**Summary:**
MQTT 5.0 SUBSCRIBE adds three new per-subscription flags:
- **No Local**: do not deliver a message to a subscriber if the publisher is the same client session.
- **Retain As Published**: forward the RETAIN flag as-is from the original PUBLISH (rather than clearing it on forwarding).
- **Retain Handling**: controls whether retained messages are sent on subscribe: 0 = send, 1 = send only if subscription did not already exist, 2 = never send.

**Scope:**
- [ ] Store subscription options alongside topic filter in session/broker subscription store.
- [ ] Apply **No Local** filter before delivering to a matching subscriber.
- [ ] Apply **Retain As Published** when forwarding (preserve or clear RETAIN bit).
- [ ] Apply **Retain Handling** when processing SUBSCRIBE and deciding whether to deliver retained messages.

**Acceptance criteria:**
- [ ] No Local: publisher does not receive its own messages on a matching subscription.
- [ ] Retain As Published: subscribers with this option see RETAIN=1 on retained messages they receive.
- [ ] Retain Handling 1: no retained message on re-subscribe.
- [ ] Retain Handling 2: no retained messages ever on subscribe.

---

### Issue #019 [MQTT5-BROKER] — Subscription Identifiers

**Spec:** §3.8.2.1.2, §3.3.2.3.8

**Summary:**
A client may attach a Subscription Identifier integer to a SUBSCRIBE. When the broker delivers a PUBLISH that matches that subscription, it MUST include the Subscription Identifier in the PUBLISH Properties. A single PUBLISH can carry multiple identifiers if it matches multiple subscriptions.

**Scope:**
- [ ] Store subscription identifier (if present) in the broker's subscription record.
- [ ] When delivering a PUBLISH for v5 clients, look up all matching subscriptions and collect their identifiers.
- [ ] Add all collected identifiers as `Subscription Identifier` properties in the outgoing PUBLISH (one property entry per identifier).
- [ ] Subscription Identifier = 0 is a protocol error; send DISCONNECT `0x82`.

**Acceptance criteria:**
- [ ] Client subscribing with identifier 42 receives PUBLISH with `Subscription Identifier = 42` in properties.
- [ ] A PUBLISH matching two subscriptions (e.g. overlapping filters) includes both identifiers.
- [ ] Identifier 0 causes DISCONNECT.

---

### Issue #020 [MQTT5-BROKER] — Shared Subscriptions

**Spec:** §4.8.2

**Summary:**
Shared subscriptions use the topic filter syntax `$share/{ShareName}/{filter}` and cause the broker to deliver each matching PUBLISH to exactly one of the subscribers in the group (load-balancing). The delivery order within the group is not mandated.

**Scope:**
- [ ] Parse the `$share/` prefix in SUBSCRIBE.
- [ ] Maintain a broker-level shared subscription group registry: `{share_name}/{filter}` → list of `Session`.
- [ ] On PUBLISH matching the filter, select one session from the group (round-robin is fine for v1).
- [ ] UNSUBACK reason code `0x11 Shared Subscriptions Not Supported` if shared subscriptions are disabled in broker config.
- [ ] Sessions that disconnect with a persistent session remain in the group; messages to them are queued.

**Acceptance criteria:**
- [ ] Two clients subscribing to `$share/workers/jobs/#` receive alternating messages from a publisher.
- [ ] Unsubscribing removes the session from the group.
- [ ] A third client subscribing to `jobs/#` (non-shared) still receives all messages.

---

### Issue #021 [MQTT5-BROKER] — Server-initiated DISCONNECT

**Spec:** §3.14

**Summary:**
In MQTT 5.0 the broker may send DISCONNECT before closing a connection, to inform the client of the reason.

**Scope:**
- [ ] Add `BrokerProtocolHandler.mqtt_send_disconnect(reason_code, reason_string=None)` coroutine.
- [ ] Call it in all broker-side error paths for v5 sessions before closing the connection.
- [ ] Key reason codes the broker should send: `0x81 Malformed Packet`, `0x82 Protocol Error`, `0x93 Receive Maximum Exceeded`, `0x94 Topic Alias Invalid`, `0x95 Topic Name Invalid`, `0x97 Quota Exceeded`, `0x9A Retain Not Supported`, `0x9B QoS Not Supported`, `0x9C Use Another Server`, `0x9D Server Moved`, `0x98 Connection Rate Exceeded`.
- [ ] For v3 sessions, continue the current behavior (close without DISCONNECT).

**Acceptance criteria:**
- [ ] Protocol error on a v5 client results in a DISCONNECT packet being received by the client before TCP close.
- [ ] v3 client behavior is unchanged.

---

### Issue #022 [MQTT5-BROKER] — Enhanced Authentication (AUTH packet, broker-side)

**Spec:** §4.12, §3.15

**Summary:**
MQTT 5.0 adds an AUTH packet that enables SASL-style challenge-response authentication. The broker receives CONNECT with `Authentication Method` property, may challenge via AUTH, and finally accepts or rejects via CONNACK.

**Scope:**
- [ ] Detect `Authentication Method` property in v5 CONNECT.
- [ ] If method is not recognized, send CONNACK `0x8C Bad Authentication Method`.
- [ ] For recognized methods: implement the plugin hook `on_mqtt_auth(client_id, auth_method, auth_data)` that plugins can implement to perform multi-step auth.
- [ ] Broker sends AUTH `0x18 Continue Authentication` if the plugin needs another round.
- [ ] Client responds with AUTH `0x18`; broker eventually sends CONNACK `0x00 Success` or `0x87 Not Authorized`.
- [ ] Re-authentication: client sends AUTH `0x19 Re-authenticate` mid-session; broker follows same flow.

**Acceptance criteria:**
- [ ] A test plugin implementing a trivial two-round auth (challenge + response) completes successfully.
- [ ] Unknown auth method produces CONNACK `0x8C`.
- [ ] Re-authentication mid-session works.
- [ ] `docs/plugins/custom_plugins.md` Broker events list is updated with `on_mqtt_auth` signature and challenge-response flow description.

---

### Issue #023 [MQTT5-BROKER] — Will Delay Interval

**Spec:** §3.1.3.2.2, §3.2.2.3.2

**Summary:**
The Will message in MQTT 5.0 has a `Will Delay Interval` property. When a session expires, the broker MUST wait `Will Delay Interval` seconds before publishing the Will, unless the session expires first (in which case the Will is published at session expiry time, whichever is sooner).

**Scope:**
- [ ] Store Will Delay Interval from Will Properties on the Session.
- [ ] After a client disconnects (without sending DISCONNECT `0x00`), schedule Will publication with the delay.
- [ ] If the session expires before the delay elapses, publish immediately.
- [ ] If the client reconnects before the delay elapses, cancel the Will.

**Acceptance criteria:**
- [ ] Will is published after the configured delay on ungraceful disconnect.
- [ ] Will is cancelled if client reconnects before delay.
- [ ] Will is published immediately if session expiry occurs before delay.

---

### Issue #024 [MQTT5-BROKER] — Message Expiry Interval

**Spec:** §3.3.2.3.3

**Summary:**
A PUBLISH message in MQTT 5.0 can carry a `Message Expiry Interval` (seconds). The broker must not deliver the message to a subscriber if the interval has elapsed.

**Scope:**
- [ ] Store message receive timestamp and expiry interval on `ApplicationMessage`.
- [ ] When delivering a queued message to a subscriber, check if `now > received_at + expiry_interval`.
- [ ] If expired: discard the message silently.
- [ ] When forwarding to a subscriber, set the `Message Expiry Interval` property in the PUBLISH to the **remaining** time (`original_expiry - elapsed`).
- [ ] Retained messages also expire.

**Acceptance criteria:**
- [ ] Message with 1-second expiry is not delivered to an offline client that reconnects after 2 seconds.
- [ ] Message with 60-second expiry delivered to an online client carries the reduced remaining interval.
- [ ] Retained message with expired interval is discarded and not sent to new subscribers.

---

### Issue #025 [MQTT5-BROKER] — Server Redirection

**Spec:** §4.11, §3.2.2.3.16, §3.14.2.2.5

**Summary:**
A broker can redirect a client to another server using the `Server Reference` property in CONNACK (reject at connect time) or DISCONNECT (redirect an established session).

**Scope:**
- [ ] Add `server_reference` field to broker config (optional).
- [ ] If set, include `Server Reference` in CONNACK or DISCONNECT Properties for v5 clients.
- [ ] Expose a broker API: `broker.redirect_client(client_id, server_reference, reason_code=0x9C)`.

**Acceptance criteria:**
- [ ] Broker configured with a server reference sends it in CONNACK when rejecting.
- [ ] `redirect_client()` sends DISCONNECT with Server Reference to a connected v5 client.

---

## Phase 3 — Client Protocol Handler

---

### Issue #026 [MQTT5-CLIENT] — MQTTClient: MQTT 5.0 connect options

**Spec:** §3.1, §4.1

**Summary:**
Expose MQTT 5.0 CONNECT properties in the `MQTTClient` API.

**Scope:**
- [ ] Add `mqtt_version: int = 4` to client config (4 = 3.1.1, 5 = MQTT 5.0).
- [ ] When `mqtt_version=5`, build v5 CONNECT packet with supported properties.
- [ ] Expose config keys: `session_expiry_interval`, `receive_maximum`, `maximum_packet_size`, `topic_alias_maximum`, `user_properties`, `authentication_method`, `authentication_data`.
- [ ] Read CONNACK Properties and store broker-reported limits on the session.

**Acceptance criteria:**
- [ ] `MQTTClient(config={"mqtt_version": 5}).connect(...)` sends a v5 CONNECT.
- [ ] CONNACK Properties are accessible after connect: `client.session.broker_receive_maximum`, etc.
- [ ] Default (`mqtt_version=4`) behavior is unchanged.
- [ ] `MQTTClient`, `ClientConfig`, and any new v5 config dataclasses have Google-style docstrings on all new public fields so `mkdocstrings` renders them correctly in `docs/references/client.md` and `docs/references/client_config.md`.

---

### Issue #027 [MQTT5-CLIENT] — MQTTClient: publish with v5 properties

**Spec:** §3.3

**Summary:**
Expose MQTT 5.0 PUBLISH properties in `MQTTClient.publish()`.

**Scope:**
- [ ] Add optional parameters to `publish()`: `payload_format_indicator`, `message_expiry_interval`, `topic_alias`, `response_topic`, `correlation_data`, `user_properties`, `content_type`.
- [ ] When the session is v5, include these as PUBLISH Properties.
- [ ] Implement topic alias sending: if `topic_alias` is specified and the broker's `Topic Alias Maximum` > 0, map and send the alias.
- [ ] Respect the broker's `Maximum Packet Size` — raise `MQTTError` if the encoded packet exceeds it.

**Acceptance criteria:**
- [ ] `client.publish("t", b"data", content_type="application/json", user_properties=[("key","val")])` sends correct wire bytes.
- [ ] Topic alias is used in subsequent publishes to the same topic.
- [ ] Publishing a packet exceeding broker's Maximum Packet Size raises an error before sending.

---

### Issue #028 [MQTT5-CLIENT] — MQTTClient: subscribe with v5 options

**Spec:** §3.8

**Summary:**
Expose MQTT 5.0 SUBSCRIBE options in `MQTTClient.subscribe()`.

**Scope:**
- [ ] Add `subscription_identifier: int | None`, `no_local: bool = False`, `retain_as_published: bool = False`, `retain_handling: int = 0`, `user_properties` to `subscribe()`.
- [ ] Build SUBSCRIBE with Properties and per-topic `SubscriptionOptions`.

**Acceptance criteria:**
- [ ] `client.subscribe("topic", no_local=True, subscription_identifier=7)` sends correct wire bytes.
- [ ] Subscription identifier is echoed back in received PUBLISH Properties.

---

### Issue #029 [MQTT5-CLIENT] — MQTTClient: receive PUBLISH with v5 properties

**Spec:** §3.3

**Summary:**
Incoming PUBLISH messages in v5 carry Properties. The client's `deliver_message()` flow should expose these.

**Scope:**
- [ ] Extend `ApplicationMessage` with a `properties: Properties | None` field.
- [ ] When delivering a v5 PUBLISH, populate `message.properties`.
- [ ] Update `deliver_message()` return type / docs.

**Acceptance criteria:**
- [ ] Received message from a v5 broker has `message.properties` with correct fields populated.
- [ ] Accessing properties on a v3-received message returns `None` safely.
- [ ] `ApplicationMessage.properties` has a docstring; `docs/references/common.md` notes its presence and type for v5 messages.

---

### Issue #030 [MQTT5-CLIENT] — MQTTClient: enhanced authentication (AUTH packet)

**Spec:** §4.12

**Summary:**
The client needs to handle the AUTH packet exchange for extended authentication.

**Scope:**
- [ ] Read `Authentication Method` / `Authentication Data` from CONNACK.
- [ ] Handle AUTH `0x18 Continue Authentication` from broker: invoke a user-supplied callback with the auth data; send AUTH `0x18` reply with the response data.
- [ ] The callback interface: `auth_callback(method: str, data: bytes) -> bytes`.
- [ ] Re-authentication: expose `client.reauthenticate(auth_data: bytes)` which sends AUTH `0x19`.

**Acceptance criteria:**
- [ ] Client with an `auth_callback` can complete a two-round challenge with a broker implementing Issue #022.
- [ ] `reauthenticate()` triggers the flow and returns when the broker sends CONNACK or AUTH success.

---

### Issue #031 [MQTT5-CLIENT] — MQTTClient: handle server-initiated DISCONNECT

**Spec:** §3.14

**Summary:**
In MQTT 5.0, the broker may send DISCONNECT. The client must handle this gracefully.

**Scope:**
- [ ] In the client protocol handler, detect incoming DISCONNECT packet.
- [ ] Raise or propagate a `ServerDisconnectedError` with the reason code and reason string.
- [ ] Expose the disconnect reason on the client for inspection after reconnect.
- [ ] If reason code is `0x9C Use Another Server` or `0x9D Server Moved`, extract and expose `Server Reference`.

**Acceptance criteria:**
- [ ] Client receives server DISCONNECT and raises a typed exception with reason code.
- [ ] `client.last_disconnect_reason` is accessible after the event.

---

## Phase 4 — Integration, Conformance & Housekeeping

---

### Issue #032 [MQTT5-COMPAT] — Interoperability test against Mosquitto 2.x

**Summary:**
Run the amqtt v5 client against a real Mosquitto 2.x broker (which has solid MQTT 5.0 support) to validate wire compatibility.

**Scope:**
- [ ] Add CI job that spins up a Mosquitto 2.x container.
- [ ] Run a set of v5 scenarios: connect with session expiry, publish with content-type, subscribe with no-local, shared subscription, topic alias.
- [ ] All scenarios must pass without protocol errors.

---

### Issue #033 [MQTT5-COMPAT] — Interoperability test: v3 client against v5 broker

**Summary:**
Verify that a MQTT 3.1.1 client can connect to the v5-capable amqtt broker and exchange messages normally.

**Scope:**
- [ ] Existing v3 integration tests must pass against the updated broker unchanged.
- [ ] Add explicit cross-version test: v3 client publishes, v5 client subscribes (and vice-versa).

---

### Issue #034 [MQTT5-CORE] — Update $SYS plugin for MQTT 5.0

**Spec:** (amqtt-specific, not in MQTT spec)

**Summary:**
The `BrokerSysPlugin` publishes diagnostics to `$SYS/#`. Add v5-specific stats.

**Scope:**
- [ ] Add `$SYS/broker/clients/v5` — count of connected MQTT 5.0 clients.
- [ ] Add `$SYS/broker/version` — report protocol versions supported.

---

### Issue #035 [MQTT5-CORE] — Documentation: MQTT 5.0

**Summary:**
Create new documentation pages and update existing ones to cover MQTT 5.0 support. This issue lands after Phase 3 when the implementation is complete enough to document accurately.

**New files to create:**

1. **`docs/mqtt5.md`** — user-facing migration and feature guide. Sections:
   - *Opting in* — `mqtt_version: 5` in client config; protocol auto-detected on broker side.
   - *New broker config options* — `receive_maximum`, `topic_alias_maximum`, `maximum_packet_size`, shared subscription toggle; YAML example.
   - *New client config options* — all v5 keys with defaults; YAML example.
   - *publish() new parameters* — `content_type`, `response_topic`, `correlation_data`, `message_expiry_interval`, `user_properties`, `topic_alias`.
   - *subscribe() new parameters* — `no_local`, `retain_as_published`, `retain_handling`, `subscription_identifier`.
   - *Backwards compatibility guarantees* — v3 clients still work unchanged; `mqtt_version` defaults to 4.
   - *Example: request/response pattern* — full working code using `response_topic` + `correlation_data`.
   - *Example: shared subscriptions* — two consumers on `$share/workers/jobs/#`.

2. **`docs/references/mqtt5.md`** — API reference for `amqtt.mqtt5` public surface:
   ```md
   ## Properties
   ::: amqtt.mqtt5.properties.Properties

   ## ReasonCode
   ::: amqtt.mqtt5.reason_codes.ReasonCode

   ## AuthPacket
   ::: amqtt.mqtt5.auth.AuthPacket
   ```

**Existing files to update:**

- **`docs/quickstart.md`**: Change the broker description from "MQTT 3.1.1 compliant" to "MQTT 3.1.1 and 5.0 compliant". Add a one-paragraph "MQTT 5.0" section pointing to `mqtt5.md`.
- **`docs/references/broker_config.md`**: Add a `## MQTT 5.0 configuration` section documenting all new v5 broker config keys with types, defaults, and a complete YAML example.
- **`docs/references/client_config.md`**: Update the default YAML block to show v5 keys (commented out with defaults). Add `:::` autodoc directives for any new config dataclasses.
- **`docs/references/client.md`**: Update the subscriber and publisher examples to show v5 variants (`mqtt_version=5`, `content_type=`, `no_local=`). Existing v3 examples stay; v5 examples go in a `### MQTT 5.0` subsection.
- **`docs/references/common.md`**: Add a note under `ApplicationMessage` that `message.properties` is a `Properties | None` populated for v5 messages.
- **`docs/plugins/custom_plugins.md`**: Add `on_mqtt_auth` to the Broker events list with full signature and a note on the challenge-response flow.
- **`mkdocs.yml`** nav: add `MQTT 5.0: mqtt5.md` as a top-level nav entry and `References > MQTT 5.0 API: references/mqtt5.md`.

**Acceptance criteria:**
- [ ] `mkdocs build` completes with no warnings about missing pages or broken `:::` directives.
- [ ] `docs/mqtt5.md` includes working code examples for at least: v5 connect, v5 publish with `content_type`, v5 subscribe with `no_local`, and the request/response pattern.
- [ ] All `:::` directives in `docs/references/mqtt5.md` render non-empty content (requires docstrings in the mqtt5 classes).
- [ ] `docs/quickstart.md` no longer describes the broker as "MQTT 3.1.1 only".

---

### Issue #036 [MQTT5-CORE] — Conformance checklist against MQTT 5.0 spec Appendix B

**Spec:** Appendix B — Mandatory normative statements

**Summary:**
Appendix B of the spec lists every MUST/MUST NOT statement as a numbered checklist. Create a tracking document mapping each statement to the issue or code location that implements it, and identify any gaps.

**Scope:**
- [ ] Enumerate all ~200+ normative statements from Appendix B.
- [ ] For each: `implemented in issue #NNN / file:line` or `NOT YET IMPLEMENTED`.
- [ ] File follow-up issues for any gaps found.

---

## Issue Dependency Graph

```
#001 (Properties) ──────────────────────────────────────────────────────────┐
#002 (Reason Codes) ─────────────────────────────────────────────────────┐  │
#003 (Session fields) ─────────────────────────────────────────────┐    │  │
#003a (Config schema) ─────────────────────────────────────────────┤    │  │
#003b (Test infrastructure) ───────────────────────────────────────┤    │  │
                                                                    │    │  │
Phase 1 (all packet issues #004–#012) ──────────────────────── depend on ──┘
                                                                    │    │
Phase 2 (broker issues #013–#025) ─────────────────────────── depend on ──┘ (#003, #003a)
Phase 3 (client issues #026–#031) ─────────────────────────── depend on ── (#003, #003a)
                                                                    │
Phase 4 (#032–#036) ──────────────────────────────────────── depend on ── Phase 2 + 3
```

Minimum viable path for a first working demo:
`#001 → #002 → #003 → #004 → #005 → #006 → #013 → #014 → #026 → #027`

This gives you a broker and client that can connect, publish, and subscribe over MQTT 5.0 with basic properties support.
