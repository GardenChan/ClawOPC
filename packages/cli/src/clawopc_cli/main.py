"""ClawOPC CLI entry point.

Usage:
    clawopc init          Initialize workspace + Boss Agent
    clawopc console       Start the Console server
    clawopc status        Show team status in terminal
    clawopc task create   Create a task from terminal (optional)
"""

from __future__ import annotations

import typer

from clawopc_cli.commands import console, init, status

app = typer.Typer(
    name="clawopc",
    help="ClawOPC — AI-powered One Person Company operating system",
    no_args_is_help=True,
    add_completion=False,
)

# Register sub-commands
app.command(name="init")(init.init_command)
app.command(name="console")(console.console_command)
app.command(name="status")(status.status_command)


if __name__ == "__main__":
    app()
