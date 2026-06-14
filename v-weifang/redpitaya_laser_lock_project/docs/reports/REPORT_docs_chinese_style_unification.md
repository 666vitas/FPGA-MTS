# REPORT: docs 中文语言和格式统一

## 0. 本文件作用

本文件记录本次 docs 文档中文化和格式统一任务。

## 1. 本次中文化了哪些文件

本次改写了以下文件：

```text
docs\README_DOCS_INDEX.md
docs\current\00_CONTEXT_FROM_GPT.md
docs\current\01_PROJECT_MASTER_PLAN.md
docs\current\02_TOP_LEARNING_OUTLINE.md
docs\current\03_CODEX_RULES.md
docs\reports\REPORT_docs_reorganization.md
```

改写内容包括：

- 标题；
- 说明文字；
- 任务描述；
- 规则；
- 下一步建议；
- 给 GPT 审查的问题。

## 2. 哪些文件保持不动

本次没有修改 `docs/old` 下的任何文件。

本次没有修改：

```text
docs\reports\REPORT_project_directory_boundary_fix.md
docs\reports\REPORT_docs_chinese_localization.md
```

除本次新增报告外，未修改其他 `reports` 文件。

## 3. 是否采用 old 文件风格

已尽量采用 `docs/old` 中旧版学习笔记的结构风格。

主要格式包括：

```text
## 0. 本文件作用
## 1. 阅读对象 / 管理对象
## 2. 当前原则
## 3. 关键内容
## 4. 规则表 / 文件表 / 阶段表
## 5. 已确认
## 6. 不确定，需要人工确认
## 7. 下一步建议
## 8. 给 GPT 审查的问题
```

不同文件按内容做了少量调整，没有强行完全一致。

## 4. 后续默认文档语言规则

后续 Codex 生成的项目文档默认使用中文。

以下内容保持英文原样：

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
red_pitaya_top.sv
adc_dat[0]
adc_dat[1]
dac_a_sum
dac_b_sum
laser_lock_core
Run Synthesis
Generate Bitstream
docs/current/00_CONTEXT_FROM_GPT.md
```

## 5. 后续 learning 文件模板建议

建议后续 `learning` 文件使用以下模板：

```text
# Lxx 标题

## 0. 本文件作用
## 1. 阅读对象
## 2. 实验定义
## 3. 当前原则
## 4. 关键路径追踪
## 5. 证据
## 6. 已确认
## 7. 不确定，需要人工确认
## 8. 下一步建议
## 9. 给 GPT 审查的问题
```

若涉及信号或文件，应优先使用表格说明。

## 6. 是否修改官方工程

没有修改官方工程。

未修改：

```text
rtl
project
sim
ip
sdc
red_pitaya_top.sv
```

## 7. 是否生成 RTL

没有生成 RTL。

没有生成或实现：

```text
laser_lock_core
```

## 8. 下一步建议

下一步仍然不要写 Verilog。

建议从：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

开始，生成：

```text
learning\L01_top_overview.md
reports\REPORT_L01_top_overview.md
```

只做 L01 学习，不开始 L02，不修改官方工程。

## 9. 给 GPT 审查的问题

1. 当前中文格式是否足够适合 FPGA/Verilog 新手阅读？
2. 后续 `learning` 文件是否统一使用本报告建议的模板？
3. 是否需要把 `docs\reports\REPORT_project_directory_boundary_fix.md` 也改成同样中文格式？
