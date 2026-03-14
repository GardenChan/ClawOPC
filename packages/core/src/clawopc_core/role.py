"""Role pack management.

Handles reading, listing, and inspecting Role packs
stored in .console/roles/<role>/.
"""

from __future__ import annotations

import json

import frontmatter

from clawopc_core.models import AvatarMeta, RolePack, WorkspaceConfig


def list_role_packs(config: WorkspaceConfig) -> list[RolePack]:
    """List all available Role packs from the roles directory."""
    packs: list[RolePack] = []
    if not config.roles_dir.exists():
        return packs

    for role_dir in sorted(config.roles_dir.iterdir()):
        if not role_dir.is_dir() or role_dir.name.startswith("."):
            continue
        pack = load_role_pack(config, role_dir.name)
        if pack:
            packs.append(pack)

    return packs


def load_role_pack(config: WorkspaceConfig, role: str) -> RolePack | None:
    """Load a RolePack summary from the roles directory.

    Does not load full file contents — just metadata for listing.
    """
    role_dir = config.roles_dir / role
    if not role_dir.exists():
        return None

    # Extract name from identity.md
    name = role  # fallback
    identity_path = role_dir / "identity.md"
    if identity_path.exists():
        post = frontmatter.load(str(identity_path))
        # Try to find the name in the content
        for line in post.content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                # Look for "我叫 <name>" pattern or "## 我的名字" section
                pass
        # Simpler: check for metadata
        name = _extract_name(post.content, role)

    # Extract title from role.md
    title = role  # fallback
    role_path = role_dir / "role.md"
    if role_path.exists():
        post = frontmatter.load(str(role_path))
        title = _extract_title(post.content, role)

    # Check avatar
    has_avatar = (role_dir / "avatar" / "avatar_idle.gif").exists()

    # List skills
    skills: list[str] = []
    skills_dir = role_dir / "skills"
    if skills_dir.exists():
        skills = sorted(f.stem for f in skills_dir.glob("*.md"))

    return RolePack(
        role=role,
        name=name,
        title=title,
        has_avatar=has_avatar,
        skills=skills,
    )


def load_avatar_meta(config: WorkspaceConfig, role: str) -> AvatarMeta | None:
    """Load avatar metadata for a role."""
    meta_path = config.roles_dir / role / "avatar" / "avatar_meta.json"
    if not meta_path.exists():
        return None

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return AvatarMeta(**data)


# ─── Helpers ─────────────────────────────────────────────────────────


def _extract_name(content: str, fallback: str) -> str:
    """Extract the character name from identity.md content."""
    in_name_section = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "## 我的名字":
            in_name_section = True
            continue
        if in_name_section and stripped and not stripped.startswith("#"):
            return stripped
        if in_name_section and stripped.startswith("#"):
            break
    return fallback


def _extract_title(content: str, fallback: str) -> str:
    """Extract the job title from role.md content."""
    in_title_section = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "## 职位":
            in_title_section = True
            continue
        if in_title_section and stripped and not stripped.startswith("#"):
            return stripped
        if in_title_section and stripped.startswith("#"):
            break
    return fallback
