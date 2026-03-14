"""Work log parsing and writing.

Handles the append-only work.log files:
  - Parsing log entries from existing files
  - Appending new entries atomically
  - Querying entries by task ID, event type, or time range
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from clawopc_core.models import WorklogEntry, WorklogEvent, WorkspaceConfig

if TYPE_CHECKING:
    from pathlib import Path

# Regex pattern for a work.log line:
# [2025-01-15T10:00:00Z] [task-20250115-001] [received] detail text
_LOG_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]\s+"
    r"\[([^\]]+)\]\s+"
    r"\[([^\]]+)\]\s*"
    r"(.*)$"
)


def parse_worklog(path: Path) -> list[WorklogEntry]:
    """Parse all entries from a work.log file.

    Args:
        path: Path to the work.log file.

    Returns:
        List of parsed WorklogEntry instances, in file order.
    """
    entries: list[WorklogEntry] = []
    if not path.exists():
        return entries

    for line in path.read_text(encoding="utf-8").splitlines():
        entry = _parse_line(line)
        if entry:
            entries.append(entry)

    return entries


def parse_worklog_tail(path: Path, n: int = 20) -> list[WorklogEntry]:
    """Parse the last N entries from a work.log file.

    More efficient than parsing the whole file for large logs.
    """
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    tail_lines = lines[-n:] if len(lines) > n else lines

    entries: list[WorklogEntry] = []
    for line in tail_lines:
        entry = _parse_line(line)
        if entry:
            entries.append(entry)

    return entries


def append_worklog(
    path: Path,
    task_id: str,
    event: WorklogEvent,
    detail: str = "",
) -> WorklogEntry:
    """Append a new entry to a work.log file.

    Uses append mode for atomicity. The entry is immediately flushed.

    Args:
        path: Path to the work.log file.
        task_id: Task ID or 'system' for system events.
        event: The event type.
        detail: Optional detail text.

    Returns:
        The created WorklogEntry.
    """
    now = datetime.now(tz=UTC)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    line = f"[{timestamp_str}] [{task_id}] [{event.value}] {detail}\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()

    return WorklogEntry(
        timestamp=now,
        task_id=task_id,
        event=event,
        detail=detail,
    )


def filter_by_task(entries: list[WorklogEntry], task_id: str) -> list[WorklogEntry]:
    """Filter log entries by task ID."""
    return [e for e in entries if e.task_id == task_id]


def filter_by_event(entries: list[WorklogEntry], event: WorklogEvent) -> list[WorklogEntry]:
    """Filter log entries by event type."""
    return [e for e in entries if e.event == event]


def get_latest_entry(path: Path) -> WorklogEntry | None:
    """Get the most recent entry from a work.log file."""
    entries = parse_worklog_tail(path, n=1)
    return entries[-1] if entries else None


def get_all_worklogs(config: WorkspaceConfig) -> dict[str, list[WorklogEntry]]:
    """Get work.log entries for all roles.

    Returns:
        Dict mapping role name to list of WorklogEntry.
    """
    result: dict[str, list[WorklogEntry]] = {}

    if not config.workspace_root.exists():
        return result

    for ws_dir in config.workspace_root.iterdir():
        if not ws_dir.is_dir() or ws_dir.name.startswith("."):
            continue

        log_path = ws_dir / "work.log"
        if log_path.exists():
            result[ws_dir.name] = parse_worklog(log_path)

    return result


# ─── Internal ────────────────────────────────────────────────────────


def _parse_line(line: str) -> WorklogEntry | None:
    """Parse a single work.log line into a WorklogEntry."""
    line = line.strip()
    if not line:
        return None

    match = _LOG_PATTERN.match(line)
    if not match:
        return None

    timestamp_str, task_id, event_str, detail = match.groups()

    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        event = WorklogEvent(event_str)
    except (ValueError, KeyError):
        return None

    return WorklogEntry(
        timestamp=timestamp,
        task_id=task_id,
        event=event,
        detail=detail.strip(),
    )
