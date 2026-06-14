# FPGA 小白项目操作路线图总入口

## 0. 本文件作用

本文件是 `docs\beginner_roadmap` 的总入口。

这个文件夹专门给 FPGA/Verilog/Vivado 新手使用。它不讲复杂理论，不假设你已经会 FPGA，而是像老师带学生做实验一样，告诉你每一步要理解什么、操作什么、发给 GPT 什么、让 Codex 生成什么、怎么判断成功、失败时先查哪里。

## 1. 文件夹内容

| 文件 | 作用 |
|---|---|
| `00_README_beginner_roadmap.md` | 本文件，总索引 |
| `01_overall_workflow_for_beginner.md` | 整个项目从文档、仿真、集成到上板的总流程 |
| `02_codex_gpt_workflow.md` | 如何让 GPT 和 Codex 分工合作 |
| `03_vivado_basic_operation_sop.md` | Vivado 基础操作 SOP |
| `04_simulation_sop.md` | 仿真操作 SOP |
| `05_integration_to_redpitaya_top_sop.md` | 接入 Red Pitaya top 前后的 SOP |
| `06_board_test_sop_v1ab.md` | `v1ab_passthrough_debug` 上板测试 SOP |
| `07_experiment_signal_checklist.md` | 实验信号接线和幅度检查清单 |
| `08_error_debug_checklist.md` | 常见错误和排查清单 |
| `09_version_stage_plan.md` | 后续版本阶段计划 |
| `10_beginner_glossary.md` | FPGA/Verilog 新手术语表，读到不懂的词回来查 |
| `11_redpitaya_hardware_quickref.md` | Red Pitaya 硬件速查卡，接口、电压范围、接线方法 |
| `12_key_signals_cheatsheet.md` | 关键信号速查表，15 个最常用信号一页列清 |

## 2. 当前项目原则

| 原则 | 说明 |
|---|---|
| 官方工程保持干净 | 当前不直接修改官方 `rtl\red_pitaya_top.sv` |
| 自定义文件放项目目录 | 自定义 RTL、仿真、文档都放 `redpitaya_laser_lock_project` |
| 先仿真再上板 | 每个版本必须先有 testbench |
| 先写 integration plan 再集成 | 不允许直接动 top |
| 先示波器再接 D2-125 | `OUT1` 必须先确认安全 |
| 第一阶段不接激光器反馈 | 避免误控制激光器 |

## 3. 推荐阅读顺序

第一次使用时按顺序读：

```text
00_README_beginner_roadmap.md        ← 先读这个
10_beginner_glossary.md              ← 遇到不懂的词随时回来查
12_key_signals_cheatsheet.md         ← 信号看得眼花了查这张表
01_overall_workflow_for_beginner.md
02_codex_gpt_workflow.md
04_simulation_sop.md
05_integration_to_redpitaya_top_sop.md
06_board_test_sop_v1ab.md
07_experiment_signal_checklist.md
11_redpitaya_hardware_quickref.md    ← 拿板子接线前必读
08_error_debug_checklist.md
09_version_stage_plan.md


如果你要打开 Vivado，再读：

```text
03_vivado_basic_operation_sop.md
```

## 4. 每个阶段固定问题

以后每个阶段都要回答：

| 问题 | 目的 |
|---|---|
| 我需要理解什么 | 防止只会复制操作，不知道在做什么 |
| 我需要操作什么 | 给出具体步骤 |
| 我需要发给 GPT 什么 | 让 GPT 做审查和决策 |
| Codex 应该生成什么 | 明确产物 |
| 成功标准是什么 | 知道什么时候可以进入下一步 |
| 失败怎么排查 | 出问题时不慌，按表检查 |

## 5. 下一步建议

当前建议先完成：

```text
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
```

在这个 integration plan 完成并审查前，不要开始 Vivado 集成，不要修改官方 `red_pitaya_top.sv`。
