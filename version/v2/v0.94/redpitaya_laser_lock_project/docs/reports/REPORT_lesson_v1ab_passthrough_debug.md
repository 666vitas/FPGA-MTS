# REPORT_lesson_v1ab_passthrough_debug

## 0. 本报告作用

本报告记录本次为 `v1ab_passthrough_debug` 生成教学型版本课程文档的结果。

## 1. 生成了哪份 lesson

本次生成：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\version_lessons\LESSON_v1ab_passthrough_debug.md
```

该 lesson 面向 FPGA / Verilog / Vivado / 激光稳频新手，按教学方式说明：

- v1ab 为什么不是 MTS error；
- v1ab 对应的最小输入输出链路；
- IN1 -> ADC -> FPGA core -> DAC -> OUT1 的数据路径；
- `adc_dat[0]`、`pd_i`、`error_o`、`dac_a_sum`、`OUT1` 的含义；
- Vivado 已完成的步骤分别代表什么；
- `bit.bin` 通过 `fpgautil` 加载到 Red Pitaya 后意味着什么；
- 第一次 IN1 -> OUT1 实验如何接线和观察；
- 如果没有信号，如何按层次排查；
- 进入 v1c 前必须满足的门槛。

## 2. 没有修改 RTL

本次没有修改任何 RTL 文件。

未修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

## 3. 没有运行 Vivado

本次没有运行 Vivado。

未执行：

- Run Synthesis；
- Run Implementation；
- Generate Bitstream；
- Reset Runs；
- 修改 Vivado 工程设置。

## 4. 当前状态记录

根据当前项目状态：

- `v1ab_passthrough_debug` 已完成 Synthesis / Implementation / Generate Bitstream；
- `.bit.bin` 已通过 `fpgautil` 加载到 Red Pitaya；
- 终端已显示：

```text
BIN FILE loaded through FPGA manager successfully
```

这说明 FPGA 当前已经临时加载 v1ab 配置，但还没有进行信号发生器和示波器的实际上板波形验证。

## 5. 下一步建议

下一步建议进入实际 `v1ab IN1 -> OUT1` 板级测试：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

建议第一次使用：

```text
sine
1 kHz
100 mVpp
0 V offset
```

继续保持安全边界：

- 不接 D2-125；
- 不接真实 PD；
- 不接 EOM；
- 不接激光器反馈；
- 不打开可能覆盖 FPGA 配置的 Red Pitaya 官方网页应用。
