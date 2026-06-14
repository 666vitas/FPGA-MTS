# 文档总索引

## 0. 本文件作用

本文件是 `redpitaya_laser_lock_project/docs` 的总索引。

它说明：

- 每个子目录放什么；
- 哪些文档是当前有效规则；
- Codex 每次开始任务前应该先读哪些文件；
- 新文档应该放在哪里；
- 后续项目文档默认使用中文；
- 后续项目文档必须默认面向 FPGA/Verilog 新手。

## 1. 管理对象

管理目录：

```text
redpitaya_laser_lock_project\docs
```

当前结构：

```text
docs\
  README_DOCS_INDEX.md
  current\
  learning\
  old\
  reports\
  corrections\
  integration\
```

原则：`docs` 根目录只保留本索引文件。新的项目文档不要直接堆在 `docs` 根目录。

## 2. 当前原则

| 原则 | 说明 |
|---|---|
| `docs/current` 是当前主线 | 项目规则、计划、上下文以这里为准 |
| `docs/learning` 用于后续学习 top | 后续 `L01`、`L02`、`L03` 等学习笔记放这里 |
| `docs/old` 是旧资料归档 | 只作参考，不是当前主线 |
| `docs/reports` 保存任务报告 | Codex 每次任务的 `REPORT_*.md` 放这里 |
| `docs/corrections` 保存错误纠正记录 | 错误修正类 `CORRECTION_*.md` 放这里 |
| `docs/integration` 保存集成方案 | 后续官方 top 接线方案、patch 说明放这里 |
| 默认中文 | 以后 Codex 生成的项目文档默认使用中文 |
| 默认新手教学风格 | 像老师给 FPGA/Verilog 新手上课一样解释 |

## 3. 文件夹作用

### 3.1 `current`

`current` 保存当前有效的项目管理文档。若 `current` 与 `old` 内容冲突，以 `current` 为准。

| 文件 | 作用 |
|---|---|
| `current\00_CONTEXT_FROM_GPT.md` | 当前项目上下文、实验背景、开发边界 |
| `current\01_PROJECT_MASTER_PLAN.md` | 项目阶段总规划 |
| `current\02_TOP_LEARNING_OUTLINE.md` | 后续重新学习 `red_pitaya_top.sv` 的大纲 |
| `current\03_CODEX_RULES.md` | Codex 工作规则 |

### 3.2 `learning`

`learning` 保存后续干净重做的 top 学习笔记。

建议命名：

```text
learning\L01_top_overview.md
learning\L02_adc_path.md
learning\L03_dac_path.md
learning\L04_clock_reset.md
learning\L05_scope_asg_pid.md
learning\L06_system_bus_ps.md
learning\L07_custom_core_insertion_point.md
```

### 3.3 `old`

`old` 保存旧版学习资料和早期草稿。

| 文件 | 作用 |
|---|---|
| `old\00_project_goal.md` | 旧版项目目标说明 |
| `old\01_official_top_learning.md` | 旧版官方 top 学习笔记 |
| `old\02_adc_signal_path.md` | 旧版 ADC 路径学习笔记 |
| `old\03_dac_signal_path.md` | 旧版 DAC 路径学习笔记 |
| `old\04_scope_asg_pid_reuse_analysis.md` | 旧版 scope/ASG/PID 复用分析草稿 |
| `old\05_mts_demod_architecture.md` | 旧版 MTS 解调架构草稿 |
| `old\06_integration_plan.md` | 旧版集成方案草稿 |
| `old\07_board_test_sop.md` | 旧版上板测试流程草稿 |

### 3.4 `reports`

`reports` 保存 Codex 每次任务的报告。

当前已有：

```text
reports\REPORT_project_directory_boundary_fix.md
reports\REPORT_docs_reorganization.md
reports\REPORT_docs_chinese_localization.md
reports\REPORT_docs_chinese_style_unification.md
```

后续报告命名建议：

```text
reports\REPORT_<topic>.md
```

### 3.5 `corrections`

`corrections` 保存错误纠正记录。

命名建议：

```text
corrections\CORRECTION_<topic>.md
```

### 3.6 `integration`

`integration` 保存后续官方 top 集成方案、接线说明、patch 说明。

命名建议：

```text
integration\INTEGRATION_PLAN_<stage>.md
```

注意：放在这里的是方案，不代表允许直接修改官方 `red_pitaya_top.sv`。

## 4. 新手教学风格总规则

以后所有 Codex 生成的项目文档、学习笔记、代码说明、REPORT，都必须默认面向 FPGA/Verilog 新手。

写作要求：

| 要求 | 说明 |
|---|---|
| 使用中文 | 方便用户直接阅读 |
| 像老师给小白上课一样解释 | 不只写结论，也要写为什么 |
| 分层讲解 | 遇到长 md 文件或长代码文件，先讲整体，再讲局部 |
| 重要文件必须讲清楚 | 说明文件作用、必须看懂的部分、暂时可不懂的部分、不要乱改的部分、和 MTS/稳频项目的关系 |
| 重要信号必须讲清楚 | 说明信号名、位宽、signed/unsigned、来自哪里、送到哪里、对项目有什么作用 |
| 涉及代码要讲硬件含义 | 说明这段代码在硬件上等价于什么电路 |
| 涉及 top 要讲系统位置 | 说明 `red_pitaya_top.sv` 在整个系统中的位置，不只罗列模块名 |
| 不确定必须明说 | 写入“不确定，需要人工确认”，不能假装确定 |

每个学习文档必须包含：

```text
新手必须明白
大白话解释
不要碰/不要改
我现在只需要记住什么
给 GPT 审查的问题
```

## 5. Codex 每次任务前应该先读哪些文件

每次开始任务前，优先阅读：

```text
docs\README_DOCS_INDEX.md
docs\current\00_CONTEXT_FROM_GPT.md
docs\current\01_PROJECT_MASTER_PLAN.md
docs\current\02_TOP_LEARNING_OUTLINE.md
docs\current\03_CODEX_RULES.md
```

如果任务涉及错误修正，还应阅读：

```text
docs\reports\REPORT_project_directory_boundary_fix.md
```

如果任务涉及旧资料，再阅读对应的：

```text
docs\old
```

## 6. 已确认

- `docs/current` 是当前有效规则和计划。
- `docs/old` 是旧资料归档，不是当前主线。
- 新的学习文档应放入 `docs/learning`。
- 新的任务报告应放入 `docs/reports`。
- 新的错误修正记录应放入 `docs/corrections`。
- 新的集成方案应放入 `docs/integration`。
- 后续 Codex 生成项目文档默认使用中文。
- 后续 Codex 生成项目文档默认采用 FPGA/Verilog 新手教学风格。

## 7. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 是否保留单独 `patches` 目录 | 目前集成方案先放 `docs/integration`，后续若 patch 变多，可再建 `patches` |
| 小任务是否都必须写 REPORT | 当前规则倾向于每次任务都写，是否简化需用户确认 |
| 旧资料是否需要逐步清理重写 | `old` 目前只归档，不删除 |

## 8. 后续文档语言规则

以后所有 Codex 生成的项目文档，默认使用中文。

以下内容保持英文原样，不翻译：

```text
文件路径
文件名
Verilog/SystemVerilog 模块名
信号名
Vivado 命令
代码片段
Git diff
```

示例：

```text
docs/current/00_CONTEXT_FROM_GPT.md
red_pitaya_top.sv
adc_dat[0]
adc_dat[1]
dac_a_sum
dac_b_sum
laser_lock_core
Run Synthesis
Generate Bitstream
```

## 9. 后续 learning 文件推荐模板

后续 `learning` 文件建议使用：

```text
# 标题

## 0. 本文件作用
## 1. 阅读对象
## 2. 实验定义
## 3. 当前原则
## 4. 大白话解释
## 5. 新手必须明白
## 6. 分层讲解
## 7. 关键文件/信号表
## 8. 证据
## 9. 不要碰/不要改
## 10. 已确认
## 11. 不确定，需要人工确认
## 12. 我现在只需要记住什么
## 13. 下一步建议
## 14. 给 GPT 审查的问题
```

## 10. 下一步建议

下一步建议从这里开始：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

然后按顺序生成新的学习笔记：

```text
learning\L01_top_overview.md
learning\L02_adc_path.md
learning\L03_dac_path.md
```

在用户明确批准之前，只做文档学习，不写 Verilog，不修改官方工程。

## 11. 给 GPT 审查的问题

1. `learning` 文件是否统一使用 `L01_top_overview.md` 这类命名？
2. `reports` 是否要求每次 Codex 工作都生成一份 `REPORT_*.md`？
3. `corrections` 是否只存放明确错误修正，不混放普通报告？
4. 后续官方 top 集成 patch 是否放在 `docs/integration`，还是新建 `patches`？
5. 新手教学风格是否还需要增加示意图、流程图或术语表？
