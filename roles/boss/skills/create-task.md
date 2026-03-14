---
skill: create-task
role: boss
---

# Create Task

## 触发条件

当需要创建新任务时使用此 skill。

## 操作方式

通过 Console「创建任务」页面：

### 步骤 1：定义任务

填写以下信息：
- **标题**：简洁明了的任务名称
- **描述**：任务的具体要求
- **背景**：相关的上下文信息（技术栈、约束条件等）
- **验收标准**：怎样算完成

### 步骤 2：设计 Pipeline

定义任务经过的角色和顺序：
- 选择角色和顺序（如：Developer → Designer → Developer）
- 为每个步骤编写 instruction（告诉该角色具体做什么）

### 步骤 3：提交

点击「创建」，Console 自动：
1. 生成任务 ID（task-YYYYMMDD-NNN）
2. 生成 task.md 文件
3. 将 task.md 投递到第一个角色的 pending/

## 任务设计原则

- 标题和描述要清晰，不留歧义
- Pipeline 步骤的 instruction 要具体
- 验收标准要可衡量
- 考虑角色的能力范围，不给角色分配超出职责的工作
