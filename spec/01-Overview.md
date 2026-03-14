# ClawOPC Spec — 01 Overview

```markdown
---
doc_id: spec-01
title: Overview
version: 0.2.0
status: draft
created_at: 2025-01-15
updated_at: 2026-03-15
---
```

---

## 什么是 ClawOPC

ClawOPC 是一个基于 AI Agent 的**一人公司（One Person Company）操作系统**。

它让一个人可以像管理一家真实公司一样，
通过 **Console（指挥台）** 调度多个 AI Agent，
每个 Agent 扮演不同的公司角色，
协作完成从创意到交付的完整业务流程。

所有组件运行在**同一台云服务器**上。

---

## 核心理念

### 所有人都是 Agent，包括你

```
传统方式：你 → 做所有事

ClawOPC：你（Boss Agent）→ Console → Employee Agent 团队 → 交付
```

在 ClawOPC 中，**Boss 也是一个 OpenClaw Agent**。
你拥有自己的 Role 包（boss role）、Skill（boss-skill）和工作区。
你通过 **Console** 这个专属界面与系统交互。

Boss Agent 的工作是：
- 通过 Console 管理团队
- 下发任务
- 做关键决策
- 把控方向

Employee Agent 的工作是：
- 执行具体任务
- 按流程流转
- 产出可交付物

---

### 虚拟员工 = OpenClaw Agent + Role 包

每个虚拟员工由以下部分组成：

```
虚拟员工 = OpenClaw Agent 实例
         + employee-skill（共用行为框架）
         + Role 包（角色身份定义）
         + HEARTBEAT.md（心跳行为指令）
```

**Boss 也是一个 OpenClaw Agent**，但与 Employee Agent 不同：

```
Boss Agent = OpenClaw Agent 实例
           + boss-skill（通过 Console 管理团队）
           + Boss Role 包（Boss 的身份定义）
           + Console（专属交互界面）
```

**OpenClaw** 是一个自托管的 AI Gateway，运行在本地或云服务器上，
通过单一 Gateway 进程管理多个 Agent（包括 Boss），每个 Agent 拥有**独立的工作区**和会话。
OpenClaw 内嵌 Pi SDK 作为编码 Agent 运行时，支持工具调用、会话持久化和多模型切换。
ClawOPC 不重复造轮子，复用 OpenClaw 的 Agent 基础设施。

**employee-skill** 是所有虚拟员工共用的行为框架，定义如何处理任务、如何产出交付物。

**Role 包** 是角色的完整定义，包含职责、性格、身份认知、技能、形象。
Console 在入职时将 Role 包映射为 OpenClaw 标准文件，虚拟员工才真正"成为"这个角色。

**HEARTBEAT.md** 定义了心跳触发时的行为指令：扫描任务、认领、处理、完成。

> **入职方式**：Employee 入职由 Console 确定性代码完成（复制文件、创建目录），
> 不让 Agent 自行完成文件操作，确保 100% 可靠。
> Boss Agent 在系统初始化时自动创建，无需入职流程。

---

### 角色即身份，身份即边界

```
AGENTS.md    → 我的行为规则和工作方式（对应 OpenClaw 工作区标准文件）
SOUL.md      → 我的性格和价值观（对应 OpenClaw 工作区标准文件）
IDENTITY.md  → 我是谁（对应 OpenClaw 工作区标准文件）
HEARTBEAT.md → 我的心跳行为（对应 OpenClaw 工作区标准文件）
skills/      → 我能做什么
avatar/      → 我长什么样
```

> **与 OpenClaw 标准的关系**：OpenClaw 工作区默认识别 `AGENTS.md`、`SOUL.md`、
> `IDENTITY.md`、`USER.md`、`TOOLS.md`、`HEARTBEAT.md` 等文件。
> ClawOPC 的 Role 包在入职时由 Console 映射为标准文件：
> `role.md` → `AGENTS.md`，`soul.md` → `SOUL.md`，`identity.md` → `IDENTITY.md`。

身份一旦激活，**不可更改**。
这保证了每个虚拟员工的行为边界清晰可预期。

---

### Avatar：角色的视觉形象

每个角色拥有两个 GIF 动态头像：

```
avatar/
├── avatar_idle.gif     ← 待机动画（等待任务时循环播放）
├── avatar_working.gif  ← 工作动画（执行任务时循环播放）
└── avatar_meta.json    ← 元数据
```

**制作规范：**

```
原始尺寸：400 × 400 px
帧率：    12 fps
色深：    256 色
文件大小：≤ 500 KB / 每个
```

**缩放展示规范：**

```
┌──────────────┬────────────┬──────────────────┬─────────────────────┐
│   场景        │   尺寸     │   使用文件         │   触发条件           │
├──────────────┼────────────┼──────────────────┼─────────────────────┤
│ 团队总览      │  48×48 px  │ avatar_idle.gif   │ 默认                │
│ 任务详情      │  80×80 px  │ avatar_idle.gif   │ pending             │
│ 工作中        │  80×80 px  │ avatar_working.gif│ processing          │
│ 角色主页      │ 240×240 px │ avatar_idle.gif   │ 默认                │
│ 入职欢迎      │ 400×400 px │ avatar_working.gif│ 入职激活时           │
└──────────────┴────────────┴──────────────────┴─────────────────────┘
```

**avatar_meta.json 标准：**

```json
{
  "size": {
    "width": 400,
    "height": 400
  },
  "fps": 12,
  "files": {
    "idle":    "avatar_idle.gif",
    "working": "avatar_working.gif"
  },
  "scale_hints": {
    "48":  "idle",
    "80":  "idle",
    "240": "idle",
    "400": "idle"
  }
}
```

---

### 文件即状态，目录即真相

ClawOPC 不依赖数据库。
所有状态都存在于**本地文件系统**中：

```
任务在哪个目录 = 任务在哪个阶段
文件内容      = 当前状态
work.log      = 完整历史
```

任何时刻，你都可以直接打开文件夹查看真相。

---

## 系统组成

所有组件运行在同一台云服务器上。
所有角色（包括 Boss）都是 OpenClaw Agent。
Console 是 Boss Agent 的专属交互界面，直接读写文件系统。
OpenClaw Gateway 通过心跳驱动 Employee Agent。
每个 Agent 拥有**独立的工作区路径**：

```
┌─────────────────────────────────────────────────────────────────┐
│                      一台云服务器                                  │
│                                                                 │
│  ┌─────────────┐                                                │
│  │   Console   │  ← Boss Agent 的专属交互界面                    │
│  │   (React)   │     Boss 通过 Console 读写文件系统               │
│  │             │     管理员工、创建任务、做决策                    │
│  └──────┬──────┘                                                │
│         │  读写文件系统                                           │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              OpenClaw Gateway (单进程 :18789)                ││
│  │                                                             ││
│  │  ┌──────────────┐                                           ││
│  │  │  Agent:      │  ← Boss Agent（你）                        ││
│  │  │  boss        │     boss-skill + Console 交互              ││
│  │  │  workspace:  │                                           ││
│  │  │  ~/ws/boss/  │                                           ││
│  │  └──────────────┘                                           ││
│  │                                                             ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │  Agent:      │  │  Agent:      │  │  Agent:      │      ││
│  │  │  developer   │  │  designer    │  │  marketing   │      ││
│  │  │  workspace:  │  │  workspace:  │  │  workspace:  │      ││
│  │  │  ~/ws/dev/   │  │  ~/ws/des/   │  │  ~/ws/mkt/   │      ││
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │      ││
│  │  │ │AGENTS.md │ │  │ │AGENTS.md │ │  │ │AGENTS.md │ │      ││
│  │  │ │SOUL.md   │ │  │ │SOUL.md   │ │  │ │SOUL.md   │ │      ││
│  │  │ │IDENTITY  │ │  │ │IDENTITY  │ │  │ │IDENTITY  │ │      ││
│  │  │ │HEARTBEAT │ │  │ │HEARTBEAT │ │  │ │HEARTBEAT │ │      ││
│  │  │ │skills/   │ │  │ │skills/   │ │  │ │skills/   │ │      ││
│  │  │ │pending/  │ │  │ │pending/  │ │  │ │pending/  │ │      ││
│  │  │ │processing│ │  │ │processing│ │  │ │processing│ │      ││
│  │  │ │done/     │ │  │ │done/     │ │  │ │done/     │ │      ││
│  │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │      ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘      ││
│  │                                                             ││
│  │  heartbeat: every 5m → 扫描 pending/ → 有活就干              ││
│  │  Pi SDK · multi-agent routing · 会话隔离                     ││
│  └──────┬──────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   本地文件系统                                ││
│  │      Boss 工作区 + 各 Employee 独立 workspace                ││
│  │      .console/ 共享管理区                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

> **架构说明**：ClawOPC 采用两层架构（Console + OpenClaw Gateway），
> 没有 Orchestrator 中间层。所有角色（包括 Boss）都是 OpenClaw Agent。
> Boss Agent 通过 Console 交互，Employee Agent 通过心跳驱动。
> 每个 Agent 有独立的工作区路径，避免共享 workspace 导致文件冲突。

---

## 核心概念速览

| 概念 | 说明 |
|------|------|
| **Boss Agent** | 你，也是一个 OpenClaw Agent，拥有 Boss Role 包和 boss-skill，通过 Console 交互 |
| **Console** | Boss Agent 的专属交互界面，React Web 应用，直接读写文件系统 |
| **OpenClaw Gateway** | 自托管 AI 多渠道网关，单进程管理多个 Agent（含 Boss），内嵌 Pi SDK |
| **Employee Agent** | Gateway 中的 Employee Agent 实例，通过心跳驱动，拥有**独立工作区**和会话 |
| **Heartbeat** | OpenClaw 原生心跳机制，每 5 分钟触发 Employee Agent 扫描任务 |
| **boss-skill** | Boss 专用 Skill，定义如何通过 Console 管理团队、创建任务、做决策 |
| **employee-skill** | Employee 共用行为框架，定义如何处理任务、如何产出交付物 |
| **Role 包** | 角色完整定义，入职时映射为 OpenClaw 标准文件（AGENTS.md / SOUL.md / IDENTITY.md） |
| **Workspace** | 每个 Agent（含 Boss）独立的文件系统工作区 |
| **Task** | Boss 下发的工作单元，携带完整 Pipeline 定义 |
| **Pipeline** | 任务经过哪些角色、按什么顺序处理 |
| **work.log** | 每个角色的工作日志，纯追加，不可修改 |

---

## 工作流全景

```
1. Boss Agent 通过 Console 发布岗位
   Console → .console/positions/<role>.md (vacant)
   Console → .console/roles/<role>/ (Role 包)

2. Console 执行入职（确定性代码）
   → 创建 Employee Agent 独立 workspace
   → 复制 Role 包 → OpenClaw 标准文件
   → 写入 HEARTBEAT.md + employee SKILL.md
   → 更新 positions/<role>.md (occupied)

3. OpenClaw Gateway 加载 Employee Agent
   → 读取工作区标准文件
   → 构建 System Prompt
   → 开始心跳循环

4. Boss Agent 通过 Console 下发任务
   Console → 创建 task.md（含 Pipeline 定义）
   → 写入第一个角色 workspace 的 pending/

5. 心跳触发，虚拟员工执行任务
   pending/ → processing/ → done/
   产出 <role>_output.md
   记录 work.log

6. Boss Agent 通过 Console 做决策
   Console 检测 done/awaiting_boss
   Boss 选择：forward / rework / complete

7. 任务流转
   Console 将任务文件携带所有历史产出
   写入下一角色 workspace 的 pending/

8. 重复 5-7 直到任务完成
```

---

## 设计原则

| 原则 | 说明 |
|------|------|
| **所有人都是 Agent** | Boss 也是 OpenClaw Agent，通过 Console 交互；统一的 Agent 模型 |
| **文件优先** | 状态存文件，不依赖数据库 |
| **心跳驱动** | 利用 OpenClaw 原生 Heartbeat，无需 Orchestrator |
| **单机部署** | Gateway 单进程 + Console，部署在同一台服务器，简单可靠 |
| **OpenClaw 优先** | 复用 OpenClaw Gateway 的 Agent 基础设施，不重复造轮子 |
| **独立工作区** | 每个 Agent（含 Boss）独立 workspace 路径，避免共享冲突 |
| **确定性入职** | Employee 入职操作由 Console 代码完成，不让 LLM 做文件操作 |
| **角色边界清晰** | 每个虚拟员工只做自己角色内的事 |
| **老板始终掌控** | 每次流转都需要 Boss 确认 |
| **历史完整保留** | work.log 只追加，任务携带全部历史 |
| **社区可扩展** | Role 包遵循标准，任何人可贡献 |

---

## 适用场景

ClawOPC 适合：

- 独立开发者 / 独立创作者
- 自由职业者
- 小型创业团队的核心决策者
- 任何想用 AI 扩展个人产能的人

---

## 文档导航

| 文档 | 内容 |
|------|------|
| [02-Architecture](./02-Architecture.md) | 架构设计（心跳驱动 + 两层架构） |
| [03-Workspace](./03-Workspace.md) | 目录结构标准 |
| [04-Task-Lifecycle](./04-Task-Lifecycle.md) | 任务生命周期 |
| [05-Task-MD-Standard](./05-Task-MD-Standard.md) | task.md 标准 |
| [06-Worklog-Standard](./06-Worklog-Standard.md) | work.log 标准 |
| [07-Employee-Skill](./07-Employee-Skill.md) | Employee Skill 定义 |
| [08-Role-Standard](./08-Role-Standard.md) | Role 包标准 |
| [09-Console-Standard](./09-Console-Standard.md) | Console UI 标准 |
| [10-OpenClaw-Standard](./10-OpenClaw-Standard.md) | OpenClaw Gateway 集成标准 |
