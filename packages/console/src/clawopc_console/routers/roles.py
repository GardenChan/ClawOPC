"""Role pack API — list and inspect available Role packs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from clawopc_console.deps import get_config
from clawopc_core.role import list_role_packs, load_avatar_meta, load_role_pack

if TYPE_CHECKING:
    from clawopc_core.models import WorkspaceConfig

router = APIRouter()


@router.get("/list")
async def get_roles(
    config: WorkspaceConfig = Depends(get_config),
) -> list[dict]:
    """List all available Role packs."""
    packs = list_role_packs(config)
    return [
        {
            "role": p.role,
            "name": p.name,
            "title": p.title,
            "has_avatar": p.has_avatar,
            "skills": p.skills,
        }
        for p in packs
    ]


@router.get("/{role}")
async def get_role_detail(
    role: str,
    config: WorkspaceConfig = Depends(get_config),
) -> dict:
    """Get detailed information about a specific Role pack."""
    pack = load_role_pack(config, role)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Role pack '{role}' not found")

    # Read file contents
    role_dir = config.roles_dir / role
    contents: dict[str, str] = {}
    for filename in ["role.md", "soul.md", "identity.md"]:
        path = role_dir / filename
        if path.exists():
            contents[filename] = path.read_text(encoding="utf-8")

    avatar_meta = load_avatar_meta(config, role)

    return {
        "role": pack.role,
        "name": pack.name,
        "title": pack.title,
        "has_avatar": pack.has_avatar,
        "skills": pack.skills,
        "contents": contents,
        "avatar_meta": avatar_meta.model_dump() if avatar_meta else None,
    }


@router.get("/{role}/avatar/{filename}")
async def get_avatar(
    role: str,
    filename: str,
    config: WorkspaceConfig = Depends(get_config),
) -> FileResponse:
    """Serve avatar image files."""
    # Validate filename to prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = config.roles_dir / role / "avatar" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Avatar file not found")

    media_type = "image/gif" if filename.endswith(".gif") else "application/json"
    return FileResponse(str(path), media_type=media_type)
