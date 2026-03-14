# ClawOPC

用文件系统驱动的虚拟员工团队。

---

## 这是什么

ClawOPC 是一个基于 AI Agent 的**一人公司（One Person Company）操作系统**。

你是 Boss。
你也是一个 OpenClaw Agent —— 拥有自己的 Role 包、Skill 和工作区。
你通过 **Console** 这个专属界面与系统交互：
创建任务、查看产出、做出决策。

虚拟员工在后台工作：
通过 OpenClaw Gateway 的**心跳机制**定时触发，
扫描任务、认领、处理、提交产出、等待你的决策。

任务在角色之间流转，
直到你说：完成。

没有 Orchestrator，没有消息队列，没有数据库。
**文件系统即协议。**

---

## 架构

ClawOPC 采用**两层架构**：Console + OpenClaw Gateway。

所有角色（包括 Boss）都是 OpenClaw Agent。
利用 OpenClaw 原生 Heartbeat 机制驱动虚拟员工，无需中间调度层。
所有组件运行在**同一台服务器**上。

```
┌─────────────────────────────────────────────────────────────────┐
│                        一台云服务器                                │
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
│  │  │  Agent:      │  ← Boss（你）                              ││
│  │  │  boss        │     通过 boss-skill 与 Console 交互        ││
│  │  │  workspace:  │     管理员工、创建任务、审批决策              ││
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

> **Boss 也是 Agent。**
> Boss 拥有自己的 Role 包（boss-skill）和工作区，
> 通过 Console 这个专属界面与系统交互。
> Console 是 Boss Agent 的"手和眼"。

---

## 核心概念

### 所有人都是 Agent

在 ClawOPC 中，**每个角色都是一个 OpenClaw Agent**：

- **Boss Agent** — 你，通过 Console 与系统交互，管理员工、创建任务、做决策
- **Employee Agent** — 虚拟员工，通过心跳驱动自动工作

```
Boss Agent（你）
  ├── boss role 包（role.md + soul.md + identity.md）
  ├── boss-skill（如何通过 Console 管理团队）
  └── Console ← Boss 的专属交互界面

Employee Agent × N
  ├── employee role 包（职能角色定义）
  ├── employee-skill（如何处理任务）
  └── HEARTBEAT.md ← 心跳驱动自动工作
```

### 虚拟员工

每个虚拟员工是一个独立的 AI 角色：
有名字、有性格、有职责、有技能。

```
虚拟员工 = OpenClaw Agent 实例
         + employee-skill（共用行为框架）
         + Role 包（角色身份定义）
         + HEARTBEAT.md（心跳行为指令）
```

他们运行在 OpenClaw Gateway 中，
通过心跳机制定时触发，
扫描文件系统中的任务，
调用 LLM 处理，
将产出写回文件系统。

### 心跳驱动

虚拟员工通过 OpenClaw 原生 Heartbeat 机制**主动巡检**：

```
每 5 分钟心跳触发：
  → Agent 读取 HEARTBEAT.md
  → 检查 pending/ 是否有 task-*.md
  → 有任务：认领 → 处理 → 产出 → done/ + awaiting_boss
  → 无任务：HEARTBEAT_OK（静默，不调 LLM，零成本）
```

### Pipeline

一个任务可以经过多个角色：

```
Developer → Designer → Developer
```

每个角色按顺序处理，
前一个角色的产出是下一个角色的输入。

### Boss 决策

每个角色完成后，等待你决策：

```
Forward   → 流转到下一个角色
Rework    → 退回重做，附上说明
Complete  → 任务完成，归档
```

### Console — Boss 的专属界面

Console 是 Boss Agent 与系统交互的界面：

```
Console 是什么：
  Boss Agent 的"手和眼"
  读写文件系统的图形化工具
  展示团队状态、待决策任务、任务历史

Console 不是什么：
  不是独立于 Agent 的管理后台
  不是监控大屏
  不处理任务（那是 Employee Agent 的事）
```

### 文件系统即协议

所有通信通过文件系统完成：

```
pending/    → 等待处理
processing/ → 正在处理
done/       → 处理完成，等待决策
```

没有消息队列，没有数据库，没有 API。
文件就是一切。

---

## 快速开始

### 1. 安装 OpenClaw

```bash
# macOS / Linux
curl -fsSL https://openclaw.ai/install.sh | bash

# 或通过 npm
npm install -g openclaw@latest
```

### 2. 初始化 OpenClaw（运行入门向导）

```bash
openclaw onboard --install-daemon
```

### 3. 初始化 ClawOPC 工作区

```bash
clawopc init ~/.openclaw/workspace
```

初始化后的目录结构：

```
~/.openclaw/
├── openclaw.json          ← Gateway 配置（含 Boss + Employee Agent）
└── workspace/
    ├── .console/
    │   ├── roles/          ← 内置 Role 包（含 boss/）
    │   └── positions/      ← 岗位文件（自动生成）
    ├── boss/               ← Boss Agent 工作区
    ├── .logs/              ← 系统日志
    └── .archive/           ← 已完成任务归档
```

### 4. 启动 Gateway

```bash
openclaw gateway --port 18789
```

### 5. 启动 Console

```bash
clawopc console
```

Console 是 Boss Agent 的专属界面。
你通过 Console 管理团队、创建任务、做决策。

### 6. 创建第一个任务

在 Console 中：

1. 发布岗位 → Console 自动完成入职（创建 Agent 工作区、复制 Role 包）
2. 点击「创建任务」→ 填写标题、描述、Pipeline
3. 任务自动投递到第一个角色的 `pending/`
4. 下一次心跳触发（≤5 分钟），虚拟员工开始工作

---

## 使用 Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  console:
    image: clawopc/console:latest
    ports:
      - "3000:3000"
    volumes:
      - openclaw-data:/root/.openclaw
    environment:
      - OPENCLAW_HOME=/root/.openclaw

  gateway:
    image: clawopc/openclaw-gateway:latest
    ports:
      - "18789:18789"
    volumes:
      - openclaw-data:/root/.openclaw
    environment:
      - OPENCLAW_HOME=/root/.openclaw
      - OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}
    restart: unless-stopped

volumes:
  openclaw-data:
```

```bash
# 启动
GATEWAY_TOKEN=your-secure-token docker-compose up -d

# 查看日志
docker-compose logs -f gateway
```

---

## 内置角色

| 角色 | 名字 | 职责 |
|------|------|------|
| **boss** | **Boss** | **团队管理、任务创建、决策审批**（你） |
| developer | Dev | 软件开发、代码实现 |
| designer | Aria | UI/UX 设计 |
| content-writer | Max | 内容创作、文案写作 |
| product-manager | Quinn | 产品需求、功能规划 |
| marketing | Nova | 市场推广、营销策划 |
| qa | Rex | 质量保证、测试方案 |
| data-analyst | Sage | 数据分析、报告撰写 |

---

## 自定义角色

创建自定义角色只需要几个文件：

```
workspace/.console/roles/my-role/
├── role.md        ← 职责定义（入职时映射为 AGENTS.md）
├── soul.md        ← 性格与价值观（入职时映射为 SOUL.md）
├── identity.md    ← 身份认知（入职时映射为 IDENTITY.md）
├── skills/        ← 职能技能包
└── avatar/        ← 视觉形象（idle.gif + working.gif）
```

然后在 Console 中发布岗位，Console 自动完成入职：
创建 Agent 独立工作区 → 复制 Role 包为 OpenClaw 标准文件 → 写入 HEARTBEAT.md → 启动心跳。

---

## 支持的 LLM（通过 OpenClaw Gateway）

| Provider | 模型 |
|----------|------|
| Anthropic | claude-opus-4-6, claude-sonnet 等 |
| OpenAI | gpt-4o, gpt-4o-mini, o1 等 |
| Amazon Bedrock | Claude, Titan 等 |
| Ollama | 本地模型 |
| Moonshot AI | Kimi, Kimi Coding |
| Qwen | 通义千问 |
| MiniMax | MiniMax 模型 |
| LiteLLM | 统一网关（支持 100+ 模型） |
| OpenRouter | 聚合多家提供商 |
| ... | 及更多，详见 OpenClaw 文档 |

配置默认模型：

```jsonc
// ~/.openclaw/openclaw.json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-20250514"
      },
      "heartbeat": {
        "every": "5m",
        "activeHours": { "start": "08:00", "end": "22:00" }
      }
    },
    "list": [
      { "agentId": "boss", "workspace": "~/.openclaw/workspace/boss" },
      { "agentId": "developer", "workspace": "~/.openclaw/workspace/developer" },
      { "agentId": "designer", "workspace": "~/.openclaw/workspace/designer" }
    ]
  }
}
```

---

## 工作区结构

```
~/.openclaw/                         ← OpenClaw 主目录
├── openclaw.json                    ← Gateway 配置
├── agents/                          ← Agent 状态和会话
│   ├── boss/                        ← Boss Agent 会话
│   ├── developer/                   ← Developer Agent 会话
│   └── .../
│
└── workspace/                       ← ClawOPC 工作区
    ├── .console/
    │   ├── roles/                   ← Role 包（原始文件）
    │   │   ├── boss/                ← Boss Role 包
    │   │   ├── developer/
    │   │   ├── designer/
    │   │   └── .../
    │   └── positions/               ← 岗位状态
    │       ├── developer.md
    │       └── designer.md
    │
    ├── boss/                        ← Boss 独立工作区
    │   ├── AGENTS.md                ← Boss 行为规则
    │   ├── SOUL.md                  ← Boss 性格
    │   ├── IDENTITY.md              ← Boss 身份
    │   ├── skills/                  ← boss-skill（管理团队）
    │   └── work.log                 ← Boss 操作日志
    │
    ├── developer/                   ← Developer 独立工作区
    │   ├── AGENTS.md                ← 行为规则（来自 role.md）
    │   ├── SOUL.md                  ← 性格价值观（来自 soul.md）
    │   ├── IDENTITY.md              ← 身份认知（来自 identity.md）
    │   ├── HEARTBEAT.md             ← 心跳行为指令
    │   ├── skills/                  ← 技能包
    │   ├── pending/                 ← 等待处理
    │   ├── processing/              ← 正在处理
    │   ├── done/                    ← 处理完成
    │   └── work.log                 ← 工作日志
    │
    ├── designer/                    ← Designer 独立工作区（结构相同）
    │   └── ...
    │
    ├── .logs/                       ← 系统日志
    │   └── token-usage.log
    │
    └── .archive/                    ← 已完成任务归档
        └── 2025-01/
            └── task-20250115-001/
```

---

## 工作流全景

```
1. Boss 在 Console 中发布岗位
   → Console 自动完成入职（确定性代码）
   → 创建 Employee Agent 独立工作区 + OpenClaw 标准文件

2. Boss 在 Console 中创建任务
   → Console 写入第一个角色的 pending/task-<id>.md

3. 心跳触发（≤5 分钟）
   → Employee Agent 扫描 pending/，发现任务
   → 移入 processing/（原子 rename）
   → 调用 LLM 处理，产出交付物
   → 移入 done/，创建 awaiting_boss 标记

4. Boss 在 Console 中做决策
   → Forward：任务文件携带所有历史产出 → 下一角色的 pending/
   → Rework：退回当前角色的 pending/，附上说明
   → Complete：归档到 .archive/

5. 重复 3-4 直到任务完成
```

---

## Spec 文档

ClawOPC 的完整设计规范：

| 文档 | 内容 |
|------|------|
| [spec-01](spec/01-Overview.md) | 系统概览 |
| [spec-02](spec/02-Architecture.md) | 架构设计（心跳驱动 + 两层架构） |
| [spec-03](spec/03-Workspace.md) | 工作区结构 |
| [spec-04](spec/04-Task-Lifecycle.md) | 任务生命周期 |
| [spec-05](spec/05-Task-MD-Standard.md) | task.md 规范 |
| [spec-06](spec/06-Worklog-Standard.md) | work.log 规范 |
| [spec-07](spec/07-Employee-Skill.md) | Employee Skill |
| [spec-08](spec/08-Role-Standard.md) | Role 包规范 |
| [spec-09](spec/09-Console-Standard.md) | Console 规范 |
| [spec-10](spec/10-OpenClaw-Standard.md) | OpenClaw Gateway 集成 |

---

## 项目结构

```
clawopc/
├── packages/
│   ├── console/           ← Console Web 界面（Boss Agent 专属）
│   └── cli/               ← clawopc CLI 工具
│
├── roles/                 ← 内置 Role 包
│   ├── boss/              ← Boss Role 包
│   ├── developer/
│   ├── designer/
│   └── .../
│
├── spec/                  ← 设计规范文档
│   ├── 01-Overview.md
│   └── .../
│
└── docs/                  ← 用户文档
    ├── quick-start.md
    ├── custom-role.md
    └── .../
```

> **注意**：ClawOPC 不包含 OpenClaw Gateway 代码。
> OpenClaw 作为独立的开源项目安装（`npm install -g openclaw@latest`）。
> ClawOPC 提供的是规范层（spec）、Console 前端、Role 包和 CLI 工具。

---

## 设计哲学

**所有人都是 Agent。**

Boss 不是系统外的操作者，
Boss 是系统内的第一个 Agent。
Boss 有自己的 Role 包、Skill 和工作区。
Console 是 Boss Agent 的专属界面，不是管理后台。

**文件系统即协议。**

不引入消息队列、不引入数据库、不引入 API。
任务的流转、状态的变更、产出的传递，
全部通过文件系统完成。

这意味着：
- 任何文本编辑器都可以查看任务状态
- 任何脚本都可以介入任务流程
- 系统崩溃后，状态完整保留在文件中
- 调试只需要 `ls` 和 `cat`

**心跳驱动，无需调度。**

利用 OpenClaw 原生 Heartbeat 机制，
虚拟员工每 5 分钟自动巡检。
有任务就干，没任务就静默。
无需 Orchestrator，无需轮询服务。

**Boss 只做决策。**

Boss 不需要了解系统内部机制。
Boss 只需要：创建任务、查看产出、做出决策。
boss-skill 定义了 Boss 如何通过 Console 管理团队。

**角色是完整的人。**

虚拟员工不是工具，不是函数调用。
他们有名字、有性格、有职责边界。
他们以一致的身份处理所有任务。

---

## 贡献

欢迎贡献 Role 包、Bug 修复、功能建议。

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## License

MIT
