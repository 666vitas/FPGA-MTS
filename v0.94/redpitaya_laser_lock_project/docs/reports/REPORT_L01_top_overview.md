# REPORT: L01_top_overview

## 0. 本文件作用

本文件记录 L01_top_overview 的执行结果。

本次任务只阅读官方：

```text
rtl\red_pitaya_top.sv
```

并生成 L01 学习文档。

## 1. 本次任务是什么

任务目标：

- 学习 `red_pitaya_top.sv` 的整体结构；
- 用新手能理解的方式说明它为什么像 Red Pitaya FPGA 的“总接线板”；
- 说明 ADC、DAC、clock/reset、PS/system bus、scope/ASG/PID 在 top 中的大概位置；
- 不深入 L02 ADC 细节；
- 不深入 L03 DAC 细节；
- 不修改官方工程；
- 不生成 Verilog。

## 2. 阅读对象

本次只读：

```text
rtl\red_pitaya_top.sv
```

没有读取或修改官方其他源码作为本次学习对象。

## 3. 生成了哪些文件

本次新增：

```text
docs\learning\L01_top_overview.md
docs\reports\REPORT_L01_top_overview.md
```

## 4. 学习结果摘要

已确认 `red_pitaya_top.sv` 是 Red Pitaya FPGA 的顶层总连接文件。

它大致连接：

| 区域 | 大概作用 |
|---|---|
| 顶层端口 | 连接 PS、DDR、ADC、DAC、PWM、XADC、扩展口、SATA、LED |
| PLL/clock/reset | 生成并分发 FPGA 内部时钟和 reset |
| PS/system bus | 连接 ARM/Linux 与 FPGA 内部模块 |
| ADC IO | 把外部 ADC 数据变成 FPGA 内部数据 |
| DAC IO | 把 FPGA 内部数据送往 DAC 输出引脚 |
| House Keeping | 管理 LED、扩展口、digital_loop、daisy mode |
| scope | 观察/采集 ADC 数据 |
| ASG | 官方任意波形发生器 |
| PID | 官方 MIMO PID 控制器 |
| daisy | 板间高速连接 |

大白话结论：

```text
red_pitaya_top.sv 不是算法文件，而是 Red Pitaya FPGA 的总接线板。
```

## 5. 证据摘要

| 证据 | 位置 |
|---|---|
| 官方注释说明 top 连接 PS 和应用模块 | `rtl\red_pitaya_top.sv` 第 1-43 行附近 |
| 顶层模块声明 | 第 52 行附近 |
| ADC/DAC 顶层端口 | 第 95-104 行附近 |
| PLL/clock/reset 区域 | 第 214-264 行附近 |
| PS 连接区域 | 第 271-325 行附近 |
| system bus interconnect | 第 327-344 行附近 |
| ADC IO 区域 | 第 383-404 行附近 |
| DAC IO 区域 | 第 406-430 行附近 |
| House Keeping | 第 432-471 行附近 |
| scope | 第 512-547 行附近 |
| ASG | 第 549-571 行附近 |
| PID | 第 573-593 行附近 |
| daisy | 第 595-639 行附近 |

## 6. 没有做什么

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

本次没有生成 RTL。

本次没有实现：

```text
laser_lock_core
```

本次没有开始：

```text
L02_adc_path
L03_dac_path
```

## 7. 已确认

- `red_pitaya_top.sv` 是官方顶层连接文件。
- ADC、DAC、clock/reset、PS/system bus、scope/ASG/PID 都在 top 中有明确区域。
- 对 MTS/激光稳频项目来说，top 的当前价值是帮助我们找未来安全接线点。
- 现阶段不应把 MTS 算法写进 top。

## 8. 不确定，需要人工确认

| 不确定项 | 说明 |
|---|---|
| `adc_dat[0]` 和 IN1 的物理对应 | 留到 L02 结合更多证据确认 |
| `adc_dat[1]` 和 IN2 的物理对应 | 留到 L02 结合更多证据确认 |
| DAC A/B 与 OUT1/OUT2 的物理对应 | 留到 L03 确认 |
| 当前 `rtl\red_pitaya_top.sv` 是否完全干净官方原版 | 如需确认，应后续单独做官方原版对比 |

## 9. 下一步建议

下一步建议是 L02：

```text
learning\L02_adc_path.md
reports\REPORT_L02_adc_path.md
```

但本次任务到 L01 为止。

不要自动继续 L02，不要写 Verilog，不要修改官方工程。

## 10. 给 GPT 审查的问题

1. L01 是否已经足够作为 top 总览？
2. 是否需要在 L01 中增加一张更详细的 ASCII 系统框图？
3. L02 是否应该专门追踪 `adc_dat_i -> adc_dat_raw -> adc_dat`？
4. L03 是否应该专门追踪 `asg_dat/pid_dat -> dac_a_sum/dac_b_sum -> ODDR`？
