# ClawOPC Spec — 02 Architecture

```markdown
---
doc_id: spec-02
title: Architecture
version: 0.2.0
status: draft
created_at: 2025-01-15
updated_at: 2026-03-15
---
```

---

## 整体架构

ClawOPC 采用**两层架构**：Console + OpenClaw Gateway。

没有 Orchestrator 中间层，没有额外的调度进程。
**所有角色（包括 Boss）都是 OpenClaw Agent。**
Boss Agent 通过 Console 与系统交互，Employee Agent 通过心跳驱动自动工作。

所有组件运行在**同一台云服务器**上。

> **核心决策**：Boss 也是 Agent，拥有 Boss Role 包和 boss-skill，
> 通过 Console 这个专属界面管理团队。Employee Agent 通过 OpenClaw
> 原生 Heartbeat 机制定时触发，扫描 pending/ 目录自主工作。

```
┌─────────────────────────────────────────────────────────────────┐
│                      一台云服务器                                  │
│                                                                 │
│  ┌─────────────┐                                                │
│  │   Console   │  ← Boss Agent 的专属交互界面                    │
│  │  (React)    │     Boss 通过 Console 读写文件系统               │
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
│  │  │              │  │              │  │              │      ││
│  │  │ workspace:   │  │ workspace:   │  │ workspace:   │      ││
│  │  │ ~/ws/dev/    │  │ ~/ws/des/    │  │ ~/ws/mkt/    │      ││
│  │  │              │  │              │  │              │      ││
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
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 组件职责

### Console

```
定位：
  Boss Agent 的专属交互界面
  Boss 通过 Console 与文件系统交互

职责：
  - 展示 workspace 整体状态
  - 接收 Boss 的操作指令
  - 发布岗位（写 positions/ 和 roles/）
  - 创建任务（写 pending/task-*.md）
  - 触发任务流转（forward / rework / complete）
  - 执行入职操作（确定性代码，非 Agent 完成）

不负责：
  - 执行任何 AI 推理
  - 修改任务内容
  - 代替 Boss 做决策

实现方式：
  - 独立的 Web 应用（React）
  - 直接读写文件系统
  - 是 Boss Agent 的"手和眼"
```

### OpenClaw Gateway

```
职责：
  - 运行单一 Gateway 进程，端口 18789
  - 托管多个 Agent 实例（每个角色一个 Agent）
  - 通过 multi-agent routing 将消息路由到对应 Agent
  - 内嵌 Pi SDK，管理 Agent 会话生命周期
  - 工具注入和 System Prompt 构建
  - Heartbeat 心跳触发（定时唤醒 Agent）

核心特性（来自 OpenClaw）：
  - 单进程多路复用（WebSocket + HTTP API + Control UI）
  - 每个 Agent 独立的工作区、会话存储、认证配置
  - 嵌入式 Pi SDK 完全控制 Agent 循环
  - 原生 Heartbeat 支持（HEARTBEAT.md + heartbeat.every）
  - 支持多模型提供商和认证轮换
```

### Boss Agent

```
定位：
  你自己，通过 Console 与系统交互的 Agent

职责：
  - 拥有独立的 agentId: boss 和独立的工作区
  - 通过 boss-skill 定义如何管理团队
  - 通过 Console 创建任务、做决策、管理员工
  - 拥有 Boss Role 包（role.md + soul.md + identity.md）

与 Employee Agent 的区别：
  - Boss 不通过心跳驱动，而是通过 Console 交互
  - Boss 不扫描 pending/，而是主动创建和审批任务
  - Boss 的 skill 是 boss-skill（管理行为），不是 employee-skill（任务处理行为）
```

### Employee Agent × N

```
职责：
  - 作为 Gateway 中的 Agent 实例（agentId: <role>）
  - 拥有独立的 workspace 路径（避免多 Agent 共享覆盖）
  - 通过 Heartbeat 机制定时触发工作循环
  - 加载 HEARTBEAT.md 中定义的心跳行为
  - 扫描 pending/ 目录，认领并处理任务
  - 执行任务，产出交付物
  - 记录 work.log
  - 完成后标记 awaiting_boss

每个 Employee Agent：
  - 拥有独立的 agentId 和独立的工作区路径
  - 独立的会话存储（~/.openclaw/agents/<agentId>/sessions/）
  - 工作区中包含 OpenClaw 标准文件（AGENTS.md / SOUL.md / IDENTITY.md / HEARTBEAT.md）
  - 通过心跳驱动，不需要持续轮询
  - 只关注自己的 pending/，不感知其他角色的存在
```

---

## 关键技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 驱动方式 | OpenClaw Heartbeat | 原生支持，无需 Orchestrator 中间层 |
| Agent 隔离 | 每个 Agent 独立 workspace 路径 | 避免多 Agent 共享 workspace 互相覆盖 |
| 身份注入 | role.md → AGENTS.md, soul.md → SOUL.md, identity.md → IDENTITY.md | 对齐 OpenClaw 标准文件映射 |
| 入职方式 | Console 确定性代码完成 | 文件操作应用确定性代码，不让 LLM 做文件操作 |
| 空转成本 | HEARTBEAT_OK 静默处理，不调 LLM | OpenClaw 原生支持 |
| 命令风险 | employee-skill 中给精确命令模板 | 避免 LLM 自行拼接命令出错 |

---

## 心跳驱动机制

ClawOPC 利用 OpenClaw 原生的 Heartbeat 机制驱动虚拟员工工作循环：

```
每 5 分钟心跳触发：
  → Agent 读取 HEARTBEAT.md
  → 检查 pending/ 是否有 task-*.md
  → 有任务：认领 → 处理 → 产出 → 完成 → done/ + awaiting_boss
  → 无任务：HEARTBEAT_OK（静默，不调 LLM）
```

### HEARTBEAT.md

每个 Agent 工作区中放置 `HEARTBEAT.md`，定义心跳行为：

```markdown
# HEARTBEAT

## 启动时检查

1. 检查 processing/ 目录是否有残留任务
   → 有：说明上次异常中断，继续处理
   → 无：正常流程

## 心跳行为

1. 列出 pending/ 目录下所有 task-*.md 文件
2. 如果没有文件 → 回复 HEARTBEAT_OK（不调 LLM）
3. 如果有文件 → 按文件名排序，取第一个
4. 执行认领（mv pending/ → processing/）
5. 读取任务内容，按 instruction 执行
6. 产出交付物，写入 done/
7. 创建 awaiting_boss 标记

## 精确命令模板

列出 pending/ 文件：
  ls pending/task-*.md 2>/dev/null

认领任务（逐个移动，先 ls 再 mv 最后验证）：
  ls pending/
  mv pending/task-<id>.md processing/task-<id>.md
  mv pending/*_output*.md processing/ 2>/dev/null
  ls processing/

完成任务（逐个移动）：
  ls processing/
  mv processing/task-<id>.md done/task-<id>.md
  mv processing/*_output*.md done/ 2>/dev/null
  touch done/awaiting_boss
  ls done/
```

### openclaw.json 心跳配置

```jsonc
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "5m",
        "activeHours": { "start": "08:00", "end": "22:00" }
      }
    }
  }
}
```

- `every: "5m"` — 每 5 分钟触发一次心跳
- `activeHours` — 限定活跃时段，避免凌晨空转浪费 Token

---

## 进程模型

同一台服务器上运行两个进程：

```
进程列表示例：

PID 1001  console (React Web 应用) ← Boss Agent 的专属界面
PID 1002  openclaw gateway --port 18789
          ├── Agent: boss       (agentId: boss, workspace: ~/ws/boss/)
          ├── Agent: developer  (agentId: developer, workspace: ~/ws/dev/)
          ├── Agent: designer   (agentId: designer, workspace: ~/ws/des/)
          ├── Agent: marketing  (agentId: marketing, workspace: ~/ws/mkt/)
          └── ... × N
```

> **与 OpenClaw 架构的对齐**：OpenClaw 使用单进程多路复用模型，
> 多个 Agent 在 Gateway 进程内通过 multi-agent routing 隔离。
> 每个 Agent 有独立的工作区路径和会话存储。

Agent 之间**不直接通信**（除非显式配置 `tools.agentToAgent`），
通过文件系统中的任务文件交换状态。

---

## 启动配置

OpenClaw Gateway 通过 `~/.openclaw/openclaw.json` 配置文件管理所有 Agent：

```jsonc
// ~/.openclaw/openclaw.json
{
  "logging": { "level": "info" },

  "agents": {
    "defaults": {
      "model": { "primary": "anthropic/claude-sonnet-4-20250514" },
      "heartbeat": {
        "every": "5m",
        "activeHours": { "start": "08:00", "end": "22:00" }
      }
    },
    "list": [
      { "agentId": "boss", "workspace": "~/.openclaw/workspace/boss" },
      { "agentId": "developer", "workspace": "~/.openclaw/workspace/developer" },
      { "agentId": "designer", "workspace": "~/.openclaw/workspace/designer" },
      { "agentId": "marketing", "workspace": "~/.openclaw/workspace/marketing" }
    ]
  },

  "session": {
    "scope": "per-sender"
  }
}
```

每个 Agent 拥有独立的 workspace 路径，
通过 `agents.list[].workspace` 配置，
避免多 Agent 共享同一 workspace 目录导致文件冲突。

### 环境变量（可选）

```bash
OPENCLAW_HOME          # 主目录，默认 ~/.openclaw
OPENCLAW_STATE_DIR     # 状态目录覆盖
OPENCLAW_CONFIG_PATH   # 配置文件路径覆盖
```

---

## 文件系统原则

```
写操作：
  先写临时文件，再 rename
  保证原子性，避免读到半写状态

读操作：
  任何时候读都安全
  幂等，不产生副作用

互斥：
  通过目录结构保证
  不依赖文件锁
  pending/ → processing/ 的移动即为加锁

多文件移动：
  SKILL.md 强调「先 ls，再逐个 mv，最后验证」
  不使用通配符批量移动
  确保每一步可追溯
```

---

## 入职流程（Console 确定性代码完成）

Employee 入职不由 Agent 自行完成，而是由 **Console 的确定性代码**执行。
Boss Agent 在系统初始化（`clawopc init`）时自动创建。

```
Boss Agent 初始化（clawopc init 时完成）：
   → 创建 Boss 工作区（~/.openclaw/workspace/boss/）
   → 从 .console/roles/boss/ 复制 Boss Role 包文件：
     role.md → AGENTS.md
     soul.md → SOUL.md
     identity.md → IDENTITY.md
     skills/boss-skill → skills/
   → 创建空 work.log
   → 在 openclaw.json 中注册 Boss Agent

Employee 入职流程：

1. Boss 在 Console 中发布岗位
   Console 在共享管理区写入 positions/<role>.md（status: vacant）

2. Console 执行入职操作（确定性代码）
   → 创建 Employee Agent 独立 workspace 目录
   → 创建 pending/ processing/ done/ 子目录
   → 从 .console/roles/<role>/ 复制 Role 包文件：
     role.md → <workspace>/AGENTS.md
     soul.md → <workspace>/SOUL.md
     identity.md → <workspace>/IDENTITY.md
     skills/ → <workspace>/skills/
   → 写入 HEARTBEAT.md（心跳行为定义）
   → 写入 employee SKILL.md（工作行为框架）
   → 创建空 work.log
   → 更新 positions/<role>.md（status: occupied）

3. OpenClaw Gateway 检测到新 Agent 配置
   → 加载 Agent 实例
   → 读取工作区标准文件（AGENTS.md / SOUL.md / IDENTITY.md / HEARTBEAT.md / skills/）
   → 构建 System Prompt
   → 开始心跳循环
```

> **为什么不让 Agent 自行入职**：
> 文件复制、目录创建、配置写入等操作是确定性的，
> 用代码实现 100% 可靠，用 LLM 做文件操作有出错风险。

---

## 任务流转（心跳视角）

```
Boss Agent（通过 Console）创建任务
  → Console 写入 <workspace>/pending/task-<id>.md

下一次心跳触发（≤5 分钟）
  → Employee Agent 读取 HEARTBEAT.md
  → 列出 pending/ 目录，发现 task-<id>.md
  → 移入 processing/（原子 rename）
  → 读取任务内容，调用 LLM 处理
  → 产出 <role>_output.md
  → 写入 work.log
  → 移入 done/，创建 awaiting_boss 标记

Console 轮询检测到 done/awaiting_boss
  → 展示给 Boss Agent
  → Boss 决策：forward / rework / complete

Console 执行流转
  → forward：将任务文件写入下一角色的 pending/
  → rework：将任务文件退回当前角色的 pending/
  → complete：归档到 .archive/
```

---

## 部署规模

```
最小部署（1人测试）：
  Console          × 1
  OpenClaw Gateway × 1（托管 1 个 Agent）

标准部署（1人公司）：
  Console          × 1
  OpenClaw Gateway × 1（托管 N 个 Agent，每个角色 1 个）

扩展部署（多项目并行）：
  Console          × 1
  OpenClaw Gateway × 1（或多实例，不同端口）
  Agent × N（同一 Gateway 内多个 Agent 并行处理）
```

> **多实例说明**：OpenClaw 支持在同一主机上运行多个 Gateway 实例，
> 需要唯一化端口、配置路径、状态目录和工作区路径。

---

## 与 OpenClaw 的关系

```
OpenClaw Gateway 负责：
  - 单进程运行，管理多个 Agent（multi-agent routing）
  - Heartbeat 心跳定时触发 Agent
  - 内嵌 Pi SDK，驱动 Agent 会话循环
  - 工具系统（exec, browser, web_search, canvas 等）
  - System Prompt 构建（buildAgentSystemPrompt）
  - 会话持久化（JSONL 格式，支持分支和压缩）
  - 多模型提供商支持和认证轮换
  - 上下文管理（自适应压缩、Cache-TTL 修剪）
  - 可选的 Control UI（浏览器管理界面 http://127.0.0.1:18789/）

ClawOPC 负责：
  - 文件系统规范（workspace 任务流转结构）
  - Role 包标准（映射为 OpenClaw AGENTS.md / SOUL.md / IDENTITY.md）
  - Boss Role 包 + boss-skill 定义（Boss Agent 的管理行为）
  - employee-skill 定义（Employee Agent 的工作行为框架）
  - HEARTBEAT.md 定义（心跳行为指令）
  - Console UI 标准（Boss Agent 的专属交互界面）
  - Console 确定性入职流程
  - 任务生命周期规范（Pipeline + Boss 决策）
  - 工作日志规范（work.log）

关系：
  ClawOPC 是运行在 OpenClaw Gateway 之上的**应用规范层**
  OpenClaw Gateway 是 ClawOPC 的运行时基础设施
  所有角色（含 Boss）都是 OpenClaw Agent
  ClawOPC 的 Role 包映射为 OpenClaw 的标准工作区文件
  ClawOPC 复用 OpenClaw 的 Agent 生命周期、工具系统和会话管理
  ClawOPC 利用 OpenClaw 的 Heartbeat 机制驱动 Employee 工作循环
```

---

## 安全边界

```
每个 Employee Agent：
  通过 OpenClaw 的工具权限控制访问范围
  推荐配置 tools.deny 限制高风险工具

  只读写自己的独立工作区
  <agent-workspace>/

  employee-skill 中给精确命令模板
  避免 LLM 自行拼接命令

Console：
  可读取所有 Agent 工作区（展示用）
  写操作仅限：
    创建/更新 positions/（发布岗位）
    入职文件操作（Role 包 → 工作区）
    任务文件的创建和流转

OpenClaw 安全机制：
  Agent 工具权限：通过 tools.deny / tools.profile 控制
  沙箱模式：可选 Docker 隔离（sandbox.mode: "all"）
  Agent 间通信：默认关闭，需显式配置 tools.agentToAgent
  工作区访问：可配置 workspaceAccess: "ro" / "none"
```

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| LLM 文件操作出错 | employee-skill 中给精确 shell 命令模板，Agent 只需 exec 运行 |
| 多文件移动非原子 | SKILL.md 强调「先 ls，再逐个 mv，最后验证」 |
| processing 中断恢复 | HEARTBEAT.md 中加启动时检查 processing/ 残留逻辑 |
| 心跳空转成本 | HEARTBEAT_OK 静默不调 LLM；activeHours 限定活跃时段 |
| YAML Front Matter 解析 | HEARTBEAT.md 中明确只需读取文件名，不需解析 YAML |

---

**02-architecture 完成。**
