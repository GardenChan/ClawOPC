"""Task management — parsing, generating, and transitioning task.md files.

Handles the complete lifecycle of task.md:
  - Generating new task files from Console input
  - Parsing existing task.md (YAML front-matter + Markdown body)
  - Updating task status during state transitions
  - Moving task files between directories (forward / rework / complete)
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import frontmatter

from clawopc_core.models import (
    Decision,
    DecisionAction,
    OutputRecord,
    PipelineStep,
    ReworkNote,
    Task,
    TaskBody,
    TaskMeta,
    TaskStatus,
    WorkspaceConfig,
)

if TYPE_CHECKING:
    from pathlib import Path

# ─── Parse ───────────────────────────────────────────────────────────


def parse_task(path: Path) -> Task:
    """Parse a task.md file into a Task model.

    Args:
        path: Path to the task.md file.

    Returns:
        A fully populated Task instance.
    """
    post = frontmatter.load(str(path))
    meta_dict = dict(post.metadata)
    content = post.content

    # Parse pipeline steps
    if "pipeline" in meta_dict:
        meta_dict["pipeline"] = [PipelineStep(**s) for s in meta_dict["pipeline"]]

    # Parse outputs
    if "outputs" in meta_dict:
        meta_dict["outputs"] = [OutputRecord(**o) for o in meta_dict["outputs"]]

    # Parse decisions
    if "decisions" in meta_dict:
        meta_dict["decisions"] = [Decision(**d) for d in (meta_dict["decisions"] or [])]

    # Parse rework_notes
    if "rework_notes" in meta_dict:
        meta_dict["rework_notes"] = [ReworkNote(**r) for r in (meta_dict["rework_notes"] or [])]

    meta = TaskMeta(**meta_dict)

    # Parse body sections
    body = _parse_body(content)

    return Task(meta=meta, body=body)


def _parse_body(content: str) -> TaskBody:
    """Parse the Markdown body into its three fixed sections."""
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    section_map = {
        "## 任务描述": "description",
        "## 背景信息": "background",
        "## 验收标准": "acceptance_criteria",
    }

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped in section_map:
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = section_map[stripped]
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()

    return TaskBody(**sections)


# ─── Generate ────────────────────────────────────────────────────────


def generate_task_id(config: WorkspaceConfig) -> str:
    """Generate the next task ID for today.

    Format: task-YYYYMMDD-NNN (3-digit zero-padded sequence).
    """
    today = datetime.now(tz=UTC).strftime("%Y%m%d")
    prefix = f"task-{today}-"

    # Scan all agent workspaces + archive for existing IDs
    existing_ids: set[str] = set()

    if config.workspace_root.exists():
        for md_file in config.workspace_root.rglob(f"{prefix}*.md"):
            stem = md_file.stem
            if stem.startswith(prefix):
                existing_ids.add(stem)

    seq = 1
    while f"{prefix}{seq:03d}" in existing_ids:
        seq += 1

    return f"{prefix}{seq:03d}"


def generate_task_md(task: Task) -> str:
    """Generate the complete task.md content from a Task model.

    Returns:
        The full Markdown string with YAML front-matter.
    """
    meta = task.meta.model_dump(mode="json")
    body = task.body

    content_parts = []
    content_parts.append(f"## 任务描述\n\n{body.description}")
    content_parts.append(f"## 背景信息\n\n{body.background or '无。'}")
    content_parts.append(f"## 验收标准\n\n{body.acceptance_criteria}")

    markdown_body = "\n\n".join(content_parts)

    post = frontmatter.Post(markdown_body, **meta)
    return frontmatter.dumps(post)


def create_task(
    config: WorkspaceConfig,
    title: str,
    description: str,
    pipeline: list[dict[str, Any]],
    background: str = "",
    acceptance_criteria: str = "",
) -> Task:
    """Create a new task and write it to the first role's pending/ directory.

    Args:
        config: Workspace configuration.
        title: Task title.
        description: Task description.
        pipeline: List of pipeline step dicts with 'role', 'instruction', optional 'timeout'.
        background: Background information.
        acceptance_criteria: Acceptance criteria in checklist format.

    Returns:
        The created Task instance.
    """
    task_id = generate_task_id(config)
    now = datetime.now(tz=UTC)

    steps = [
        PipelineStep(step=i, role=s["role"], instruction=s["instruction"], timeout=s.get("timeout"))
        for i, s in enumerate(pipeline)
    ]

    outputs = [
        OutputRecord(step=i, role=s["role"], file=_output_filename(s["role"], i, steps))
        for i, s in enumerate(pipeline)
    ]

    first_role = steps[0].role

    meta = TaskMeta(
        id=task_id,
        title=title,
        created_at=now,
        created_by="boss",
        status=TaskStatus.PENDING,
        pipeline=steps,
        pipeline_cursor=0,
        current_role=first_role,
        outputs=outputs,
    )

    body = TaskBody(
        description=description,
        background=background,
        acceptance_criteria=acceptance_criteria,
    )

    task = Task(meta=meta, body=body)

    # Write to first role's pending/
    pending_dir = config.agent_workspace(first_role) / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    task_path = pending_dir / f"{task_id}.md"
    task_path.write_text(generate_task_md(task), encoding="utf-8")

    return task


# ─── Transitions ─────────────────────────────────────────────────────


def forward_task(config: WorkspaceConfig, task: Task, comment: str = "") -> Task:
    """Forward a task to the next pipeline step.

    Moves all task files from current role's done/ to next role's pending/.
    Updates task metadata accordingly.
    """
    meta = task.meta
    now = datetime.now(tz=UTC)
    current_role = meta.current_role
    current_cursor = meta.pipeline_cursor

    # Record decision
    meta.decisions.append(
        Decision(
            at=now,
            step=current_cursor,
            role=current_role,
            action=DecisionAction.FORWARD,
            comment=comment,
        )
    )

    # Advance cursor
    meta.pipeline_cursor += 1
    next_step = meta.pipeline[meta.pipeline_cursor]
    meta.current_role = next_step.role
    meta.status = TaskStatus.PENDING

    # Move files
    src_dir = config.agent_workspace(current_role) / "done"
    dst_dir = config.agent_workspace(next_step.role) / "pending"
    dst_dir.mkdir(parents=True, exist_ok=True)

    _move_task_files(src_dir, dst_dir, meta.id)

    # Remove awaiting_boss marker
    awaiting = src_dir / "awaiting_boss"
    if awaiting.exists():
        awaiting.unlink()

    # Write updated task.md
    task_path = dst_dir / f"{meta.id}.md"
    task_path.write_text(generate_task_md(task), encoding="utf-8")

    return task


def rework_task(config: WorkspaceConfig, task: Task, note: str, comment: str = "") -> Task:
    """Rework a task — return it to the current role's pending/.

    Adds a rework note and moves files back from done/ to pending/.
    """
    meta = task.meta
    now = datetime.now(tz=UTC)
    current_role = meta.current_role

    # Record decision
    meta.decisions.append(
        Decision(
            at=now,
            step=meta.pipeline_cursor,
            role=current_role,
            action=DecisionAction.REWORK,
            comment=comment,
        )
    )

    # Add rework note
    meta.rework_notes.append(
        ReworkNote(
            at=now,
            step=meta.pipeline_cursor,
            role=current_role,
            note=note,
        )
    )

    meta.status = TaskStatus.PENDING

    # Move files from done/ back to pending/
    src_dir = config.agent_workspace(current_role) / "done"
    dst_dir = config.agent_workspace(current_role) / "pending"
    dst_dir.mkdir(parents=True, exist_ok=True)

    _move_task_files(src_dir, dst_dir, meta.id)

    # Remove awaiting_boss marker
    awaiting = src_dir / "awaiting_boss"
    if awaiting.exists():
        awaiting.unlink()

    # Write updated task.md
    task_path = dst_dir / f"{meta.id}.md"
    task_path.write_text(generate_task_md(task), encoding="utf-8")

    return task


def complete_task(config: WorkspaceConfig, task: Task, comment: str = "") -> Task:
    """Complete a task — archive it.

    Moves all task files from current role's done/ to the archive.
    """
    meta = task.meta
    now = datetime.now(tz=UTC)

    # Record decision
    meta.decisions.append(
        Decision(
            at=now,
            step=meta.pipeline_cursor,
            role=meta.current_role,
            action=DecisionAction.COMPLETE,
            comment=comment,
        )
    )

    meta.status = TaskStatus.COMPLETE
    meta.completed_at = now

    # Archive
    month_str = now.strftime("%Y-%m")
    archive_dir = config.archive_dir / month_str / meta.id
    archive_dir.mkdir(parents=True, exist_ok=True)

    src_dir = config.agent_workspace(meta.current_role) / "done"
    _move_task_files(src_dir, archive_dir, meta.id)

    # Remove awaiting_boss marker
    awaiting = src_dir / "awaiting_boss"
    if awaiting.exists():
        awaiting.unlink()

    # Write final task.md to archive
    task_path = archive_dir / f"{meta.id}.md"
    task_path.write_text(generate_task_md(task), encoding="utf-8")

    return task


# ─── Helpers ─────────────────────────────────────────────────────────


def _output_filename(role: str, step: int, all_steps: list[PipelineStep]) -> str:
    """Determine the output filename, handling duplicate roles in pipeline."""
    occurrence = sum(1 for s in all_steps[:step] if s.role == role)
    if occurrence == 0:
        return f"{role}_output.md"
    return f"{role}_output_{occurrence + 1}.md"


def _move_task_files(src_dir: Path, dst_dir: Path, task_id: str) -> None:
    """Move all files related to a task from src to dst directory."""
    if not src_dir.exists():
        return

    for f in src_dir.iterdir():
        if f.name == "awaiting_boss":
            continue
        if f.name.startswith(task_id) or f.name.endswith("_output.md") or "_output_" in f.name:
            shutil.move(str(f), str(dst_dir / f.name))
