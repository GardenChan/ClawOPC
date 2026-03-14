---
skill: make-decision
role: boss
---

# Make Decision

## 触发条件

当员工完成任务步骤，产出等待审阅时使用此 skill。

## 操作方式

通过 Console「待决策」页面：

### 审阅产出

1. 查看任务详情和当前步骤
2. 阅读员工的产出内容
3. 对照验收标准评估质量

### 三种决策

#### Forward（流转）

产出质量达标，流转到下一个角色：
- 点击「Forward」
- Console 自动将任务移入下一角色的 pending/
- 所有历史产出随任务一起传递

#### Rework（退回）

产出不满足要求，需要修改：
- 填写退回说明（具体说明哪里需要改进）
- 点击「Rework」
- Console 自动将任务退回当前角色的 pending/
- 退回说明会写入 task.md 的 rework_notes

#### Complete（完成）

任务全部完成，归档：
- 确认所有步骤的产出都满意
- 点击「Complete」
- Console 自动将任务归档到 .archive/

## 决策原则

- 审阅产出后再做决策，不盲目 Forward
- Rework 说明要具体，告诉员工哪里需要改、怎么改
- 不反复 Rework 同一个问题，如果描述不清是 Boss 的责任
- 任务完成后及时 Complete，不积压
