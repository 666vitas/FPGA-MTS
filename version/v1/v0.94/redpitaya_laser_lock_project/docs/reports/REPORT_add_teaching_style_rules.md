# REPORT add teaching style rules

## 0. 本报告作用

本报告记录本次新增“教学型开发规则”主线文档。

本次目标是让后续 Codex 输出不只是生成代码，而是帮助用户通过 Red Pitaya + MTS 激光稳频项目真正学习 FPGA、Verilog、Vivado 和激光稳频实验开发。

## 1. 新增文件

本次新增：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md
```

该文件规定后续所有文档、代码说明、`REPORT`、`BOARD_TEST`、`DEBUG_PLAN` 都必须使用教学型写法。

## 2. 文档主要内容

新增文档包含：

- 后续每个版本必须回答的 8 个问题；
- 每个版本固定教学文档模板；
- 每次生成 RTL 必须配套 `EXPLAIN_<module_name>.md`；
- 每次 Vivado 操作必须解释“为什么”；
- 每次实验失败必须区分六类问题；
- 每个版本必须有学习成果检查题；
- 后续 `v1ab` 到 `v5` 的教学版学习目标；
- 后续 Codex 输出的强制要求；
- 每次任务开始前必须阅读的主线文档列表。

## 3. 没有修改 RTL

本次没有修改任何 RTL 文件。

没有修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl
```

## 4. 没有运行 Vivado

本次没有运行 Vivado。

没有执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

也没有修改 Vivado 工程。

## 5. 没有生成 bitstream

本次没有生成 bitstream，也没有接板子。

## 6. 后续使用方式

以后每次开始新任务，Codex 应先阅读：

```text
docs\project_master\00_PROJECT_FINAL_GOAL.md
docs\project_master\01_CURRENT_STATUS_SUMMARY.md
docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
docs\project_master\08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md
```

如果涉及实验测试，还应阅读：

```text
docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
```

如果涉及 Codex/GPT 协作，还应阅读：

```text
docs\project_master\06_CODEX_GPT_WORKFLOW.md
```

## 7. 下一步建议

下一步建议：

1. 用户/GPT 审查 `08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md`；
2. 审查通过后，把后续 `v1ab`、`v1c`、`v1d` 等版本都按该教学规则生成 `LESSON_vX_xxx.md`；
3. 后续每次修改 RTL 时，同时生成对应 `EXPLAIN_<module_name>.md`；
4. 继续保持不跳阶段：先完成 `USE_LASER_LOCK_CORE=1` bitstream，再进入 `v1ab IN1 -> OUT1` 上板测试。
