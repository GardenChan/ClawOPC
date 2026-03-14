# ClawOPC Spec — 03 Workspace

```markdown
---
doc_id: spec-03
title: Workspace
version: 0.2.0
status: draft
created_at: 2025-01-15
updated_at: 2026-03-15
---
```

---

## 什么是 Workspace

Workspace 是 ClawOPC 的**唯一真相来源**。

所有状态、任务、日志、角色定义
全部以文件形式存储在文件系统中。

没有数据库，没有消息队列。
**目录结构即系统状态。**

> **核心概念**：ClawOPC 有三类 workspace：
> 1. **共享管理区** — `~/.openclaw/workspace/.console/`，Console 管理的 Role 包和岗位信息
> 2. **Boss 工作区** — `~/.openclaw/workspace/boss/`，Boss Agent 的独立工作区
> 3. **Employee 独立工作区** — 每个 Employee Agent 有自己独立的 workspace 路径，存放任务文件和标准文件
>
> 这种设计避免了多 Agent 共享同一目录导致的文件冲突。

---

## 完整目录结构

```
~/.openclaw/                           ← OpenClaw 主目录
├── openclaw.json                      ← Gateway 配置文件
├── credentials/                       ← 渠道凭证
├── agents/                            ← Agent 状态和会话
│   ├── boss/
│   │   ├── agent/                     ← 认证配置
│   │   └── sessions/                  ← 会话记录（JSONL）
│   ├── developer/
│   │   ├── agent/                     ← 认证配置
│   │   └── sessions/                  ← 会话记录（JSONL）
│   ├── designer/
│   │   ├── agent/
│   │   └── sessions/
│   └── .../
│
├── workspace/                         ← ClawOPC 共享管理区
│   ├── .console/                      ← Console 管理区（只有 Console 写）
│   │   ├── positions/                 ← 岗位信息
│   │   │   ├── developer.md
│   │   │   ├── designer.md
│   │   │   └── ...
│   │   └── roles/                     ← Role 包存储
│   │       ├── boss/                  ← Boss Role 包
│   │       │   ├── role.md
│   │       │   ├── soul.md
│   │       │   ├── identity.md
│   │       │   └── skills/
│   │       │       └── boss-skill.md
│   │       ├── developer/             ← 开发者 Role 包
│   │       │   ├── role.md            ← 职责定义（入职时映射为 AGENTS.md）
│   │       │   ├── soul.md            ← 性格与价值观（入职时映射为 SOUL.md）
│   │       │   ├── identity.md        ← 身份认知（入职时映射为 IDENTITY.md）
│   │       │   ├── skills/            ← 职能技能包
│   │       │   └── avatar/            ← 视觉形象
│   │       │       ├── avatar_idle.gif
│   │       │       ├── avatar_working.gif
│   │       │       └── avatar_meta.json
│   │       ├── designer/
│   │       │   └── ...
│   │       └── .../
│   │
│   ├── .logs/                         ← 系统日志
│   │   └── token-usage.log            ← Token 用量记录
│   │
│   └── .archive/                      ← 已完成任务归档
│       └── 2025-01/
│           └── task-20250115-001/
│
├── workspace/boss/                    ← Boss 独立工作区
│   ├── AGENTS.md                      ← Boss 行为规则（来自 boss/role.md）
│   ├── SOUL.md                        ← Boss 性格（来自 boss/soul.md）
│   ├── IDENTITY.md                    ← Boss 身份（来自 boss/identity.md）
│   ├── skills/                        ← boss-skill（管理团队行为）
│   │   └── SKILL.md
│   └── work.log                       ← Boss 操作日志
│
├── workspace/developer/               ← Developer 独立工作区
│   ├── AGENTS.md                      ← 行为规则（来自 role.md）
│   ├── SOUL.md                        ← 性格价值观（来自 soul.md）
│   ├── IDENTITY.md                    ← 身份认知（来自 identity.md）
│   ├── HEARTBEAT.md                   ← 心跳行为指令
│   ├── skills/                        ← 技能包（employee-skill + 职能 skills）
│   │   └── SKILL.md                   ← employee-skill 入口
│   ├── pending/                       ← 等待处理的任务
│   ├── processing/                    ← 正在处理的任务
│   ├── done/                          ← 已完成的任务
│   └── work.log                       ← 工作日志
│
└── workspace/designer/                ← Designer 独立工作区（结构相同）
    ├── AGENTS.md
    ├── SOUL.md
    ├── IDENTITY.md
    ├── HEARTBEAT.md
    ├── skills/
    ├── pending/
    ├── processing/
    ├── done/
    └── work.log
```

> **注意**：`~/.openclaw/` 目录由 OpenClaw 管理。
> `.console/` 是 ClawOPC 共享管理区，存放 Role 包和岗位信息。
> Boss 有自己的独立工作区（无 pending/processing/done/，Boss 不处理任务）。
> 每个 Employee Agent 的独立工作区由 `openclaw.json` 中的 `workspace` 字段配置。

---

## .console/ 共享管理区

Console 的管理区，只有 Console 有写权限。
存放 Role 包原始文件和岗位状态。

### positions/

存储所有岗位的状态文件：

```
.console/positions/
├── developer.md
├── designer.md
├── marketing.md
└── ...
```

每个岗位文件格式：

```markdown
---
role: developer
status: vacant          ← vacant / occupied
agent_id:               ← Agent ID（occupied 时填写）
occupied_at:            ← 入职时间（occupied 时填写）
---
```

状态只有两种：

```
vacant    → 岗位空缺，等待入职
occupied  → 岗位已入职，虚拟员工在岗
```

### roles/

存储所有 Role 包的**原始文件**，每个角色一个子目录：

```
.console/roles/
├── developer/
│   ├── role.md           ← 职责定义
│   ├── soul.md           ← 性格与价值观
│   ├── identity.md       ← 身份认知
│   ├── skills/           ← 技能包
│   │   ├── code-review.md
│   │   ├── write-code.md
│   │   └── ...
│   └── avatar/           ← 视觉形象
│       ├── avatar_idle.gif
│       ├── avatar_working.gif
│       └── avatar_meta.json
└── designer/
    └── ...
```

> 入职时，Console 将 Role 包文件复制到 Agent 独立工作区并映射为 OpenClaw 标准文件。
> `.console/roles/` 保留原始文件作为主副本。

Role 包详细规范见 [08-Role-Standard](./08-Role-Standard.md)。

---

## Agent 独立工作区

每个 Agent 拥有**独立的工作区路径**，由 Console 在入职时创建。

### 标准文件（OpenClaw 识别）

```
<agent-workspace>/
├── AGENTS.md             ← 行为规则（来自 Role 包 role.md）
├── SOUL.md               ← 性格价值观（来自 Role 包 soul.md）
├── IDENTITY.md           ← 身份认知（来自 Role 包 identity.md）
├── HEARTBEAT.md          ← 心跳行为指令（ClawOPC 生成）
└── skills/
    └── SKILL.md          ← employee-skill 入口（ClawOPC 生成）
```

这些文件由 OpenClaw 的 `buildAgentSystemPrompt()` 自动读取，
注入到 Agent 的 System Prompt 中。

### 任务目录

```
<agent-workspace>/
├── pending/              ← 等待处理
├── processing/           ← 正在处理
├── done/                 ← 已完成
└── work.log              ← 工作日志
```

### pending/

任务进入角色工作区的入口。

```
任务文件命名：
  task-<id>.md

示例：
  task-20250115-001.md
  task-20250115-002.md
```

心跳触发时，Agent 扫描此目录，发现文件即开始处理。

### processing/

任务正在被处理时移入此目录。

```
移入操作：
  pending/task-<id>.md → processing/task-<id>.md

此操作为原子操作（rename）
同一时间只有一个任务在 processing/
```

处理完成后，产出文件写入同目录：

```
processing/
├── task-<id>.md              ← 任务文件
└── <role>_output.md          ← 本角色产出物
```

### done/

任务处理完成，等待 Boss 决策时移入此目录。

```
done/
├── task-<id>.md              ← 任务文件
├── <role>_output.md          ← 本角色产出物
└── awaiting_boss             ← 标记文件，触发 Console 提醒
```

`awaiting_boss` 是一个空文件，
Console 检测到此文件即向 Boss 展示待决策提醒。

### work.log

角色的完整工作日志，**只追加，不修改**。

```
格式：
  [timestamp] [task-id] [event] [detail]

示例：
  [2025-01-15T10:00:00Z] [task-20250115-001] [received] 任务已接收
  [2025-01-15T10:00:05Z] [task-20250115-001] [started] 开始处理
  [2025-01-15T10:05:30Z] [task-20250115-001] [done] 产出已完成
  [2025-01-15T10:05:31Z] [task-20250115-001] [awaiting_boss] 等待 Boss 决策
```

work.log 详细规范见 [06-Worklog-Standard](./06-Worklog-Standard.md)。

---

## 任务文件在目录间的流转

```
创建
  Console → <agent-workspace>/pending/task-<id>.md

认领（心跳触发）
  pending/ → processing/

完成
  processing/ → done/
  写入 awaiting_boss

Boss 决策 forward
  done/ 中的所有文件
  → 打包携带
  → <next-agent-workspace>/pending/task-<id>.md

Boss 决策 rework
  done/ 中的所有文件
  → 退回
  → <agent-workspace>/pending/task-<id>.md

Boss 决策 complete
  done/ 归档到 .archive/
  任务结束
```

---

## 任务携带历史

任务每经过一个角色，产出物随任务一起流转。

```
task-20250115-001.md 经过 developer 后：

  task-20250115-001.md        ← 任务定义（含 Pipeline）
  developer_output.md         ← Developer 产出

Console 执行 forward 时，将以上所有文件
写入 designer 工作区的 pending/。

designer 处理完成后：

  task-20250115-001.md        ← 任务定义
  developer_output.md         ← Developer 产出
  designer_output.md          ← Designer 产出

进入下一角色时，继续携带所有历史。
```

---

## 目录权限规范

```
目录                                   读          写
──────────────────────────────────────────────────────────────
.console/positions/                   Console     Console
.console/roles/                       Console     Console
<agent-workspace>/pending/            Agent       Console（投递）
<agent-workspace>/processing/         Agent       Agent
<agent-workspace>/done/               Console     Agent
<agent-workspace>/work.log            Console     Agent
<agent-workspace>/AGENTS.md           Agent(RO)   Console（入职时）
<agent-workspace>/SOUL.md             Agent(RO)   Console（入职时）
<agent-workspace>/IDENTITY.md         Agent(RO)   Console（入职时）
<agent-workspace>/HEARTBEAT.md        Agent(RO)   Console（入职时）
```

---

## 命名规范

```
任务 ID：
  task-<YYYYMMDD>-<序号3位>
  示例：task-20250115-001

角色目录名：
  全小写，连字符分隔
  示例：developer / ui-designer / content-writer

产出文件名：
  <role>_output.md
  示例：developer_output.md / designer_output.md

标记文件：
  awaiting_boss     ← 等待 Boss 决策
  （无扩展名，空文件）
```

---

## 初始化

### 系统初始化

新部署时，`clawopc init` 命令初始化共享管理区：

```bash
~/.openclaw/workspace/
  .console/positions/    ← 创建目录
  .console/roles/        ← 创建目录，导入内置 Role 包
  .logs/                 ← 创建目录
  .archive/              ← 创建目录
```

### Agent 入职初始化

发布岗位并执行入职时，Console 确定性代码创建 Agent 独立工作区：

```bash
# Console 入职操作（确定性代码）
<agent-workspace>/
  AGENTS.md              ← 从 .console/roles/<role>/role.md 复制映射
  SOUL.md                ← 从 .console/roles/<role>/soul.md 复制映射
  IDENTITY.md            ← 从 .console/roles/<role>/identity.md 复制映射
  HEARTBEAT.md           ← ClawOPC 生成的心跳行为指令
  skills/
    SKILL.md             ← ClawOPC 生成的 employee-skill
    <skill-name>.md      ← 从 .console/roles/<role>/skills/ 复制
  pending/               ← 创建目录
  processing/            ← 创建目录
  done/                  ← 创建目录
  work.log               ← 创建空文件
```

---

**03-workspace 完成。**
