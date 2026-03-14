"""Team overview API — provides real-time status of all agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from clawopc_console.deps import get_config
from clawopc_core.role import load_role_pack
from clawopc_core.worklog import get_latest_entry
from clawopc_core.workspace import get_agent_state, list_positions

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig

router = APIRouter()


@router.get("/overview")
async def get_team_overview(config: WorkspaceConfig = Depends(get_config)) -> list[dict]:
    """Get an overview of all team members with their current state.

    Returns a list of agent cards with:
      - role, name, title
      - state (working / idle / awaiting_decision / offline)
      - current task ID (if working)
      - latest worklog entry
    """
    positions = list_positions(config)
    agents = []

    for pos in positions:
        if pos.role == "boss":
            continue  # Boss is not shown as a team member

        state = get_agent_state(config, pos.role)
        pack = load_role_pack(config, pos.role)

        # Get latest worklog entry
        log_path = config.agent_workspace(pos.role) / "work.log"
        latest = get_latest_entry(log_path)

        # Find current task ID if working
        current_task_id = None
        processing_dir = config.agent_workspace(pos.role) / "processing"
        if processing_dir.exists():
            task_files = list(processing_dir.glob("task-*.md"))
            if task_files:
                current_task_id = task_files[0].stem

        agents.append(
            {
                "role": pos.role,
                "name": pack.name if pack else pos.role,
                "title": pack.title if pack else pos.role,
                "state": state.value,
                "position_status": pos.status.value,
                "current_task_id": current_task_id,
                "has_avatar": pack.has_avatar if pack else False,
                "latest_log": {
                    "timestamp": latest.timestamp.isoformat() if latest else None,
                    "event": latest.event.value if latest else None,
                    "detail": latest.detail if latest else None,
                }
                if latest
                else None,
            }
        )

    return agents
