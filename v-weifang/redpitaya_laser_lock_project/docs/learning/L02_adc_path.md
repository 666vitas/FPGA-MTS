# L02_adc_path：ADC 输入路径学习
L02 学习结论：

以后我的 laser_lock_core 输入候选为：
pd_i  = adc_dat[0]
ref_i = adc_dat[1]

原因：
adc_dat[0] 和 adc_dat[1] 已经是官方 top 内部转换后的 signed 14 bit ADC 数据，
并且当前已经送给 scope 和 PID 使用。

注意：
adc_dat[0]/adc_dat[1] 是否物理对应 IN1/IN2 还需要后续实测确认。
digital_loop 必须注意，若开启 digital_loop，adc_dat 可能不是外部 ADC 输入。

## 0. 本文件作用

本文件只做 L02：学习官方 `rtl\red_pitaya_top.sv` 中 ADC 输入数据从外部端口进入 FPGA 内部的路径。

本章重点追踪：

```text
adc_dat_i -> adc_dat_raw -> adc_dat
```

并判断：

```text
adc_dat[0] 是否可以作为 future laser_lock_core 的 pd_i 候选
adc_dat[1] 是否可以作为 future laser_lock_core 的 ref_i 候选
```

本章不分析 DAC 输出路径，不写 Verilog，不实现 `laser_lock_core`。

## 1. 阅读对象

本次只读官方文件：

```text
rtl\red_pitaya_top.sv
```

只读，不修改。

## 2. 实验定义

本项目的当前实验目标是：

```text
PD signal
REF signal
  -> Red Pitaya FPGA
  -> error signal
```

未来候选输入定义：

```text
PD signal  -> Red Pitaya IN1 -> future pd_i
REF signal -> Red Pitaya IN2 -> future ref_i
```

L02 只学习“ADC 数据在 FPGA 里叫什么、怎么变成内部数据、送到哪里”。真正的物理 IN1/IN2 对应关系还需要后续板级资料或实验确认。

## 3. 当前原则

| 原则 | 说明 |
|---|---|
| 只做 L02 | 只学习 ADC 输入路径 |
| 官方工程只读 | 不修改 `rtl\red_pitaya_top.sv` |
| 不写 Verilog | 不生成任何自定义模块 |
| 不开始 L03 | 不分析 DAC 输出路径 |
| 不假装确定 | 物理通道对应写入“不确定，需要人工确认” |
| 面向新手 | 每个重要信号说明位宽、signed/unsigned、来源、去向、项目作用 |

## 4. 大白话解释

ADC 的作用是把外部模拟电压变成 FPGA 里的数字数值。

在 `red_pitaya_top.sv` 里，ADC 数据大概走这条路：

```text
外部 ADC 芯片/板级接口
  -> adc_dat_i
  -> adc_dat_raw
  -> adc_dat
  -> scope / PID / future laser_lock_core candidate
```

可以这样理解：

- `adc_dat_i`：刚从外部 ADC 接进 top 的“原始数字线”；
- `adc_dat_raw`：从 16 bit 原始数据里取出来的高 14 bit；
- `adc_dat`：转换成 FPGA 内部常用 signed 14 bit 格式后的 ADC 数据；
- `adc_dat[0]`、`adc_dat[1]`：当前官方模块已经拿去给 scope 和 PID 使用的两路 ADC 数据。

对你的 MTS/激光稳频项目来说，我们真正关心的是：以后自定义 `laser_lock_core` 能不能读 `adc_dat[0]` 当 PD，读 `adc_dat[1]` 当 REF。答案是：从 top 代码结构看，它们是很合理的候选；但它们是否百分百对应前面板 IN1/IN2，还需要板级资料或示波器实验确认。

## 5. 新手必须明白

### 5.1 `adc_dat_i` 是外部输入，不是内部最终可用数据

`adc_dat_i` 是 top 模块的 input 端口。它来自 Red Pitaya 板上的 ADC 相关硬件连接。

它的声明是：

```systemverilog
input logic [MNA-1:0] [16-1:0] adc_dat_i
```

默认 `MNA = 2`，所以它可以理解成：

```text
adc_dat_i[0][15:0]
adc_dat_i[1][15:0]
```

也就是两路 ADC，每路 16 bit。

### 5.2 `adc_dat_raw` 是从 `adc_dat_i` 取高 14 bit

top 里把每路 `adc_dat_i` 的 `[15:2]` 取出来，变成 14 bit 的 `adc_dat_raw`：

```text
adc_dat_raw[0] = adc_dat_i[0][15:2]
adc_dat_raw[1] = adc_dat_i[1][15:2]
```

新手可以先这样记：官方 top 丢掉最低 2 bit，只保留高 14 bit。

### 5.3 `adc_dat` 是内部 signed 14 bit 数据

`adc_dat` 的类型来自：

```systemverilog
localparam type SBA_T = logic signed [14-1:0];
SBA_T [MNA-1:0] adc_dat;
```

所以 `adc_dat[0]`、`adc_dat[1]` 是 signed 14 bit。

### 5.4 `adc_dat` 在 `adc_clk` 时钟上更新

`adc_dat` 在这个 always 块里更新：

```systemverilog
always @(posedge adc_clk) begin
  adc_dat[0] <= ...
  adc_dat[1] <= ...
end
```

所以 `adc_dat` 属于 `adc_clk` 时钟域。

### 5.5 `digital_loop` 会改变 `adc_dat` 的来源

正常情况下，`adc_dat` 来自外部 ADC。

但如果 `digital_loop = 1`，代码会让：

```text
adc_dat[0] <= dac_a
adc_dat[1] <= dac_b
```

也就是说，开启 `digital_loop` 时，`adc_dat` 不再代表外部输入，而是内部 DAC 回环数据。

对实验来说，这一点很重要：以后验证 PD/REF 输入时，要确认 `digital_loop` 没有让 ADC 数据变成内部回环。

## 6. 分层讲解

### 6.1 第一层：ADC 顶层端口

top 的 ADC 端口包括：

```text
adc_dat_i
adc_clk_i
adc_clk_o
adc_cdcs_o
```

本章重点是 `adc_dat_i`。时钟只讲到 `adc_clk` 和 `adc_rstn` 的来源，不深入 PLL 内部。

### 6.2 第二层：`adc_dat_i` 的维度

代码里有：

```systemverilog
parameter MNA = 2
input logic [MNA-1:0] [16-1:0] adc_dat_i
```

默认 `MNA=2`，所以：

| 信号 | 含义 |
|---|---|
| `adc_dat_i[0]` | 第 0 路 ADC 原始输入，16 bit |
| `adc_dat_i[1]` | 第 1 路 ADC 原始输入，16 bit |

注意：这里的代码能确认“有两路 ADC 数字数据”。但 `adc_dat_i[0]` 是否就是前面板 IN1，仍需要板级资料或实验确认。

### 6.3 第三层：`adc_dat_raw`

代码里有：

```systemverilog
logic [2-1:0] [14-1:0] adc_dat_raw;
assign adc_dat_raw[0] = adc_dat_i[0][16-1:2];
assign adc_dat_raw[1] = adc_dat_i[1][16-1:2];
```

硬件上等价于什么？

这不是复杂运算，只是“接线选位”。FPGA 综合后，相当于把 `adc_dat_i[x]` 的高 14 根线接到 `adc_dat_raw[x]`，最低 2 bit 不用。

### 6.4 第四层：`adc_dat`

代码里有：

```systemverilog
adc_dat[0] <= digital_loop ? dac_a : {adc_dat_raw[0][13], ~adc_dat_raw[0][12:0]};
adc_dat[1] <= digital_loop ? dac_b : {adc_dat_raw[1][13], ~adc_dat_raw[1][12:0]};
```

分开看：

如果 `digital_loop = 0`：

```text
adc_dat[0] = {adc_dat_raw[0][13], ~adc_dat_raw[0][12:0]}
adc_dat[1] = {adc_dat_raw[1][13], ~adc_dat_raw[1][12:0]}
```

也就是最高位保留，低 13 位取反。官方注释写的是：

```text
transform into 2's complement (negative slope)
```

大白话：官方 ADC 原始格式不是直接给算法用的 signed 数字，top 在这里把它转换成内部更常用的 two's complement signed 格式。

硬件上等价于什么？

- 一个 14 bit 寄存器；
- 若干根取反线；
- 一个由 `digital_loop` 控制的 2 选 1 mux；
- 每个 `adc_clk` 上升沿更新一次。

### 6.5 第五层：`adc_dat` 送到哪里

当前 top 里可以看到：

```text
adc_dat[0] -> red_pitaya_scope.adc_a_i  // CH 1
adc_dat[1] -> red_pitaya_scope.adc_b_i  // CH 2

adc_dat[0] -> red_pitaya_pid.dat_a_i    // in 1
adc_dat[1] -> red_pitaya_pid.dat_b_i    // in 2
```

这说明 `adc_dat[0]` 和 `adc_dat[1]` 已经是官方 scope/PID 使用的内部 ADC 数据。

对未来 `laser_lock_core` 来说，这很有价值：如果要做 PD/REF 数字处理，读 `adc_dat[0]`、`adc_dat[1]` 是合理的候选方案。

## 7. ADC 关键端口/信号表

| 信号名 | 位宽/类型 | signed/unsigned | 来源 | 去向 | 对 MTS/稳频项目的作用 |
|---|---|---|---|---|---|
| `MNA` | parameter，默认 `2` | 不适用 | top 参数 | 决定 ADC 通道数组数量 | 表明默认有 2 路 acquisition 数据 |
| `adc_dat_i` | `[MNA-1:0][16-1:0]` | 未声明 signed，按 unsigned logic 理解 | top 外部 ADC 数据端口 | 生成 `adc_dat_raw` | 原始 ADC 数据入口 |
| `adc_dat_i[0]` | 16 bit | 未声明 signed | 第 0 路 ADC 输入 | `adc_dat_raw[0]` | future PD 输入候选的原始来源 |
| `adc_dat_i[1]` | 16 bit | 未声明 signed | 第 1 路 ADC 输入 | `adc_dat_raw[1]` | future REF 输入候选的原始来源 |
| `adc_dat_raw` | `[2-1:0][14-1:0]` | 未声明 signed | `adc_dat_i[x][15:2]` | 生成 `adc_dat` | 取高 14 bit 后的 ADC 数据 |
| `SBA_T` | `logic signed [14-1:0]` | signed | localparam type | 用于 `adc_dat`、`pid_dat` | 表明内部 acquire 数据是 signed 14 bit |
| `adc_dat` | `SBA_T [MNA-1:0]` | signed 14 bit | `adc_dat_raw` 转换后，或 `digital_loop` 回环 | scope、PID、future core candidate | future `laser_lock_core` 输入候选 |
| `adc_dat[0]` | signed 14 bit | signed | `adc_dat_raw[0]` 转换后 | scope CH1、PID in1 | future `pd_i` 候选 |
| `adc_dat[1]` | signed 14 bit | signed | `adc_dat_raw[1]` 转换后 | scope CH2、PID in2 | future `ref_i` 候选 |
| `adc_clk_i` | `[2-1:0]` | 不适用 | 外部 ADC differential clock | `IBUFDS` | ADC 时钟源头之一 |
| `adc_clk` | 1 bit clock | 不适用 | `red_pitaya_pll` 的 `clk_adc` 经 `BUFG` | ADC 数据寄存、scope、PID 等 | future `laser_lock_core.clk_i` 候选 |
| `adc_rstn` | 1 bit reset | 不适用，active low | `frstn[0] & pll_locked` 在 `adc_clk` 下寄存 | ADC 时钟域模块 | future `laser_lock_core.rstn_i` 候选 |
| `digital_loop` | 1 bit | 不适用 | `red_pitaya_hk` 输出 | ADC 数据 mux 控制 | 开启时 `adc_dat` 不代表外部 ADC，需要注意 |

## 8. 证据

| 结论 | 证据位置 | 代码/说明 |
|---|---|---|
| 默认 acquisition 模块数量是 2 | `rtl\red_pitaya_top.sv` 第 56 行附近 | `parameter MNA = 2` |
| `adc_dat_i` 是 ADC 数据输入端口 | 第 95 行附近 | `input logic [MNA-1:0] [16-1:0] adc_dat_i` |
| `adc_clk_i` 是 ADC clock 输入 | 第 96 行附近 | `input logic [2-1:0] adc_clk_i` |
| `SBA_T` 是 signed 14 bit | 第 183 行附近 | `localparam type SBA_T = logic signed [14-1:0]` |
| `adc_dat` 使用 `SBA_T` | 第 186 行附近 | `SBA_T [MNA-1:0] adc_dat` |
| `adc_clk`、`adc_rstn` 是 ADC clock/reset 信号 | 第 170-172 行附近 | `logic adc_clk; logic adc_rstn;` |
| `adc_clk_i` 先进入 `IBUFDS` | 第 219 行附近 | `IBUFDS i_clk ... .O(adc_clk_in)` |
| PLL 输出 `pll_adc_clk` | 第 221-234 行附近 | `red_pitaya_pll pll` 的 `.clk_adc(pll_adc_clk)` |
| `adc_clk` 来自 `pll_adc_clk` 经 `BUFG` | 第 236 行附近 | `BUFG bufg_adc_clk (.O(adc_clk), .I(pll_adc_clk))` |
| `adc_rstn` 由 `frstn[0] & pll_locked` 生成 | 第 256-258 行附近 | `adc_rstn <= frstn[0] & pll_locked` |
| ADC IO 区域开始 | 第 384 行附近 | `// ADC IO` |
| `adc_dat_raw` 是 2 路 14 bit | 第 392 行附近 | `logic [2-1:0] [14-1:0] adc_dat_raw` |
| `adc_dat_raw[0]` 来自 `adc_dat_i[0][15:2]` | 第 397 行附近 | `assign adc_dat_raw[0] = adc_dat_i[0][16-1:2]` |
| `adc_dat_raw[1]` 来自 `adc_dat_i[1][15:2]` | 第 398 行附近 | `assign adc_dat_raw[1] = adc_dat_i[1][16-1:2]` |
| `adc_dat` 在 `adc_clk` 上升沿更新 | 第 401 行附近 | `always @(posedge adc_clk)` |
| `adc_dat[0]` 转换表达式 | 第 402 行附近 | `adc_dat[0] <= digital_loop ? dac_a : ...` |
| `adc_dat[1]` 转换表达式 | 第 403 行附近 | `adc_dat[1] <= digital_loop ? dac_b : ...` |
| `digital_loop` 来自 HK | 第 445-452 行附近 | `red_pitaya_hk` 输出 `.digital_loop(digital_loop)` |
| `adc_dat[0]` 送 scope CH1 | 第 517-520 行附近 | `.adc_a_i(adc_dat[0]) // CH 1` |
| `adc_dat[1]` 送 scope CH2 | 第 517-520 行附近 | `.adc_b_i(adc_dat[1]) // CH 2` |
| `adc_dat[0]` 送 PID in1 | 第 577-582 行附近 | `.dat_a_i(adc_dat[0]) // in 1` |
| `adc_dat[1]` 送 PID in2 | 第 577-582 行附近 | `.dat_b_i(adc_dat[1]) // in 2` |

## 9. 不要碰/不要改

L02 阶段不要修改任何官方代码。

特别不要改：

```text
rtl\red_pitaya_top.sv
adc_dat_i
adc_dat_raw
adc_dat
adc_clk
adc_rstn
digital_loop
red_pitaya_hk
red_pitaya_scope
red_pitaya_pid
```

不要做：

- 不修改 ADC 输入逻辑；
- 不修改 `adc_dat` 相关代码；
- 不写自定义模块；
- 不实现 `laser_lock_core`；
- 不开始 DAC 路径分析；
- 不修改 PLL/reset；
- 不修改 official scope/PID/HK。

## 10. 已确认

- `adc_dat_i` 是 top 的 ADC 数据输入端口。
- 默认 `MNA=2`，所以有 `adc_dat_i[0]` 和 `adc_dat_i[1]` 两路。
- 每路 `adc_dat_i[x]` 是 16 bit。
- `adc_dat_raw[x]` 来自 `adc_dat_i[x][15:2]`，是 14 bit。
- `adc_dat` 是 `SBA_T` 类型，即 signed 14 bit。
- `adc_dat` 在 `adc_clk` 上升沿寄存更新。
- 正常非 `digital_loop` 情况下，`adc_dat[x]` 来自 `adc_dat_raw[x]` 的格式转换。
- `adc_dat[0]` 当前送到 scope CH1 和 PID in1。
- `adc_dat[1]` 当前送到 scope CH2 和 PID in2。
- `adc_dat[0]` 可以作为 future `laser_lock_core.pd_i` 的候选。
- `adc_dat[1]` 可以作为 future `laser_lock_core.ref_i` 的候选。
- `adc_rstn` 是 active low，并由 `frstn[0] & pll_locked` 在 `adc_clk` 下生成。

## 11. 不确定，需要人工确认

| 不确定项 | 为什么不确定 | 后续如何确认 |
|---|---|---|
| `adc_dat[0]` 是否物理对应 Red Pitaya IN1 | top 里可见 CH1 注释，但物理前面板映射需要板级资料确认 | 查官方硬件资料、约束、或用信号发生器上板测试 |
| `adc_dat[1]` 是否物理对应 Red Pitaya IN2 | top 里可见 CH2 注释，但物理前面板映射需要板级资料确认 | 查官方硬件资料、约束、或用信号发生器上板测试 |
| `digital_loop` 默认运行时是否为 0 | top 里只能看到它来自 `red_pitaya_hk`，默认值和软件配置需确认 | 查 HK/软件配置，或实验观察 |
| ADC 输入电压范围和实际码值比例 | top 只处理数字数据，不说明模拟前端量程 | 查 Red Pitaya 125-14 硬件资料 |
| ADC 格式转换的极性与示波器观察是否一致 | top 注释说明 negative slope，但实验看到的正负方向还需验证 | 用已知正弦波输入观察 scope/OUT |

## 12. 我现在只需要记住什么

现在只需要记住：

1. `adc_dat_i` 是外部 ADC 进 top 的原始 16 bit 数据。
2. `adc_dat_raw` 是从 `adc_dat_i` 取高 14 bit。
3. `adc_dat` 是转换后的 signed 14 bit 内部 ADC 数据。
4. `adc_dat[0]`、`adc_dat[1]` 已经送给官方 scope 和 PID。
5. 对你的项目来说，`adc_dat[0]` 是 future `pd_i` 候选，`adc_dat[1]` 是 future `ref_i` 候选。
6. 但 IN1/IN2 的物理对应关系还不能只靠本章完全确认。

## 13. 下一步建议

下一步建议做 L03：

```text
learning\L03_dac_path.md
reports\REPORT_L03_dac_path.md
```

但只有在用户明确要求时才开始。

现在不要继续 L03，不要写 Verilog，不要修改官方工程。

## 14. 给 GPT 审查的问题

1. `adc_dat[0]` 作为 future `pd_i` 候选是否合理？
2. `adc_dat[1]` 作为 future `ref_i` 候选是否合理？
3. 是否应该在后续 integration plan 中明确要求 `digital_loop = 0` 才进行真实 ADC 输入实验？
4. L02 是否需要补充官方硬件资料来确认 IN1/IN2 与 `adc_dat[0]`/`adc_dat[1]` 的对应关系？
