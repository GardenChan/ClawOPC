"""FastAPI application — the Console backend.

This is the main entry point for the Console server.
It serves both the REST API and the React frontend static files.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from clawopc_console.routers import decisions, positions, roles, tasks, team
from clawopc_console.watcher import FileWatcher
from clawopc_console.ws.handler import router as ws_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Frontend build output directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — start/stop the file watcher."""
    watcher = FileWatcher.get_instance()
    await watcher.start()
    yield
    await watcher.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ClawOPC Console",
        description="Boss Agent's web interface for managing the AI team",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow the frontend dev server during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(team.router, prefix="/api/team", tags=["team"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
    app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
    app.include_router(roles.router, prefix="/api/roles", tags=["roles"])

    # WebSocket
    app.include_router(ws_router)

    # Serve frontend static files (production)
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return app


app = create_app()
