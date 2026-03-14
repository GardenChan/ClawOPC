"""Position (job slot) management.

Handles CRUD operations for position files in .console/positions/.
Each position file tracks whether a role slot is vacant or occupied.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import frontmatter

from clawopc_core.models import Position, PositionStatus, WorkspaceConfig

if TYPE_CHECKING:
    from pathlib import Path


def load_position(path: Path) -> Position | None:
    """Load a position from a .md file.

    Args:
        path: Path to the position .md file.

    Returns:
        A Position instance, or None if the file is invalid.
    """
    if not path.exists():
        return None

    try:
        post = frontmatter.load(str(path))
        meta = dict(post.metadata)
        return Position(
            role=meta.get("role", path.stem),
            status=PositionStatus(meta.get("status", "vacant")),
            agent_id=meta.get("agent_id") or None,
            occupied_at=meta.get("occupied_at"),
        )
    except Exception:
        return None


def save_position(config: WorkspaceConfig, position: Position) -> Path:
    """Save a position to a .md file.

    Args:
        config: Workspace configuration.
        position: The Position to save.

    Returns:
        Path to the written file.
    """
    config.positions_dir.mkdir(parents=True, exist_ok=True)
    path = config.positions_dir / f"{position.role}.md"

    meta = {
        "role": position.role,
        "status": position.status.value,
        "agent_id": position.agent_id or "",
        "occupied_at": position.occupied_at.isoformat() if position.occupied_at else "",
    }

    post = frontmatter.Post("", **meta)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    return path


def publish_position(config: WorkspaceConfig, role: str) -> Position:
    """Publish a vacant position for a role.

    Args:
        config: Workspace configuration.
        role: The role name.

    Returns:
        The created Position.
    """
    position = Position(role=role, status=PositionStatus.VACANT)
    save_position(config, position)
    return position


def occupy_position(config: WorkspaceConfig, role: str, agent_id: str) -> Position:
    """Mark a position as occupied after onboarding.

    Args:
        config: Workspace configuration.
        role: The role name.
        agent_id: The OpenClaw agent ID.

    Returns:
        The updated Position.
    """
    position = Position(
        role=role,
        status=PositionStatus.OCCUPIED,
        agent_id=agent_id,
        occupied_at=datetime.now(tz=UTC),
    )
    save_position(config, position)
    return position


def vacate_position(config: WorkspaceConfig, role: str) -> Position:
    """Mark a position as vacant (employee removed).

    Args:
        config: Workspace configuration.
        role: The role name.

    Returns:
        The updated Position.
    """
    position = Position(role=role, status=PositionStatus.VACANT)
    save_position(config, position)
    return position


def get_position(config: WorkspaceConfig, role: str) -> Position | None:
    """Get a position by role name.

    Args:
        config: Workspace configuration.
        role: The role name.

    Returns:
        The Position, or None if not found.
    """
    path = config.positions_dir / f"{role}.md"
    return load_position(path)
