"""Boss decision API — forward, rework, or complete tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from clawopc_console.deps import get_config
from clawopc_core.task import (
    complete_task,
    forward_task,
    parse_task,
    rework_task,
)

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig

router = APIRouter()


class ForwardRequest(BaseModel):
    """Request body for forwarding a task."""

    task_id: str
    comment: str = ""


class ReworkRequest(BaseModel):
    """Request body for reworking a task."""

    task_id: str
    note: str
    comment: str = ""


class CompleteRequest(BaseModel):
    """Request body for completing a task."""

    task_id: str
    comment: str = ""


@router.get("/pending")
async def list_pending_decisions(
    config: WorkspaceConfig = Depends(get_config),
) -> list[dict]:
    """List all tasks awaiting Boss decision (done/awaiting_boss exists)."""
    pending: list[dict] = []

    if not config.workspace_root.exists():
        return pending

    for ws_dir in sorted(config.workspace_root.iterdir()):
        if not ws_dir.is_dir() or ws_dir.name.startswith("."):
            continue

        awaiting_file = ws_dir / "done" / "awaiting_boss"
        if not awaiting_file.exists():
            continue

        done_dir = ws_dir / "done"
        for task_file in sorted(done_dir.glob("task-*.md")):
            try:
                task = parse_task(task_file)
                meta = task.meta

                # Determine available actions
                can_forward = meta.pipeline_cursor < len(meta.pipeline) - 1
                next_role = meta.pipeline[meta.pipeline_cursor + 1].role if can_forward else None

                # Read output files
                outputs = []
                for output in meta.outputs:
                    if output.completed_at:
                        output_path = done_dir / output.file
                        content = ""
                        if output_path.exists():
                            content = output_path.read_text(encoding="utf-8")
                        outputs.append(
                            {
                                "step": output.step,
                                "role": output.role,
                                "file": output.file,
                                "content": content,
                                "completed_at": output.completed_at.isoformat(),
                            }
                        )

                pending.append(
                    {
                        "task": task.model_dump(mode="json"),
                        "role": ws_dir.name,
                        "can_forward": can_forward,
                        "next_role": next_role,
                        "outputs": outputs,
                    }
                )
            except Exception:
                continue

    return pending


@router.post("/forward")
async def forward(
    req: ForwardRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Forward a task to the next pipeline step."""
    task = _find_awaiting_task(config, req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {req.task_id} not found in done/")

    meta = task.meta
    if meta.pipeline_cursor >= len(meta.pipeline) - 1:
        raise HTTPException(status_code=400, detail="Already at last pipeline step, use complete")

    updated = forward_task(config, task, comment=req.comment)
    return {
        "action": "forward",
        "task_id": updated.meta.id,
        "next_role": updated.meta.current_role,
        "pipeline_cursor": updated.meta.pipeline_cursor,
    }


@router.post("/rework")
async def rework(
    req: ReworkRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Return a task to the current role for rework."""
    if not req.note.strip():
        raise HTTPException(status_code=400, detail="Rework note is required")

    task = _find_awaiting_task(config, req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {req.task_id} not found in done/")

    updated = rework_task(config, task, note=req.note, comment=req.comment)
    return {
        "action": "rework",
        "task_id": updated.meta.id,
        "role": updated.meta.current_role,
    }


@router.post("/complete")
async def complete(
    req: CompleteRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Complete a task and archive it."""
    task = _find_awaiting_task(config, req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {req.task_id} not found in done/")

    updated = complete_task(config, task, comment=req.comment)
    return {
        "action": "complete",
        "task_id": updated.meta.id,
        "completed_at": updated.meta.completed_at.isoformat()
        if updated.meta.completed_at
        else None,
    }


# ─── Helpers ─────────────────────────────────────────────────────────


def _find_awaiting_task(config: WorkspaceConfig, task_id: str):
    """Find a task in any agent's done/ directory."""
    from clawopc_core.task import parse_task

    if not config.workspace_root.exists():
        return None

    for ws_dir in config.workspace_root.iterdir():
        if not ws_dir.is_dir() or ws_dir.name.startswith("."):
            continue

        task_path = ws_dir / "done" / f"{task_id}.md"
        if task_path.exists():
            return parse_task(task_path)

    return None
