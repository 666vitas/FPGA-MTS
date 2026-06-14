# 文档整理合并说明

## 0. 本文件作用

本文件总结之前冗余文档如何合并到新的 `docs\project_master` 主线文档中。

这次整理不删除旧文档，不移动旧文档，只是建立一套新的优先阅读入口。旧文档继续作为历史记录、细节证据和阶段报告保存。

## 1. 被合并的内容

本次把旧资料按主题合并如下：

| 旧内容 | 合并到哪里 | 说明 |
|---|---|---|
| `L01_top_overview` | `01_CURRENT_STATUS_SUMMARY.md`、`04_VIVADO_OPERATION_GUIDE.md` | 合并为 top 是总接线板、不要乱改底层逻辑、top 必须保持为 `red_pitaya_top.sv` |
| `L02_adc_path` | `01_CURRENT_STATUS_SUMMARY.md`、`03_VERSION_EXECUTION_CHECKLISTS.md` | 合并为 `adc_dat[0]` 是 `IN1` 候选、`adc_dat[1]` 是 `IN2` 候选 |
| `L03_dac_path` | `03_VERSION_EXECUTION_CHECKLISTS.md`、`04_VIVADO_OPERATION_GUIDE.md` | 合并为 `error_o -> DAC A / OUT1`，并强调复用官方 DAC 后级 |
| `L04_clock_reset` | `01_CURRENT_STATUS_SUMMARY.md`、`03_VERSION_EXECUTION_CHECKLISTS.md` | 合并为 `adc_clk`、`adc_rstn` 是当前 core 的候选时钟复位 |
| `IMPLEMENTATION_PLAN_mts_error_chain_v1` | `00_PROJECT_FINAL_GOAL.md`、`02_VERSION_ROADMAP_V1_TO_AI.md` | 合并为最终链路、第一阶段边界、v1ab 到 v1g 路线 |
| `BOARD_TEST_v1ab_passthrough_debug.md` | `05_EXPERIMENT_TEST_GUIDE.md`、`03_VERSION_EXECUTION_CHECKLISTS.md` | 合并为 `IN1 -> OUT1`、`IN2 -> OUT1` 上板 SOP 和安全原则 |
| `beginner_roadmap` | `03_VERSION_EXECUTION_CHECKLISTS.md`、`04_VIVADO_OPERATION_GUIDE.md`、`06_CODEX_GPT_WORKFLOW.md` | 合并为新手执行清单、Vivado 基础操作和协作流程 |
| `patch/integration` 文档 | `04_VIVADO_OPERATION_GUIDE.md`、`03_VERSION_EXECUTION_CHECKLISTS.md` | 合并为 Add Sources、top 确认、patch 状态、回退原则 |
| workspace merge 报告 | `01_CURRENT_STATUS_SUMMARY.md`、本文件 | 合并为当前 `v0.94\rtl` 已有 v1ab 所需 RTL、top 已含 v1ab 关键词的状态摘要 |

简化后的主线是：

```text
最终目标
  -> 当前状态
  -> 版本路线
  -> 执行清单
  -> Vivado 操作
  -> 实验测试
  -> Codex/GPT 协作
```

## 2. 哪些旧文档仍保留

旧文档全部保留，不删除。

继续保留的目录包括：

```text
docs\learning
docs\current
docs\integration
docs\board_tests
docs\beginner_roadmap
docs\old
docs\reports
patches
rtl
sim
experiment_logs
```

它们的作用变为：

- 作为历史记录；
- 作为细节证据；
- 作为旧版本回退参考；
- 作为 GPT/Codex 审查时可追溯材料。

以后不是不能看旧文档，而是不要把旧文档当作第一入口。第一入口改为 `docs\project_master`。

## 3. 后续优先阅读哪些文件

以后优先看：

```text
docs\project_master\00_PROJECT_FINAL_GOAL.md
docs\project_master\01_CURRENT_STATUS_SUMMARY.md
docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
docs\project_master\04_VIVADO_OPERATION_GUIDE.md
docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
```

如果是让 Codex/GPT 接手任务，也建议先让它读：

```text
docs\project_master\06_CODEX_GPT_WORKFLOW.md
docs\project_master\07_DOCUMENT_CLEANUP_SUMMARY.md
```

## 4. 不再重复生成哪些内容

以后不要重复生成新的零散 top 学习文档，除非进入新模块。

尤其不要反复生成：

- 新的 `L01 top overview`；
- 新的 `L02 ADC path`；
- 新的 `L03 DAC path`；
- 新的 `L04 clock/reset`；
- 与 `v1ab` 内容重复的 board test；
- 与 Add Sources 重复的 Vivado 入门说明；
- 与 `IMPLEMENTATION_PLAN_mts_error_chain_v1` 重复的大路线规划。

如果进入新模块，例如 `mixer_core`、`lpf_core`、`bpf_core`、`pid_lock_core`，可以生成新的模块学习文档或 correction 文档。但必须服务于当前版本，不要偏离主线。
