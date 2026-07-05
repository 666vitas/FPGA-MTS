# v3REG0_TIMING_FIX_1：ramp_generator 配置寄存器 timing 修复

日期：2026-07-05

## 触发原因

用户手动 Vivado implementation timing failed：

```text
WNS = -3.697 ns
TNS = -274.520 ns
Failing Endpoints = 830

Worst path:
From: i_custom_register_bank/.../C
To:   i_ramp_generator/.../D
Logic Levels = 18
High Fanout = 30
Total Delay = 11.685 ns
Logic Delay = 5.276 ns
Net Delay = 6.409 ns
Requirement = 8.000 ns
```

结论：当前 v3REG-0 不能 Generate Bitstream，不能烧录，不能上板。

## 修复范围

只修改：

```text
v0.94/rtl/ramp_generator.sv
version/STATUS.md
version/v3/V3REG0_TIMING_FIX_1_REGISTERED_RAMP_CONFIG_2026-07-05.md
```

未修改：

```text
red_pitaya_top.sv
custom_register_bank.sv
laser_lock_core.sv
pi_controller_seq.sv
pi_controller.sv
mixer_core.sv
lpf_core.sv
output_protect.sv
XDC / constraints
Vivado project structure
```

## RTL 修复内容

在 `ramp_generator` 内部新增本地配置寄存器：

```text
offset_q
amp_q
step_q
update_div_q
update_div_m1_q
limit_q
```

修复前，`offset_i / amp_i / step_i / update_div_i / limit_i` 直接进入三角波位置更新、限幅和 tick 判断的组合逻辑。这样 `custom_register_bank` 的寄存器输出可以一路穿过较深组合逻辑到 `ramp_generator` 内部寄存器 D 端，形成 implementation timing fail。

修复后，`ramp_generator` 先把输入参数采样到本地配置寄存器，再由本地 q 寄存器参与后续组合计算。`custom_register_bank -> ramp_generator` 的路径被切到配置寄存器 D 端，不再穿过完整三角波 datapath。

`update_div_i` 的处理也改为两级：

```text
update_div_i
-> sanitize
-> update_div_q
-> update_div_m1_q
-> tick_w = (update_cnt_q == update_div_m1_q)
```

这样 tick 判断不再每周期直接执行 `update_div_i - 1`。

## 保持的功能边界

```text
reset 时 scan_o = 0
enable=0 时 scan_o = 0
enable=1 时输出 offset + triangle
默认 offset=6962、amp=410、step=1、update_div=1524、limit=8191
默认输出仍对应约 0.80~0.90 V、约 50 Hz
saturated_o 行为保留
输出仍限制在 +/-8191
```

## 本次验证

只运行独立语法检查：

```text
cd v0.94
xvlog -sv rtl/ramp_generator.sv
```

结果：

```text
0 error
```

本次没有运行 Vivado synthesis / implementation，没有生成 bitstream / bin，没有烧录 Red Pitaya。

## 用户下一步

用户需要手动在 Vivado 中执行：

```text
1. Reset Runs
2. Run Synthesis
3. Run Implementation
4. 检查 timing summary
```

通过标准仍然是：

```text
WNS >= 0
TNS = 0
Failing Endpoints = 0
```

只有 timing 通过后，才允许继续 Generate Bitstream。timing 未通过前禁止烧录、禁止上板、禁止 OUT2 接任何真实执行器。

## v3REG0_TIMING_FIX_2

用户手动 Vivado 结果仍有 1 条 setup fail：

```text
WNS = -0.085 ns
TNS = -0.085 ns
Failing Endpoints = 1
Worst path: i_ramp_generator/step_q_reg[5]/C -> i_ramp_generator/direction_up_q_reg/D
```

本次只修改 `v0.94/rtl/ramp_generator.sv`。原实现中 `step_q -> pos +/- step -> amp 边界比较 -> direction_up_q` 仍在同一个 `pll_adc_clk` 周期内完成。修复后改成两拍更新：

```text
tick 拍：只计算 pos_candidate_q，并寄存 candidate_direction_up_q / update_pending_q
提交拍：只用已寄存的 pos_candidate_q / candidate_direction_up_q 做边界判断和方向翻转
```

这样 `direction_up_q` 不再由 `step_q` 同周期组合决定，`step_q` 只到 `pos_candidate_q`，下一拍才由 candidate 决定方向。

验证：

```text
cd v0.94
xvlog -sv rtl/ramp_generator.sv
```

结果：0 error。未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录 Red Pitaya。
