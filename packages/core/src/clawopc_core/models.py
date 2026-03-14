"""Pydantic data models for ClawOPC.

All domain entities are defined here as the single source of truth
for data validation and serialization.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Pydantic needs this at runtime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

# ─── Enums ───────────────────────────────────────────────────────────


class TaskStatus(StrEnum):
    """Task lifecycle status, determined by the directory the task file resides in."""

    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_BOSS = "awaiting_boss"
    COMPLETE = "complete"


class PositionStatus(StrEnum):
    """Position status — whether a role slot is filled."""

    VACANT = "vacant"
    OCCUPIED = "occupied"


class AgentState(StrEnum):
    """Real-time state of an agent as observed by the Console."""

    WORKING = "working"
    IDLE = "idle"
    AWAITING_DECISION = "awaiting_decision"
    OFFLINE = "offline"


class WorklogEvent(StrEnum):
    """Event types that can appear in work.log."""

    # Task lifecycle
    RECEIVED = "received"
    STARTED = "started"
    WORKING = "working"
    DONE = "done"
    AWAITING_BOSS = "awaiting_boss"
    FORWARDED = "forwarded"
    REWORK = "rework"
    COMPLETE = "complete"

    # System
    ONLINE = "online"
    OFFLINE = "offline"
    TIMEOUT = "timeout"
    ERROR = "error"


class DecisionAction(StrEnum):
    """Boss decision actions."""

    FORWARD = "forward"
    REWORK = "rework"
    COMPLETE = "complete"


# ─── Pipeline ────────────────────────────────────────────────────────


class PipelineStep(BaseModel):
    """A single step in a task's pipeline."""

    step: int
    role: str
    instruction: str
    timeout: int | None = None  # seconds, None means no timeout


class OutputRecord(BaseModel):
    """Record of an output file produced at a pipeline step."""

    step: int
    role: str
    file: str
    completed_at: datetime | None = None


class Decision(BaseModel):
    """A boss decision record."""

    at: datetime
    step: int
    role: str
    action: DecisionAction
    comment: str = ""


class ReworkNote(BaseModel):
    """A rework note from the boss."""

    at: datetime
    step: int
    role: str
    note: str


# ─── Task ────────────────────────────────────────────────────────────


class TaskMeta(BaseModel):
    """YAML front-matter metadata of a task.md file."""

    id: str
    title: str
    created_at: datetime
    created_by: str = "boss"
    status: TaskStatus = TaskStatus.PENDING

    pipeline: list[PipelineStep]
    pipeline_cursor: int = 0
    current_role: str

    outputs: list[OutputRecord] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    rework_notes: list[ReworkNote] = Field(default_factory=list)

    completed_at: datetime | None = None


class TaskBody(BaseModel):
    """Markdown body sections of a task.md file."""

    description: str = ""
    background: str = ""
    acceptance_criteria: str = ""


class Task(BaseModel):
    """Complete representation of a task.md file."""

    meta: TaskMeta
    body: TaskBody = Field(default_factory=TaskBody)


# ─── Position ────────────────────────────────────────────────────────


class Position(BaseModel):
    """A position (job slot) in the company."""

    role: str
    status: PositionStatus = PositionStatus.VACANT
    agent_id: str | None = None
    occupied_at: datetime | None = None


# ─── Role ────────────────────────────────────────────────────────────


class AvatarMeta(BaseModel):
    """Metadata for a role's avatar."""

    role: str
    name: str
    size: dict[str, int] = Field(default_factory=lambda: {"width": 400, "height": 400})
    fps: int = 12
    files: dict[str, str] = Field(
        default_factory=lambda: {"idle": "avatar_idle.gif", "working": "avatar_working.gif"}
    )
    scale_hints: dict[str, str] = Field(default_factory=dict)


class RolePack(BaseModel):
    """Metadata about a role pack (does not hold file contents)."""

    role: str
    name: str  # display name from identity.md
    title: str  # job title from role.md
    has_avatar: bool = False
    skills: list[str] = Field(default_factory=list)  # skill file names


# ─── Worklog ─────────────────────────────────────────────────────────


class WorklogEntry(BaseModel):
    """A single parsed line from work.log."""

    timestamp: datetime
    task_id: str
    event: WorklogEvent
    detail: str = ""


# ─── Workspace Config ────────────────────────────────────────────────


class WorkspaceConfig(BaseModel):
    """Configuration for the ClawOPC workspace root."""

    workspace_root: Path = Path("~/.openclaw/workspace").expanduser()

    @property
    def console_dir(self) -> Path:
        return self.workspace_root / ".console"

    @property
    def positions_dir(self) -> Path:
        return self.console_dir / "positions"

    @property
    def roles_dir(self) -> Path:
        return self.console_dir / "roles"

    @property
    def logs_dir(self) -> Path:
        return self.workspace_root / ".logs"

    @property
    def archive_dir(self) -> Path:
        return self.workspace_root / ".archive"

    def agent_workspace(self, role: str) -> Path:
        return self.workspace_root / role
