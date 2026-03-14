# ClawOPC Spec — 05 Task MD Standard

```markdown
---
doc_id: spec-05
title: Task MD Standard
version: 0.1.0
status: draft
created_at: 2025-01-15
---
```

---

## 什么是 task.md

task.md 是任务的**完整载体**。

它随任务在角色之间流转，
携带任务定义、Pipeline、当前状态、
所有历史产出的引用、Boss 的决策记录。

任务的一切信息都在 task.md 里。

---

## 完整格式

```markdown
---
# ─── 基础信息 ───────────────────────────────────
id: task-20250115-001
title: 实现用户登录功能
created_at: 2025-01-15T09:00:00Z
created_by: boss
status: processing          ← pending / processing / awaiting_boss / complete

# ─── Pipeline ────────────────────────────────────
pipeline:
  - step: 0
    role: developer
    instruction: |
      实现用户登录功能，包括：
      - 用户名 + 密码登录
      - JWT Token 生成
      - 错误处理
    timeout: 3600

  - step: 1
    role: designer
    instruction: |
      根据 developer 的实现说明，
      设计登录页面 UI，输出设计稿说明文档。
    timeout: 7200

  - step: 2
    role: developer
    instruction: |
      根据 designer 的设计稿说明，
      实现前端登录页面。
    timeout: 3600

pipeline_cursor: 0          ← 当前在第几步

# ─── 当前处理角色 ─────────────────────────────────
current_role: developer

# ─── 产出物清单 ───────────────────────────────────
outputs:
  - step: 0
    role: developer
    file: developer_output.md
    completed_at: ~          ← 完成时填写

  - step: 1
    role: designer
    file: designer_output.md
    completed_at: ~

  - step: 2
    role: developer
    file: developer_output_2.md
    completed_at: ~

# ─── Boss 决策记录 ────────────────────────────────
decisions:
  []                         ← 每次 Boss 决策后追加

# ─── Rework 记录 ─────────────────────────────────
rework_notes:
  []                         ← 每次 rework 后追加

# ─── 完成信息 ─────────────────────────────────────
completed_at: ~              ← complete 时填写
---

## 任务描述

实现用户登录功能。

用户可以通过用户名和密码登录系统，
登录成功后获得 JWT Token，
用于后续 API 请求的身份验证。

## 背景信息

- 技术栈：Node.js + Express
- 数据库：PostgreSQL
- 认证方式：JWT，有效期 24 小时
- 现有用户表：users（id, username, password_hash, created_at）

## 验收标准

- [ ] POST /auth/login 接口可用
- [ ] 密码错误返回 401
- [ ] 登录成功返回 token
- [ ] token 24 小时后过期
```

---

## 字段说明

### 基础信息

```
id            任务唯一标识
              格式：task-<YYYYMMDD>-<序号3位>
              示例：task-20250115-001

title         任务标题，简短描述任务目标

created_at    任务创建时间，ISO 8601 格式

created_by    创建者，固定为 boss

status        当前状态
              pending        → 等待处理
              processing     → 正在处理
              awaiting_boss  → 等待 Boss 决策
              complete       → 已完成
```

### Pipeline

```
pipeline      有序列表，定义任务经过哪些角色

  step        步骤序号，从 0 开始
  role        处理此步骤的角色名
  instruction 给该角色的具体指令
              支持多行文本
  timeout     超时时间（秒），可选，默认不限制

pipeline_cursor
              当前执行到第几步（从 0 开始）
              forward 时 +1
              rework 时不变
```

### 当前处理角色

```
current_role  当前负责处理任务的角色
              由 pipeline[pipeline_cursor].role 决定
              每次流转时更新
```

### 产出物清单

```
outputs       记录每个步骤的产出文件

  step        对应 Pipeline 的步骤序号
  role        产出此文件的角色
  file        产出文件名
              格式：<role>_output.md
              同一角色出现多次时：
                第一次：developer_output.md
                第二次：developer_output_2.md
                第三次：developer_output_3.md
  completed_at 完成时间，未完成时为 ~
```

### Boss 决策记录

```
decisions     Boss 每次决策的完整记录

格式：
  decisions:
    - at: 2025-01-15T10:30:00Z
      step: 0
      role: developer
      action: forward         ← forward / rework / complete
      comment: |
        实现符合预期，流转到设计师。
```

### Rework 记录

```
rework_notes  Boss 每次 rework 时的说明

格式：
  rework_notes:
    - at: 2025-01-15T11:00:00Z
      step: 1
      role: designer
      note: |
        设计稿缺少错误状态的 UI 说明，
        请补充密码错误、账号不存在两种错误提示的设计。
```

---

## 状态流转时的字段变化

### 创建时

```yaml
status: pending
pipeline_cursor: 0
current_role: developer
outputs:
  - step: 0
    role: developer
    file: developer_output.md
    completed_at: ~
decisions: []
rework_notes: []
completed_at: ~
```

### 认领时（pending → processing）

```yaml
status: processing
# 其他字段不变
```

### 完成处理（processing → awaiting_boss）

```yaml
status: awaiting_boss
outputs:
  - step: 0
    role: developer
    file: developer_output.md
    completed_at: 2025-01-15T10:25:00Z    ← 填写完成时间
```

### Boss Forward（awaiting_boss → 下一角色 pending）

```yaml
status: pending
pipeline_cursor: 1                         ← +1
current_role: designer                     ← 更新为下一角色
decisions:
  - at: 2025-01-15T10:30:00Z
    step: 0
    role: developer
    action: forward
    comment: 实现符合预期，流转到设计师。
```

### Boss Rework（awaiting_boss → 当前角色 pending）

```yaml
status: pending
pipeline_cursor: 0                         ← 不变
current_role: developer                    ← 不变
decisions:
  - at: 2025-01-15T10:30:00Z
    step: 0
    role: developer
    action: rework
    comment: 缺少错误处理，请补充。
rework_notes:
  - at: 2025-01-15T10:30:00Z
    step: 0
    role: developer
    note: 请补充密码错误和用户不存在的错误处理逻辑。
```

### Boss Complete

```yaml
status: complete
completed_at: 2025-01-15T16:00:00Z        ← 填写完成时间
decisions:
  - ...
  - at: 2025-01-15T16:00:00Z
    step: 2
    role: developer
    action: complete
    comment: 全部完成，符合验收标准。
```

---

## 产出文件命名规则

同一角色在 Pipeline 中出现多次时：

```
第 1 次出现 → <role>_output.md
第 2 次出现 → <role>_output_2.md
第 3 次出现 → <role>_output_3.md

示例：
  developer_output.md
  designer_output.md
  developer_output_2.md
```

---

## 任务文件随流转携带的内容

每次流转时，进入下一角色 pending/ 的内容：

```
<role>/pending/
├── task-<id>.md              ← 更新后的任务文件
├── developer_output.md       ← 历史产出（如有）
├── designer_output.md        ← 历史产出（如有）
└── ...                       ← 所有历史产出
```

新角色可以读取所有历史产出，
了解任务的完整上下文。

---

## 任务描述区块

task.md 的 YAML Front Matter 之后是 Markdown 正文，
包含三个固定区块：

```markdown
## 任务描述

用自然语言描述任务目标。
Boss 创建时填写，流转过程中不修改。

## 背景信息

任务相关的背景知识、技术栈、约束条件。
Boss 创建时填写，流转过程中不修改。

## 验收标准

任务完成的判断标准，使用 checklist 格式。
Boss 创建时填写，complete 时由 Boss 确认。
```

---

## 最小合法 task.md

最简单的任务，只有一个角色，无背景信息：

```markdown
---
id: task-20250115-001
title: 写一篇产品介绍文章
created_at: 2025-01-15T09:00:00Z
created_by: boss
status: pending

pipeline:
  - step: 0
    role: content-writer
    instruction: |
      写一篇 500 字的产品介绍文章，
      介绍 ClawOPC 是什么，解决什么问题。

pipeline_cursor: 0
current_role: content-writer

outputs:
  - step: 0
    role: content-writer
    file: content-writer_output.md
    completed_at: ~

decisions: []
rework_notes: []
completed_at: ~
---

## 任务描述

写一篇 ClawOPC 产品介绍文章。

## 背景信息

无。

## 验收标准

- [ ] 字数 500 字左右
- [ ] 语言简洁清晰
- [ ] 包含核心价值主张
```

---

**05-task-md-standard 完成。**
输出 06-worklog-standard？👇