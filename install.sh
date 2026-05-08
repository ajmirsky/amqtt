#!/usr/bin/env bash
set -euo pipefail

DEST="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
SRC="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$DEST/.agents/scripts" "$DEST/.agents/commands" "$DEST/.codex" "$DEST/.claude"

if [[ -f "$DEST/AGENTS.md" ]]; then
  echo "AGENTS.md already exists at $DEST/AGENTS.md; leaving it unchanged."
else
  cp "$SRC/AGENTS.md" "$DEST/AGENTS.md"
  echo "Installed AGENTS.md"
fi

cp "$SRC/.agents/scripts/agent_log_turn.py" "$DEST/.agents/scripts/agent_log_turn.py"
cp "$SRC/.agents/scripts/agent_analyze_session.py" "$DEST/.agents/scripts/agent_analyze_session.py"
cp "$SRC/.agents/commands/analyze-agent.md" "$DEST/.agents/commands/analyze-agent.md"
chmod +x "$DEST/.agents/scripts/agent_log_turn.py" "$DEST/.agents/scripts/agent_analyze_session.py"

cp "$SRC/.codex/config.example.toml" "$DEST/.codex/config.example.toml"
if [[ -f "$DEST/.codex/config.toml" ]]; then
  echo ".codex/config.toml already exists; leaving it unchanged. See .codex/config.example.toml."
else
  cp "$SRC/.codex/config.toml" "$DEST/.codex/config.toml"
  echo "Installed .codex/config.toml"
fi
cp "$SRC/.claude/settings.example.json" "$DEST/.claude/settings.example.json"
if [[ -f "$DEST/.claude/settings.json" ]]; then
  echo ".claude/settings.json already exists; leaving it unchanged. See .claude/settings.example.json."
else
  cp "$SRC/.claude/settings.json" "$DEST/.claude/settings.json"
  echo "Installed .claude/settings.json"
fi
cp "$SRC/.gitignore.example" "$DEST/.agents/gitignore.example"

echo "Installed agent support files under $DEST/.agents"
echo "Codex example:  $DEST/.codex/config.example.toml"
echo "Claude example: $DEST/.claude/settings.example.json"
echo "Review $DEST/.agents/gitignore.example for generated log ignore rules."
