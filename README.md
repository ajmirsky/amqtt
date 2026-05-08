# amqtt Agent Support Files

This package adds coding-agent support without changing your project README.

Recommended repo layout after installation:

```text
README.md                    # existing human-facing project README
AGENTS.md                    # root-level coding-agent guidance
ISSUES.md                    # MQTT 5.0 work breakdown
CONVENTIONS.md               # coding/style/testing rules
.agents/
  scripts/
    agent_log_turn.py
    agent_analyze_session.py
  commands/
    analyze-agent.md
  turn_log.jsonl             # generated; usually ignored
  session-logs/              # generated; track or ignore by preference
.codex/
  config.toml                # optional, local Codex hook config
.claude/
  settings.json              # optional, local Claude Code hook config
```

## Install

From inside this unpacked package:

```bash
./install.sh /path/to/amqtt
```

Or copy manually from the repo root:

```bash
cp AGENTS.md /path/to/amqtt/AGENTS.md
mkdir -p /path/to/amqtt/.agents/scripts /path/to/amqtt/.agents/commands
cp .agents/scripts/*.py /path/to/amqtt/.agents/scripts/
cp .agents/commands/analyze-agent.md /path/to/amqtt/.agents/commands/
chmod +x /path/to/amqtt/.agents/scripts/*.py
```

## Codex hook

This package includes both `.codex/config.toml` and `.codex/config.example.toml`. Copy or merge the config into your repo as needed:

```toml
[features]
hooks = true

[[hooks.Stop]]

[[hooks.Stop.hooks]]
type = "command"
command = 'ROOT=$(git rev-parse --show-toplevel) && AGENT_TURN_LOG="$ROOT/.agents/turn_log.jsonl" python3 "$ROOT/.agents/scripts/agent_log_turn.py"'
timeout = 30
statusMessage = "Logging Codex turn"
```

Codex project-local config must be trusted before hooks load.

## Claude Code hook

This package includes both `.claude/settings.json` and `.claude/settings.example.json`. Copy or merge the `Stop` hook into your existing Claude Code settings.

## Generate a session log

```bash
python3 .agents/scripts/agent_analyze_session.py
```

With a slug:

```bash
python3 .agents/scripts/agent_analyze_session.py --slug mqtt5-properties
```

Archive the current turn log after generating a report:

```bash
python3 .agents/scripts/agent_analyze_session.py --archive
```

The analyzer writes session logs to `.agents/session-logs/` and uses `ISSUES.md` when available to fill issue titles and acceptance criteria.

## Recommended .gitignore

Append `.gitignore.example` to your repo `.gitignore`, or choose whether you want generated session logs tracked.
