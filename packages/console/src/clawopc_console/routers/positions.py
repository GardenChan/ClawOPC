"""Position management API — publish, onboard, and manage positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from clawopc_console.deps import get_config
from clawopc_core.position import get_position, occupy_position, publish_position
from clawopc_core.workspace import list_positions, onboard_employee

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig

router = APIRouter()


class PublishPositionRequest(BaseModel):
    """Request body for publishing a new position."""

    role: str


class OnboardRequest(BaseModel):
    """Request body for onboarding an employee."""

    role: str


@router.get("/list")
async def get_positions(
    config: WorkspaceConfig = Depends(get_config),
) -> list[dict]:
    """List all positions with their status."""
    positions = list_positions(config)
    return [
        {
            "role": p.role,
            "status": p.status.value,
            "agent_id": p.agent_id,
            "occupied_at": p.occupied_at.isoformat() if p.occupied_at else None,
        }
        for p in positions
    ]


@router.post("/publish")
async def publish(
    req: PublishPositionRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Publish a vacant position for a role.

    The role must have a Role pack in .console/roles/.
    """
    role_dir = config.roles_dir / req.role
    if not role_dir.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Role pack for '{req.role}' not found in {config.roles_dir}",
        )

    existing = get_position(config, req.role)
    if existing and existing.status.value == "occupied":
        raise HTTPException(
            status_code=400,
            detail=f"Position '{req.role}' is already occupied",
        )

    position = publish_position(config, req.role)
    return {
        "role": position.role,
        "status": position.status.value,
    }


@router.post("/onboard")
async def onboard(
    req: OnboardRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Execute the deterministic onboarding process for an employee.

    Creates the agent workspace, copies Role pack files,
    writes HEARTBEAT.md and SKILL.md, and updates the position.
    """
    position = get_position(config, req.role)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position '{req.role}' not found")
    if position.status.value == "occupied":
        raise HTTPException(status_code=400, detail=f"Position '{req.role}' is already occupied")

    # Execute onboarding
    onboard_employee(config, req.role)

    # Mark position as occupied
    updated = occupy_position(config, req.role, agent_id=req.role)

    return {
        "role": updated.role,
        "status": updated.status.value,
        "agent_id": updated.agent_id,
        "occupied_at": updated.occupied_at.isoformat() if updated.occupied_at else None,
    }
