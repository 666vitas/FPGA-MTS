# REPORT: docs 目录重组

## 0. 本文件作用

本文件记录 `docs` 目录重组任务的结果。

## 1. 本次任务是什么

任务目标：

- 重组 `redpitaya_laser_lock_project\docs`；
- 不删除任何 Markdown 文件；
- 把当前文档、旧资料、报告、修正记录、集成方案分开；
- 生成总索引文件。

目标目录：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs
```

## 2. 创建了哪些目录

在 `docs` 下创建了：

| 目录 | 作用 |
|---|---|
| `current` | 当前有效项目管理文档 |
| `learning` | 后续 top 学习笔记 |
| `old` | 旧版资料归档 |
| `reports` | Codex 任务报告 |
| `corrections` | 错误纠正记录 |
| `integration` | 后续官方 top 集成方案 |

## 3. 移动了哪些文件

### 3.1 移动到 `current`

| 原文件 | 新位置 |
|---|---|
| `00_CONTEXT_FROM_GPT.md` | `current\00_CONTEXT_FROM_GPT.md` |
| `01_PROJECT_MASTER_PLAN.md` | `current\01_PROJECT_MASTER_PLAN.md` |
| `02_TOP_LEARNING_OUTLINE.md` | `current\02_TOP_LEARNING_OUTLINE.md` |
| `03_CODEX_RULES.md` | `current\03_CODEX_RULES.md` |

### 3.2 移动到 `old`

| 原文件 | 新位置 |
|---|---|
| `00_project_goal.md` | `old\00_project_goal.md` |
| `01_official_top_learning.md` | `old\01_official_top_learning.md` |
| `02_adc_signal_path.md` | `old\02_adc_signal_path.md` |
| `03_dac_signal_path.md` | `old\03_dac_signal_path.md` |
| `04_scope_asg_pid_reuse_analysis.md` | `old\04_scope_asg_pid_reuse_analysis.md` |
| `05_mts_demod_architecture.md` | `old\05_mts_demod_architecture.md` |
| `06_integration_plan.md` | `old\06_integration_plan.md` |
| `07_board_test_sop.md` | `old\07_board_test_sop.md` |

### 3.3 移动到 `reports`

| 原文件 | 新位置 |
|---|---|
| `REPORT_project_directory_boundary_fix.md` | `reports\REPORT_project_directory_boundary_fix.md` |

## 4. 没有删除任何文件

已确认：本次没有删除任何 Markdown 文件。

所有指定文件只是从 `docs` 根目录移动到对应子目录。

## 5. 没有修改官方工程

本次没有修改官方工程。

未修改：

```text
rtl
project
sim
ip
sdc
red_pitaya_top.sv
```

## 6. 没有生成 RTL

本次没有生成 Verilog/SystemVerilog。

没有实现：

```text
laser_lock_core
```

## 7. 当前 docs 结构

```text
docs\
  README_DOCS_INDEX.md
  current\
    00_CONTEXT_FROM_GPT.md
    01_PROJECT_MASTER_PLAN.md
    02_TOP_LEARNING_OUTLINE.md
    03_CODEX_RULES.md
  learning\
  old\
    00_project_goal.md
    01_official_top_learning.md
    02_adc_signal_path.md
    03_dac_signal_path.md
    04_scope_asg_pid_reuse_analysis.md
    05_mts_demod_architecture.md
    06_integration_plan.md
    07_board_test_sop.md
  reports\
    REPORT_project_directory_boundary_fix.md
    REPORT_docs_reorganization.md
    REPORT_docs_chinese_localization.md
  corrections\
  integration\
```

## 8. 已确认

- `docs/current` 是当前有效文档。
- `docs/old` 是旧资料归档。
- `docs/reports` 保存任务报告。
- `docs/corrections` 保存错误修正记录。
- `docs/integration` 保存后续集成方案。
- `docs` 根目录不再堆放新文档。

## 9. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 是否需要把 `old` 中有价值内容整理到 `learning` | 后续学习时可逐章决定 |
| 是否需要新建 `patches` 目录 | 当前先使用 `integration` |
| 小任务是否必须写 REPORT | 当前规则要求写 |

## 10. 下一步建议

下一步建议从：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

开始，生成：

```text
learning\L01_top_overview.md
reports\REPORT_L01_top_overview.md
```

注意：不要写 RTL，不要修改官方工程。

## 11. 给 GPT 审查的问题

1. `old\06_integration_plan.md` 是否只作为历史参考保留？
2. 后续学习输出是否固定使用 `L01`、`L02`、`L03` 命名？
3. 每次 Codex 任务是否都必须生成 `reports\REPORT_*.md`？
4. `corrections` 和 `reports` 是否严格分开？
5. 官方 top 集成 patch 应放在 `integration`，还是后续建立 `patches`？
