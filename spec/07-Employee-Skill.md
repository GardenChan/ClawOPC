# ClawOPC Spec — 07 Employee Skill

```markdown
---
doc_id: spec-07
title: Employee Skill
version: 0.2.0
status: draft
created_at: 2025-01-15
updated_at: 2026-03-15
---
```

---

## 什么是 Employee Skill

Employee Skill 是每个虚拟员工（Employee Agent）的**行为框架**。

它定义了虚拟员工处理任务的完整行为规范：
- 如何响应心跳
- 如何认领任务
- 如何处理任务
- 如何产出交付物
- 如何与 Boss 交互

Employee Skill 是所有 **Employee Agent** 共用的基础 Skill，
与 Role 包无关，与具体职能无关。

> **与 boss-skill 的区别**：
> `employee-skill` 定义 Employee Agent 如何**处理任务**（心跳扫描 → 认领 → 处理 → 产出）。
> `boss-skill` 定义 Boss Agent 如何**管理团队**（通过 Console 创建任务、做决策、管理员工）。
> 两者互不混用。

> **注意**：入职和身份激活由 **Console 确定性代码**完成，
> 不属于 Employee Skill 的范畴。Employee Skill 只关注任务处理行为。

---

## Skill 结构

```
skills/
├── SKILL.md              ← Skill 入口，定义整体行为
├── task-loop.md          ← 任务处理主循环（心跳驱动）
├── output-standard.md    ← 产出物规范
└── communication.md      ← 与 Boss 的沟通规范
```

> **与旧版的区别**：`onboarding.md` 和 `identity-activation.md` 已移除，
> 入职操作由 Console 确定性代码完成（见 [02-Architecture](./02-Architecture.md)）。

---

## SKILL.md

Skill 入口文件，定义整体行为：

```markdown
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
```

---

## task-loop.md

任务处理主循环，由心跳触发执行：

```markdown
# 任务主循环（心跳驱动）

## 触发方式

每次心跳触发时执行此流程。
不是持续轮询，而是 OpenClaw Heartbeat 定时触发。

## 启动时检查

每次心跳触发，先检查 processing/ 目录：

  ls processing/task-*.md 2>/dev/null

  有文件 → 说明上次心跳中断，继续处理
  无文件 → 正常扫描 pending/

## 扫描 pending/

  ls pending/task-*.md 2>/dev/null

  有文件 → 按文件名排序，取第一个处理
  无文件 → HEARTBEAT_OK（回复 HEARTBEAT_OK，不调 LLM）

同一时间只处理一个任务。

## 认领任务

精确命令序列（先 ls，再逐个 mv，最后验证）：

  # 1. 确认文件存在
  ls pending/

  # 2. 移动任务文件
  mv pending/task-<id>.md processing/task-<id>.md

  # 3. 移动附带的历史产出文件（如有）
  mv pending/<role>_output.md processing/ 2>/dev/null
  mv pending/<role>_output_*.md processing/ 2>/dev/null

  # 4. 验证移动结果
  ls processing/

写入 work.log：
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [task-<id>] [received] 任务已接收" >> work.log

## 读取任务

读取 processing/task-<id>.md：

  理解任务目标（## 任务描述）
  了解背景信息（## 背景信息）
  确认验收标准（## 验收标准）
  读取当前步骤的 instruction：
    pipeline[pipeline_cursor].instruction
  读取所有历史产出（如有）

写入 work.log：
  [started] 开始处理，读取任务描述

## 处理任务

根据任务内容和当前步骤的 instruction，
调用自身 Skills 执行工作。

处理过程中持续写入 work.log：
  [working] <当前正在做什么>

处理原则：
  - 严格按照 instruction 执行
  - 参考历史产出，保持上下文一致
  - 遇到歧义，选择最合理的解释并记录
  - 遇到无法处理的情况，记录原因并标记

## 完成任务

产出完成后，精确命令序列：

1. 确定产出文件名
   读取 task.md 中 outputs[pipeline_cursor].file
   按此文件名写入产出

2. 写入产出文件
   将产出内容写入 processing/<output_file>

3. 更新 task.md
   outputs[pipeline_cursor].completed_at = 当前时间
   status = awaiting_boss

4. 移动所有文件到 done/（逐个移动，先 ls 再 mv 最后验证）

   # 列出当前文件
   ls processing/

   # 逐个移动
   mv processing/task-<id>.md done/task-<id>.md
   mv processing/<role>_output.md done/<role>_output.md
   # ... 移动所有历史产出

   # 验证
   ls done/

5. 创建标记文件
   touch done/awaiting_boss

6. 写入 work.log
   [done] 产出已完成，写入 <output_file>
   [awaiting_boss] 等待 Boss 决策

## 异常处理

### API 调用失败

  写入 work.log：[error] <错误信息>
  等待下一次心跳重试
  3 次心跳仍失败后：
    写入 work.log：[error] 重试失败，等待人工介入
    保持 processing 状态，停止处理此任务

### 任务超时

  当处理时间超过 pipeline[cursor].timeout 时：
    写入 work.log：[timeout] 任务超时
    将任务移入 done/
    创建 awaiting_boss 标记
    在 task.md 中记录超时原因

### 任务文件损坏

  写入 work.log：[error] 任务文件无法解析
  将损坏文件保留在 processing/
  等待人工介入
```

---

## output-standard.md

产出物规范，所有虚拟员工的产出必须遵守：

```markdown
# 产出物规范

## 文件格式

产出文件为 Markdown 格式：
  文件名：<role>_output.md（由 task.md 指定）
  编码：UTF-8
  换行：Unix（\n）

## 必须包含的区块

### 1. 产出摘要

## 产出摘要

用 2-3 句话描述本次产出的核心内容。
Boss 通过此摘要快速了解产出结果。

### 2. 产出内容

## 产出内容

具体的产出物。
根据任务类型，可以是：
  - 代码
  - 文档
  - 设计说明
  - 分析报告
  - 其他

### 3. 说明与备注

## 说明与备注

处理过程中的重要决策、假设、限制说明。
遇到歧义时的处理方式。
需要 Boss 或下一个角色注意的事项。

### 4. 验收自查

## 验收自查

对照 task.md 中的验收标准逐项自查：

- [x] 验收项 1：已完成
- [x] 验收项 2：已完成
- [ ] 验收项 3：未完成，原因：...

## 产出质量原则

- 产出必须直接回应 instruction
- 不添加 instruction 未要求的内容
- 不遗漏 instruction 明确要求的内容
- 遇到无法完成的要求，明确说明原因
- 产出内容自洽，不出现矛盾
```

---

## communication.md

与 Boss 的沟通规范：

```markdown
# 沟通规范

## 基本原则

虚拟员工通过文件系统与 Boss 交互，
不直接发送消息，不主动联系 Boss。

所有沟通通过以下方式：
  - task.md（任务定义和决策记录）
  - <role>_output.md（产出物和说明）
  - work.log（工作过程记录）

## 产出物即沟通

产出物是与 Boss 最主要的沟通方式：

  产出摘要    → 让 Boss 快速了解结果
  说明与备注  → 解释重要决策和限制
  验收自查    → 主动对照验收标准

## 遇到问题时

遇到无法处理的情况：

  不要停止等待
  不要发送消息
  
  而是：
    在产出物的"说明与备注"中详细说明问题
    在验收自查中标记未完成项及原因
    完成能完成的部分，提交产出
    等待 Boss 通过 rework 给出指导

## 不做的事

  不主动联系 Boss
  不修改 task.md 中 Boss 填写的字段
  不跨越工作区访问其他角色的文件
  不修改历史产出（只读）
```

---

## Employee Skill 与 Role 包的关系

```
Employee Skill（employee-skill）：
  所有 Employee Agent 共用
  定义"如何处理任务"
  与职能无关
  注入到 Employee Agent 工作区的 skills/SKILL.md

Boss Skill（boss-skill）：
  Boss Agent 专用
  定义"如何管理团队"
  通过 Console 交互
  注入到 Boss Agent 工作区的 skills/SKILL.md

Role 包：
  每个角色独有（包括 Boss）
  定义"做什么工作"、"以什么身份工作"
  入职时由 Console 映射为 OpenClaw 标准文件

HEARTBEAT.md：
  所有 Employee Agent 共用模板（Boss 不使用心跳）
  定义"何时工作"（心跳触发行为）
  入职时由 Console 写入 Employee Agent 工作区

关系：
  Employee：HEARTBEAT.md 触发心跳 → employee-skill 定义处理流程 → Role 包提供身份和技能
  Boss：Console 交互触发 → boss-skill 定义管理流程 → Boss Role 包提供身份
```

---

## 进程退出处理

OpenClaw Gateway 停止或 Agent 退出时：

```
1. 完成当前正在写入的文件操作
2. Agent 实例释放

注意：
  如果任务正在 processing/ 中：
    不移动任务文件
    任务保持 processing 状态
    下次 Agent 启动时，HEARTBEAT.md 中的启动检查
    检测到 processing/ 有文件 → 继续处理
```

> **注意**：退出时不再修改 positions/ 文件和 work.log。
> 这些由 Console 根据心跳状态（heartbeat 是否超时）判断角色是否在线。

---

**07-employee-skill 完成。**
