"""Tests for worklog parsing and writing."""

from pathlib import Path

import pytest

from clawopc_core.models import WorklogEvent
from clawopc_core.worklog import (
    append_worklog,
    filter_by_event,
    filter_by_task,
    get_latest_entry,
    parse_worklog,
)


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    """Create a temporary work.log with sample entries."""
    log = tmp_path / "work.log"
    log.write_text(
        "[2025-01-15T10:00:00Z] [task-20250115-001] [received] 任务已接收\n"
        "[2025-01-15T10:00:05Z] [task-20250115-001] [started] 开始处理\n"
        "[2025-01-15T10:05:00Z] [task-20250115-001] [working] 分析需求\n"
        "[2025-01-15T10:10:00Z] [task-20250115-001] [done] 产出已完成\n"
        "[2025-01-15T10:10:01Z] [task-20250115-001] [awaiting_boss] 等待 Boss 决策\n"
    )
    return log


def test_parse_worklog(log_file: Path):
    entries = parse_worklog(log_file)
    assert len(entries) == 5
    assert entries[0].event == WorklogEvent.RECEIVED
    assert entries[4].event == WorklogEvent.AWAITING_BOSS


def test_parse_empty_worklog(tmp_path: Path):
    log = tmp_path / "work.log"
    log.touch()
    entries = parse_worklog(log)
    assert len(entries) == 0


def test_parse_nonexistent_worklog(tmp_path: Path):
    entries = parse_worklog(tmp_path / "nonexistent.log")
    assert len(entries) == 0


def test_append_worklog(tmp_path: Path):
    log = tmp_path / "work.log"
    log.touch()

    entry = append_worklog(log, "task-20250115-001", WorklogEvent.RECEIVED, "Test entry")
    assert entry.task_id == "task-20250115-001"
    assert entry.event == WorklogEvent.RECEIVED

    entries = parse_worklog(log)
    assert len(entries) == 1


def test_filter_by_task(log_file: Path):
    entries = parse_worklog(log_file)
    filtered = filter_by_task(entries, "task-20250115-001")
    assert len(filtered) == 5


def test_filter_by_event(log_file: Path):
    entries = parse_worklog(log_file)
    filtered = filter_by_event(entries, WorklogEvent.WORKING)
    assert len(filtered) == 1


def test_get_latest_entry(log_file: Path):
    entry = get_latest_entry(log_file)
    assert entry is not None
    assert entry.event == WorklogEvent.AWAITING_BOSS
