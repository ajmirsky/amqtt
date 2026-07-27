## Summary

- ...

## Compatibility

No MQTT 3 behavior changes. This is additive MQTT 5 implementation work.

<!--
Use explicit bullets when the impact needs more detail:

- MQTT 3 behavior: unchanged
- Public API impact: none
- Config impact: none
- Wire protocol impact: additive MQTT 5 support
-->

## Review notes

This branch is stacked locally on `<previous-branch>`, but this PR targets `mqtt5/main` to follow the normal contributor workflow.

Incremental diff against the previous PR branch:
https://github.com/ajmirsky/amqtt/compare/<previous-branch>...<current-branch>

<!--
For the first branch in the stack, use:

This is the first branch in the MQTT 5 PR stack targeting `mqtt5/main`.

Incremental diff against `mqtt5/main`:
https://github.com/ajmirsky/amqtt/compare/mqtt5/main...<current-branch>
-->

## Verification

- `uv run ...`

Closes #NNN
