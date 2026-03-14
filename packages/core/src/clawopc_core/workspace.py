"""Workspace filesystem operations.

This module provides all deterministic file system operations
for the ClawOPC workspace — directory creation, file copying,
agent onboarding, and workspace status inspection.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from clawopc_core.models import (
    AgentState,
    Position,
    WorkspaceConfig,
)

if TYPE_CHECKING:
    from pathlib import Path


def init_workspace(config: WorkspaceConfig) -> None:
    """Initialize the ClawOPC workspace with all required directories.

    Called by `clawopc init`. Creates the shared management area,
    logs directory, and archive directory.
    """
    config.console_dir.mkdir(parents=True, exist_ok=True)
    config.positions_dir.mkdir(parents=True, exist_ok=True)
    config.roles_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.archive_dir.mkdir(parents=True, exist_ok=True)


def init_boss_workspace(config: WorkspaceConfig) -> None:
    """Initialize the Boss Agent workspace.

    Creates the boss workspace directory, copies the Boss Role pack
    files, and creates the work.log file.
    """
    boss_ws = config.agent_workspace("boss")
    boss_ws.mkdir(parents=True, exist_ok=True)

    skills_dir = boss_ws / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Copy Role pack → OpenClaw standard files
    boss_role_dir = config.roles_dir / "boss"
    if boss_role_dir.exists():
        _copy_role_to_workspace(boss_role_dir, boss_ws)

    # Create empty work.log
    work_log = boss_ws / "work.log"
    if not work_log.exists():
        work_log.touch()


def onboard_employee(config: WorkspaceConfig, role: str) -> None:
    """Execute the deterministic onboarding process for an Employee Agent.

    This is called by the Console (not by the Agent itself).
    Creates the agent workspace, copies Role pack files,
    writes HEARTBEAT.md and employee SKILL.md, and updates the position file.
    """
    agent_ws = config.agent_workspace(role)

    # Create workspace directories
    agent_ws.mkdir(parents=True, exist_ok=True)
    (agent_ws / "pending").mkdir(exist_ok=True)
    (agent_ws / "processing").mkdir(exist_ok=True)
    (agent_ws / "done").mkdir(exist_ok=True)

    skills_dir = agent_ws / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Copy Role pack → OpenClaw standard files
    role_dir = config.roles_dir / role
    if role_dir.exists():
        _copy_role_to_workspace(role_dir, agent_ws)

    # Write HEARTBEAT.md
    heartbeat_path = agent_ws / "HEARTBEAT.md"
    if not heartbeat_path.exists():
        heartbeat_path.write_text(_generate_heartbeat_md(), encoding="utf-8")

    # Write employee SKILL.md entry
    skill_entry = skills_dir / "SKILL.md"
    if not skill_entry.exists():
        skill_entry.write_text(_generate_employee_skill_md(), encoding="utf-8")

    # Create empty work.log
    work_log = agent_ws / "work.log"
    if not work_log.exists():
        work_log.touch()


def get_agent_state(config: WorkspaceConfig, role: str) -> AgentState:
    """Determine the real-time state of an agent by inspecting its workspace."""
    agent_ws = config.agent_workspace(role)

    if not agent_ws.exists():
        return AgentState.OFFLINE

    # Check for awaiting_boss
    awaiting_boss = agent_ws / "done" / "awaiting_boss"
    if awaiting_boss.exists():
        return AgentState.AWAITING_DECISION

    # Check for processing tasks
    processing_dir = agent_ws / "processing"
    if processing_dir.exists() and any(processing_dir.glob("task-*.md")):
        return AgentState.WORKING

    return AgentState.IDLE


def list_roles(config: WorkspaceConfig) -> list[str]:
    """List all available roles from the roles directory."""
    if not config.roles_dir.exists():
        return []
    return sorted(
        d.name for d in config.roles_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )


def list_positions(config: WorkspaceConfig) -> list[Position]:
    """List all positions from the positions directory."""
    from clawopc_core.position import load_position

    positions: list[Position] = []
    if not config.positions_dir.exists():
        return positions

    for f in sorted(config.positions_dir.glob("*.md")):
        pos = load_position(f)
        if pos:
            positions.append(pos)
    return positions


# ─── Internal helpers ────────────────────────────────────────────────


def _copy_role_to_workspace(role_dir: Path, workspace: Path) -> None:
    """Copy Role pack files to an agent workspace, mapping to OpenClaw standard names."""
    mappings = {
        "role.md": "AGENTS.md",
        "soul.md": "SOUL.md",
        "identity.md": "IDENTITY.md",
    }

    for src_name, dst_name in mappings.items():
        src = role_dir / src_name
        if src.exists():
            shutil.copy2(src, workspace / dst_name)

    # Copy skills
    src_skills = role_dir / "skills"
    dst_skills = workspace / "skills"
    if src_skills.exists():
        dst_skills.mkdir(exist_ok=True)
        for skill_file in src_skills.glob("*.md"):
            shutil.copy2(skill_file, dst_skills / skill_file.name)

    # Copy avatar (keep in workspace for Console to serve)
    src_avatar = role_dir / "avatar"
    if src_avatar.exists():
        dst_avatar = workspace / "avatar"
        if dst_avatar.exists():
            shutil.rmtree(dst_avatar)
        shutil.copytree(src_avatar, dst_avatar)


def _generate_heartbeat_md() -> str:
    """Generate the HEARTBEAT.md template for Employee agents."""
    return """\
# HEARTBEAT

## 启动时检查

1. 检查 processing/ 目录是否有残留任务
   → 有：说明上次异常中断，继续处理
   → 无：正常流程

## 心跳行为

1. 列出 pending/ 目录下所有 task-*.md 文件：
   ls pending/task-*.md 2>/dev/null

2. 如果没有文件 → 回复 HEARTBEAT_OK

3. 如果有文件 → 按文件名排序，取第一个

4. 执行认领（先 ls，再逐个 mv，最后验证）：
   ls pending/
   mv pending/task-<id>.md processing/task-<id>.md
   mv pending/*_output*.md processing/ 2>/dev/null
   ls processing/

5. 读取任务内容，按 instruction 执行工作

6. 完成后移入 done/（逐个移动并验证）：
   mv processing/task-<id>.md done/task-<id>.md
   mv processing/*_output*.md done/ 2>/dev/null
   touch done/awaiting_boss
   ls done/

7. 写入 work.log 记录完整过程
"""


def _generate_employee_skill_md() -> str:
    """Generate the employee SKILL.md entry file."""
    return """\
# Employee Skill

## 核心原则

- 我是一名虚拟员工，在 ClawOPC 系统中工作
- 我只处理属于我角色的任务
- 我的产出必须符合 output-standard.md 的规范
- 我通过文件系统与其他组件交互，不直接通信
- 我忠实执行任务，不擅自扩大或缩小任务范围
- 我遇到无法处理的情况时，如实记录并等待 Boss 决策

## 心跳响应

我通过 HEARTBEAT.md 中的指令响应心跳触发。
每次心跳触发时：
1. 检查 processing/ 是否有残留任务（异常中断恢复）
2. 扫描 pending/ 是否有新任务
3. 有任务 → 按 task-loop.md 流程处理
4. 无任务 → HEARTBEAT_OK（静默，不做任何操作）

## 文件操作安全

所有文件操作使用精确的 shell 命令模板：
- 先 ls 确认文件存在
- 再逐个 mv 移动文件
- 最后 ls 验证结果
- 不使用通配符批量移动
"""
