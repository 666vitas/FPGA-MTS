# L04_clock_reset：clock/reset 路径学习

## 0. 本文件作用

本文件只做 L04：学习官方 `rtl\red_pitaya_top.sv` 中 clock/reset 的基本路径。

本章重点追踪：

```text
adc_clk_i
  -> IBUFDS
  -> adc_clk_in
  -> red_pitaya_pll
  -> pll_adc_clk / pll_dac_clk_1x / pll_dac_clk_2x / pll_dac_clk_2p
  -> BUFG
  -> adc_clk / dac_clk_1x / dac_clk_2x / dac_clk_2p
```

以及 reset：

```text
frstn[0] + pll_locked
  -> adc_rstn
  -> dac_rst
```

本章不写 Verilog，不修改官方工程，不实现 `laser_lock_core`，不开始 L05 scope/ASG/PID 分析。

## 1. 阅读对象

本次只阅读官方文件：

```text
rtl\red_pitaya_top.sv
```

只读，不修改。

## 2. 实验定义

本项目未来要做：

```text
PD signal
REF signal
  -> future laser_lock_core
  -> error signal
```

从 L02 已知，future `laser_lock_core` 的输入候选是：

```text
adc_dat[0] -> future pd_i
adc_dat[1] -> future ref_i
```

从 L03 已知，future `laser_lock_core` 的输出候选最终要走 DAC 路径：

```text
future error_o   -> DAC A / OUT1 候选
future control_o -> DAC B / OUT2 候选
```

所以 L04 要回答一个非常关键的问题：

```text
future laser_lock_core 第一版应该用哪个 clock/reset？
```

本章结论先写在前面：第一版应优先使用：

```text
clk_i  <- adc_clk
rstn_i <- adc_rstn
```

但这只是学习结论，不是本章接线修改。

## 3. 当前原则

| 原则 | 说明 |
|---|---|
| 只做 L04 | 只学习 clock/reset 路径 |
| 官方工程只读 | 不修改 `rtl\red_pitaya_top.sv` |
| 不写 Verilog | 不生成任何 RTL |
| 不实现 `laser_lock_core` | 本章只学习，不开发 |
| 不修改 PLL | 不改 `red_pitaya_pll` 实例和连接 |
| 不修改 BUFG | 不改 clock buffer |
| 不修改 reset 逻辑 | 不改 `adc_rstn`、`dac_rst` 生成 |
| 不开始 L05 | 不展开 scope/ASG/PID 内部分析 |
| 面向新手 | 用大白话解释 clock、reset、时钟域 |

## 4. 大白话解释

### 4.1 clock 像硬件世界的节拍器

FPGA 里的寄存器不是“随时想变就变”，而是在 clock 的边沿一起更新。

你可以把 clock 想成硬件世界的节拍器：

```text
咚 -> 所有听这个 clock 的寄存器更新一次
咚 -> 再更新一次
咚 -> 再更新一次
```

如果一个模块用 `adc_clk`，它就按 `adc_clk` 的节奏工作。
如果一个模块用 `dac_clk_1x`，它就按 `dac_clk_1x` 的节奏工作。

### 4.2 reset 像让硬件统一回到初始状态

reset 的作用是让硬件从一个确定状态开始，而不是上电后寄存器乱七八糟。

大白话：

```text
clock 负责“什么时候动”
reset 负责“一开始回到哪里”
```

### 4.3 不同时钟域像不同节奏的乐队

如果两个模块用不同 clock，就像两个乐队用不同节奏演奏。

一个模块说：

```text
我每 8 ns 更新一次。
```

另一个模块说：

```text
我每 4 ns 更新一次。
```

这时如果直接把一个模块的信号随便接到另一个模块，可能会出现亚稳态、偶发错误、仿真看不出来但上板不稳定等问题。

这就是为什么新手阶段不要跨时钟域。

### 4.4 为什么第一版 future `laser_lock_core` 应该用 `adc_clk` / `adc_rstn`

原因很简单：

- L02 里 `adc_dat[0]`、`adc_dat[1]` 是在 `adc_clk` 上更新的；
- 官方 scope 用 `adc_clk` / `adc_rstn`；
- 官方 ASG 用 `adc_clk` / `adc_rstn`；
- 官方 PID 用 `adc_clk` / `adc_rstn`；
- system bus 也挂在 `adc_clk` / `adc_rstn` 相关接口上；
- 第一版 MTS core 只需要读 ADC 数据并产生 error 数字信号，最自然就是跟 ADC 数据在同一个节奏里工作。

所以第一版不要自己造新 clock，不要用 DAC clock 当算法主时钟，也不要做跨时钟域。

## 5. 新手必须明白

### 5.1 `adc_clk_i` 是外部差分 ADC clock 输入

top 端口里有：

```systemverilog
input logic [2-1:0] adc_clk_i
```

注释写的是：

```text
ADC clock {p,n}
```

这说明它是两根线组成的差分时钟输入。差分时钟不是一个普通单线 clock，而是一对互补信号。

### 5.2 `IBUFDS` 把差分 clock 变成 FPGA 内部单端 clock

官方代码是：

```systemverilog
IBUFDS i_clk (.I (adc_clk_i[1]), .IB (adc_clk_i[0]), .O (adc_clk_in));
```

大白话：

```text
adc_clk_i[1] / adc_clk_i[0] 是板子进来的差分时钟
IBUFDS 是 FPGA 的差分输入缓冲器
adc_clk_in 是 FPGA 内部可以送给 PLL 的单端时钟
```

硬件上等价于一个专用差分时钟输入缓冲器，不是普通逻辑门。

### 5.3 `red_pitaya_pll` 生成多路内部 clock

官方 `red_pitaya_pll` 使用 `adc_clk_in` 作为输入，输出多路 clock：

```text
pll_adc_clk
pll_dac_clk_1x
pll_dac_clk_2x
pll_dac_clk_2p
pll_ser_clk
pll_pwm_clk
```

本章重点只看：

```text
pll_adc_clk
pll_dac_clk_1x
pll_dac_clk_2x
pll_dac_clk_2p
```

其中官方注释说明：

- `pll_adc_clk`：ADC clock；
- `pll_dac_clk_1x`：DAC clock 125MHz；
- `pll_dac_clk_2x`：DAC clock 250MHz；
- `pll_dac_clk_2p`：DAC clock 250MHz -45DGR。

### 5.4 `BUFG` 把 PLL 输出送上 FPGA 全局时钟网络

官方代码是：

```systemverilog
BUFG bufg_adc_clk    (.O (adc_clk   ), .I (pll_adc_clk   ));
BUFG bufg_dac_clk_1x (.O (dac_clk_1x), .I (pll_dac_clk_1x));
BUFG bufg_dac_clk_2x (.O (dac_clk_2x), .I (pll_dac_clk_2x));
BUFG bufg_dac_clk_2p (.O (dac_clk_2p), .I (pll_dac_clk_2p));
```

大白话：PLL 产生 clock 后，还要通过 `BUFG` 这种专用全局 clock buffer，把 clock 稳定地送到 FPGA 很多地方。

新手不要把 `BUFG` 当普通 wire。它是 FPGA 专用 clock 资源。

### 5.5 `pll_locked` 表示 PLL 是否稳定

`red_pitaya_pll` 输出：

```systemverilog
.pll_locked(pll_locked)
```

大白话：

```text
pll_locked = 1：PLL 已经锁定，输出 clock 稳定，可以让逻辑开始工作。
pll_locked = 0：PLL 还没稳定，逻辑应该保持 reset。
```

所以 reset 生成逻辑会用到 `pll_locked`。

### 5.6 `frstn` 来自 PS

`frstn` 的声明是：

```systemverilog
logic [4-1:0] frstn;
```

它在 `red_pitaya_ps ps` 实例中由：

```systemverilog
.fclk_rstn_o(frstn)
```

连接出来。

大白话：`frstn` 是 PS 侧给 PL 侧的复位信号组。`frstn[0]` 被官方 top 用作很多 PL 逻辑 reset 的基础信号。

### 5.7 `adc_rstn` 是 active low reset

官方代码：

```systemverilog
always @(posedge adc_clk)
adc_rstn <= frstn[0] & pll_locked;
```

这说明：

- `adc_rstn` 在 `adc_clk` 时钟域生成；
- `adc_rstn` 是 active low；
- 只有 `frstn[0] = 1` 且 `pll_locked = 1` 时，`adc_rstn` 才为 1；
- 如果 PS reset 没释放，或 PLL 没锁定，`adc_rstn` 就为 0。

### 5.8 `dac_rst` 是 active high reset

官方代码：

```systemverilog
always @(posedge dac_clk_1x)
dac_rst <= ~frstn[0] | ~pll_locked;
```

这说明：

- `dac_rst` 在 `dac_clk_1x` 时钟域生成；
- `dac_rst` 是 active high；
- 如果 `frstn[0] = 0` 或 `pll_locked = 0`，`dac_rst` 就为 1，DAC 相关输出保持 reset。

注意 `adc_rstn` 和 `dac_rst` 极性不同：

```text
adc_rstn: n 结尾，active low，0 表示 reset
dac_rst : 没有 n，active high，1 表示 reset
```

## 6. 分层讲解

### 6.1 第一层：外部 clock 入口

clock 从 top 端口进来：

```text
adc_clk_i[1:0]
```

这是 ADC clock 差分输入。它不是算法信号，而是整个 FPGA clock 系统的重要源头。

### 6.2 第二层：差分输入缓冲

`adc_clk_i` 先进入：

```text
IBUFDS i_clk
```

输出：

```text
adc_clk_in
```

这一步把板级差分 clock 变成 FPGA 内部可用 clock。

### 6.3 第三层：PLL 生成多路 clock

`adc_clk_in` 进入：

```text
red_pitaya_pll pll
```

PLL 输出：

```text
pll_adc_clk
pll_dac_clk_1x
pll_dac_clk_2x
pll_dac_clk_2p
```

大白话：PLL 像一个“节拍加工厂”，用输入时钟加工出不同用途的节拍。

### 6.4 第四层：BUFG 分发 clock

PLL 输出还不是最终全局 clock。它们经过 `BUFG` 变成：

```text
pll_adc_clk     -> adc_clk
pll_dac_clk_1x  -> dac_clk_1x
pll_dac_clk_2x  -> dac_clk_2x
pll_dac_clk_2p  -> dac_clk_2p
```

大白话：`BUFG` 像把节拍送到全场的广播系统。

### 6.5 第五层：`adc_clk` 用在哪里

从 top 中可以看到，`adc_clk` 用在很多官方模块：

```text
ADC 数据寄存
system bus interface
red_pitaya_ams
red_pitaya_pdm
red_pitaya_scope
red_pitaya_asg
red_pitaya_pid
red_pitaya_daisy 部分接口
```

本章不分析这些模块内部，只确认一件事：

```text
adc_clk 是官方工程里非常核心的工作时钟。
```

### 6.6 第六层：DAC clock 用在哪里

从 L03 和本章代码可以看到：

- `dac_clk_1x` 用于 `dac_dat_a` / `dac_dat_b` 的输出寄存，也用于部分 DAC ODDR；
- `dac_clk_2x` 用于 `oddr_dac_wrt`；
- `dac_clk_2p` 用于 `oddr_dac_clk`；
- `dac_rst` 在 `dac_clk_1x` 域生成，并用于 DAC ODDR reset。

大白话：DAC 输出是一个板级高速接口，所以它需要专门的 DAC 时钟组合。新手阶段不要拿这些 clock 来随便跑算法。

### 6.7 第七层：reset 生成

官方 reset 的核心逻辑是：

```text
adc_rstn = frstn[0] & pll_locked
dac_rst  = ~frstn[0] | ~pll_locked
```

注意它们还分别在自己的 clock 域里寄存：

```text
adc_rstn 在 adc_clk 域
dac_rst  在 dac_clk_1x 域
```

这说明官方设计已经在尽量让 reset 跟对应时钟域匹配。

### 6.8 第八层：和 L02 ADC 的关系

L02 里 `adc_dat[0]`、`adc_dat[1]` 是在：

```systemverilog
always @(posedge adc_clk)
```

里更新的。

所以 future `laser_lock_core` 如果读 `adc_dat[0]` / `adc_dat[1]`，最自然就是使用同一个：

```text
adc_clk
adc_rstn
```

这样输入数据和算法模块在同一时钟域，第一版最简单、最稳。

### 6.9 第九层：和 L03 DAC 的关系

L03 里 DAC 最终输出有自己的：

```text
dac_clk_1x
dac_clk_2x
dac_clk_2p
dac_rst
```

但是官方 DAC 求和信号来源 `asg_dat`、`pid_dat` 的模块本身大量使用 `adc_clk` / `adc_rstn`。第一版 future `laser_lock_core` 先在 `adc_clk` 域工作，是为了和 ADC 数据、官方主处理路径保持一致。

真正要接入 DAC 时，要在后续 integration plan 里谨慎处理“算法输出到 DAC 输出链路”的边界。本章只确认：不要直接乱跨时钟域，不要乱改 DAC clock/ODDR。

## 7. clock/reset 关键端口/信号表

| 信号名 | 位宽/类型 | signed/unsigned | 来源 | 去向 | 对 MTS/稳频项目的作用 |
|---|---|---|---|---|---|
| `adc_clk_i` | `[2-1:0]` input | 不适用 | 外部 ADC clock 差分输入 | `IBUFDS i_clk` | 整个 clock 链路的板级输入源 |
| `adc_clk_i[1]` | 1 bit | 不适用 | 差分 clock p/n 之一 | `IBUFDS.I` | 差分时钟输入的一端 |
| `adc_clk_i[0]` | 1 bit | 不适用 | 差分 clock p/n 之一 | `IBUFDS.IB` | 差分时钟输入的另一端 |
| `adc_clk_in` | 1 bit | 不适用 | `IBUFDS` 输出 | `red_pitaya_pll.clk` | PLL 的输入时钟 |
| `red_pitaya_pll pll` | 模块实例 | 不适用 | `adc_clk_in`、`frstn[0]` | 多路 `pll_*` clock、`pll_locked` | 生成 ADC/DAC 等内部时钟 |
| `pll_adc_clk` | 1 bit clock | 不适用 | PLL 输出 | `BUFG bufg_adc_clk` | 生成 `adc_clk` 的前级 |
| `pll_dac_clk_1x` | 1 bit clock | 不适用 | PLL 输出 | `BUFG bufg_dac_clk_1x` | 生成 `dac_clk_1x` 的前级 |
| `pll_dac_clk_2x` | 1 bit clock | 不适用 | PLL 输出 | `BUFG bufg_dac_clk_2x` | 生成 `dac_clk_2x` 的前级 |
| `pll_dac_clk_2p` | 1 bit clock | 不适用 | PLL 输出 | `BUFG bufg_dac_clk_2p` | 生成 `dac_clk_2p` 的前级 |
| `pll_locked` | 1 bit | 不适用 | PLL 状态输出 | reset 生成逻辑 | 表示 PLL 是否稳定，决定是否释放 reset |
| `BUFG` | FPGA clock buffer | 不适用 | PLL 输出 clock | 全局 clock 网络 | 把 clock 稳定分发到 FPGA 内部 |
| `adc_clk` | 1 bit clock | 不适用 | `pll_adc_clk` 经 `BUFG` | ADC 数据、scope、ASG、PID、system bus 等 | future `laser_lock_core.clk_i` 第一版首选 |
| `dac_clk_1x` | 1 bit clock | 不适用 | `pll_dac_clk_1x` 经 `BUFG` | DAC 数据寄存、部分 ODDR、`dac_rst` 生成 | DAC 输出接口用，不建议第一版算法使用 |
| `dac_clk_2x` | 1 bit clock | 不适用 | `pll_dac_clk_2x` 经 `BUFG` | `oddr_dac_wrt` | DAC 写时序用，不要乱改 |
| `dac_clk_2p` | 1 bit clock | 不适用 | `pll_dac_clk_2p` 经 `BUFG` | `oddr_dac_clk` | DAC clock 输出用，不要乱改 |
| `fclk` | `[4-1:0]` | 不适用 | `red_pitaya_ps.fclk_clk_o` | PS/PL 相关逻辑 | PS 侧输出的 fabric clock 组，本章不深入 |
| `frstn` | `[4-1:0]` | 不适用 | `red_pitaya_ps.fclk_rstn_o` | PLL reset、ADC/DAC/PWM reset 生成 | PS 侧输出的 active low reset 组 |
| `frstn[0]` | 1 bit | 不适用 | `frstn` 第 0 路 | PLL reset 和内部 reset 生成 | reset 基础信号之一 |
| `adc_rstn` | 1 bit reset | active low | `frstn[0] & pll_locked`，在 `adc_clk` 域寄存 | ADC 域模块 | future `laser_lock_core.rstn_i` 第一版首选 |
| `dac_rst` | 1 bit reset | active high | `~frstn[0] | ~pll_locked`，在 `dac_clk_1x` 域寄存 | DAC ODDR | DAC 输出接口 reset，不建议第一版算法使用 |
| `future laser_lock_core.clk_i` | 1 bit clock | 不适用 | 建议接 `adc_clk` | future custom core | 第一版算法主时钟候选 |
| `future laser_lock_core.rstn_i` | 1 bit reset | active low | 建议接 `adc_rstn` | future custom core | 第一版算法 reset 候选 |

## 8. 证据

| 结论 | 证据位置 | 代码/说明 |
|---|---|---|
| `adc_clk_i` 是 ADC clock 输入端口 | `rtl\red_pitaya_top.sv` 第 96 行 | `input logic [2-1:0] adc_clk_i` |
| `fclk` / `frstn` 声明 | 第 131-132 行 | `logic [4-1:0] fclk`、`logic [4-1:0] frstn` |
| PLL 前级信号声明 | 第 155-163 行 | `adc_clk_in`、`pll_adc_clk`、`pll_dac_clk_*`、`pll_locked` |
| `adc_clk` / `adc_rstn` 声明 | 第 170-172 行 | `logic adc_clk`、`logic adc_rstn` |
| `dac_clk_1x/2x/2p` / `dac_rst` 声明 | 第 188-192 行 | DAC clock/reset signals |
| system bus 使用 `adc_clk` / `adc_rstn` | 第 208-209 行 | `ps_sys`、`sys` 接 `.clk(adc_clk)`、`.rstn(adc_rstn)` |
| `adc_clk_i` 经 `IBUFDS` 变成 `adc_clk_in` | 第 218-219 行 | `IBUFDS i_clk ... .O(adc_clk_in)` |
| `red_pitaya_pll` 输入 clock 是 `adc_clk_in` | 第 221-224 行 | `.clk(adc_clk_in)`、`.rstn(frstn[0])` |
| PLL 输出 ADC/DAC clock | 第 225-233 行 | `.clk_adc`、`.clk_dac_1x`、`.clk_dac_2x`、`.clk_dac_2p`、`.pll_locked` |
| PLL 输出经 `BUFG` 变成全局 clock | 第 236-239 行 | `BUFG bufg_adc_clk`、`bufg_dac_clk_*` |
| `pll_locked` 被用于状态计数 | 第 243-249 行 | PLL 未锁定时计数 |
| `adc_rstn` 生成 | 第 256-258 行 | `adc_rstn <= frstn[0] & pll_locked` |
| `dac_rst` 生成 | 第 260-262 行 | `dac_rst <= ~frstn[0] | ~pll_locked` |
| `frstn` 来自 PS | 第 275-300 行 | `.fclk_rstn_o(frstn)` |
| ADC 数据在 `adc_clk` 域寄存 | 第 400-403 行 | `always @(posedge adc_clk)` 更新 `adc_dat` |
| DAC 数据寄存在 `dac_clk_1x` 域 | 第 418-423 行 | `always @(posedge dac_clk_1x)` 更新 `dac_dat_a/b` |
| DAC ODDR 使用 DAC clocks | 第 425-430 行 | `dac_clk_2p`、`dac_clk_2x`、`dac_clk_1x` |
| scope 使用 `adc_clk` / `adc_rstn` | 第 517-522 行 | `.adc_clk_i(adc_clk)`、`.adc_rstn_i(adc_rstn)` |
| ASG 使用 `adc_clk` / `adc_rstn` | 第 554-559 行 | `.dac_clk_i(adc_clk)`、`.dac_rstn_i(adc_rstn)` |
| PID 使用 `adc_clk` / `adc_rstn` | 第 577-584 行 | `.clk_i(adc_clk)`、`.rstn_i(adc_rstn)` |

## 9. 不要碰/不要改

L04 阶段不要修改任何官方代码。

特别不要碰：

```text
rtl\red_pitaya_top.sv
adc_clk_i
IBUFDS i_clk
red_pitaya_pll pll
BUFG bufg_adc_clk
BUFG bufg_dac_clk_1x
BUFG bufg_dac_clk_2x
BUFG bufg_dac_clk_2p
adc_clk
dac_clk_1x
dac_clk_2x
dac_clk_2p
frstn
pll_locked
adc_rstn
dac_rst
```

新手特别要注意：

- PLL 不是普通算法模块；
- BUFG 不是普通 wire；
- reset 不是随便取反就行；
- 不同时钟域之间不能随便直接传信号；
- DAC clock 是为了满足外部 DAC 高速时序，不是第一版算法的玩具。

## 10. 已确认

- `adc_clk_i` 是 top 的 ADC clock 差分输入。
- `adc_clk_i[1]` / `adc_clk_i[0]` 经 `IBUFDS` 变成 `adc_clk_in`。
- `adc_clk_in` 进入 `red_pitaya_pll`。
- `red_pitaya_pll` 生成 `pll_adc_clk`、`pll_dac_clk_1x`、`pll_dac_clk_2x`、`pll_dac_clk_2p`。
- `pll_adc_clk` 经 `BUFG` 变成 `adc_clk`。
- `pll_dac_clk_1x` 经 `BUFG` 变成 `dac_clk_1x`。
- `pll_dac_clk_2x` 经 `BUFG` 变成 `dac_clk_2x`。
- `pll_dac_clk_2p` 经 `BUFG` 变成 `dac_clk_2p`。
- `pll_locked` 表示 PLL 是否锁定。
- `frstn` 来自 `red_pitaya_ps` 的 `.fclk_rstn_o(frstn)`。
- `adc_rstn` 在 `adc_clk` 域由 `frstn[0] & pll_locked` 生成，是 active low。
- `dac_rst` 在 `dac_clk_1x` 域由 `~frstn[0] | ~pll_locked` 生成，是 active high。
- `adc_dat[0]` / `adc_dat[1]` 在 `adc_clk` 域更新。
- 官方 scope、ASG、PID 都使用 `adc_clk` / `adc_rstn`。
- future `laser_lock_core` 第一版应优先使用 `adc_clk` / `adc_rstn`。

## 11. 不确定，需要人工确认

| 不确定项 | 为什么不确定 | 后续如何确认 |
|---|---|---|
| `adc_clk_i` 的实际频率和板级来源 | top 注释能看出是 ADC clock，但具体频率/芯片来源需硬件资料确认 | 查 Red Pitaya STEMlab 125-14 官方硬件资料 |
| `pll_dac_clk_2p` 的 -45DGR 相位为什么这样设置 | top 注释写明 -45DGR，但原因涉及 DAC 芯片时序 | 查 DAC 芯片手册和官方约束 |
| `frstn[0]` 的上电释放时序 | top 只显示它来自 PS，不显示 PS 内部细节 | 查 `red_pitaya_ps` 或 Vivado block design，但当前 L04 不展开 |
| future `laser_lock_core` 输出接入 DAC 路径是否需要 CDC | 第一版建议同用 `adc_clk`，但正式集成时仍需审查 DAC 路径边界 | 后续 L07/integration plan 单独确认 |
| 是否所有后续参数控制也走 `adc_clk` 域 | 涉及 PS/system bus 和寄存器设计，L04 不展开 | 后续 L06/system bus 学习 |

## 12. 我现在只需要记住什么

现在只需要记住八句话：

1. clock 是硬件世界的节拍器。
2. reset 是让硬件统一回到初始状态。
3. `adc_clk_i` 是外部差分 ADC clock 输入。
4. `IBUFDS` 把差分 clock 变成 `adc_clk_in`。
5. `red_pitaya_pll` 用 `adc_clk_in` 生成 ADC/DAC 等多路 clock。
6. `BUFG` 把 PLL clock 分发成 FPGA 内部全局 clock。
7. `adc_rstn` 只有在 `frstn[0]` 释放且 `pll_locked` 为 1 时才释放。
8. future `laser_lock_core` 第一版优先用 `adc_clk` 和 `adc_rstn`，不要跨时钟域。

## 13. 下一步建议

下一步建议做 L05：

```text
learning\L05_scope_asg_pid.md
reports\REPORT_L05_scope_asg_pid.md
```

但只有在用户明确要求时才开始。

现在不要继续 L05，不要写 Verilog，不要修改官方工程。

## 14. 给 GPT 审查的问题

1. 是否同意 future `laser_lock_core` 第一版使用 `adc_clk` / `adc_rstn`？
2. 是否同意第一版避免跨时钟域，不使用 `dac_clk_1x` 作为算法主时钟？
3. L04 对 `adc_rstn` active low 和 `dac_rst` active high 的解释是否足够清楚？
4. 是否需要后续单独查官方硬件资料确认 `adc_clk_i` 频率和 DAC clock 相位设置？
5. 后续 integration plan 是否必须明确写出“不修改 PLL/BUFG/reset/ODDR”？
