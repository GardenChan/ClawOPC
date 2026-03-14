---
skill: manage-team
role: boss
---

# Manage Team

## 触发条件

当需要管理团队（发布岗位、入职员工、查看状态）时使用此 skill。

## 操作方式

所有操作通过 Console 界面完成：

### 发布岗位

1. 在 Console「设置」页面选择角色
2. 点击「发布岗位」
3. Console 自动完成入职流程：
   - 创建 Agent 独立工作区
   - 复制 Role 包 → OpenClaw 标准文件
   - 写入 HEARTBEAT.md 和 employee-skill

### 查看团队状态

1. 在 Console「团队总览」页面
2. 查看每个角色的实时状态（工作中/待机/等待决策/离线）
3. 查看最新的工作日志

### 管理员工

- 通过 Console 管理岗位状态
- 通过工作日志了解员工动态
- 通过待决策列表处理员工产出

## 注意事项

- Boss 不直接操作文件系统，所有操作通过 Console 完成
- 发布岗位前确认 Role 包已就绪
- 入职流程是确定性代码执行，不需要 Boss 手动操作
