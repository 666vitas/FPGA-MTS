# PATCH_GUIDE_v1ab_passthrough_debug

## 0. 本文件作用

本文件指导如何审查和应用：

```text
redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

这个 patch 的目标是把已经通过仿真的 `laser_lock_core` 接入官方 `rtl\red_pitaya_top.sv`，用于 `v1ab_passthrough_debug` 上板验证。

重要提醒：

- 本文件只是说明；
- patch 当前还没有应用；
- 官方 `rtl\red_pitaya_top.sv` 当前没有被本任务修改；
- Vivado 工程当前没有被本任务修改。

## 1. patch 修改了哪些位置

### 1.1 新增 localparam

patch 计划在 `red_pitaya_top.sv` 的 local signals 区域新增：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 0;
```

含义：

| 参数 | 作用 |
|---|---|
| `USE_LASER_LOCK_CORE` | 选择官方 DAC 路径还是 `laser_lock_core` 路径 |
| `LASER_LOCK_OUTPUT_MODE` | 选择 `pd_i` 还是 `ref_i` 直通到 `error_o` |

`LASER_LOCK_OUTPUT_MODE` 的设置：

| 值 | 用途 |
|---:|---|
| 0 | v1a：`IN1 -> OUT1` |
| 1 | v1b：`IN2 -> OUT1` |

### 1.2 新增 laser_lock_core 相关信号

patch 计划新增：

```systemverilog
logic signed [13:0] laser_error;
logic signed [13:0] laser_control;
```

说明：

| 信号 | 位宽 | signed/unsigned | 来源 | 去向 |
|---|---:|---|---|---|
| `laser_error` | 14 bit | signed | `laser_lock_core.error_o` | DAC A saturation 前的 `dac_a_sum` mux |
| `laser_control` | 14 bit | signed | `laser_lock_core.control_o` | 第一阶段不用于输出，保留用于后续 |

### 1.3 实例化 laser_lock_core

patch 计划在 ADC 数据转换之后、DAC IO 区域之前实例化：

```systemverilog
laser_lock_core #(
  .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
) i_laser_lock_core (
  .clk_i     (adc_clk      ),
  .rstn_i    (adc_rstn     ),
  .pd_i      (adc_dat[0]   ),
  .ref_i     (adc_dat[1]   ),
  .error_o   (laser_error  ),
  .control_o (laser_control)
);
```

这表示：

```text
clk_i  <- adc_clk
rstn_i <- adc_rstn
pd_i   <- adc_dat[0]
ref_i  <- adc_dat[1]
```

### 1.4 修改 dac_a_sum/dac_b_sum mux

patch 计划把官方：

```systemverilog
assign dac_a_sum = asg_dat[0] + pid_dat[0];
assign dac_b_sum = asg_dat[1] + pid_dat[1];
```

改为：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE
                 ? {laser_error[14-1], laser_error}
                 : asg_dat[0] + pid_dat[0];

assign dac_b_sum = USE_LASER_LOCK_CORE
                 ? 15'sd0
                 : asg_dat[1] + pid_dat[1];
```

也就是：

| `USE_LASER_LOCK_CORE` | DAC A | DAC B |
|---:|---|---|
| 0 | 官方 `asg_dat[0] + pid_dat[0]` | 官方 `asg_dat[1] + pid_dat[1]` |
| 1 | `laser_error` 符号扩展到 15 bit | `15'sd0` |

## 2. 为什么这样改

### 2.1 为什么接到 DAC A saturation 前

`laser_lock_core.error_o` 是 14-bit signed 数字信号。

官方 DAC 路径原来是：

```text
asg_dat + pid_dat
  -> dac_a_sum / dac_b_sum
  -> saturation
  -> signed-to-unsigned / negative-slope conversion
  -> DAC ODDR
  -> dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

我们把 `laser_error` 接到 `dac_a_sum` 附近，是为了继续复用官方后面的保护和板级输出逻辑。

### 2.2 为什么不直接驱动 dac_dat_o

不能直接驱动：

```text
dac_dat_o
dac_wrt_o
dac_sel_o
dac_clk_o
dac_rst_o
```

原因：

- 这些是板级 DAC 输出层信号；
- 它们和 ODDR、DAC 时钟、DAC 格式有关；
- 新手阶段直接改这些信号，容易破坏硬件时序；
- 官方已经写好了 saturation、格式转换和 ODDR，应该复用。

大白话：我们只把自己的 error 信号交给官方 DAC 管道入口，不去拆官方 DAC 管道本身。

## 3. 如何回退

### 3.1 方式 1：把 USE_LASER_LOCK_CORE 改为 0

最简单回退方式：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b0;
```

这样 DAC A/B 回到官方路径：

```systemverilog
dac_a_sum = asg_dat[0] + pid_dat[0];
dac_b_sum = asg_dat[1] + pid_dat[1];
```

### 3.2 方式 2：恢复 red_pitaya_top.sv 备份

应用 patch 前，必须先备份：

```text
rtl\red_pitaya_top.sv
```

例如备份为：

```text
rtl\red_pitaya_top.sv.before_v1ab
```

如果出问题，就用备份恢复。

### 3.3 方式 3：反向应用 patch

如果使用命令行 patch 工具，可以反向应用：

```text
git apply -R redpitaya_laser_lock_project\patches\PATCH_v1ab_passthrough_debug.diff
```

注意：只有在 patch 是通过 `git apply` 应用且文件没有被额外手改时，反向应用最可靠。

## 4. Vivado 里还需要添加哪些源文件

应用 patch 后，还必须把自定义 RTL 加入 Vivado `Design Sources`：

```text
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
```

原因：

- `red_pitaya_top.sv` 里会实例化 `laser_lock_core`；
- `laser_lock_core.sv` 里会实例化 `output_protect`；
- 如果 Vivado 工程没有加入这两个文件，综合时会报 `module not found`。

## 5. OUTPUT_MODE 如何切换

在 patch 中：

```systemverilog
localparam int LASER_LOCK_OUTPUT_MODE = 0;
```

含义：

| 值 | 测试目标 |
|---:|---|
| 0 | 测试 `IN1 -> OUT1` |
| 1 | 测试 `IN2 -> OUT1` |

修改 `LASER_LOCK_OUTPUT_MODE` 后，需要重新：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

原因：`OUTPUT_MODE` 是编译时参数，不是运行时按钮。

## 6. 应用 patch 前检查清单

应用 patch 前必须确认：

| 检查项 | 是否完成 |
|---|---|
| 已备份 `rtl\red_pitaya_top.sv` | 待确认 |
| `v1ab` testbench 已通过 | 已通过 |
| GPT 已审查 patch | 待确认 |
| 用户明确允许应用 patch | 待确认 |
| `OUT1` 只接示波器 | 必须确认 |
| 不接 `D2-125` | 必须确认 |
| 不接激光器反馈 | 必须确认 |
| `IN2` REF 已衰减到安全范围 | 必须确认 |
| 不把 6.32 Vpp REF 直接接入 `IN2` | 必须确认 |
| 已准备回退方式 | 必须确认 |

## 7. patch 禁止修改的内容

本 patch 不应该修改：

```text
ODDR
PLL
BUFG
ADC 输入格式转换
PS/AXI/DDR
XDC
dac_dat_o/dac_wrt_o/dac_sel_o/dac_clk_o/dac_rst_o 输出层
```

审查 patch 时，如果发现这些区域被改动，应停止应用。

## 8. 下一步建议

下一步不是直接应用 patch。

推荐顺序：

1. 把 `PATCH_v1ab_passthrough_debug.diff` 和本文件发给 GPT 审查；
2. 用户确认是否允许应用 patch；
3. 应用前备份 `rtl\red_pitaya_top.sv`；
4. 应用 patch；
5. 在 Vivado 中添加 `laser_lock_core.sv` 和 `output_protect.sv`；
6. 再运行 `Run Synthesis`、`Run Implementation`、`Generate Bitstream`；
7. 上板时只接示波器，按 `BOARD_TEST_v1ab_passthrough_debug.md` 测试。
