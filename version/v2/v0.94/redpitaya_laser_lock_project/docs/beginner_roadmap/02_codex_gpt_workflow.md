# GPT + Codex 协作流程

## 0. 本文件作用

本文件说明你作为 FPGA/Verilog 新手，应该怎样让 GPT 和 Codex 配合工作。

大白话：GPT 更像总工程师和老师，负责审查思路；Codex 更像会动手的助教，负责读文件、改文件、跑仿真、写报告。

## 1. 我需要理解什么

| 角色 | 适合做什么 |
|---|---|
| GPT | 审查方案、解释原理、判断风险 |
| Codex | 生成文件、修改代码、运行命令、整理 REPORT |
| 用户 | 提供实验参数、确认是否进入下一阶段、做真实接线 |

不要让 Codex 直接跳到上板集成。每一步都要有文档和审查。

## 2. 我需要操作什么

推荐流程：

1. 先让 Codex 生成小版本 RTL 和 testbench。
2. 让 Codex 跑仿真。
3. 把 RTL、testbench、REPORT 发给 GPT。
4. 让 GPT 审查。
5. GPT 同意后，再让 Codex 生成 integration plan。
6. integration plan 再给 GPT 审查。
7. 审查通过后，才进入 Vivado 集成。

## 3. 我需要发给 GPT 什么

推荐发送模板：

```text
当前版本：
v1ab_passthrough_debug

目标：
验证 IN1/IN2 到 OUT1 的直通路径。

请审查：
1. laser_lock_core.sv
2. output_protect.sv
3. tb_laser_lock_core_v1ab.sv
4. REPORT_v1ab_passthrough_debug.md
5. BOARD_TEST_v1ab_passthrough_debug.md

重点看：
- reset 是否安全
- signed/unsigned 是否合理
- OUTPUT_MODE 是否适合上板调试
- 是否可以进入 integration plan
```

## 4. Codex 应该生成什么

Codex 每次任务应生成：

| 类型 | 例子 |
|---|---|
| 代码 | `rtl\laser_lock_core.sv` |
| 仿真 | `sim\tb_laser_lock_core_v1ab.sv` |
| 报告 | `docs\reports\REPORT_*.md` |
| 上板说明 | `docs\board_tests\BOARD_TEST_*.md` |
| 集成方案 | `docs\integration\INTEGRATION_PLAN_*.md` |

## 5. 成功标准是什么

一次 Codex 任务完成的标准：

- 文件在正确目录；
- 没有修改官方工程；
- testbench 可以运行；
- 报告说明清楚；
- 下一步建议明确；
- 不确定项写出来，没有假装确定。

## 6. 失败怎么排查

| 问题 | 处理 |
|---|---|
| Codex 改错目录 | 立即要求生成 CORRECTION，并迁回 `redpitaya_laser_lock_project` |
| Codex 跳过 REPORT | 要求补 `docs\reports\REPORT_*.md` |
| Codex 想直接改 top | 要求先生成 `docs\integration\INTEGRATION_PLAN_*.md` |
| GPT 和 Codex 意见不同 | 优先让 GPT 审查风险，再决定是否继续 |

## 7. 现在只需要记住什么

你不需要自己写 Verilog，但你需要控制节奏：

```text
计划 -> 代码 -> 仿真 -> REPORT -> GPT 审查 -> integration plan -> 再考虑 Vivado
```
