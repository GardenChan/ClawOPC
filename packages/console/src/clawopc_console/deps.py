"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from clawopc_console.config import get_workspace_config

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig


def get_config() -> WorkspaceConfig:
    """Dependency: provide WorkspaceConfig to route handlers."""
    return get_workspace_config()
