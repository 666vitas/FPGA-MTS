# top 文件学习大纲

## 0. 本文件作用

本文件定义后续如何重新学习官方 `red_pitaya_top.sv`。

当前只做学习文档，不写 Verilog，不修改官方代码，不实现 `laser_lock_core`。

本文件还规定：后续所有 top 学习文档都必须面向 FPGA/Verilog 新手，不能只写工程师式简略结论。

## 1. 阅读对象 / 管理对象

主要阅读对象：

```text
rtl\red_pitaya_top.sv
```

辅助阅读对象按每章需要再列出。

输出目录：

```text
redpitaya_laser_lock_project\docs\learning
redpitaya_laser_lock_project\docs\reports
```

## 2. 当前原则

| 原则 | 说明 |
|---|---|
| 官方工程只读 | 只读 `rtl/project/sim/ip/sdc`，不修改 |
| 每章单独输出 | 每章生成一个 `learning\Lxx_*.md` |
| 每章有 REPORT | 每章生成一个 `reports\REPORT_*.md` |
| 记录证据 | 说明来自哪个文件、哪个信号、哪个代码区域 |
| 记录不确定项 | 不能确认的内容必须写入“不确定，需要人工确认” |
| 不写 RTL | 学习阶段不实现任何 Verilog/SystemVerilog |
| 面向新手 | 像老师讲课一样解释“是什么、为什么、和实验有什么关系” |

## 3. 新手教学风格要求

后续每个 `learning` 文档必须默认面向 FPGA/Verilog 新手。

必须做到：

| 项目 | 要求 |
|---|---|
| 语言 | 使用中文 |
| 讲解方式 | 像老师给小白上课一样解释 |
| 结论 | 不只给结论，还要解释为什么 |
| 长文件 | 必须分层讲解，先整体、后局部 |
| top 文件 | 说明 `red_pitaya_top.sv` 在系统中的位置 |
| 代码 | 若涉及代码，说明它在硬件上等价于什么电路 |
| 不确定项 | 明确写入“不确定，需要人工确认” |

每个重要文件都要说明：

- 这个文件是干什么的；
- 新手必须看懂哪几部分；
- 哪些地方暂时可以不懂；
- 哪些地方千万不要乱改；
- 这个文件和 MTS/稳频项目有什么关系。

每个重要信号都要说明：

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

## 4. 后续 learning 文件推荐模板

建议后续 `learning` 文件统一使用以下结构：

```text
# 标题

## 0. 本文件作用

说明这个文件是学习什么的。

## 1. 阅读对象

列出本次阅读的文件，例如：

rtl/red_pitaya_top.sv

## 2. 实验定义

说明本章和 MTS/激光稳频实验的关系。

## 3. 当前原则

说明本章只读哪些文件，不改哪些文件。

## 4. 大白话解释

用新手能听懂的话解释本章主题。

## 5. 新手必须明白

列出本章最重要、必须掌握的概念。

## 6. 分层讲解

先讲系统位置，再讲模块，再讲信号。

## 7. 关键文件/信号表

用表格说明文件、信号、位宽、方向、作用。

## 8. 证据

列出证据来自哪个文件、哪个代码区域、哪个信号。

## 9. 不要碰/不要改

明确哪些官方代码不能改。

## 10. 已确认

列出已经能确认的结论。

## 11. 不确定，需要人工确认

列出不能假装确定的内容。

## 12. 我现在只需要记住什么

用几句话总结新手当前该记住的重点。

## 13. 下一步建议

说明下一步做什么，不做什么。

## 14. 给 GPT 审查的问题

列出需要 GPT 或用户复核的问题。
```

## 5. 学习章节总表

| 编号 | 名称 | 阅读文件 | learning 输出 | REPORT 输出 | 禁止事项 |
|---|---|---|---|---|---|
| L01 | `L01_top_overview` | `rtl\red_pitaya_top.sv` | `learning\L01_top_overview.md` | `reports\REPORT_L01_top_overview.md` | 不修改官方代码 |
| L02 | `L02_adc_path` | `rtl\red_pitaya_top.sv` | `learning\L02_adc_path.md` | `reports\REPORT_L02_adc_path.md` | 不修改 ADC 逻辑 |
| L03 | `L03_dac_path` | `rtl\red_pitaya_top.sv` | `learning\L03_dac_path.md` | `reports\REPORT_L03_dac_path.md` | 不修改 DAC/ODDR |
| L04 | `L04_clock_reset` | `rtl\red_pitaya_top.sv` | `learning\L04_clock_reset.md` | `reports\REPORT_L04_clock_reset.md` | 不修改 PLL/reset |
| L05 | `L05_scope_asg_pid` | `rtl\red_pitaya_top.sv` 和相关官方模块 | `learning\L05_scope_asg_pid.md` | `reports\REPORT_L05_scope_asg_pid.md` | 不修改 scope/ASG/PID |
| L06 | `L06_system_bus_ps` | `rtl\red_pitaya_top.sv`、`rtl\red_pitaya_ps.sv` | `learning\L06_system_bus_ps.md` | `reports\REPORT_L06_system_bus_ps.md` | 不修改 PS/AXI/DDR |
| L07 | `L07_custom_core_insertion_point` | 前六章学习结果 | `learning\L07_custom_core_insertion_point.md` | `reports\REPORT_L07_custom_core_insertion_point.md` | 不直接集成 |

## 6. L01_top_overview

阅读文件：

```text
rtl\red_pitaya_top.sv
```

学习目标：

- 看懂 top 文件整体结构；
- 说明 `red_pitaya_top.sv` 在 Red Pitaya 系统中的位置；
- 列出主要端口组；
- 列出主要内部模块；
- 区分 ADC、DAC、clock/reset、PS/system bus、scope/ASG/PID；
- 用大白话说明 top 文件为什么像“板级总接线图”。

输出：

```text
learning\L01_top_overview.md
reports\REPORT_L01_top_overview.md
```

禁止：

- 不修改官方代码；
- 不写 RTL；
- 不做集成方案。

## 7. L02_adc_path

阅读文件：

```text
rtl\red_pitaya_top.sv
```

学习目标：

- 追踪 `adc_dat_i` 到内部 ADC 数据；
- 理解 `adc_dat[0]`、`adc_dat[1]` 的位宽和 signed 格式；
- 对每个重要 ADC 信号说明信号名、位宽、signed/unsigned、来源、去向、对 MTS/稳频项目的作用；
- 判断 IN1/IN2 与内部信号的候选关系；
- 记录不确定项。

输出：

```text
learning\L02_adc_path.md
reports\REPORT_L02_adc_path.md
```

禁止：

- 不修改 ADC 输入逻辑；
- 不修改 `adc_dat` 相关代码；
- 不写自定义模块。

## 8. L03_dac_path

阅读文件：

```text
rtl\red_pitaya_top.sv
```

学习目标：

- 追踪 ASG/PID 到 DAC 输出路径；
- 理解 `dac_a_sum`、`dac_b_sum`；
- 理解 saturation；
- 理解 signed-to-unsigned / negative-slope conversion；
- 明确 ODDR 边界不能修改；
- 说明 DAC 相关代码在硬件上等价于加法器、限幅器、格式转换寄存器和 DDR 输出单元。

输出：

```text
learning\L03_dac_path.md
reports\REPORT_L03_dac_path.md
```

禁止：

- 不修改 DAC 输出逻辑；
- 不修改 `ODDR`；
- 不修改 `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o`。

## 9. L04_clock_reset

阅读文件：

```text
rtl\red_pitaya_top.sv
```

学习目标：

- 理解外部 ADC clock；
- 理解 PLL 输出；
- 理解 `adc_clk`、DAC clock；
- 理解 `adc_rstn`；
- 判断未来 custom core 应使用哪个 clock/reset；
- 用大白话说明 clock 像“节拍器”，reset 像“统一回到初始状态”。

输出：

```text
learning\L04_clock_reset.md
reports\REPORT_L04_clock_reset.md
```

禁止：

- 不修改 PLL；
- 不修改 reset 生成逻辑。

## 10. L05_scope_asg_pid

阅读文件：

```text
rtl\red_pitaya_top.sv
```

必要时只读相关官方模块源码。

学习目标：

- 理解 scope 观察哪些信号；
- 理解 ASG 如何产生 DAC 信号；
- 理解 PID 的输入输出；
- 判断哪些官方功能应保留作为调试和回退路径；
- 给新手解释 scope/ASG/PID 在 Red Pitaya 工程中的作用，而不是只列模块名。

输出：

```text
learning\L05_scope_asg_pid.md
reports\REPORT_L05_scope_asg_pid.md
```

禁止：

- 不修改 scope；
- 不修改 ASG；
- 不修改 PID。

## 11. L06_system_bus_ps

阅读文件：

```text
rtl\red_pitaya_top.sv
rtl\red_pitaya_ps.sv
```

学习目标：

- 理解 PS/PL 连接；
- 理解 system bus 连接方式；
- 理解为什么早期不改 PS/AXI/DDR；
- 记录未来 gain/offset 控制可能需要的软件接口；
- 给新手解释 PS 像“软件控制端”，PL 像“硬件实时处理端”。

输出：

```text
learning\L06_system_bus_ps.md
reports\REPORT_L06_system_bus_ps.md
```

禁止：

- 不修改 `red_pitaya_ps.sv`；
- 不修改 PS/AXI/DDR；
- 不修改 Vivado 工程。

## 12. L07_custom_core_insertion_point

阅读文件：

```text
learning\L01_top_overview.md
learning\L02_adc_path.md
learning\L03_dac_path.md
learning\L04_clock_reset.md
learning\L05_scope_asg_pid.md
learning\L06_system_bus_ps.md
```

学习目标：

- 总结 future `laser_lock_core` 可能输入点；
- 总结 future error signal 可能输出点；
- 规划 mux 和官方回退路径；
- 明确哪些官方保护逻辑必须保留；
- 写出后续 integration plan 的问题清单；
- 用新手能理解的话说明“插入点”不是随便改 top，而是找一个安全的接线位置。

输出：

```text
learning\L07_custom_core_insertion_point.md
reports\REPORT_L07_custom_core_insertion_point.md
```

禁止：

- 不直接修改官方 top；
- 不生成 RTL；
- 不接入 `laser_lock_core`。

## 13. 已确认

- 学习顺序从 L01 到 L07。
- 每章都要有 learning 文件和 REPORT 文件。
- 每章都禁止修改官方代码。
- 当前不开始实现 `laser_lock_core`。
- 每个学习文档都必须包含新手教学小节。
- 每个重要信号都必须解释位宽、signed/unsigned、来源、去向和项目作用。

## 14. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 每章 REPORT 是否必须很详细 | 需要用户确认颗粒度 |
| 是否需要每章都引用具体行号 | 建议需要，但行号可能随文件变化 |
| 是否允许读取相关官方模块 | 当前允许只读，不能修改 |
| 是否需要每章都画 ASCII 流程图 | 对新手有帮助，但是否强制需要用户确认 |

## 15. 下一步建议

下一步只做：

```text
learning\L01_top_overview.md
reports\REPORT_L01_top_overview.md
```

不要开始 L02，不要写 RTL，不要修改官方工程。

## 16. 给 GPT 审查的问题

1. L01 到 L07 的顺序是否适合 FPGA/Verilog 新手？
2. 每个学习文档固定加入“新手必须明白”“大白话解释”“不要碰/不要改”“我现在只需要记住什么”是否合适？
3. L07 是否应只产生问题清单，不产生 patch？
4. 是否需要后续每章都增加“术语表”？
