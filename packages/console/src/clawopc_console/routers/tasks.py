"""Task management API — create tasks, list tasks, get task details."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from clawopc_console.deps import get_config
from clawopc_core.task import create_task, parse_task

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig

router = APIRouter()


class CreateTaskRequest(BaseModel):
    """Request body for creating a new task."""

    title: str
    description: str
    background: str = ""
    acceptance_criteria: str = ""
    pipeline: list[dict[str, Any]]


@router.post("/create")
async def create_new_task(
    req: CreateTaskRequest,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Create a new task and dispatch it to the first pipeline role.

    Returns the created task metadata.
    """
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")
    if not req.pipeline:
        raise HTTPException(status_code=400, detail="Pipeline must have at least one step")

    for i, step in enumerate(req.pipeline):
        if not step.get("role"):
            raise HTTPException(status_code=400, detail=f"Pipeline step {i} missing role")
        if not step.get("instruction"):
            raise HTTPException(status_code=400, detail=f"Pipeline step {i} missing instruction")

    task = create_task(
        config=config,
        title=req.title,
        description=req.description,
        pipeline=req.pipeline,
        background=req.background,
        acceptance_criteria=req.acceptance_criteria,
    )

    return {
        "id": task.meta.id,
        "title": task.meta.title,
        "status": task.meta.status.value,
        "current_role": task.meta.current_role,
        "pipeline_cursor": task.meta.pipeline_cursor,
        "created_at": task.meta.created_at.isoformat(),
    }


@router.get("/list")
async def list_tasks(
    config: WorkspaceConfig = Depends(get_config),
) -> list[dict]:
    """List all tasks across all agent workspaces.

    Scans pending/, processing/, done/ of all agents plus the archive.
    """
    tasks: list[dict] = []

    if not config.workspace_root.exists():
        return tasks

    # Scan all agent workspaces
    for ws_dir in sorted(config.workspace_root.iterdir()):
        if not ws_dir.is_dir() or ws_dir.name.startswith("."):
            continue

        for subdir_name in ["pending", "processing", "done"]:
            subdir = ws_dir / subdir_name
            if not subdir.exists():
                continue

            for task_file in sorted(subdir.glob("task-*.md")):
                try:
                    task = parse_task(task_file)
                    tasks.append(
                        {
                            "id": task.meta.id,
                            "title": task.meta.title,
                            "status": task.meta.status.value,
                            "current_role": task.meta.current_role,
                            "pipeline_cursor": task.meta.pipeline_cursor,
                            "pipeline_total": len(task.meta.pipeline),
                            "created_at": task.meta.created_at.isoformat(),
                            "location": f"{ws_dir.name}/{subdir_name}",
                        }
                    )
                except Exception:
                    continue

    # Scan archive
    if config.archive_dir.exists():
        for task_file in sorted(config.archive_dir.rglob("task-*.md")):
            try:
                task = parse_task(task_file)
                tasks.append(
                    {
                        "id": task.meta.id,
                        "title": task.meta.title,
                        "status": task.meta.status.value,
                        "current_role": task.meta.current_role,
                        "pipeline_cursor": task.meta.pipeline_cursor,
                        "pipeline_total": len(task.meta.pipeline),
                        "created_at": task.meta.created_at.isoformat(),
                        "completed_at": (
                            task.meta.completed_at.isoformat() if task.meta.completed_at else None
                        ),
                        "location": "archive",
                    }
                )
            except Exception:
                continue

    # Sort by created_at descending
    tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return tasks


@router.get("/{task_id}")
async def get_task_detail(
    task_id: str,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Get detailed information about a specific task.

    Searches all agent workspaces and the archive for the task.
    """
    # Search in agent workspaces
    if config.workspace_root.exists():
        for task_file in config.workspace_root.rglob(f"{task_id}.md"):
            try:
                task = parse_task(task_file)
                return task.model_dump(mode="json")
            except Exception:
                continue

    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
