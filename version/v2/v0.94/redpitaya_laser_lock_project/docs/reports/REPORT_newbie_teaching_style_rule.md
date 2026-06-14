# REPORT: 新手教学风格规则加入

## 0. 本文件作用

本文件记录本次在项目文档规则中加入“FPGA/Verilog 新手教学风格要求”的任务。

## 1. 本次任务是什么

本次任务是在现有 docs 规则中加入一条长期规则：

以后所有 Codex 生成的项目文档、学习笔记、代码说明、REPORT，都必须默认面向 FPGA/Verilog 新手。

写作不能只写工程师式简略结论，而要像老师给小白上课一样解释。

## 2. 修改了哪些文件

本次修改了：

```text
docs\README_DOCS_INDEX.md
docs\current\02_TOP_LEARNING_OUTLINE.md
docs\current\03_CODEX_RULES.md
```

本次新增了：

```text
docs\reports\REPORT_newbie_teaching_style_rule.md
```

## 3. 加入了哪些规则

加入的核心规则包括：

- 默认使用中文；
- 像老师给 FPGA/Verilog 新手上课一样解释；
- 不只给结论，也要解释为什么；
- 长 md 文件或长代码文件必须分层讲解；
- 重要文件必须说明作用、必须看懂部分、暂时可不懂部分、不要乱改部分、和 MTS/稳频项目的关系；
- 重要信号必须说明信号名、位宽、signed/unsigned、来源、去向、项目作用；
- 每个学习文档必须包含“新手必须明白”；
- 每个学习文档必须包含“大白话解释”；
- 每个学习文档必须包含“不要碰/不要改”；
- 每个学习文档必须包含“我现在只需要记住什么”；
- 每个学习文档必须包含“给 GPT 审查的问题”；
- 涉及代码时必须解释硬件等价电路；
- 涉及 top 文件时必须说明它在系统中的位置；
- 不确定项必须写入“不确定，需要人工确认”。

## 4. 没有修改哪些内容

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

本次没有修改任何 Verilog/SystemVerilog 文件。

本次没有生成 RTL。

本次没有开始 L01 学习。

## 5. 已确认

- 新手教学风格规则已经写入 `docs\README_DOCS_INDEX.md`。
- 新手教学风格规则已经写入 `docs\current\02_TOP_LEARNING_OUTLINE.md`。
- 新手教学风格规则已经写入 `docs\current\03_CODEX_RULES.md`。
- 后续 learning 文件模板已经加入新手必备小节。

## 6. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 是否每篇学习文档都必须画 ASCII 流程图 | 当前建议，但未强制 |
| 是否每篇学习文档都必须有术语表 | 当前建议后续 GPT 审查 |
| REPORT 是否也要固定加入“大白话解释” | 当前规则要求面向新手，但未固定 REPORT 模板 |

## 7. 下一步建议

下一步仍然不要写 Verilog，不要修改官方工程。

如果用户确认开始学习，再从：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

开始生成：

```text
learning\L01_top_overview.md
reports\REPORT_L01_top_overview.md
```

## 8. 给 GPT 审查的问题

1. 新手教学风格是否足够明确？
2. 后续 learning 文件是否必须增加“术语表”？
3. 后续 REPORT 是否也固定使用“新手必须明白 / 大白话解释 / 不确定项”结构？
