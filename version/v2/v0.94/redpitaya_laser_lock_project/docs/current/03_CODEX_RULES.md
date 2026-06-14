# Codex 工作规则

## 0. 本文件作用

本文件规定 Codex 在本项目中的工作边界。

Codex 每次开始任务前都应阅读本文件，避免误改官方工程或把自定义文件放错位置。

本文件也规定：后续 Codex 生成的项目文档、学习笔记、代码说明、REPORT，都必须默认面向 FPGA/Verilog 新手。

## 1. 管理对象

官方工程根目录：

```text
E:\new\fpga_lock\v94\v0.94
```

自定义项目目录：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

## 2. 当前原则

| 规则 | 说明 |
|---|---|
| 官方工程只读 | 当前只允许阅读官方文件 |
| 自定义文件独立放置 | 自定义内容只能放在 `redpitaya_laser_lock_project` |
| 不直接修改官方 top | 未经明确允许，不改 `red_pitaya_top.sv` |
| 先写文档再写代码 | 代码生成前必须有计划 |
| 先写 integration plan 再集成 | 集成前必须先写方案 |
| 默认中文文档 | 方便 FPGA/Verilog 新手阅读 |
| 默认新手教学风格 | 像老师给小白上课一样解释 |

## 3. 官方工程只读范围

以下目录当前只读：

```text
rtl
project
sim
ip
sdc
```

不得直接修改：

```text
red_pitaya_top.sv
red_pitaya_ps.sv
PS/AXI/DDR/PLL/ODDR/XDC
```

不得直接修改官方：

- ADC IO 输入格式转换底层逻辑；
- DAC ODDR 输出逻辑；
- PS / AXI / DDR；
- PLL；
- XDC / SDC 约束；
- scope / ASG / PID / HK 官方源码。

## 4. 自定义文件位置

自定义文档：

```text
redpitaya_laser_lock_project\docs
```

自定义 RTL：

```text
redpitaya_laser_lock_project\rtl
```

自定义 testbench：

```text
redpitaya_laser_lock_project\sim
```

实验记录：

```text
redpitaya_laser_lock_project\experiment_logs
```

禁止把自定义 RTL 放到官方：

```text
rtl
```

禁止把自定义 testbench 放到官方：

```text
sim
```

## 5. 新手教学风格规则

以后所有 Codex 生成的项目文档、学习笔记、代码说明、REPORT，都必须默认面向 FPGA/Verilog 新手。

写作风格要求：

| 要求 | 说明 |
|---|---|
| 使用中文 | 默认中文解释 |
| 像老师讲课 | 假设用户是 FPGA/Verilog 新手 |
| 不只给结论 | 必须解释为什么 |
| 长文件分层讲解 | 先讲系统位置，再讲模块，再讲信号和代码 |
| 不确定项单独列出 | 不能假装确定 |

每个重要文件都要告诉用户：

- 这个文件是干什么的；
- 新手必须看懂哪几部分；
- 哪些地方暂时可以不懂；
- 哪些地方千万不要乱改；
- 这个文件和 MTS/稳频项目有什么关系。

每个重要信号都要解释：

- 信号名；
- 位宽；
- signed/unsigned；
- 来自哪里；
- 送到哪里；
- 对 MTS/稳频项目有什么作用。

每个学习文档必须包含：

```text
新手必须明白
大白话解释
不要碰/不要改
我现在只需要记住什么
给 GPT 审查的问题
```

如果涉及代码，必须说明这段代码在硬件上等价于什么电路。

如果涉及 top 文件，必须说明它在系统中的位置，而不是只罗列模块名。

如果有不确定项，必须明确写入“不确定，需要人工确认”。

## 6. 文档规则

每次任务必须生成或更新 REPORT：

```text
docs\reports\REPORT_<topic>.md
```

每次错误必须生成 CORRECTION：

```text
docs\corrections\CORRECTION_<topic>.md
```

每次集成前必须先生成 integration plan：

```text
docs\integration\INTEGRATION_PLAN_<stage>.md
```

后续所有项目文档默认使用中文。

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

## 7. 代码生成规则

当前阶段不写 Verilog。

当用户明确要求代码生成时，必须提供：

| 项目 | 说明 |
|---|---|
| 文件列表 | 说明新增/修改哪些文件 |
| 每个文件作用 | 说明为什么需要它 |
| 完整 diff | 每次代码生成必须给 diff |
| testbench | 必须有对应仿真 |
| Vivado 步骤 | 说明如何加入文件和运行 |
| 验证步骤 | 说明仿真或示波器如何验证 |
| 回退方式 | 说明如何撤回或关闭功能 |
| 硬件含义 | 解释关键代码在硬件上等价于什么电路 |

代码只能放在：

```text
redpitaya_laser_lock_project\rtl
redpitaya_laser_lock_project\sim
```

## 8. 集成规则

每次官方 top 集成前，必须先写：

```text
docs\integration\INTEGRATION_PLAN_<stage>.md
```

integration plan 必须说明：

- 读取哪些官方信号；
- 驱动哪些官方信号；
- mux 放在哪里；
- 如何保留官方路径；
- 哪些官方保护逻辑不动；
- 如何回退；
- 如何验证；
- 对 FPGA/Verilog 新手来说，这个接线方案为什么安全。

除非用户明确允许，否则不允许直接修改：

```text
rtl\red_pitaya_top.sv
```

## 9. 已确认

- 官方工程当前只读。
- 自定义文件只能放在 `redpitaya_laser_lock_project`。
- 不允许直接修改官方 `red_pitaya_top.sv`。
- 不允许修改 `PS/AXI/DDR/PLL/ODDR/XDC`。
- 每次任务必须生成 REPORT。
- 每次错误必须生成 CORRECTION。
- 每次代码生成必须给 diff。
- 每次集成前必须先生成 integration plan。
- 默认所有文档使用中文。
- 默认所有项目文档、学习笔记、代码说明、REPORT 面向 FPGA/Verilog 新手。

## 10. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 小任务是否也必须生成 REPORT | 当前按“必须”执行，若要简化需用户确认 |
| 是否允许未来自动生成 patch | 需要用户明确允许 |
| 何时允许修改官方 Vivado 工程 | 必须由用户明确批准 |
| 是否每篇学习文档都需要 ASCII 图 | 有助于新手理解，但是否强制需要用户确认 |

## 11. 下一步建议

当前不要写 RTL。

当前不要修改官方工程。

当前不要开始 L01 学习，除非用户明确要求。

下一步如用户允许，可按：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

开始生成新的 `learning` 文档。

## 12. 给 GPT 审查的问题

1. 这些规则是否足够保护官方工程？
2. REPORT 和 CORRECTION 是否应该严格分开？
3. 是否需要增加“每次任务前必须读 README_DOCS_INDEX.md”的硬规则？
4. 新手教学风格是否需要更强制地要求“术语表”和“ASCII 流程图”？
