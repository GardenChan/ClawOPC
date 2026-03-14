# ClawOPC Spec — 06 Worklog Standard

```markdown
---
doc_id: spec-06
title: Worklog Standard
version: 0.1.0
status: draft
created_at: 2025-01-15
---
```

---

## 什么是 work.log

work.log 是每个角色的**完整工作历史**。

每个角色工作区有且只有一个 work.log，
记录该角色处理过的所有任务、所有事件。

**只追加，不修改，不删除。**

---

## 文件位置

```
workspace/
├── developer/
│   └── work.log      ← Developer 的工作日志
├── designer/
│   └── work.log      ← Designer 的工作日志
├── boss/
│   └── work.log      ← Boss 的工作日志
└── .../
    └── work.log
```

---

## 基本格式

每条日志是一行，格式固定：

```
[timestamp] [task-id] [event] detail
```

```
字段说明：

timestamp   ISO 8601 格式，精确到秒，UTC 时区
            示例：2025-01-15T10:00:00Z

task-id     任务唯一标识
            示例：task-20250115-001

event       事件类型（见下方事件列表）

detail      事件详情，自然语言描述
            可为空
```

---

## 事件类型

### 任务生命周期事件

```
received        任务进入 pending/，等待处理
started         任务移入 processing/，开始处理
working         处理过程中的进度记录（可多条）
done            产出完成，移入 done/
awaiting_boss   标记 awaiting_boss，等待 Boss 决策
forwarded       Boss 决策 forward，任务流转到下一角色
rework          Boss 决策 rework，任务退回重做
complete        Boss 决策 complete，任务完成
```

### 系统事件

```
online          角色上线（OpenClaw 启动，身份激活完成）
offline         角色下线（OpenClaw 进程退出）
timeout         任务超时
error           处理过程中发生错误
```

---

## 完整示例

```
[2025-01-15T08:55:00Z] [system] [online] Developer 已上线，身份激活完成
[2025-01-15T10:00:00Z] [task-20250115-001] [received] 任务已进入 pending
[2025-01-15T10:00:05Z] [task-20250115-001] [started] 开始处理，读取任务描述
[2025-01-15T10:01:00Z] [task-20250115-001] [working] 分析需求，确认技术方案
[2025-01-15T10:03:30Z] [task-20250115-001] [working] 实现 POST /auth/login 接口
[2025-01-15T10:06:00Z] [task-20250115-001] [working] 实现 JWT Token 生成逻辑
[2025-01-15T10:09:45Z] [task-20250115-001] [working] 补充错误处理，编写说明文档
[2025-01-15T10:12:00Z] [task-20250115-001] [done] 产出已完成，写入 developer_output.md
[2025-01-15T10:12:01Z] [task-20250115-001] [awaiting_boss] 等待 Boss 决策
[2025-01-15T10:30:00Z] [task-20250115-001] [forwarded] Boss 决策 forward → designer
[2025-01-15T11:00:00Z] [task-20250115-002] [received] 任务已进入 pending
[2025-01-15T11:00:06Z] [task-20250115-002] [started] 开始处理
[2025-01-15T11:02:00Z] [task-20250115-002] [working] 分析需求
[2025-01-15T11:30:00Z] [task-20250115-002] [done] 产出已完成
[2025-01-15T11:30:01Z] [task-20250115-002] [awaiting_boss] 等待 Boss 决策
[2025-01-15T11:45:00Z] [task-20250115-002] [rework] Boss 决策 rework：缺少错误处理
[2025-01-15T11:45:30Z] [task-20250115-002] [received] rework 任务重新进入 pending
[2025-01-15T11:45:35Z] [task-20250115-002] [started] 重新开始处理
[2025-01-15T12:10:00Z] [task-20250115-002] [done] 产出已完成（rework 后）
[2025-01-15T12:10:01Z] [task-20250115-002] [awaiting_boss] 等待 Boss 决策
[2025-01-15T12:30:00Z] [task-20250115-002] [complete] Boss 决策 complete，任务完成
[2025-01-15T18:00:00Z] [system] [offline] Developer 下线
```

---

## 写入规则

### 原子写入

```
每条日志写入必须原子完成：
  使用追加模式（append）打开文件
  写入一行
  立即 flush

不允许：
  批量缓存后写入
  覆盖已有内容
  修改已有行
```

### 时序保证

```
同一任务的事件必须按时间顺序写入：
  received → started → working → done → awaiting_boss
  → forwarded / rework / complete

不同任务的事件可以交错出现（多任务并行时）
```

### 编码

```
UTF-8 编码
Unix 换行符（\n）
每行末尾无多余空格
```

---

## system 事件

system 事件不属于任何任务，task-id 字段填写 system：

```
[2025-01-15T08:55:00Z] [system] [online] Developer 已上线，身份激活完成
[2025-01-15T18:00:00Z] [system] [offline] Developer 下线
```

online 事件在身份激活完成后立即写入，
offline 事件在进程退出前写入。

---

## error 事件

处理过程中发生错误时写入：

```
[2025-01-15T10:05:00Z] [task-20250115-001] [error] 调用 LLM API 超时，重试第 1 次
[2025-01-15T10:05:10Z] [task-20250115-001] [error] 调用 LLM API 超时，重试第 2 次
[2025-01-15T10:05:20Z] [task-20250115-001] [working] 重试成功，继续处理
```

error 事件不中断任务，
除非错误导致任务无法继续（此时写入 timeout 或等待人工介入）。

---

## timeout 事件

任务超时时写入：

```
[2025-01-15T11:00:05Z] [task-20250115-001] [timeout] 任务超时（3600s），等待 Boss 处理
```

timeout 后任务状态变为 awaiting_boss，
Console 展示超时提醒。

---

## working 事件写入频率

```
working 事件用于记录处理进度：

建议写入时机：
  - 开始一个新的子任务
  - 完成一个关键步骤
  - 遇到需要记录的中间状态

不建议：
  - 每秒写入（过于频繁，日志膨胀）
  - 只写一条（过于稀疏，无法追踪进度）

建议频率：
  每个任务 3 ~ 10 条 working 事件
```

---

## Console 如何使用 work.log

Console 读取 work.log 用于：

```
1. 团队总览
   展示每个角色的最新状态
   读取最后一条日志，判断角色当前在做什么

2. 任务详情
   过滤特定 task-id 的所有日志
   展示任务在该角色的完整处理过程

3. 角色主页
   展示该角色的历史任务列表
   统计处理任务数、平均处理时长

4. 异常检测
   检测 error 事件
   检测 timeout 事件
   向 Boss 发出提醒
```

---

## 日志查询示例

查询特定任务的所有事件：

```bash
grep "task-20250115-001" workspace/developer/work.log
```

查询特定角色今天的所有事件：

```bash
grep "2025-01-15" workspace/developer/work.log
```

查询所有角色的 error 事件：

```bash
grep "\[error\]" workspace/*/work.log
```

查询所有角色当前在线状态：

```bash
grep "\[online\]\|\[offline\]" workspace/*/work.log | sort
```

---

## 日志轮转

work.log 长期运行会持续增长：

```
轮转策略：
  当 work.log 超过 50MB 时
  Console 执行轮转：
    work.log → work.log.2025-01
    创建新的空 work.log

历史日志保留：
  work.log           ← 当前
  work.log.2025-01   ← 上个月
  work.log.2024-12   ← 更早

保留期限：
  默认保留 6 个月
  可通过配置修改
```

---

## 最小合法 work.log

新角色上线后，最小的合法 work.log：

```
[2025-01-15T08:55:00Z] [system] [online] Developer 已上线，身份激活完成
```

---

**06-worklog-standard 完成。**
输出 07-employee-skill？👇