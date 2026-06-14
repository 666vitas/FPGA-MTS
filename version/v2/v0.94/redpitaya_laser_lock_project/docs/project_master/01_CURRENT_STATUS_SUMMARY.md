# 当前状态总结

## 0. 本文件作用

本文件总结当前项目已经完成什么、还没有完成什么，以及下一步最小目标是什么。它面向 FPGA / Verilog / Vivado 新手，尽量用“总账本”的方式帮你判断项目现在站在哪个位置。

## 1. 已完成

根据已有 `docs`、`reports`、`integration`、`board_tests`、`beginner_roadmap`、`patches`、`rtl`、`sim` 内容，当前已经完成以下资料和阶段成果：

- `L01_top_overview`：学习了 `red_pitaya_top.sv` 的总体作用。可以把它理解成 Red Pitaya FPGA 的“总接线板”。
- `L02_adc_path`：整理了 ADC 输入路径，候选结论是 `adc_dat[0]` 对应 `IN1`，`adc_dat[1]` 对应 `IN2`。
- `L03_dac_path`：整理了 DAC 输出路径，后续应复用官方 DAC saturation、格式转换和 ODDR，不直接驱动底层 DAC 引脚。
- `L04_clock_reset`：整理了 `adc_clk`、`adc_rstn` 等时钟复位关系。
- `IMPLEMENTATION_PLAN_mts_error_chain_v1`：明确第一阶段使用外部 `4.6 MHz REF`，FPGA 不生成 REF、不驱动 EOM，只做数字处理链路。
- `v1ab_passthrough_debug`：把 v1a `IN1 -> OUT1` 和 v1b `IN2 -> OUT1` 合并为一个可通过 `OUTPUT_MODE` 选择的调试版本。
- `laser_lock_core.sv`：已实现 `pd_i/ref_i` 直通选择、`error_o` 输出和 `control_o = 0`。
- `output_protect.sv`：已实现基础输出保护寄存器，用于 reset 时输出安全值。
- `tb_laser_lock_core_v1ab.sv`：已覆盖 `OUTPUT_MODE=0` 和 `OUTPUT_MODE=1` 的仿真检查。
- `BOARD_TEST_v1ab`：已写出 `IN1 -> OUT1` 和 `IN2 -> OUT1` 的上板测试 SOP。
- `INTEGRATION_PLAN_v1ab`：已规划 `laser_lock_core` 如何接入 `red_pitaya_top.sv`。
- `patch guide / patch`：已生成 `PATCH_v1ab_passthrough_debug.diff` 和说明文档。
- `beginner_roadmap`：已整理 Vivado、仿真、集成、上板、失败排查等新手路线。
- workspace merge：已把 `laser_lock_core.sv` 和 `output_protect.sv` 汇总到当前开发工程 `E:\new\fpga_lock\v94\v0.94\rtl`。
- `v1ab` RTL 已生成；
- `tb_laser_lock_core_v1ab.sv` 已通过；
- Vivado `synthesis / implementation / bitstream` 已成功；
- `.bit` 已转换为 `.bit.bin`；
- `.bit.bin` 已上传到 Red Pitaya；
- 已通过命令加载成功：

```bash
fpgautil -b /root/red_pitaya_top.bit.bin
```

终端显示：

```text
BIN FILE loaded through FPGA manager successfully
```

这说明 FPGA 当前已经临时加载了 v1ab bitstream。

但是：当前还没有实际连接信号发生器和示波器完成物理测试。因此 `v1ab` 还不能算完整通过。

## 2. 当前 RTL 状态

当前 `v1ab` 的 RTL 行为很简单，目的是验证输入输出通路，不是实现 MTS 解调。

`laser_lock_core.sv` 当前状态：

```text
OUTPUT_MODE = 0: pd_i  -> error_o
OUTPUT_MODE = 1: ref_i -> error_o
control_o = 0
```

还没有实现：

- mixer；
- LPF；
- BPF；
- PID；
- sweep；
- lock/relock FSM；
- AI。

所以当前版本不能称为真正的 MTS error generator。它只是上板调试用的“通路验证版”。

## 3. 当前 Vivado / top 状态需要确认

当前 Vivado 编译和 bitstream 生成已经成功。后续如果重新打开 Vivado 或切换 `LASER_LOCK_OUTPUT_MODE`，仍需要确认以下项目：

- `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv` 是否存在；
- `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv` 是否存在；
- `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv` 是否已经 patch；
- Vivado `Sources` 是否已经添加 `laser_lock_core.sv` 和 `output_protect.sv`；
- `Run Synthesis / Run Implementation / Generate Bitstream` 是否对应当前参数重新执行过。

最近的 workspace merge 报告显示，当前开发区 `red_pitaya_top.sv` 已经包含：

```text
USE_LASER_LOCK_CORE
LASER_LOCK_OUTPUT_MODE
i_laser_lock_core
laser_error
laser_control
```

并且当前参数为：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 0
```

当前 `LASER_LOCK_OUTPUT_MODE = 0` 的 bitstream 已经加载到板子，目标是先测试 `IN1 -> OUT1`。

如果后续要测试 `IN2 -> OUT1`，必须把：

```text
LASER_LOCK_OUTPUT_MODE = 1
```

然后重新：

```text
Generate Bitstream
转 .bit.bin
scp 上传
fpgautil 加载
```

## 4. 当前阻塞点

项目当前还没完成物理上板波形验证。

已完成：

```text
RTL -> testbench -> synthesis -> implementation -> bitstream -> bit.bin -> fpgautil 加载
```

当前缺少：

```text
信号发生器 + 示波器 实际验证 IN1 -> OUT1
信号发生器 + 示波器 实际验证 IN2 -> OUT1
```

当前不应该直接进入 `v1c_mixer_only`。因为如果 `v1ab` 的 `IN1/IN2 -> OUT1` 通路还没被板上验证，后面 mixer 出问题时会分不清是算法问题、Vivado/bitstream 问题，还是 ADC/DAC 接线问题。

## 5. 下一步最小目标

`v1ab` 的最小目标必须按顺序完成：

```text
Step 1: v1ab-1 IN1 -> OUT1
Step 2: v1ab-2 IN2 -> OUT1
Step 3: 两步都通过后，才进入 v1c_mixer_only
```

### Step 1：v1ab-1：IN1 -> OUT1

接线：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

信号：

```text
1 kHz sine
100 mVpp
0 V offset
```

目的：

```text
证明 ADC -> FPGA core -> DAC 这条链路通了。
```

### Step 2：v1ab-2：IN2 -> OUT1

需要重新设置：

```text
LASER_LOCK_OUTPUT_MODE = 1
```

并重新：

```text
Generate Bitstream
转 .bit.bin
scp 上传
fpgautil 加载
```

接线：

```text
4.6 MHz REF 安全幅度 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF 同时 -> 示波器 CH2
```

信号：

```text
4.6 MHz sine
建议先 100 mVpp 到 500 mVpp
0 V offset
不要第一次就直接 ±1 V
严禁 6.32 Vpp 直接进 IN2
```

目的：

```text
证明 REF 能进入 FPGA，后续 mixer 有参考输入。
```

成功以后，才进入 `v1c_mixer_only`。

## 6. 当前马上执行的操作

当前不要开始 `v1c_mixer_only`，也不要接真实实验链路。马上执行的最小闭环是先完成 `v1ab IN1 -> OUT1` 物理测试。

操作顺序：

1. 保持当前已加载的 `LASER_LOCK_OUTPUT_MODE = 0` v1ab bitstream；
2. 不打开可能覆盖 FPGA 的 Red Pitaya 官方网页应用；
3. 信号发生器设置为 `1 kHz sine, 100 mVpp, 0 V offset`；
4. 信号发生器输出先接示波器确认；
5. 按 Step 1 接线；
6. 示波器观察 `OUT1` 是否有 1 kHz 同频波形；
7. 记录幅度、极性、是否削顶、是否顶死；
8. 不接 `D2-125`；
9. 不接真实 `PD`；
10. 不接激光器反馈。

这一轮只验证最基础的通路：

```text
信号发生器 -> IN1 -> FPGA -> OUT1 -> 示波器
```

只要这个通路没有被确认，就不要进入 `IN2 -> OUT1`、mixer、LPF 或真实 MTS 链路。`IN1 -> OUT1` 通过后，下一步才是重新生成 `OUTPUT_MODE=1` 的 bitstream 测 `IN2 -> OUT1`。
