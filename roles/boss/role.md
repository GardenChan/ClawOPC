---
role: boss
version: 1.0.0
---

# Boss

## 职位

团队管理者

## 职责

- 创建和分配任务给虚拟员工
- 审阅员工产出并做出决策（Forward / Rework / Complete）
- 管理团队：发布岗位、入职员工
- 制定任务 Pipeline（角色执行顺序）
- 把控整体质量和进度

## 工作边界

负责：
  - 任务创建与定义
  - 决策审批（流转 / 退回 / 完成）
  - 岗位发布与员工入职
  - 任务质量把控

不负责：
  - 具体任务执行（由 Employee Agent 完成）
  - 技术实现细节
  - 文件系统操作（由 Console 代理完成）

## 输入

接受以下类型的信息：
  - 员工产出（done/ + awaiting_boss）
  - 团队状态总览
  - 待决策任务列表

## 输出

产出以下类型的决策：
  - Forward：将任务流转给下一个角色
  - Rework：退回给当前角色重做，附上说明
  - Complete：标记任务完成，归档

## 协作

Boss 不直接与 Employee 通信。
所有交互通过文件系统完成：
  - 创建任务 → pending/
  - 审阅产出 → done/awaiting_boss
  - 做出决策 → Forward / Rework / Complete
