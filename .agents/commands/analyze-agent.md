---
description: Write a Session Log markdown file for this agent session and fill in the interpretive sections.
argument-hint: "[slug]"
---

Generate a Session Log for the current coding-agent session.

The user may have passed an optional slug as an argument: `$ARGUMENTS`.

## Step 1 — Run the analyzer

If `$ARGUMENTS` is non-empty, run:

```bash
python3 .agents/scripts/agent_analyze_session.py --slug "$ARGUMENTS"
```

If `$ARGUMENTS` is empty, run:

```bash
python3 .agents/scripts/agent_analyze_session.py
```

The script writes a file to `.agents/session-logs/` named `<YYYY-MM-DD>_<label><letter>.md`, such as `2026-05-08_0034a.md` or `2026-05-08_mqtt5-propsa.md`. Note the path from stdout.

## Step 2 — Fill in the agent placeholders

The generated file contains `<!-- AGENT: ... -->` comment blocks that need replacing.

1. **Summary of what was implemented**  
   Replace the comment with 3–6 sentences describing what the session actually accomplished. Base this on the numbered prompts already listed in the file and on what happened in the session. Focus on outcomes: features, fixes, refactors, files touched, or exploration.

2. **Status checklist**  
   Replace or update the checklist with `- [x]` / `- [ ]` items. If the session is linked to an issue in `ISSUES.md`, use that issue's acceptance criteria. Tick boxes honestly based on what was actually completed.

Do not modify the token usage section; it is computed mechanically.

## Step 3 — Archive the turn log

After the session log is written and edited, archive the current turn log so future sessions start fresh:

```bash
python3 .agents/scripts/agent_analyze_session.py --archive --output /tmp/agent-session-archive-check.md
rm -f /tmp/agent-session-archive-check.md
```

Or move it manually:

```bash
mkdir -p .agents
n=$(find .agents -name 'turn_log.*.jsonl' | sed -E 's/.*turn_log\.([0-9]+)\.jsonl/\1/' | sort -n | tail -1)
n=${n:-0}
next=$(printf "%04d" "$((10#$n + 1))")
git mv .agents/turn_log.jsonl ".agents/turn_log.${next}.jsonl" 2>/dev/null || mv .agents/turn_log.jsonl ".agents/turn_log.${next}.jsonl"
```

## Step 4 — Confirm

Tell the user the session log file path, the issue or slug it is linked to, whether the interpretive sections were filled in, and the archive path for the turn log.

Guardrails: do not fabricate. If the session was exploratory and made no code changes, say so. If no reasonable acceptance criteria can be inferred, write `_No acceptance criteria available._`.
