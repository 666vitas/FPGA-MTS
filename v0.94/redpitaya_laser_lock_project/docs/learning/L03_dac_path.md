# L03_dac_path：DAC 输出路径学习

## 0. 本文件作用

本文件只做 L03：学习官方 `rtl\red_pitaya_top.sv` 中 DAC 输出路径。

本章重点追踪：

```text
asg_dat / pid_dat
  -> dac_a_sum / dac_b_sum
  -> dac_a / dac_b
  -> dac_dat_a / dac_dat_b
  -> ODDR oddr_dac_*
  -> dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

本章不写 Verilog，不修改官方工程，不实现 `laser_lock_core`，也不开始 L04 clock/reset 学习。

## 1. 阅读对象

本次只阅读官方文件：

```text
rtl\red_pitaya_top.sv
```

只读，不修改。

## 2. 实验定义

本项目未来希望让 Red Pitaya FPGA 输出 MTS/激光稳频需要的 error signal：

```text
PD signal
REF signal
  -> future laser_lock_core
  -> error signal
  -> Red Pitaya OUT1
```

未来候选关系是：

```text
future laser_lock_core.error_o   -> DAC A / OUT1 候选
future laser_lock_core.control_o -> DAC B / OUT2 候选
```

但是 L03 当前只学习官方 DAC 输出链路，不接入 `laser_lock_core`，不改 `red_pitaya_top.sv`。

## 3. 当前原则

| 原则 | 说明 |
|---|---|
| 只做 L03 | 只学习 DAC 输出路径 |
| 官方工程只读 | 不修改 `rtl\red_pitaya_top.sv` |
| 不写 Verilog | 不生成任何 RTL |
| 不实现 `laser_lock_core` | 本章只学习，不开发 |
| 不修改 DAC/ODDR | 不碰官方 DAC 输出时序 |
| 不开始 L04 | clock/reset 只在 DAC 相关处简单提到，不深入分析 |
| 面向新手 | 每个重要信号说明位宽、signed/unsigned、来源、去向和项目作用 |

## 4. 大白话解释

可以把 DAC 输出路径想象成“把 FPGA 里的数字波形送到模拟输出口”的流水线。

官方现在有两个主要数字波形来源：

- `asg_dat`：官方 ASG 任意波形发生器的输出；
- `pid_dat`：官方 PID 控制器的输出。

它们先相加：

```text
ASG 输出 + PID 输出 -> dac_a_sum / dac_b_sum
```

然后官方代码会做限幅，也就是 saturation。限幅的作用像“保险栏”：如果相加结果超过 14 bit DAC 能表达的范围，就把它压到最大值或最小值，避免数字溢出后反而变成错误波形。

接着官方代码把 signed 14 bit 数据转换成外部 DAC 需要的格式：

```text
dac_a / dac_b -> dac_dat_a / dac_dat_b
```

最后用 `ODDR` 把数据、时钟、写信号、通道选择信号按 DAC 芯片需要的高速时序送到 FPGA 引脚：

```text
dac_dat_a / dac_dat_b
  -> ODDR
  -> dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

对 MTS/稳频项目来说，最重要的直觉是：

```text
future laser_lock_core 的输出，未来应该接在官方 saturation 前面，
而不是直接改 dac_dat_o 或 ODDR。
```

这样可以保留官方已经写好的限幅、格式转换和 DAC 时序输出。

## 5. 新手必须明白

### 5.1 `asg_dat` 是官方 ASG 的输出

`asg_dat` 的声明是：

```systemverilog
SBG_T [2-1:0] asg_dat;
```

`SBG_T` 是：

```systemverilog
logic signed [14-1:0]
```

所以 `asg_dat[0]` 和 `asg_dat[1]` 都是 signed 14 bit。

大白话：`asg_dat` 是官方“波形发生器”吐出来的两路数字波形。`asg_dat[0]` 对应 CH 1，`asg_dat[1]` 对应 CH 2。

### 5.2 `pid_dat` 是官方 PID 的输出

`pid_dat` 的声明是：

```systemverilog
SBA_T [2-1:0] pid_dat;
```

`SBA_T` 也是：

```systemverilog
logic signed [14-1:0]
```

所以 `pid_dat[0]` 和 `pid_dat[1]` 也是 signed 14 bit。

大白话：`pid_dat` 是官方 PID 控制器算出来的两路输出。当前项目还不做 FPGA PID，但官方路径里它已经存在。

### 5.3 `dac_a_sum` 和 `dac_b_sum` 是 15 bit signed 求和结果

官方代码是：

```systemverilog
assign dac_a_sum = asg_dat[0] + pid_dat[0];
assign dac_b_sum = asg_dat[1] + pid_dat[1];
```

`dac_a_sum`、`dac_b_sum` 是 signed 15 bit。

为什么是 15 bit？

因为两个 signed 14 bit 数相加，结果可能需要多 1 bit 才能安全表示。硬件上等价于两个加法器：

```text
14 bit signed + 14 bit signed -> 15 bit signed
```

### 5.4 saturation 是限幅保护

官方代码是：

```systemverilog
assign dac_a = (^dac_a_sum[15-1:15-2]) ? {dac_a_sum[15-1], {13{~dac_a_sum[15-1]}}} : dac_a_sum[14-1:0];
assign dac_b = (^dac_b_sum[15-1:15-2]) ? {dac_b_sum[15-1], {13{~dac_b_sum[15-1]}}} : dac_b_sum[14-1:0];
```

新手可以先这样理解：

- `dac_a_sum` / `dac_b_sum` 是 15 bit；
- 真正 DAC 数据是 14 bit；
- 如果 15 bit 结果没有溢出，就取低 14 bit；
- 如果溢出，就夹到 signed 14 bit 最大值或最小值。

`^dac_a_sum[15-1:15-2]` 是对最高两位做异或。对于 signed 数，如果最高两位不一致，说明从 15 bit 缩回 14 bit 会出问题，于是触发限幅。

硬件上等价于：

```text
溢出检测电路 + 2 选 1 mux + 最大/最小值夹紧电路
```

### 5.5 `dac_dat_a` / `dac_dat_b` 是 DAC 芯片需要的输出格式

官方代码是：

```systemverilog
dac_dat_a <= {dac_a[14-1], ~dac_a[14-2:0]};
dac_dat_b <= {dac_b[14-1], ~dac_b[14-2:0]};
```

注释写的是：

```text
output registers + signed to unsigned (also to negative slope)
```

大白话解释：

- FPGA 内部的 `dac_a` / `dac_b` 是 signed 14 bit；
- 外部 DAC 芯片需要的不是这个直接格式；
- 官方代码保留最高位，然后把低 13 位取反；
- 这一步同时完成格式转换和 negative-slope 极性处理。

硬件上等价于：

```text
14 bit 寄存器 + 13 根取反线
```

### 5.6 `ODDR oddr_dac_*` 是最终板级 DAC 时序输出

`ODDR` 是 FPGA 里的 DDR 输出单元。它可以在一个时钟周期的两个边沿输出不同数据。

在这里它负责把 DAC 需要的信号按正确时序送到外部引脚：

```text
ODDR oddr_dac_clk -> dac_clk_o
ODDR oddr_dac_wrt -> dac_wrt_o
ODDR oddr_dac_sel -> dac_sel_o
ODDR oddr_dac_rst -> dac_rst_o
ODDR oddr_dac_dat -> dac_dat_o
```

这部分是板级高速接口，不是 MTS 算法。新手阶段千万不要乱改。

## 6. 分层讲解

### 6.1 第一层：DAC 顶层输出端口

`red_pitaya_top.sv` 的 DAC 顶层端口包括：

```text
dac_dat_o
dac_wrt_o
dac_sel_o
dac_clk_o
dac_rst_o
```

这些信号是最终出 FPGA、连到外部 DAC 芯片的板级信号。

本项目后续不应该直接驱动这些信号，而应该保留官方 `ODDR` 输出。

### 6.2 第二层：官方输出数据来源

官方当前 DAC 输出主要来自：

```text
red_pitaya_asg -> asg_dat[0] / asg_dat[1]
red_pitaya_pid -> pid_dat[0] / pid_dat[1]
```

其中：

```text
asg_dat[0] -> DAC A 求和路径
asg_dat[1] -> DAC B 求和路径
pid_dat[0] -> DAC A 求和路径
pid_dat[1] -> DAC B 求和路径
```

### 6.3 第三层：求和

官方求和代码：

```systemverilog
assign dac_a_sum = asg_dat[0] + pid_dat[0];
assign dac_b_sum = asg_dat[1] + pid_dat[1];
```

大白话：

```text
DAC A 输出 = 官方 ASG 通道 1 + 官方 PID 输出 1
DAC B 输出 = 官方 ASG 通道 2 + 官方 PID 输出 2
```

这里的结果先放进 15 bit signed 的 `dac_a_sum` / `dac_b_sum`，不是直接送 DAC。

### 6.4 第四层：saturation 限幅

`dac_a_sum` / `dac_b_sum` 经过 saturation 变成：

```text
dac_a
dac_b
```

`dac_a` / `dac_b` 是 14 bit。它们已经被限制在 DAC 可用的 signed 14 bit 范围内。

这一步对未来项目很重要：如果 `laser_lock_core.error_o` 未来接入 DAC A，也应该让它继续经过官方 saturation。

### 6.5 第五层：signed-to-unsigned / negative-slope conversion

`dac_a` / `dac_b` 经过格式转换后变成：

```text
dac_dat_a
dac_dat_b
```

这一层发生在：

```systemverilog
always @(posedge dac_clk_1x)
```

所以 `dac_dat_a` / `dac_dat_b` 是在 `dac_clk_1x` 时钟下寄存输出的。

本章不深入 clock/reset，只记住：DAC 输出路径有自己的 DAC 时钟，后续 L04 会专门学习。

### 6.6 第六层：ODDR 输出到外部 DAC

最后由 `ODDR` 输出：

```text
dac_dat_b / dac_dat_a -> oddr_dac_dat -> dac_dat_o
控制时序              -> oddr_dac_*   -> dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

`oddr_dac_dat` 的 `D1` 接 `dac_dat_b`，`D2` 接 `dac_dat_a`。这说明官方用 DDR 方式在一个物理数据总线上交替送两路 DAC 数据。

### 6.7 future `laser_lock_core` 的候选接入位置

从 L03 证据看，未来如果要接入：

```text
future laser_lock_core.error_o
future laser_lock_core.control_o
```

合理候选位置不是 `dac_dat_o`，而是在 saturation 前的求和路径附近。

未来 integration plan 可以考虑：

```text
USE_LASER_LOCK_CORE = 0:
  dac_a_sum = asg_dat[0] + pid_dat[0]
  dac_b_sum = asg_dat[1] + pid_dat[1]

USE_LASER_LOCK_CORE = 1:
  dac_a_sum = sign-extend(future laser_lock_core.error_o)
  dac_b_sum = sign-extend(future laser_lock_core.control_o)
```

注意：这只是 L03 学习后得到的候选方案，不是本章修改内容。真正接入必须等后续 integration plan 和 GPT/用户审查。

## 7. DAC 关键端口/信号表

| 信号名 | 位宽/类型 | signed/unsigned | 来源 | 去向 | 对 MTS/稳频项目的作用 |
|---|---|---|---|---|---|
| `SBG_T` | `logic signed [14-1:0]` | signed | localparam type | `asg_dat` | 说明官方 generate 数据是 signed 14 bit |
| `SBA_T` | `logic signed [14-1:0]` | signed | localparam type | `pid_dat` | 说明官方 PID 输出也是 signed 14 bit |
| `asg_dat` | `SBG_T [2-1:0]` | signed 14 bit each | `red_pitaya_asg` | `dac_a_sum` / `dac_b_sum` | 官方 ASG 输出，未来需要保留回退路径 |
| `asg_dat[0]` | signed 14 bit | signed | ASG `dac_a_o` | `dac_a_sum` | 官方 DAC A / CH 1 数据来源之一 |
| `asg_dat[1]` | signed 14 bit | signed | ASG `dac_b_o` | `dac_b_sum` | 官方 DAC B / CH 2 数据来源之一 |
| `pid_dat` | `SBA_T [2-1:0]` | signed 14 bit each | `red_pitaya_pid` | `dac_a_sum` / `dac_b_sum` | 官方 PID 输出，当前项目暂不使用但官方路径存在 |
| `pid_dat[0]` | signed 14 bit | signed | PID `dat_a_o` | `dac_a_sum` | 官方 DAC A 数据来源之一 |
| `pid_dat[1]` | signed 14 bit | signed | PID `dat_b_o` | `dac_b_sum` | 官方 DAC B 数据来源之一 |
| `dac_a_sum` | `logic signed [15-1:0]` | signed | `asg_dat[0] + pid_dat[0]` | saturation 生成 `dac_a` | 未来 `error_o` 候选接入位置附近 |
| `dac_b_sum` | `logic signed [15-1:0]` | signed | `asg_dat[1] + pid_dat[1]` | saturation 生成 `dac_b` | 未来 `control_o` 候选接入位置附近 |
| `dac_a` | `[14-1:0]` | 声明未写 signed，但数据按 signed 含义使用 | `dac_a_sum` 限幅后 | `dac_dat_a` | DAC A 限幅后的内部数据 |
| `dac_b` | `[14-1:0]` | 声明未写 signed，但数据按 signed 含义使用 | `dac_b_sum` 限幅后 | `dac_dat_b` | DAC B 限幅后的内部数据 |
| `dac_dat_a` | `[14-1:0]` | DAC 输出格式 | `dac_a` 格式转换后 | `oddr_dac_dat.D2` | 送到 DAC DDR 输出的数据 A |
| `dac_dat_b` | `[14-1:0]` | DAC 输出格式 | `dac_b` 格式转换后 | `oddr_dac_dat.D1` | 送到 DAC DDR 输出的数据 B |
| `dac_dat_o` | `[14-1:0]` output | DAC 物理输出格式 | `ODDR oddr_dac_dat` | 外部 DAC 芯片 | 最终 DAC 数据引脚，不能乱改 |
| `dac_wrt_o` | 1 bit output | 不适用 | `ODDR oddr_dac_wrt` | 外部 DAC 芯片 | DAC 写时序，不能乱改 |
| `dac_sel_o` | 1 bit output | 不适用 | `ODDR oddr_dac_sel` | 外部 DAC 芯片 | DAC 通道选择，不能乱改 |
| `dac_clk_o` | 1 bit output | 不适用 | `ODDR oddr_dac_clk` | 外部 DAC 芯片 | DAC 时钟，不能乱改 |
| `dac_rst_o` | 1 bit output | 不适用 | `ODDR oddr_dac_rst` | 外部 DAC 芯片 | DAC reset，不能乱改 |
| `dac_clk_1x` | 1 bit clock | 不适用 | PLL/BUFG | DAC 寄存和部分 ODDR | DAC 路径时钟，L04 再深入 |
| `dac_clk_2x` | 1 bit clock | 不适用 | PLL/BUFG | `oddr_dac_wrt` | DAC 写时序用，L04 再深入 |
| `dac_clk_2p` | 1 bit clock | 不适用 | PLL/BUFG | `oddr_dac_clk` | DAC clock 输出用，L04 再深入 |
| `future laser_lock_core.error_o` | 预计 signed 14 bit | signed | future custom core | future DAC A 候选 | 未来 error signal 到 OUT1 的候选输出 |
| `future laser_lock_core.control_o` | 预计 signed 14 bit | signed | future custom core | future DAC B 候选 | 未来 control signal 到 OUT2 的候选输出 |

## 8. 证据

| 结论 | 证据位置 | 代码/说明 |
|---|---|---|
| DAC 顶层输出端口存在 | `rtl\red_pitaya_top.sv` 第 99-104 行 | `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` |
| `SBG_T` 是 signed 14 bit | 第 184 行 | `localparam type SBG_T = logic signed [14-1:0]` |
| `SBA_T` 是 signed 14 bit | 第 183 行 | `localparam type SBA_T = logic signed [14-1:0]` |
| DAC 内部信号声明 | 第 188-196 行 | `dac_dat_a`、`dac_dat_b`、`dac_a`、`dac_b`、`dac_a_sum`、`dac_b_sum` |
| `asg_dat` 声明 | 第 198-199 行 | `SBG_T [2-1:0] asg_dat` |
| `pid_dat` 声明 | 第 201-202 行 | `SBA_T [2-1:0] pid_dat` |
| DAC 时钟来自 PLL/BUFG | 第 226-239 行 | `clk_dac_1x`、`clk_dac_2x`、`clk_dac_2p` 到 `dac_clk_1x/2x/2p` |
| DAC IO 区域开始 | 第 406-408 行 | `// DAC IO` |
| `dac_a_sum` 来自 ASG/PID 求和 | 第 410-412 行 | `asg_dat[0] + pid_dat[0]` |
| saturation 生成 `dac_a` / `dac_b` | 第 414-416 行 | 溢出检测后限幅 |
| signed-to-unsigned / negative-slope conversion | 第 418-423 行 | `dac_dat_a <= {dac_a[13], ~dac_a[12:0]}` |
| ODDR 输出 DAC 信号 | 第 425-430 行 | `ODDR oddr_dac_*` |
| ASG 输出到 `asg_dat` | 第 554-559 行 | `.dac_a_o(asg_dat[0])`、`.dac_b_o(asg_dat[1])` |
| PID 输出到 `pid_dat` | 第 577-584 行 | `.dat_a_o(pid_dat[0])`、`.dat_b_o(pid_dat[1])` |

## 9. 不要碰/不要改

L03 阶段不要修改任何官方代码。

特别不要碰：

```text
rtl\red_pitaya_top.sv
dac_a_sum
dac_b_sum
dac_a
dac_b
dac_dat_a
dac_dat_b
dac_dat_o
dac_wrt_o
dac_sel_o
dac_clk_o
dac_rst_o
ODDR oddr_dac_*
red_pitaya_asg
red_pitaya_pid
red_pitaya_pll
```

新手特别要记住：`dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` 是外部 DAC 芯片的物理接口。这里不是写算法的地方。一旦乱改，可能不是“波形不对”，而是整个 DAC 时序坏掉。

## 10. 已确认

- `asg_dat` 来自官方 `red_pitaya_asg`。
- `asg_dat[0]` 接 ASG CH 1 输出，`asg_dat[1]` 接 ASG CH 2 输出。
- `pid_dat` 来自官方 `red_pitaya_pid`。
- `pid_dat[0]` 接 PID out 1，`pid_dat[1]` 接 PID out 2。
- `dac_a_sum = asg_dat[0] + pid_dat[0]`。
- `dac_b_sum = asg_dat[1] + pid_dat[1]`。
- `dac_a_sum` 和 `dac_b_sum` 是 signed 15 bit。
- `dac_a` 和 `dac_b` 是 saturation 后的 14 bit 数据。
- `dac_dat_a` 和 `dac_dat_b` 是经过 signed-to-unsigned / negative-slope conversion 后的 DAC 输出格式。
- 最终 `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` 由 `ODDR oddr_dac_*` 驱动。
- future `laser_lock_core.error_o` 的合理候选接入点在 DAC A saturation 前的求和路径附近，而不是直接驱动 `dac_dat_o`。
- future `laser_lock_core.control_o` 的合理候选接入点在 DAC B saturation 前的求和路径附近，而不是直接驱动 `dac_dat_o`。

## 11. 不确定，需要人工确认

| 不确定项 | 为什么不确定 | 后续如何确认 |
|---|---|---|
| DAC A 是否物理对应 Red Pitaya OUT1 | top 注释有 CH 1/CH 2，但物理前面板映射仍建议用板级资料或实验确认 | 查官方硬件资料，或用 ASG 输出测试 OUT1/OUT2 |
| DAC B 是否物理对应 Red Pitaya OUT2 | 同上 | 查官方硬件资料，或用 ASG 输出测试 |
| `dac_dat_a` / `dac_dat_b` 最终模拟输出是否反相 | top 注释写了 negative slope，实际示波器极性需实验确认 | 输入已知正弦/斜坡，观察 OUT1/OUT2 |
| DAC 输出电压范围与码值比例 | top 只处理数字码值，不说明模拟输出幅度 | 查 Red Pitaya STEMlab 125-14 硬件资料 |
| future mux 的精确写法 | L03 只学习，不生成 integration plan | 后续 L07 或 integration plan 中审查 |
| `control_o` 在早期阶段是否固定为 0 | 取决于后续阶段定义 | 阶段设计时确认 |

## 12. 我现在只需要记住什么

现在只需要记住六句话：

1. 官方 DAC 输出不是直接从一个信号出去，而是一条完整流水线。
2. 官方当前路径是 `asg_dat + pid_dat -> dac_a_sum/dac_b_sum`。
3. `dac_a_sum` / `dac_b_sum` 是 15 bit signed，用来容纳求和结果。
4. saturation 把 15 bit 求和结果安全压回 14 bit。
5. `dac_dat_a` / `dac_dat_b` 是给 DAC 芯片用的格式，不等同于内部 signed 数据。
6. `ODDR oddr_dac_*` 是最终 DAC 时序输出，绝对不要乱改。

## 13. 下一步建议

下一步建议做 L04：

```text
learning\L04_clock_reset.md
reports\REPORT_L04_clock_reset.md
```

但只有在用户明确要求时才开始。

现在不要继续 L04，不要写 Verilog，不要修改官方工程。

## 14. 给 GPT 审查的问题

1. 是否同意 future `laser_lock_core.error_o` 的候选接入点应放在 DAC A saturation 前，而不是直接驱动 `dac_dat_o`？
2. 是否同意 future `laser_lock_core.control_o` 的候选接入点应放在 DAC B saturation 前，而不是直接驱动 `dac_dat_o`？
3. L03 对 `signed-to-unsigned / negative-slope conversion` 的解释是否足够适合 FPGA/Verilog 新手？
4. 后续 integration plan 是否应该强制保留官方 saturation、格式转换和 `ODDR oddr_dac_*`？
5. 是否需要在 L03 后补充官方硬件资料，用来确认 DAC A/B 与 OUT1/OUT2 的物理对应关系？
