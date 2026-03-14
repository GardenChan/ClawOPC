# ClawOPC Spec — 04 Task Lifecycle

```markdown
---
doc_id: spec-04
title: Task Lifecycle
version: 0.1.0
status: draft
created_at: 2025-01-15
---
```

---

## 什么是任务

任务是 ClawOPC 的**最小工作单元**。

每个任务由 Boss 创建，
携带完整的 Pipeline 定义，
经过一个或多个虚拟员工处理，
最终由 Boss 确认完成。

---

## 任务状态

```
pending       → 等待角色处理
processing    → 角色正在处理
awaiting_boss → 等待 Boss 决策
complete      → 任务完成
```

状态由任务文件所在目录决定：

```
<role>/pending/      → pending
<role>/processing/   → processing
<role>/done/         → awaiting_boss（含 awaiting_boss 标记文件）
归档                  → complete
```

---

## 完整生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Boss 创建任务                                               │
│       │                                                     │
│       ▼                                                     │
│  <role-1>/pending/          [pending]                       │
│       │                                                     │
│       │  OpenClaw 认领                                       │
│       ▼                                                     │
│  <role-1>/processing/       [processing]                    │
│       │                                                     │
│       │  处理完成                                            │
│       ▼                                                     │
│  <role-1>/done/             [awaiting_boss]                 │
│       │                                                     │
│       │  Boss 决策                                           │
│       ├──── forward ────► <role-2>/pending/                 │
│       │                        │                            │
│       │                        │  重复上述流程               │
│       │                        ▼                            │
│       │                   <role-N>/done/  [awaiting_boss]   │
│       │                        │                            │
│       │                        │  Boss 决策                  │
│       ├──── rework  ────► <role-1>/pending/                 │
│       │                                                     │
│       └──── complete ───► 归档  [complete]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 阶段详解

### 1. 创建任务

Boss Agent 通过 Console 创建任务：

```
操作：
  在 Console 中填写任务标题
  填写任务描述
  定义 Pipeline（经过哪些角色，按什么顺序）
  选择第一个处理角色

结果：
  生成 task-<id>.md
  写入 <role-1>/pending/
```

task.md 详细格式见 [05-task-md-standard](./05-task-md-standard.md)。

---

### 2. 认领任务（pending → processing）

Employee OpenClaw 轮询 pending/ 目录：

```
检测到新文件
  → 读取 task-<id>.md
  → 确认任务属于自己的角色
  → 执行 rename：
       pending/task-<id>.md
     → processing/task-<id>.md
  → 写入 work.log：[received]
  → 开始处理
```

rename 操作保证原子性，
同一任务不会被两个进程同时认领。

---

### 3. 处理任务（processing）

Employee OpenClaw 执行任务：

```
读取 task-<id>.md
  → 理解任务目标
  → 读取历史产出（如有）
  → 调用自身 Skills 执行工作
  → 产出 <role>_output.md

写入 work.log：
  [started]
  [working] （过程中持续记录）
  [done]
```

---

### 4. 完成处理（processing → done）

处理完成后：

```
写入产出文件：
  processing/<role>_output.md

移动任务文件：
  processing/task-<id>.md → done/task-<id>.md
  processing/<role>_output.md → done/<role>_output.md

创建标记文件：
  done/awaiting_boss

写入 work.log：
  [awaiting_boss]
```

---

### 5. Boss 决策

Console 检测到 done/awaiting_boss，展示给 Boss Agent：

```
展示给 Boss：
  任务信息
  本角色产出物
  所有历史产出
  Pipeline 当前位置

Boss 有三个选择：
  forward   → 流转到下一个角色
  rework    → 退回当前角色重做
  complete  → 任务完成，结束
```

---

### 6a. Forward（流转到下一角色）

```
Console 执行：
  读取 Pipeline，确认下一个角色（role-2）
  将 done/ 下所有文件打包：
    task-<id>.md
    <role-1>_output.md
    <role-2>_output.md（如有）
    ...
  写入 <role-2>/pending/task-<id>.md
  删除 done/awaiting_boss

写入 work.log（role-1）：
  [forwarded] → role-2
```

---

### 6b. Rework（退回重做）

```
Console 执行：
  将 done/ 下所有文件退回：
    task-<id>.md（附加 Boss 的 rework 说明）
    所有历史产出
  写入 <role>/pending/task-<id>.md
  删除 done/awaiting_boss

写入 work.log：
  [rework] Boss 说明：<rework 原因>
```

rework 时，Boss 的说明会追加到 task.md 的 rework_notes 字段。

---

### 6c. Complete（任务完成）

```
Console 执行：
  将 done/ 下所有文件归档
  更新 task-<id>.md 状态为 complete
  记录完成时间
  删除 done/awaiting_boss

写入 work.log：
  [complete]
```

---

## Pipeline 定义

Pipeline 定义了任务经过哪些角色、按什么顺序：

```yaml
pipeline:
  - role: developer
    instruction: 实现功能，输出代码和说明文档
  - role: designer
    instruction: 根据功能说明，设计 UI 界面
  - role: developer
    instruction: 根据设计稿，实现前端代码
```

同一个角色可以在 Pipeline 中出现多次。

Pipeline 存储在 task.md 中，
每次流转时 Console 读取 Pipeline 确认下一个角色。

---

## 当前位置追踪

task.md 中记录 Pipeline 当前位置：

```yaml
pipeline_cursor: 0    ← 当前在第几步（从 0 开始）
```

每次 forward 时，Console 将 cursor +1。

```
cursor = 0  → developer
cursor = 1  → designer
cursor = 2  → developer（第二次）
cursor = 3  → Pipeline 结束，只能 complete
```

---

## 任务超时

```
每个 Pipeline 步骤可设置超时时间：

pipeline:
  - role: developer
    instruction: 实现功能
    timeout: 3600        ← 秒，默认不限制

超时后：
  Console 标记任务为 timeout
  展示给 Boss
  Boss 决策：rework 或 complete
```

---

## 任务归档

complete 后，任务文件归档到：

```
workspace/.archive/
└── <YYYY-MM>/
    └── task-<id>/
        ├── task-<id>.md
        ├── developer_output.md
        ├── designer_output.md
        └── work.log（各角色合并）
```

归档后任务只读，不可再操作。

---

## 状态速查

```
文件位置                          任务状态
────────────────────────────────────────────────────
<role>/pending/task-<id>.md      pending
<role>/processing/task-<id>.md   processing
<role>/done/task-<id>.md         awaiting_boss
  + done/awaiting_boss
.archive/.../task-<id>/          complete
```

---

**04-task-lifecycle 完成。**
输出 05-task-md-standard？👇