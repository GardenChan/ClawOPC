"""Tests for workspace operations."""

from pathlib import Path

import pytest

from clawopc_core.models import AgentState, WorkspaceConfig
from clawopc_core.workspace import (
    get_agent_state,
    init_boss_workspace,
    init_workspace,
    onboard_employee,
)


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> WorkspaceConfig:
    """Create a temporary workspace config."""
    return WorkspaceConfig(workspace_root=tmp_path / "workspace")


def test_init_workspace(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)

    assert tmp_workspace.console_dir.exists()
    assert tmp_workspace.positions_dir.exists()
    assert tmp_workspace.roles_dir.exists()
    assert tmp_workspace.logs_dir.exists()
    assert tmp_workspace.archive_dir.exists()


def test_init_boss_workspace(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)
    init_boss_workspace(tmp_workspace)

    boss_ws = tmp_workspace.agent_workspace("boss")
    assert boss_ws.exists()
    assert (boss_ws / "skills").exists()
    assert (boss_ws / "work.log").exists()


def test_onboard_employee(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)

    # Create a minimal role pack
    role_dir = tmp_workspace.roles_dir / "developer"
    role_dir.mkdir(parents=True)
    (role_dir / "role.md").write_text("# Developer\n## 职位\n开发工程师\n")
    (role_dir / "identity.md").write_text("# Identity\n## 我的名字\nDev\n")

    onboard_employee(tmp_workspace, "developer")

    dev_ws = tmp_workspace.agent_workspace("developer")
    assert dev_ws.exists()
    assert (dev_ws / "pending").exists()
    assert (dev_ws / "processing").exists()
    assert (dev_ws / "done").exists()
    assert (dev_ws / "AGENTS.md").exists()
    assert (dev_ws / "HEARTBEAT.md").exists()
    assert (dev_ws / "skills" / "SKILL.md").exists()
    assert (dev_ws / "work.log").exists()


def test_get_agent_state_offline(tmp_workspace: WorkspaceConfig):
    assert get_agent_state(tmp_workspace, "developer") == AgentState.OFFLINE


def test_get_agent_state_idle(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)
    dev_ws = tmp_workspace.agent_workspace("developer")
    dev_ws.mkdir(parents=True)
    (dev_ws / "pending").mkdir()
    (dev_ws / "processing").mkdir()
    (dev_ws / "done").mkdir()

    assert get_agent_state(tmp_workspace, "developer") == AgentState.IDLE


def test_get_agent_state_working(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)
    dev_ws = tmp_workspace.agent_workspace("developer")
    dev_ws.mkdir(parents=True)
    (dev_ws / "pending").mkdir()
    (dev_ws / "processing").mkdir()
    (dev_ws / "done").mkdir()

    # Put a task in processing
    (dev_ws / "processing" / "task-20250115-001.md").write_text("test")

    assert get_agent_state(tmp_workspace, "developer") == AgentState.WORKING


def test_get_agent_state_awaiting_decision(tmp_workspace: WorkspaceConfig):
    init_workspace(tmp_workspace)
    dev_ws = tmp_workspace.agent_workspace("developer")
    dev_ws.mkdir(parents=True)
    (dev_ws / "pending").mkdir()
    (dev_ws / "processing").mkdir()
    (dev_ws / "done").mkdir()
    (dev_ws / "done" / "awaiting_boss").touch()

    assert get_agent_state(tmp_workspace, "developer") == AgentState.AWAITING_DECISION
