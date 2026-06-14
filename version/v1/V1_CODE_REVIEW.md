# V1_CODE_REVIEW

## 2026-05-27 v1d_mixer_lpf 成功基线记录

### 1. 代码审查和仿真结论

`v1d_mixer_lpf` 当前代码可作为成功基线，依据如下：

- `red_pitaya_top.sv` 已切换为 `LASER_LOCK_OUTPUT_MODE = 3`；
- `USE_LASER_LOCK_CORE = 1'b1`；
- `lpf_core.sv` 已通过单模块仿真：`tb_lpf_core PASS`；
- `laser_lock_core` v1d 集成仿真已通过：`tb_laser_lock_core_v1d PASS`；
- `OUTPUT_MODE=0/1/2` 保留历史功能；
- `OUTPUT_MODE=3` 只新增 `mixer_core -> lpf_core -> output_protect`；
- 未修改官方 ADC / DAC / PLL / ODDR / PS / AXI / XDC / SDC。

### 2. 上板结果反向验证代码链路

v1d 上板信号源差频测试已经观察到预期结果：

```text
100 kHz x 102 kHz -> OUT1 约 1.992 kHz，周期约 502 us，Vpp 约 68.3 mV
100 kHz x 101 kHz -> OUT1 约 1 kHz
```

这说明当前代码链路：

```text
adc_dat[0] / IN1
adc_dat[1] / IN2
  -> laser_lock_core
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> DAC A / OUT1
```

已经在真实 Red Pitaya 上工作。

### 3. 当前边界

该成功基线只证明信号源条件下的 `mixer + post-mixer LPF` 可用。它仍然不证明已经得到最终 MTS error，因为尚未接真实 PD、尚未接真实实验 REF、尚未加入 pre-mixer BPF/gain，也尚未做 D2-125 安全接入。

> 当前状态以 [[STATUS]] 为准。本文件保留 v1ab/v1c 的代码审查历史。

## 2026-05-27 v1d 受控 RTL 开发记录

当前动作：

```text
v1d_mixer_lpf 已开始受控 RTL 开发。
```

本次新增 / 修改范围：

```text
新增：E:\new\fpga_lock\v94\v0.94\rtl\lpf_core.sv
新增：E:\new\fpga_lock\v94\v0.94\sim\tb_lpf_core.sv
新增：E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v1d.sv
修改：E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

代码链路目标：

```text
OUTPUT_MODE=2:
  pd_i x ref_i
    -> mixer_core
    -> output_protect
    -> OUT1

OUTPUT_MODE=3:
  pd_i x ref_i
    -> mixer_core
    -> lpf_core
    -> output_protect
    -> OUT1
```

审查重点：

1. `lpf_core.sv` 是 mixer 后 LPF，不是 `10 MHz LPF / 1.8 MHz HPF`；
2. `lpf_core.sv` 使用 signed 输入和 signed 输出；
3. 内部 accumulator 使用 32-bit； 
4. `LPF_SHIFT` 可参数化，当前默认 `12`；
5. reset 后输出 0；
6. `enable_i=0` 时 accumulator 和输出清零；
7. 输出 saturation 到 signed 14-bit；
8. `laser_lock_core.sv` 保留 `OUTPUT_MODE=0/1/2`；
9. 新增 `OUTPUT_MODE=3`，只代表 mixer + post-mixer LPF；
10. 本次没有修改 `red_pitaya_top.sv`、ODDR、PLL、ADC IO、DAC IO、PS/AXI/DDR、XDC/SDC。

当前状态：

```text
尚未运行 Vivado；
尚未 Generate Bitstream；
尚未上板；
尚未接真实 PD；
尚未接 D2-125。
```

进入 bitstream 前必须先看到：

```text
PASS: tb_lpf_core
PASS: tb_laser_lock_core_v1d
```

## 2026-05-21 v1c 通过后的代码审查状态

当前最新结论：

```text
v1c_mixer_only 已经真实上板通过。
```

通过证据：

1. `tb_mixer_core` 已通过；
2. `tb_laser_lock_core_v1c` 已通过；
3. Vivado `Generate Bitstream` 成功；
4. Timing 通过，`WNS` 为正，`Failing Endpoints = 0`；
5. `.bit.bin` 已通过 `fpgautil` 加载；
6. `100 kHz x 100 kHz` 输入下，`OUT1 / CH4` 看到明显波形；
7. `OUT1 Vpp` 约 `20-22 mV`；
8. cursor 测得约 `5 us`，对应 `200 kHz`；
9. 拔掉 `IN1` 后，`OUT1` 波形消失。

代码链路结论：

```text
adc_dat[0] -> laser_lock_core.pd_i
adc_dat[1] -> laser_lock_core.ref_i
mixer_core(pd_i, ref_i)
  -> output_protect
  -> laser_error
  -> dac_a_sum_laser
  -> official DAC saturation / conversion
  -> OUT1
```

这说明 v1c 的代码连接和上板行为已经互相印证：当前 `OUT1` 不是单路直通，也不是示波器噪声，而是依赖 `IN1` 和 `IN2` 两路输入的数字混频结果。

历史记录说明：

本文后面关于 v1ab、v1c 开发前审查、v1c 上板前审查的内容仍保留为历史记录。凡是出现“当前还没有 mixer”“当前准备 v1c”“当前需要先验证 v1c”的表述，都应理解为历史阶段，不代表当前最新状态。

下一阶段代码审查重点将转为 `v1d_mixer_lpf`：

- post-mixer LPF 的截止频率和位宽；
- IIR/FIR 方案选择；
- LPF 后是否需要 saturation；
- 是否仍保持 `OUT1` 示波器优先；
- 不接 `D2-125`；
- 不做 BPF/gain/PID/AI。

## 2026-05-20 v1c 最新代码审查结论

当前 v1c 相关验证状态：

1. `v1ab-1: IN1 -> OUT1` 已经上板通过；
2. `v1ab-2: IN2 -> OUT1` 已经上板通过；
3. `tb_mixer_core` 已通过；
4. `tb_laser_lock_core_v1c` 已通过；
5. Vivado 已经成功 `Generate Bitstream`。

当前 top 参数必须保持：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 2;
```

审查解释：

- `USE_LASER_LOCK_CORE = 1'b1` 表示启用项目自己的 `laser_lock_core` 路径；
- `LASER_LOCK_OUTPUT_MODE = 2` 表示 `laser_lock_core` 选择 `mixer_core(pd_i, ref_i)`；
- `mixer_core` 只等效真实链路中的 `ZFM-3+ Mixer`；
- `mixer_core` 不包含 LPF，不包含 BPF/gain，不包含 PID；
- `control_o` 仍应保持为 `14'sd0`，当前不输出激光器控制量。

当前可以准备 v1c 上板测试，但不能把 bitstream 成功理解为已经得到 MTS error。bitstream 成功只说明 Vivado 可以把当前设计放进 FPGA；真正的 mixer-only 行为还必须由示波器验证。

安全边界：

- 不允许接 `D2-125`；
- 不允许接激光器反馈；
- 不允许直接用真实 PD 做第一轮测试；
- 第一轮必须用两路干净正弦确认 mixer-only 输出。

## 0. 本文件作用

本文件记录 v1 当前代码审查结论。它不是新的 RTL，也不修改任何 Verilog。

## 1. 当前审查对象

当前 v1ab 已经涉及的关键文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

历史审查参考：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\V1AB_SKILL_BASED_CODE_REVIEW.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports\REPORT_compare_top_official_vs_dev.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports\FIX_PLAN_dac_mux_use1_bitstream.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports\REPORT_fix_dac_mux_use1_apply.md
```

## 2. v1ab 代码审查结论

当前 `v1ab_passthrough_debug` 的核心链路已经通过真实上板测试：

```text
IN1 -> adc_dat[0] -> laser_lock_core.pd_i -> error_o -> DAC A -> OUT1
IN2 -> adc_dat[1] -> laser_lock_core.ref_i -> error_o -> DAC A -> OUT1
```

这说明当前 top 接入对 v1ab 目标是可行的。

## 3. red_pitaya_top.sv 审查结论

当前 top 的 v1ab 接入原则是：

- `USE_LASER_LOCK_CORE = 1'b1` 时启用项目路径；
- `LASER_LOCK_OUTPUT_MODE = 0` 时测试 `IN1 -> OUT1`；
- `LASER_LOCK_OUTPUT_MODE = 1` 时测试 `IN2 -> OUT1`；
- `laser_error` 进入 DAC A / OUT1 路径；
- DAC B 保持官方路径，不作为当前 REF 直通判断依据。

当前 top 接入安全边界：

- 不应修改 ODDR；
- 不应修改 PLL；
- 不应修改 ADC IO；
- 不应修改 PS/AXI/DDR；
- 不应修改 XDC/SDC；
- 不应破坏官方 DAC saturation / conversion 后级结构。

## 4. laser_lock_core.sv 审查结论

当前 v1ab 逻辑：

```text
OUTPUT_MODE = 0: pd_i  -> output_protect -> error_o
OUTPUT_MODE = 1: ref_i -> output_protect -> error_o
control_o = 14'sd0
```

教学解释：

`control_o = 14'sd0` 不是软件赋值，而是在硬件上把 OUT2 相关控制输出固定为 0。当前没有 PID，所以不应该让 OUT2 输出控制量。

## 5. output_protect.sv 审查结论

当前作用：

- reset 时输出 0；
- enable 关闭时输出 0；
- enable 打开时寄存输入数据到输出。

当前限制：

- 它不是完整 saturation 模块；
- 它没有解决 mixer 28-bit 到 14-bit 的缩放问题；
- v1c 以后仍要单独审查 scaling / saturation。

## 6. 当前不得误改的官方底层模块

后续 v1c/v1d/v1f 默认不得误改：

```text
ODDR
dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
PLL / BUFG
ADC IO
PS/AXI/DDR
XADC/AMS
XDC/SDC
```

## 7. v1c 前代码审查结论

可以准备进入 `v1c_mixer_only`，因为：

- `IN1 -> OUT1` 已通过；
- `IN2 -> OUT1` 已通过；
- 两路 ADC 输入可用；
- DAC A / OUT1 输出可用。

但 `v1c` 必须只改 mixer 相关最小范围：

- 新增 `mixer_core.sv`；
- 修改 `laser_lock_core.sv` 接入 mixer；
- 保持 `control_o = 0`；
- 不修改 `red_pitaya_top.sv` 的官方底层结构；
- 不接 D2-125。

## 8. v1c_mixer_only 代码审查记录

本次 v1c 只在允许范围内修改和新增文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\sim\tb_mixer_core.sv
E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v1c.sv
```

没有修改：

```text
red_pitaya_top.sv
ODDR
PLL / BUFG
ADC IO
DAC IO
dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
PS/AXI/DDR
XDC/SDC
官方干净原版 guanfang-v0.94
```

### 8.1 mixer_core.sv 审查

`mixer_core.sv` 对应真实链路中的 `ZFM-3+ Mixer`。输入是两路 signed 14-bit：

```text
pd_i  : 来自 IN1 / adc_dat[0]
ref_i : 来自 IN2 / adc_dat[1]
```

审查点：

- `14-bit signed x 14-bit signed` 的原始乘法结果按 `28-bit signed` 保存；
- 使用算术右移 `SHIFT = 13` 缩放回接近 14-bit 输出范围；
- 缩放后进入 saturation，避免无保护截断导致符号错误或削顶不可控；
- `rstn_i = 0` 时 `mix_o = 0`；
- `enable_i = 0` 时 `mix_o = 0`；
- 所有输出寄存在 `clk_i` 上升沿，适合接入当前 `adc_clk` 域。

### 8.2 laser_lock_core.sv 审查

`laser_lock_core.sv` 保留 v1ab 已通过模式，并新增 v1c 模式：

```text
OUTPUT_MODE = 0: pd_i -> output_protect -> error_o
OUTPUT_MODE = 1: ref_i -> output_protect -> error_o
OUTPUT_MODE = 2: mixer_core(pd_i, ref_i) -> output_protect -> error_o
其他值       : 0 -> output_protect -> error_o
```

`control_o` 仍然固定为 `14'sd0`，因此当前没有 PID，没有 OUT2 控制输出。

### 8.3 当前风险

- `OUTPUT_MODE = 2` 比 passthrough 多 mixer 寄存器延迟，再经过 `output_protect` 寄存器，示波器上可能表现为相位延迟；
- mixer-only 输出还没有 LPF，所以同频输入时可能看到 DC/低频成分与 `2f` 成分混在一起；
- 当前还没有 Vivado 综合验证，也没有上板验证；
- 进入上板前必须确认 `mixer_core.sv` 和两个 testbench 已加入相应仿真/工程流程。
