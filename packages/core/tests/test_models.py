"""Tests for ClawOPC core data models."""

from datetime import UTC, datetime

from clawopc_core.models import (
    PipelineStep,
    Position,
    PositionStatus,
    TaskMeta,
    TaskStatus,
    WorklogEntry,
    WorklogEvent,
    WorkspaceConfig,
)


def test_task_status_enum():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.PROCESSING == "processing"
    assert TaskStatus.AWAITING_BOSS == "awaiting_boss"
    assert TaskStatus.COMPLETE == "complete"


def test_pipeline_step():
    step = PipelineStep(step=0, role="developer", instruction="Write code")
    assert step.step == 0
    assert step.role == "developer"
    assert step.timeout is None


def test_task_meta():
    meta = TaskMeta(
        id="task-20250115-001",
        title="Test Task",
        created_at=datetime(2025, 1, 15, 9, 0, tzinfo=UTC),
        pipeline=[PipelineStep(step=0, role="developer", instruction="Do work")],
        current_role="developer",
    )
    assert meta.status == TaskStatus.PENDING
    assert meta.pipeline_cursor == 0
    assert len(meta.decisions) == 0


def test_workspace_config():
    config = WorkspaceConfig()
    assert config.console_dir.name == ".console"
    assert config.positions_dir.name == "positions"
    assert config.roles_dir.name == "roles"


def test_position():
    pos = Position(role="developer", status=PositionStatus.VACANT)
    assert pos.agent_id is None
    assert pos.occupied_at is None


def test_worklog_entry():
    entry = WorklogEntry(
        timestamp=datetime(2025, 1, 15, 10, 0, tzinfo=UTC),
        task_id="task-20250115-001",
        event=WorklogEvent.RECEIVED,
        detail="Task received",
    )
    assert entry.event == WorklogEvent.RECEIVED
