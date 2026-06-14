# PUBLIC_DEMO_OUTLINE

## 1. Demo 定位

公开 Demo 展示一个脱敏后的“AI 辅助工科研究生项目管理平台”，案例来自 Red Pitaya FPGA 激光稳频项目，但不公开完整 RTL、真实路径、导师信息和未发表实验数据。

一句话介绍：

```text
把 FPGA 激光稳频项目拆成阶段、任务、验证矩阵、AI 审查包和实验记录，让 AI 不再乱改代码、乱跳阶段。
```

## 2. Demo README 结构

建议公开仓库 README：

```text
# AI Research Project Template for Engineering Students

## 1. 这个 Demo 解决什么问题
## 2. 示例项目：Red Pitaya FPGA 激光稳频
## 3. 项目阶段：v1-v5
## 4. 验证矩阵：设计/代码/仿真/综合/上板/实验/论文证据
## 5. GPT 审查包如何生成
## 6. Codex 任务包如何生成
## 7. 实验日志和周报如何沉淀论文证据
## 8. 不能公开和不能自动化的内容
## 9. 如何迁移到自己的工科项目
```

## 3. 展示截图建议

| 截图 | 展示内容 | 目的 |
|---|---|---|
| 项目状态页 | 当前阶段、已完成、下一步、禁止项 | 让观众看到 AI 每次任务前先读状态 |
| 验证矩阵 | 模块从设计到论文证据的状态 | 解释为什么“仿真通过”不等于“可以上板” |
| GPT 审查包 | 背景、相关文件、结果、问题 | 展示如何让 GPT 做项目负责人而不是乱猜 |
| Codex 任务包 | 允许修改文件、禁止修改文件、验收标准 | 展示如何约束代码代理不越界 |
| 实验日志 | bitstream、接线、示波器现象、结论 | 展示科研证据如何积累 |
| 周报 | 本周完成、失败、下周计划、导师问题 | 展示如何把碎片工作变成周报 |

## 4. 小红书/B站/知乎标题建议

| 平台 | 标题 |
|---|---|
| 小红书 | 我把 FPGA 实验项目做成了 AI 项目管理模板 |
| 小红书 | 研究生别再让 AI 乱改代码：先做验证矩阵 |
| B站 | 用 GPT + Codex 管理一个真实 FPGA 激光稳频项目 |
| B站 | 仿真通过为什么还不能上板？一个科研项目管理 Demo |
| 知乎 | 工科研究生如何用 AI 管理实验、代码和论文证据链 |
| 知乎 | 从 Red Pitaya 激光稳频项目看 AI 代码代理的边界管理 |

## 5. 不能公开的内容

| 类型 | 不能公开内容 | 处理方式 |
|---|---|---|
| 真实路径 | `E:\new\fpga_lock\...` 等本机路径 | 替换为 `<PROJECT_ROOT>` |
| 完整 RTL | `pi_controller.sv`、`laser_lock_core.sv` 等完整源码 | 只展示接口示意或伪代码 |
| 未发表数据 | 原始示波器 CSV、真实锁定性能数据 | 用模拟数据或脱敏统计 |
| 导师信息 | 导师姓名、课题组内部安排 | 删除或写成“导师/课题组” |
| 实验室配置 | 详细设备编号、网络地址、账号 | 删除或模糊化 |
| 未确认结论 | 尚未上板或未闭环的性能判断 | 标为“示例状态”或“待验证” |

## 6. Demo 文件树建议

```text
demo/
  README.md
  templates/
    PROJECT_STATE_TEMPLATE.md
    VERIFICATION_MATRIX_TEMPLATE.md
    GPT_REVIEW_PACKAGE_TEMPLATE.md
    CODEX_TASK_TEMPLATE.md
    EXPERIMENT_LOG_TEMPLATE.md
    WEEKLY_REPORT_TEMPLATE.md
  examples/
    red_pitaya_laser_lock_project_state.md
    red_pitaya_verification_matrix.md
    red_pitaya_codex_task_example.md
  screenshots/
    project_state.png
    verification_matrix.png
    experiment_log.png
```

## 7. 可执行清单

- [ ] 把真实路径替换为 `<PROJECT_ROOT>`。
- [ ] 用伪代码替换完整 RTL。
- [ ] 用模拟波形或手绘框图替换真实未发表数据。
- [ ] 保留 v1-v5 阶段管理和验证矩阵思想。
- [ ] 准备一个“仿真通过但还不能上板”的典型讲解案例。

