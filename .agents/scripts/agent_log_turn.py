#!/usr/bin/env python3
"""
Agent turn logger.

Appends one JSON record per assistant turn to .agents/turn_log.jsonl.

The script is intentionally agent-neutral, but it understands the Claude Code
Stop-hook payload shape:

    {
      "session_id": "...",
      "cwd": "/path/to/repo",
      "transcript_path": "/path/to/transcript.jsonl"
    }

It reads the transcript, finds the latest assistant response and the preceding
real user prompt, captures token usage if present, and records issue metadata
from one of:

1. AGENT_ISSUE or CLAUDE_ISSUE
2. .agent-issue or .claude-issue in cwd or a parent directory
3. the current git branch name
4. an issue reference in the prompt text

Environment:
    AGENT_TURN_LOG=/path/to/turn_log.jsonl
    AGENT_ISSUE=123

Default log path:
    <git-root>/.agents/turn_log.jsonl, falling back to ~/.agents/turn_log.jsonl
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BRANCH_ISSUE_RE = re.compile(
    r"(?:^|[/_-])(?:issue|bug|feat|feature|fix|gh|#)?[/_-]?(\d{1,6})(?:$|[/_-])",
    re.IGNORECASE,
)
PROMPT_ISSUE_RE = re.compile(
    r"github\.com/[\w.-]+/[\w.-]+/issues/(\d+)"
    r"|(?:^|\s)#(\d{1,6})(?:\s|$|[.,;:!?])",
    re.IGNORECASE,
)


def current_git_root(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def default_log_path(cwd: Path) -> Path:
    if override := os.environ.get("AGENT_TURN_LOG"):
        return Path(override).expanduser()
    root = current_git_root(cwd)
    if root:
        return root / ".agents" / "turn_log.jsonl"
    return Path.home() / ".agents" / "turn_log.jsonl"


def current_git_branch(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode == 0:
        return result.stdout.strip() or None
    return None


def extract_text(content: Any) -> str:
    """Extract text from common transcript content shapes."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(str(block["text"]))
                elif "content" in block and isinstance(block["content"], str):
                    parts.append(block["content"])
        return "\n".join(parts)
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        if isinstance(content.get("content"), str):
            return content["content"]
    return ""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                entries.append(value)
    return entries


def message_of(entry: dict[str, Any]) -> dict[str, Any]:
    msg = entry.get("message")
    return msg if isinstance(msg, dict) else entry


def entry_role(entry: dict[str, Any]) -> str | None:
    if isinstance(entry.get("type"), str):
        # Claude Code transcript uses top-level type=user|assistant.
        return entry["type"]
    msg = entry.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("role"), str):
        return msg["role"]
    if isinstance(entry.get("role"), str):
        return entry["role"]
    return None


def is_real_user_entry(entry: dict[str, Any]) -> bool:
    if entry_role(entry) != "user":
        return False
    if entry.get("toolUseResult"):
        return False
    content = message_of(entry).get("content")
    if isinstance(content, list):
        has_text = any(isinstance(b, dict) and b.get("type") == "text" for b in content)
        all_tool = bool(content) and all(
            isinstance(b, dict) and b.get("type") in {"tool_result", "tool_use_result"}
            for b in content
        )
        return has_text and not all_tool
    return bool(extract_text(content).strip())


def assistant_message_id(entry: dict[str, Any]) -> str | None:
    msg = message_of(entry)
    mid = msg.get("id") or entry.get("id")
    return str(mid) if mid else None


def find_last_turn(entries: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Find the latest assistant entry and its preceding user prompt.

    Handles transcript streams that contain multiple snapshots of the same
    assistant message by using the last occurrence.
    """
    last_assistant: dict[str, Any] | None = None
    last_idx: int | None = None

    for i in range(len(entries) - 1, -1, -1):
        if entry_role(entries[i]) == "assistant":
            last_assistant = entries[i]
            last_idx = i
            break

    if last_assistant is None or last_idx is None:
        return None, None

    last_user = None
    for i in range(last_idx - 1, -1, -1):
        if is_real_user_entry(entries[i]):
            last_user = entries[i]
            break

    return last_user, last_assistant


def find_last_todos(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return todos from the most recent TodoWrite-like tool call, if present."""
    last_todos: list[dict[str, Any]] = []
    for entry in entries:
        if entry_role(entry) != "assistant":
            continue
        content = message_of(entry).get("content") or []
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            name = block.get("name") or block.get("tool_name")
            if name not in {"TodoWrite", "todo_write", "update_plan"}:
                continue
            payload = block.get("input") or block.get("arguments") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {}
            todos = payload.get("todos") if isinstance(payload, dict) else None
            if isinstance(todos, list):
                last_todos = [t for t in todos if isinstance(t, dict)]
    return last_todos


def find_issue_file(start: Path) -> Path | None:
    cur = start.resolve()
    while True:
        for name in (".agent-issue", ".claude-issue"):
            candidate = cur / name
            if candidate.is_file():
                return candidate
        if (cur / ".git").exists() or cur.parent == cur:
            return None
        cur = cur.parent


def detect_issue(cwd: Path, prompt_text: str | None) -> tuple[str | None, str | None]:
    for env_name in ("AGENT_ISSUE", "CLAUDE_ISSUE"):
        env_issue = os.environ.get(env_name, "").strip()
        if env_issue:
            return env_issue.lstrip("#"), f"env:{env_name}"

    issue_file = find_issue_file(cwd)
    if issue_file:
        try:
            value = issue_file.read_text(encoding="utf-8").strip()
        except OSError:
            value = ""
        if value:
            return value.lstrip("#"), f"file:{issue_file.name}"

    branch = current_git_branch(cwd)
    if branch:
        match = BRANCH_ISSUE_RE.search(branch)
        if match:
            return match.group(1), "branch"

    if prompt_text:
        match = PROMPT_ISSUE_RE.search(prompt_text)
        if match:
            return (match.group(1) or match.group(2)), "prompt"

    return None, None


def usage_from(entry: dict[str, Any]) -> dict[str, int | None]:
    msg = message_of(entry)
    usage = msg.get("usage") or entry.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    cache_creation = usage.get("cache_creation_input_tokens")
    cache_read = usage.get("cache_read_input_tokens")

    total_input = (
        (input_tokens or 0)
        + (cache_creation or 0)
        + (cache_read or 0)
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation,
        "cache_read_input_tokens": cache_read,
        "total_input_tokens": total_input,
    }


def build_record(payload: dict[str, Any]) -> dict[str, Any] | None:
    cwd = Path(payload.get("cwd") or os.getcwd()).expanduser()
    transcript_path_raw = payload.get("transcript_path")

    if not transcript_path_raw:
        # Direct-record mode for non-hook callers.
        if payload.get("prompt") or payload.get("response"):
            prompt_text = str(payload.get("prompt") or "")
            issue, issue_source = detect_issue(cwd, prompt_text)
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": payload.get("session_id") or "manual",
                "cwd": str(cwd),
                "branch": current_git_branch(cwd),
                "issue": issue,
                "issue_source": issue_source,
                "transcript_path": None,
                "message_id": payload.get("message_id"),
                "model": payload.get("model"),
                "prompt": prompt_text,
                "response": str(payload.get("response") or ""),
                "usage": usage_from(payload),
                "todos": payload.get("todos") if isinstance(payload.get("todos"), list) else [],
            }
        return None

    transcript_path = Path(os.path.expanduser(str(transcript_path_raw)))
    if not transcript_path.is_file():
        parent = transcript_path.parent
        if not parent.is_dir():
            return None
        candidates = sorted(
            parent.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return None
        transcript_path = candidates[0]

    entries = load_jsonl(transcript_path)
    user_entry, assistant_entry = find_last_turn(entries)
    if assistant_entry is None:
        return None

    assistant_msg = message_of(assistant_entry)
    user_msg = message_of(user_entry or {})
    prompt_text = extract_text(user_msg.get("content")) if user_entry else None
    response_text = extract_text(assistant_msg.get("content"))
    issue, issue_source = detect_issue(cwd, prompt_text)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": payload.get("session_id") or transcript_path.stem,
        "cwd": str(cwd),
        "branch": current_git_branch(cwd),
        "issue": issue,
        "issue_source": issue_source,
        "transcript_path": str(transcript_path),
        "message_id": assistant_message_id(assistant_entry),
        "model": assistant_msg.get("model") or assistant_entry.get("model"),
        "prompt": prompt_text,
        "response": response_text,
        "usage": usage_from(assistant_entry),
        "todos": find_last_todos(entries),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict):
        return 0

    record = build_record(payload)
    if record is None:
        return 0

    cwd = Path(record.get("cwd") or os.getcwd())
    log_path = default_log_path(cwd)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
