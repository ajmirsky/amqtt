# HCME Task List

Source: https://github.com/the-hcma/my-tracks/issues/1269

Goal: track upstream amqtt work that would let `the-hcma/my-tracks` delete or simplify MQTT broker accommodations around TLS, persistent sessions, `$SYS`, diagnostics, and logging.

## High Priority

- [ ] Add configurable mTLS client-certificate policy and CRL support.
  - Affected areas: `amqtt/contexts.py`, `amqtt/broker.py`, docs, config examples.
  - Add listener options for requiring client certificates, selecting `ssl.VerifyMode`, and loading CRL material.
  - Preserve the current default behavior for existing TLS listeners unless the new options are set.
  - Cover `CERT_OPTIONAL`, `CERT_REQUIRED`, missing-file errors, and CRL verify flags in tests.

- [ ] Refresh live TLS identity when reusing a persistent session.
  - Affected areas: `amqtt/broker.py`, `amqtt/mqtt/protocol/broker_handler.py`, `amqtt/session.py`.
  - When a client reconnects with `clean_session=False` and an existing cached session is reused, copy the current connection's `ssl_object` onto the reused session.
  - Clear stale TLS state when the reconnect is non-TLS.
  - Add a regression test proving auth plugins see the new peer certificate after reconnect.

- [ ] Support in-memory or externally supplied TLS material.
  - Affected areas: listener config, SSL context creation, broker lifecycle.
  - Decide the public API: PEM bytes, prebuilt `ssl.SSLContext`, or both.
  - Avoid requiring applications to write cert/key/CA/CRL bytes to temporary files.
  - Add tests for path-based config and the new in-memory/context-based config.

- [ ] Add a listener-safe TLS reload API.
  - Affected areas: `Broker`, server/listener lifecycle, docs.
  - Reload listener certificates and verification material without forcing applications to tear down and recreate the entire broker.
  - Define behavior for active connections: keep existing sockets, drain/restart listener sockets, or explicit per-listener restart.
  - Add lifecycle tests that prove new connections use the updated TLS context.

- [ ] Make QoS 1 PUBACK behavior configurable and less noisy.
  - Affected areas: `amqtt/mqtt/protocol/handler.py`, broker config, tests.
  - Replace the hard-coded 5 second PUBACK timeout with a documented config option.
  - Decide whether timeout should raise, warn and drop, retry later, or be policy-controlled.
  - Ensure late PUBACKs and mobile/IoT disconnect patterns do not produce unhandled task noise.

- [ ] Default `$SYS` broadcasts to QoS 0 or make their QoS configurable.
  - Affected areas: `amqtt/plugins/sys/broker.py`, `BrokerContext.broadcast_message`, tests.
  - Pass explicit QoS for `$SYS` messages instead of inheriting subscriber QoS by default.
  - Add plugin config for `$SYS` QoS if defaulting to QoS 0 is too broad a compatibility change.
  - Test retained `$SYS` values and periodic broadcasts with the selected QoS behavior.

## Medium Priority

- [ ] Improve unsupported MQTT protocol-level handling.
  - Affected areas: `amqtt/mqtt/protocol/broker_handler.py`, `amqtt/mqtt/connect.py`, tests.
  - Preferred: support MQTT 3.1 clients using `MQIsdp` and protocol level 3 where feasible.
  - Fallback: keep rejecting level 3, but emit clearer logs and CONNACK-facing diagnostics that say MQTT 3.1.1 protocol level 4 is required.
  - Add protocol parsing and rejection tests for level 3 and malformed CONNECT packets.

- [ ] Clarify listener connection-count log wording.
  - Affected area: `amqtt/broker.py`.
  - Replace the ambiguous `connections acquired` wording with `connections in use` or separate acquire/release messages.
  - Add a focused logging regression test or update existing caplog expectations.

- [ ] Expose inbound SNI for server-side diagnostics.
  - Affected areas: SSL context creation, adapters/session metadata, docs.
  - Capture inbound SNI via `SSLContext.set_servername_callback` and expose it on the session or namespaced session attributes.
  - Make the behavior work for TCP TLS listeners and document any websocket limitations.
  - Add tests for SNI capture where the test transport stack supports it.

- [ ] Improve early post-TLS disconnect diagnostics.
  - Affected areas: `amqtt/broker.py`, adapters, logging tests.
  - When TLS negotiation succeeds but the client disconnects before sending MQTT data, log a concise diagnostic that includes peer address and any captured SNI.
  - Avoid logging expected client disconnects as internal broker errors.

## Cleanup And Coordination

- [ ] Split the work into small upstream PRs in roughly this order: mTLS/CRL, session TLS refresh, `$SYS` QoS, PUBACK timeout, logging wording, SNI/diagnostics, TLS reload.
- [ ] For each merged change, identify the matching my-tracks accommodation that can be deleted.
- [ ] Update amqtt documentation and sample broker config for every new public setting.
- [ ] Add changelog/release notes that call out compatibility impact and migration guidance.
- [ ] After the first release containing these fixes, ask my-tracks to verify which workarounds can be removed.
