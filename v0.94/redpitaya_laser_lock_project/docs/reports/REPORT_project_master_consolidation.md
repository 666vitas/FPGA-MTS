# REPORT project master consolidation

## 0. 本报告作用

本报告记录本次项目主线文档整理工作。

本次目标是把 `redpitaya_laser_lock_project` 中已有的 docs、reports、integration、board_tests、beginner_roadmap、patches、rtl、sim 等内容，整理成一套新的 `docs\project_master` 主线文档，供后续开发优先阅读。

## 1. 本次阅读了哪些目录

本次阅读和整理参考了以下目录：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\learning
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\current
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\integration
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\board_tests
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\beginner_roadmap
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\patches
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim
```

重点归纳了：

- `L01-L04` top/ADC/DAC/clock/reset 学习内容；
- `IMPLEMENTATION_PLAN_mts_error_chain_v1`；
- `INTEGRATION_PLAN_v1ab_passthrough_debug`；
- `PATCH_GUIDE_v1ab_passthrough_debug`；
- `BOARD_TEST_v1ab_passthrough_debug`；
- `beginner_roadmap`；
- `REPORT_workspace_merge_to_v094.md`；
- `laser_lock_core.sv`、`output_protect.sv` 和 `tb_laser_lock_core_v1ab.sv` 的当前作用。

## 2. 生成了哪些 project_master 文件

本次新增：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\00_PROJECT_FINAL_GOAL.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\01_CURRENT_STATUS_SUMMARY.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\04_VIVADO_OPERATION_GUIDE.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\06_CODEX_GPT_WORKFLOW.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\07_DOCUMENT_CLEANUP_SUMMARY.md
```

同时新增本报告：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports\REPORT_project_master_consolidation.md
```

## 3. 没有修改 RTL

本次没有修改任何 RTL 文件。

没有修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl
```

本次也没有写新的 Verilog/SystemVerilog。

## 4. 没有运行 Vivado

本次没有运行 Vivado。

没有执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

也没有修改 `.xpr` 工程。

## 5. 没有删除旧文档

本次没有删除旧文档，没有移动旧文档。

旧文档继续保留在：

```text
docs\learning
docs\current
docs\integration
docs\board_tests
docs\beginner_roadmap
docs\old
docs\reports
```

## 6. 旧文档如何处理

旧文档现在作为历史记录和证据库保留。

后续优先阅读：

```text
docs\project_master
```

旧文档不再作为第一阅读入口。需要查细节、追溯历史、找旧版本 SOP 或 patch 说明时，再回到旧目录。

合并关系已写入：

```text
docs\project_master\07_DOCUMENT_CLEANUP_SUMMARY.md
```

## 7. 下一步建议

建议下一步按以下顺序进行：

1. 用户/GPT 审查 `docs\project_master`；
2. 然后确认 `E:\new\fpga_lock\v94\v0.94\rtl` 是否已有 `v1ab` 所需 RTL；
3. 确认 `red_pitaya_top.sv` 是否 patch；
4. 进入 Vivado synthesis。

在完成 `v1ab` synthesis、implementation、bitstream 和上板验证前，不建议开始 `v1c_mixer_only`。
