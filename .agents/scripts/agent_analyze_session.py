#!/usr/bin/env python3
"""
Generate a session log from .agents/turn_log.jsonl.

The logger records mechanical data only: prompts, responses, issue references,
branch, and token usage. This analyzer turns those records into a markdown
session log with placeholders for an agent/human to fill in the interpretive
sections.

Usage:
    python3 .agents/scripts/agent_analyze_session.py
    python3 .agents/scripts/agent_analyze_session.py --slug mqtt5-props
    python3 .agents/scripts/agent_analyze_session.py --session <session-id>
    python3 .agents/scripts/agent_analyze_session.py --archive
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ISSUES_MD_RE = re.compile(
    r"^###\s+Issue\s+#(\d+)\s+.*?—\s+(.+)$",
    re.MULTILINE,
)
SLUG_CLEAN_RE = re.compile(r"[^\w\s.-]+")
SLUG_COLLAPSE_RE = re.compile(r"[\s_-]+")


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


def default_paths(cwd: Path) -> tuple[Path, Path]:
    root = current_git_root(cwd) or cwd
    if override := os.environ.get("AGENT_TURN_LOG"):
        log_path = Path(override).expanduser()
        logs_dir = log_path.parent / "session-logs"
    else:
        log_path = root / ".agents" / "turn_log.jsonl"
        logs_dir = root / ".agents" / "session-logs"
    return log_path, logs_dir


def normalize_slug(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    raw = SLUG_CLEAN_RE.sub("", raw)
    raw = SLUG_COLLAPSE_RE.sub("-", raw)
    return raw.strip("-.").lower()[:80]


def fmt_timestamp(ts: str | None) -> str:
    try:
        dt = datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return ts or "—"


def fmt_num(value: Any) -> str:
    return "—" if value is None else f"{int(value):,}"


def load_turns(log_path: Path, session_id: str | None = None) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []

    turns: list[dict[str, Any]] = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if session_id and rec.get("session_id") != session_id:
                continue
            turns.append(rec)

    if session_id:
        return turns

    # Default to the most recent session_id group, preserving original order.
    for rec in reversed(turns):
        sid = rec.get("session_id")
        if sid:
            return [t for t in turns if t.get("session_id") == sid]
    return turns


def parse_issues_md(path: Path) -> dict[int, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    return {int(m.group(1)): m.group(2).strip() for m in ISSUES_MD_RE.finditer(text)}


def issue_acceptance_criteria(path: Path, issue: str | None) -> list[str]:
    if not issue or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    m = re.search(
        rf"^###\s+Issue\s+#{re.escape(str(issue))}\b.*?(?=^###\s+Issue\s+#|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        return []
    block = m.group(0)
    ac = re.search(
        r"\*\*Acceptance criteria:\*\*\s*\n(?P<body>.*?)(?=\n---|\n## |\n### |\Z)",
        block,
        re.DOTALL,
    )
    if not ac:
        return []
    criteria: list[str] = []
    for line in ac.group("body").splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            criteria.append(stripped[2:].strip())
    return criteria


def build_output_path(logs_dir: Path, turns: list[dict[str, Any]], slug: str | None) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    issue = next((t.get("issue") for t in turns if t.get("issue")), None)
    session_id = next((t.get("session_id") for t in turns if t.get("session_id")), "session")

    if slug:
        stem_part = normalize_slug(slug)
    elif issue:
        try:
            stem_part = f"{int(issue):04d}"
        except (TypeError, ValueError):
            stem_part = f"issue-{issue}"
    else:
        stem_part = str(session_id)[:8]

    logs_dir.mkdir(parents=True, exist_ok=True)
    suffix_ord = ord("a")
    out_path = logs_dir / f"{today}_{stem_part}{chr(suffix_ord)}.md"
    while out_path.exists():
        suffix_ord += 1
        out_path = logs_dir / f"{today}_{stem_part}{chr(suffix_ord)}.md"
    return out_path


def build_report(turns: list[dict[str, Any]], cwd: Path, slug: str | None) -> str:
    issue = next((t.get("issue") for t in turns if t.get("issue")), None)
    branch = next((t.get("branch") for t in turns if t.get("branch")), current_git_branch(cwd))
    session_id = next((t.get("session_id") for t in turns if t.get("session_id")), "unknown")
    last_ts = turns[-1].get("timestamp") if turns else None

    issues_path = cwd / "ISSUES.md"
    issues_index = parse_issues_md(issues_path)
    issue_title = issues_index.get(int(issue)) if issue and str(issue).isdigit() else None
    criteria = issue_acceptance_criteria(issues_path, str(issue) if issue else None)

    if slug:
        header_ref = normalize_slug(slug)
    elif issue_title:
        header_ref = f"Issue #{issue} — {issue_title}"
    elif issue:
        header_ref = f"Issue #{issue}"
    else:
        header_ref = f"Session {str(session_id)[:8]}"

    lines: list[str] = []
    lines.append(f"# Session Log — {header_ref}")
    if issue_title:
        lines.append(f"**Issue:** #{issue} — {issue_title}")
    elif issue:
        lines.append(f"**Issue:** #{issue} — title unknown")
    else:
        lines.append("**Issue:** not linked")
    lines.append(f"**Date:** {fmt_timestamp(last_ts)}")
    lines.append(f"**Branch:** `{branch}`" if branch else "**Branch:** _unknown_")
    lines.append(f"**Session:** `{session_id}`")
    if slug and issue:
        lines.append(f"**Label override:** `{normalize_slug(slug)}` (detected issue was #{issue})")
    lines.append("")

    lines.append("## Prompts given this session")
    lines.append("")
    if not turns:
        lines.append("_No prompts recorded for this session._")
    else:
        for i, turn in enumerate(turns, 1):
            prompt = (turn.get("prompt") or "").strip()
            if not prompt:
                lines.append(f"{i}. _(empty prompt)_")
                continue
            prompt_lines = prompt.splitlines()
            lines.append(f"{i}. {prompt_lines[0]}")
            for extra in prompt_lines[1:]:
                lines.append(f"   {extra}")
    lines.append("")

    final_todos = next((t.get("todos") for t in reversed(turns) if t.get("todos")), [])
    if final_todos:
        lines.append("## Tasks")
        lines.append("")
        for todo in final_todos:
            status = str(todo.get("status", "pending"))
            content = str(todo.get("content", ""))
            box = "x" if status in {"completed", "done"} else " "
            lines.append(f"- [{box}] {content}")
        lines.append("")

    lines.append("## Summary of what was implemented")
    lines.append("")
    lines.append(
        "<!-- AGENT: replace this with 3-6 sentences describing what was actually "
        "implemented or explored. Base it on the prompts above and the session "
        "context. Do not invent work that was not done. -->"
    )
    lines.append("")

    lines.append("## Status")
    lines.append("")
    if criteria:
        for item in criteria:
            lines.append(f"- [ ] {item}")
        lines.append("")
        lines.append(
            "<!-- AGENT: mark completed criteria with [x] only when they were actually completed. -->"
        )
    else:
        lines.append(
            "<!-- AGENT: add 2-5 honest checklist items, or write "
            "`_No acceptance criteria available._` if none can be inferred. -->"
        )
    lines.append("")

    total_in = sum(((t.get("usage") or {}).get("input_tokens") or 0) for t in turns)
    total_out = sum(((t.get("usage") or {}).get("output_tokens") or 0) for t in turns)
    total_cc = sum(((t.get("usage") or {}).get("cache_creation_input_tokens") or 0) for t in turns)
    total_cr = sum(((t.get("usage") or {}).get("cache_read_input_tokens") or 0) for t in turns)
    grand = total_in + total_out + total_cc + total_cr

    lines.append("## Token usage")
    lines.append("")
    lines.append(f"**Turns recorded:** {len(turns)}")
    lines.append("")
    lines.append("| Category | Tokens |")
    lines.append("|---|--:|")
    lines.append(f"| Input (fresh) | {fmt_num(total_in)} |")
    lines.append(f"| Cache creation | {fmt_num(total_cc)} |")
    lines.append(f"| Cache read | {fmt_num(total_cr)} |")
    lines.append(f"| Output | {fmt_num(total_out)} |")
    lines.append(f"| **Grand total** | **{fmt_num(grand)}** |")
    lines.append("")

    if turns:
        lines.append("<details>")
        lines.append("<summary>Per-turn token breakdown</summary>")
        lines.append("")
        lines.append("| # | Prompt (first line) | Input | Cache create | Cache read | Output |")
        lines.append("|--:|---|--:|--:|--:|--:|")
        for i, turn in enumerate(turns, 1):
            usage = turn.get("usage") or {}
            prompt = (turn.get("prompt") or "").strip().splitlines()
            first_line = prompt[0] if prompt else "(empty)"
            if len(first_line) > 60:
                first_line = first_line[:57] + "..."
            first_line = first_line.replace("|", "\\|")
            lines.append(
                f"| {i} | {first_line} | "
                f"{fmt_num(usage.get('input_tokens'))} | "
                f"{fmt_num(usage.get('cache_creation_input_tokens'))} | "
                f"{fmt_num(usage.get('cache_read_input_tokens'))} | "
                f"{fmt_num(usage.get('output_tokens'))} |"
            )
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines)


def archive_turn_log(log_path: Path) -> Path | None:
    if not log_path.exists():
        return None
    existing = glob.glob(str(log_path.with_name("turn_log.*.jsonl")))
    nums: list[int] = []
    for filename in existing:
        parts = Path(filename).name.split(".")
        if len(parts) >= 3:
            try:
                nums.append(int(parts[1]))
            except ValueError:
                pass
    dest = log_path.with_name(f"turn_log.{max(nums, default=0) + 1:04d}.jsonl")

    try:
        result = subprocess.run(["git", "mv", str(log_path), str(dest)], capture_output=True, text=True)
        if result.returncode != 0:
            log_path.rename(dest)
    except (FileNotFoundError, OSError):
        log_path.rename(dest)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Override the session label and filename stem")
    parser.add_argument("--session", help="Analyze a specific session id")
    parser.add_argument("--cwd", help="Repository root / working directory")
    parser.add_argument("--output", help="Write the report to a specific path")
    parser.add_argument("--archive", action="store_true", help="Archive turn_log.jsonl after writing the report")
    args = parser.parse_args()

    cwd = Path(args.cwd).expanduser() if args.cwd else Path.cwd()
    root = current_git_root(cwd) or cwd
    log_path, logs_dir = default_paths(root)
    turns = load_turns(log_path, args.session)

    if args.output:
        out_path = Path(args.output).expanduser()
    else:
        out_path = build_output_path(logs_dir, turns, args.slug)

    report = build_report(turns, root, args.slug)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path} ({len(turns)} turns)")

    if args.archive:
        archived = archive_turn_log(log_path)
        if archived:
            print(f"Archived turn log to {archived}")
        else:
            print("No turn log found; archive skipped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
