"""clawopc status — show team status in the terminal.

A quick terminal view of all agents' current state,
without needing to open the Console web interface.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clawopc_core.models import WorkspaceConfig
from clawopc_core.role import load_role_pack
from clawopc_core.worklog import get_latest_entry
from clawopc_core.workspace import get_agent_state, list_positions

console = Console()

STATE_ICONS = {
    "working": "🔵",
    "idle": "⚪",
    "awaiting_decision": "🟡",
    "offline": "🔴",
}


def status_command(
    workspace: str = typer.Option(
        "~/.openclaw/workspace",
        "--workspace",
        "-w",
        help="Workspace root directory",
    ),
) -> None:
    """Show the current status of all team members."""
    workspace_path = Path(workspace).expanduser()
    config = WorkspaceConfig(workspace_root=workspace_path)

    positions = list_positions(config)

    if not positions:
        console.print("\n  ⚠️  No positions found. Run [bold]clawopc init[/bold] first.\n")
        raise typer.Exit(1)

    table = Table(title="🏢 ClawOPC Team Status", show_header=True, header_style="bold cyan")
    table.add_column("Status", width=4, justify="center")
    table.add_column("Name", min_width=10)
    table.add_column("Role", min_width=12)
    table.add_column("State", min_width=16)
    table.add_column("Current Task", min_width=20)
    table.add_column("Latest Activity", min_width=30)

    for pos in positions:
        if pos.role == "boss":
            continue

        state = get_agent_state(config, pos.role)
        pack = load_role_pack(config, pos.role)
        name = pack.name if pack else pos.role
        title = pack.title if pack else pos.role

        # Icon
        icon = STATE_ICONS.get(state.value, "❓")

        # Current task
        current_task = "—"
        processing_dir = config.agent_workspace(pos.role) / "processing"
        if processing_dir.exists():
            task_files = list(processing_dir.glob("task-*.md"))
            if task_files:
                current_task = task_files[0].stem

        # Latest activity
        latest_activity = "—"
        log_path = config.agent_workspace(pos.role) / "work.log"
        latest = get_latest_entry(log_path)
        if latest:
            time_str = latest.timestamp.strftime("%H:%M:%S")
            latest_activity = f"[{time_str}] {latest.event.value}: {latest.detail[:40]}"

        table.add_row(
            icon,
            f"[bold]{name}[/bold]",
            title,
            state.value.replace("_", " ").title(),
            current_task,
            latest_activity,
        )

    console.print()
    console.print(table)
    console.print()
