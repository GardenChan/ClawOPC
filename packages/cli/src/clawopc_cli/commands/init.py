"""clawopc init — initialize the ClawOPC workspace and Boss Agent.

Creates the shared management area, copies built-in Role packs,
initializes the Boss Agent workspace, and prepares the system for use.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from clawopc_core.models import WorkspaceConfig
from clawopc_core.workspace import init_boss_workspace, init_workspace

console = Console()


def _find_project_root() -> Path | None:
    """Walk up from this file to find the project root (contains pyproject.toml + roles/)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Safety limit
        if (current / "roles").is_dir() and (current / "pyproject.toml").is_file():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


# Built-in roles directory (shipped with the project)
_project_root = _find_project_root()
BUILTIN_ROLES_DIR = _project_root / "roles" if _project_root else Path("roles")


def init_command(
    workspace: str = typer.Option(
        "~/.openclaw/workspace",
        "--workspace",
        "-w",
        help="Workspace root directory",
    ),
) -> None:
    """Initialize the ClawOPC workspace and Boss Agent."""
    workspace_path = Path(workspace).expanduser()
    config = WorkspaceConfig(workspace_root=workspace_path)

    console.print()
    console.print(
        Panel.fit(
            "[bold blue]ClawOPC[/bold blue] — AI-powered One Person Company",
            subtitle="Initializing workspace...",
        )
    )
    console.print()

    # 1. Create workspace directories
    with console.status("[bold green]Creating workspace directories..."):
        init_workspace(config)
    console.print("  ✅ Workspace directories created")

    # 2. Copy built-in Role packs
    with console.status("[bold green]Installing built-in Role packs..."):
        _install_builtin_roles(config)
    console.print("  ✅ Built-in Role packs installed")

    # 3. Initialize Boss Agent workspace
    with console.status("[bold green]Initializing Boss Agent..."):
        init_boss_workspace(config)
    console.print("  ✅ Boss Agent initialized")

    console.print()
    console.print(
        Panel.fit(
            "[bold green]✅ ClawOPC workspace initialized![/bold green]\n\n"
            f"  📁 Workspace: [cyan]{workspace_path}[/cyan]\n"
            f"  👤 Boss Agent: [cyan]{config.agent_workspace('boss')}[/cyan]\n"
            f"  📋 Role packs: [cyan]{config.roles_dir}[/cyan]\n\n"
            "Next steps:\n"
            "  1. Run [bold]clawopc console[/bold] to start the Console\n"
            "  2. Open the Console in your browser\n"
            "  3. Publish positions and start creating tasks!",
            title="[bold]Setup Complete[/bold]",
        )
    )


def _install_builtin_roles(config: WorkspaceConfig) -> None:
    """Copy built-in Role packs to .console/roles/."""
    if not BUILTIN_ROLES_DIR.exists():
        return

    for role_dir in BUILTIN_ROLES_DIR.iterdir():
        if not role_dir.is_dir() or role_dir.name.startswith("."):
            continue

        dst = config.roles_dir / role_dir.name
        if dst.exists():
            continue  # Don't overwrite existing Role packs

        shutil.copytree(role_dir, dst)
