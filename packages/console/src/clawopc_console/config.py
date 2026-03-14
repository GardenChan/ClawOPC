"""Console configuration — centralized settings for the Console server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

from clawopc_core.models import WorkspaceConfig


class ConsoleSettings(BaseSettings):
    """Console server settings, loaded from environment variables."""

    # Server
    host: str = "127.0.0.1"
    port: int = 3000

    # Workspace
    workspace_root: Path = Path("~/.openclaw/workspace").expanduser()

    # Polling / WebSocket
    poll_interval_seconds: float = 5.0

    model_config = {"env_prefix": "CLAWOPC_"}


@lru_cache
def get_settings() -> ConsoleSettings:
    """Get the singleton ConsoleSettings instance."""
    return ConsoleSettings()


def get_workspace_config() -> WorkspaceConfig:
    """Get the WorkspaceConfig derived from ConsoleSettings."""
    settings = get_settings()
    return WorkspaceConfig(workspace_root=settings.workspace_root)
