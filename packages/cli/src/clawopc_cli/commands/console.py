"""clawopc console — start the Console server.

Launches the FastAPI backend with Uvicorn, serving both the REST API
and the React frontend (if built).
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def console_command(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(3000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (development)"),
) -> None:
    """Start the ClawOPC Console server."""
    import uvicorn

    console.print()
    console.print(f"  🚀 Starting ClawOPC Console on [bold cyan]http://{host}:{port}[/bold cyan]")
    console.print(f"  📡 API docs at [bold cyan]http://{host}:{port}/docs[/bold cyan]")
    console.print()

    uvicorn.run(
        "clawopc_console.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
