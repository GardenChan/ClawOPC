"""File watcher — monitors workspace for changes and triggers WebSocket broadcasts.

Uses the `watchfiles` library (Rust-based) to efficiently detect file changes
in the workspace directory tree. When changes are detected, relevant events
are broadcast to all connected WebSocket clients.
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from watchfiles import Change, awatch

from clawopc_console.config import get_workspace_config
from clawopc_console.ws.handler import broadcast


class FileWatcher:
    """Watches the workspace directory for file changes."""

    _instance: FileWatcher | None = None

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    @classmethod
    def get_instance(cls) -> FileWatcher:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        """Start watching the workspace directory."""
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())

    async def stop(self) -> None:
        """Stop the file watcher."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _watch_loop(self) -> None:
        """Main watch loop — monitors the workspace and broadcasts changes."""
        config = get_workspace_config()
        watch_path = config.workspace_root

        if not watch_path.exists():
            return

        try:
            async for changes in awatch(str(watch_path)):
                if not self._running:
                    break

                for change_type, change_path in changes:
                    await self._handle_change(change_type, Path(change_path))
        except asyncio.CancelledError:
            pass

    async def _handle_change(self, change_type: Change, path: Path) -> None:
        """Handle a single file change event.

        Determines what kind of workspace event occurred and broadcasts
        the appropriate WebSocket message.
        """
        name = path.name
        parent = path.parent.name

        # Detect awaiting_boss creation → new decision needed
        if name == "awaiting_boss" and parent == "done":
            role = path.parent.parent.name
            await broadcast("new_decision", {"role": role})
            return

        # Detect awaiting_boss removal → decision was made
        if name == "awaiting_boss" and change_type == Change.deleted:
            role = path.parent.parent.name
            await broadcast("decision_made", {"role": role})
            return

        # Detect task file movements
        if name.startswith("task-") and name.endswith(".md"):
            role = path.parent.parent.name
            directory = parent  # pending, processing, or done

            if change_type == Change.added:
                await broadcast(
                    "task_moved",
                    {
                        "role": role,
                        "task_id": path.stem,
                        "directory": directory,
                    },
                )
            return

        # Detect work.log updates
        if name == "work.log":
            role = path.parent.name
            await broadcast("worklog_updated", {"role": role})
            return
