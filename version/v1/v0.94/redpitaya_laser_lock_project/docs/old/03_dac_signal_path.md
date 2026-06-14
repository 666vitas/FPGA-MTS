# 03 DAC 输出路径追踪

实验定义：

- OUT1 = FPGA 解调得到的 error signal，用示波器观察。
- OUT2 = 后续 PID 控制输出，接激光器 scan/current slow feedback。

阅读对象：

- `rtl/red_pitaya_top.sv`
- `project/redpitaya.srcs/sources_1/imports/RedPitaya-FPGA-master/rtl/classic/red_pitaya_asg.v`
- `project/redpitaya.srcs/sources_1/imports/RedPitaya-FPGA-master/rtl/classic/red_pitaya_pid.v`

原则：本文件只追踪 DAC 输出路径，不修改官方代码，不写新模块，不写 Verilog。

## 1. 顶层 DAC 外部端口

在 `red_pitaya_top` 顶层端口中，高速 DAC 相关外部端口有：

| 端口名 | 方向 | 代码声明 | 说明 |
|---|---|---|---|
| `dac_dat_o` | output | `logic [14-1:0]` | DAC combined data，14-bit 数据总线 |
| `dac_wrt_o` | output | `logic` | DAC write |
| `dac_sel_o` | output | `logic` | DAC channel select |
| `dac_clk_o` | output | `logic` | DAC clock |
| `dac_rst_o` | output | `logic` | DAC reset |
| `dac_pwm_o` | output | `logic [4-1:0]` | 4 路 1-bit PWM DAC，不是本节主追踪的高速 DAC 路径 |

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 99-106 行 `// DAC`、`dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o`、`dac_pwm_o`

## 2. `dac_a_sum` / `dac_b_sum` 是怎么得到的

DAC 主数据路径在 `DAC IO` 段开始。官方 top 先把 ASG 输出和 PID 输出相加：

```text
dac_a_sum = asg_dat[0] + pid_dat[0]
dac_b_sum = asg_dat[1] + pid_dat[1]
```

其中：

- `asg_dat` 定义为 `SBG_T [2-1:0]`，`SBG_T = logic signed [14-1:0]`，所以 top 中把 ASG 输出当作 14-bit signed generate stream 使用。
- `pid_dat` 定义为 `SBA_T [2-1:0]`，`SBA_T = logic signed [14-1:0]`，所以 top 中把 PID 输出当作 14-bit signed acquire/control stream 使用。
- `dac_a_sum` / `dac_b_sum` 定义为 `logic signed [15-1:0]`，即 15-bit signed，用来容纳两个 14-bit signed 数据相加后的结果。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 182-184 行 `SBA_T`、`SBG_T`
- 位置/关键词：第 194-202 行 `dac_a_sum`、`dac_b_sum`、`asg_dat`、`pid_dat`
- 位置/关键词：第 410-412 行 `Sumation of ASG and PID`、`assign dac_a_sum`、`assign dac_b_sum`

`asg_dat` 进入 DAC 路径：

- `red_pitaya_asg` 的 `dac_a_o` 接到 `asg_dat[0]`，注释为 CH 1。
- `red_pitaya_asg` 的 `dac_b_o` 接到 `asg_dat[1]`，注释为 CH 2。
- ASG 实例时钟接 `adc_clk`，复位接 `adc_rstn`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 554-559 行 `red_pitaya_asg i_asg`
- 文件：`project/.../rtl/classic/red_pitaya_asg.v`
- 模块：`red_pitaya_asg`
- 位置/关键词：第 51-56 行端口 `dac_a_o`、`dac_b_o`、`dac_clk_i`、`dac_rstn_i`

`pid_dat` 进入 DAC 路径：

- `red_pitaya_pid` 的 `dat_a_o` 接到 `pid_dat[0]`。
- `red_pitaya_pid` 的 `dat_b_o` 接到 `pid_dat[1]`。
- PID 实例时钟接 `adc_clk`，复位接 `adc_rstn`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 577-584 行 `red_pitaya_pid i_pid`
- 文件：`project/.../rtl/classic/red_pitaya_pid.v`
- 模块：`red_pitaya_pid`
- 位置/关键词：第 52-59 行端口 `dat_a_i`、`dat_b_i`、`dat_a_o`、`dat_b_o`
- 位置/关键词：第 224-225 行 `assign dat_a_o = out_1_sat`、`assign dat_b_o = out_2_sat`

## 3. `dac_a` / `dac_b` 是怎么由 `dac_a_sum` / `dac_b_sum` 得到的

`dac_a` 和 `dac_b` 是 `dac_a_sum` / `dac_b_sum` 饱和后的 14-bit 结果：

```text
如果 dac_a_sum 最高两位出现溢出模式，则饱和到正/负满量程；
否则 dac_a = dac_a_sum[13:0]

如果 dac_b_sum 最高两位出现溢出模式，则饱和到正/负满量程；
否则 dac_b = dac_b_sum[13:0]
```

饱和判断使用 `^dac_a_sum[14:13]` 和 `^dac_b_sum[14:13]`。当 15-bit signed sum 的最高两位不同，说明从 15 bit 截到 14 bit 会溢出，于是生成饱和值：

- 正溢出时最高位为 `0`，结果为 `0` 加 13 个 `1`，即 14-bit signed 正最大。
- 负溢出时最高位为 `1`，结果为 `1` 加 13 个 `0`，即 14-bit signed 负最大幅度。

注意：`dac_a` / `dac_b` 在声明上是普通 `logic [14-1:0]`，没有写 `signed`。但从前后文看，它们承载的是 14-bit two's complement 数值。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 194-196 行 `dac_a`、`dac_b`、`dac_a_sum`、`dac_b_sum`
- 位置/关键词：第 414-416 行 `// saturation`、`assign dac_a`、`assign dac_b`

## 4. `dac_dat_a` / `dac_dat_b` 是怎么由 `dac_a` / `dac_b` 得到的

`dac_dat_a` 和 `dac_dat_b` 在 `posedge dac_clk_1x` 下寄存生成：

```text
dac_dat_a = {dac_a[13], ~dac_a[12:0]}
dac_dat_b = {dac_b[13], ~dac_b[12:0]}
```

代码注释明确说明这里做了：

- output registers
- signed to unsigned
- also to negative slope

因此，这一步是把内部 14-bit two's complement 格式转换成板级 DAC 需要的 unsigned negative-slope 格式，并寄存到 DAC 1x 时钟域。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 418 行注释 `output registers + signed to unsigned (also to negative slope)`
- 位置/关键词：第 419-423 行 `always @(posedge dac_clk_1x)`、`dac_dat_a`、`dac_dat_b`

## 5. `dac_dat_o` 最终如何输出

最终高速 DAC 输出经过 ODDR。

相关 ODDR：

- `oddr_dac_clk` 输出 `dac_clk_o`，时钟为 `dac_clk_2p`。
- `oddr_dac_wrt` 输出 `dac_wrt_o`，时钟为 `dac_clk_2x`。
- `oddr_dac_sel` 输出 `dac_sel_o`，时钟为 `dac_clk_1x`。
- `oddr_dac_rst` 输出 `dac_rst_o`，时钟为 `dac_clk_1x`。
- `oddr_dac_dat [13:0]` 输出 `dac_dat_o[13:0]`，时钟为 `dac_clk_1x`，其中 `D1=dac_dat_b`，`D2=dac_dat_a`。

这说明 A/B 两路数据通过 DDR 方式复用到同一组 14-bit `dac_dat_o` 外部总线上。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 425-430 行 `// DDR outputs`、`ODDR oddr_dac_*`

时钟来源：

- `dac_clk_1x` 来自 PLL 输出 `pll_dac_clk_1x` 经 `BUFG`。
- `dac_clk_2x` 来自 PLL 输出 `pll_dac_clk_2x` 经 `BUFG`。
- `dac_clk_2p` 来自 PLL 输出 `pll_dac_clk_2p` 经 `BUFG`。
- top 注释写 `clk_dac_1x` 是 DAC clock 125 MHz，`clk_dac_2x` 是 250 MHz，`clk_dac_2p` 是 250 MHz -45DGR。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 221-239 行 `red_pitaya_pll` 和 `BUFG bufg_dac_clk_*`

## 6. `dac_a` / `dac_b` 对应物理 OUT1 还是 OUT2？

代码中可以确认：

- `asg_dat[0]` 注释为 CH 1，参与 `dac_a_sum`，最后进入 `dac_a` 和 `dac_dat_a`。
- `asg_dat[1]` 注释为 CH 2，参与 `dac_b_sum`，最后进入 `dac_b` 和 `dac_dat_b`。
- `oddr_dac_dat` 中 `D1=dac_dat_b`、`D2=dac_dat_a`，说明 A/B 最终被 DDR 复用到 `dac_dat_o`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 554-557 行 `asg_dat[0] // CH 1`、`asg_dat[1] // CH 2`
- 位置/关键词：第 411-416 行 `dac_a_sum`、`dac_b_sum`、`dac_a`、`dac_b`
- 位置/关键词：第 421-430 行 `dac_dat_a`、`dac_dat_b`、`ODDR oddr_dac_dat`

结合命名和注释，可以把 `dac_a` 暂定理解为 DAC CH1 路径，把 `dac_b` 暂定理解为 DAC CH2 路径。但 `dac_a` 是否物理对应 Red Pitaya 前面板 OUT1、`dac_b` 是否物理对应 OUT2，不能仅由 `red_pitaya_top.sv` 完全确认。

结论：不确定，需要结合硬件文档、XDC 约束、DAC 芯片连接或实测确认。

对你的实验定义，建议暂定：

- OUT1/error signal 观察通道 -> 候选 `dac_a` / `dac_dat_a` 路径
- OUT2/PID control 输出通道 -> 候选 `dac_b` / `dac_dat_b` 路径

但最终必须通过硬件文档或实测确认。

## 7. 当前 DAC 输出由哪些模块共同决定

当前高速 DAC 输出由以下两类数据共同决定：

1. `asg_dat[0/1]`：来自 `red_pitaya_asg`。
2. `pid_dat[0/1]`：来自 `red_pitaya_pid`。

它们在 DAC IO 段相加：

```text
dac_a_sum = asg_dat[0] + pid_dat[0]
dac_b_sum = asg_dat[1] + pid_dat[1]
```

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 410-412 行 `asg_dat`、`pid_dat`
- 位置/关键词：第 554-571 行 `red_pitaya_asg i_asg`
- 位置/关键词：第 577-593 行 `red_pitaya_pid i_pid`

是否还有其他路径：

- 在 `red_pitaya_top.sv` 当前 DAC 主路径中，没有看到第三个模块直接参与 `dac_a_sum` / `dac_b_sum`。
- `digital_loop` 会让 ADC 数据从 `dac_a/dac_b` 回灌到 `adc_dat[0/1]`，但它不是 DAC 输出的额外来源。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 400-404 行。
- `dac_pwm_o` 是独立的 PWM DAC 输出，不进入高速 DAC `dac_dat_o` 路径。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 350-381 行、第 99-106 行。

结论：当前高速 DAC 主输出由 `asg_dat` 和 `pid_dat` 共同决定；未看到其他直接数据源。不确定，需要人工确认是否软件配置可让 ASG/PID 输出为零或旁路。

## 8. 未来新增 `laser_lock_core` 的安全接入建议

你的目标定义是：

- OUT1 输出 FPGA 解调得到的 error signal，用示波器观察。
- OUT2 输出后续 PID 控制量，接激光器 scan/current slow feedback。

最安全的硬件接入原则：

1. 不改 ODDR 输出层。
2. 不改 DAC signed-to-unsigned/negative-slope 转换层。
3. 尽量保留官方 `dac_a_sum/dac_b_sum` 后面的饱和保护。
4. 在 `dac_a_sum/dac_b_sum` 前增加选择逻辑，把官方路径和 `laser_lock_core` 路径做二选一。

推荐连接概念：

| `laser_lock_core` 输出 | 推荐进入的官方路径 | 用途 |
|---|---|---|
| `error_o` | `dac_a_sum` 前的 A 路选择输入 | OUT1，用示波器观察 error signal |
| `pid_o` 或 `control_o` | `dac_b_sum` 前的 B 路选择输入 | OUT2，后续接激光器反馈 |

这样做的好处是：

- `USE_LASER_LOCK_CORE = 0` 时，保持官方 `asg_dat + pid_dat` 原始 DAC 输出。
- `USE_LASER_LOCK_CORE = 1` 时，A/B 两路改用 `laser_lock_core` 的 error/control 输出。
- 后面的 `dac_a/dac_b` 饱和、`dac_dat_a/dac_dat_b` 格式转换、ODDR 时序输出都继续复用官方逻辑。

不确定，需要人工确认：

- `laser_lock_core.error_o` 和 `laser_lock_core.pid_o/control_o` 的位宽、符号、满量程定义尚未设计。
- OUT1/OUT2 与 `dac_a/dac_b` 的物理对应关系需要硬件文档或实测确认。
- 激光器执行器是否允许直接接 Red Pitaya OUT2，还需要模拟前端、电压范围、限流和保护方案确认。

## 9. 三种接入方案比较

| 方案 | 做法 | 优点 | 风险 |
|---|---|---|---|
| A. 替换 `asg_dat` | 用 `laser_lock_core` 输出替代 `asg_dat[0/1]`，仍与 `pid_dat` 相加 | 可把 laser 输出当作“发生器输出”进入 DAC；保留 PID 项叠加 | ASG 原本可能用于调制源，替换后会丢官方 ASG 功能；如果 PID 未清零，会和 laser 输出叠加，容易误输出 |
| B. 替换 `pid_dat` | 用 `laser_lock_core` 输出替代 `pid_dat[0/1]`，仍与 `asg_dat` 相加 | 概念上把 laser 控制量当作“控制器输出”；ASG 可继续作为调制源或偏置源 | 如果 ASG 未清零或仍在输出，会叠加到 laser 输出；OUT1 error 观察不一定适合放在 PID 路径 |
| C. 在 `dac_a_sum/dac_b_sum` 前新增 mux | 官方 `asg+pid` 路径和 laser `error/control` 路径二选一 | 最小侵入、可一键回到官方路径、保留后级饱和/格式转换/ODDR | 需要新增选择控制；必须设计安全默认值、复位默认官方路径或安全零输出 |

推荐：方案 C。

原因：它把“官方路径”和“laser lock 路径”分清楚，最容易回退，也最不容易在调试时让 ASG/PID 残留输出与 laser 输出意外叠加。

## 10. 推荐最小侵入式方案

推荐引入一个顶层选择概念：

```text
USE_LASER_LOCK_CORE = 0：
  A 路 DAC = 官方 asg_dat[0] + pid_dat[0]
  B 路 DAC = 官方 asg_dat[1] + pid_dat[1]

USE_LASER_LOCK_CORE = 1：
  A 路 DAC = laser_lock_core.error_o
  B 路 DAC = laser_lock_core.control_o
```

注意：这只是后续集成方案说明，不是本阶段要写的 Verilog。

推荐保留的官方后级：

```text
选择后的 A/B 路
  -> 现有 dac_a_sum / dac_b_sum 等价位置
  -> 现有 saturation
  -> 现有 signed-to-unsigned negative-slope 转换
  -> 现有 ODDR DAC 输出
```

安全建议：

- `USE_LASER_LOCK_CORE` 默认值应为 `0`，保持官方原始 DAC 输出。
- laser 模式开启前，先确认 `laser_lock_core` 输出有独立限幅、使能和安全零输出。
- OUT2 接激光器反馈前，必须先用示波器或假负载验证幅度、极性、饱和行为。
- 如果 OUT1 用来观察 error，建议第一阶段只接示波器，不接执行器。

证据：后级可复用位置来自 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 410-430 行 `dac_a_sum` 到 `ODDR oddr_dac_dat`。

## 11. DAC 相关信号表

| 信号名 | 位宽 | signed/unsigned | 时钟域 | 当前用途 | 可否作为接入点 | 风险 |
|---|---:|---|---|---|---|---|
| `asg_dat` | 2 路 x 14 bit | top 中为 signed `SBG_T` | 由 ASG 在 `adc_clk` 下产生 | ASG 输出，参与 DAC 求和 | 可作为接入点，但不推荐直接替换 | 可能破坏 ASG 调制/测试功能；与 PID 叠加风险 |
| `asg_dat[0]` | 14 bit | signed `SBG_T` | `adc_clk` 相关 | DAC A/CH1 ASG 分量 | 可用于 OUT1 路径候选 | 物理 OUT1 映射不确定，需要人工确认 |
| `asg_dat[1]` | 14 bit | signed `SBG_T` | `adc_clk` 相关 | DAC B/CH2 ASG 分量 | 可用于 OUT2 路径候选 | 物理 OUT2 映射不确定，需要人工确认 |
| `pid_dat` | 2 路 x 14 bit | top 中为 signed `SBA_T` | 由 PID 在 `adc_clk` 下产生 | PID 输出，参与 DAC 求和 | 可作为接入点，但不推荐直接替换 | 若 ASG 非零，会叠加；原 PID 功能被覆盖 |
| `pid_dat[0]` | 14 bit | signed `SBA_T` | `adc_clk` 相关 | DAC A/CH1 PID 分量 | 可用于 OUT1 路径候选 | error 观察和控制输出语义可能混淆 |
| `pid_dat[1]` | 14 bit | signed `SBA_T` | `adc_clk` 相关 | DAC B/CH2 PID 分量 | 可用于 OUT2 路径候选 | 与 ASG 叠加风险 |
| `dac_a_sum` | 15 bit | signed | 组合逻辑，输入来自 `adc_clk` 域信号 | A 路 ASG+PID 求和 | 推荐在它前面加 mux | 需处理跨时钟/组合路径和安全默认值 |
| `dac_b_sum` | 15 bit | signed | 组合逻辑，输入来自 `adc_clk` 域信号 | B 路 ASG+PID 求和 | 推荐在它前面加 mux | 需处理跨时钟/组合路径和安全默认值 |
| `dac_a` | 14 bit | 声明 unsigned，语义为 signed two's complement | 组合逻辑 | A 路饱和结果 | 不推荐在此后接入 | 绕过前级求和结构，且接近格式转换层 |
| `dac_b` | 14 bit | 声明 unsigned，语义为 signed two's complement | 组合逻辑 | B 路饱和结果 | 不推荐在此后接入 | 绕过前级求和结构，且接近格式转换层 |
| `dac_dat_a` | 14 bit | unsigned DAC 格式 | `dac_clk_1x` | A 路 signed-to-unsigned/negative-slope 后寄存值 | 不推荐接入 | 接入会绕过官方格式转换和饱和 |
| `dac_dat_b` | 14 bit | unsigned DAC 格式 | `dac_clk_1x` | B 路 signed-to-unsigned/negative-slope 后寄存值 | 不推荐接入 | 接入会绕过官方格式转换和饱和 |
| `dac_dat_o` | 14 bit | 外部 DAC 数据格式 | ODDR 输出 | 物理 DAC combined data 输出 | 绝对不推荐接入 | 板级时序/ODDR/物理接口风险最高 |
| `dac_wrt_o` | 1 bit | 外部 DAC 控制 | ODDR 输出 | DAC write | 不作为数据接入点 | 改动会破坏 DAC 时序 |
| `dac_sel_o` | 1 bit | 外部 DAC 控制 | ODDR 输出 | DAC channel select | 不作为数据接入点 | 改动会破坏 A/B 通道复用 |
| `dac_clk_o` | 1 bit | 外部 DAC clock | ODDR 输出 | DAC clock | 不作为数据接入点 | 改动会破坏板级 DAC 时钟 |
| `dac_rst_o` | 1 bit | 外部 DAC reset | ODDR 输出 | DAC reset | 不作为数据接入点 | 改动会影响 DAC 初始化/复位 |
| `dac_pwm_o` | 4 路 x 1 bit | PWM/PDM | `adc_clk`/PDM 相关 | 慢速 PWM DAC 输出 | 不属于高速 DAC 主路径 | 可另作慢控制研究，但不是本任务主线 |

表格证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 182-202 行类型和 DAC/ASG/PID 内部信号声明
- 位置/关键词：第 221-262 行 DAC 时钟和 reset 来源
- 位置/关键词：第 410-430 行 DAC 求和、饱和、格式转换和 ODDR 输出
- 位置/关键词：第 554-593 行 ASG/PID 输出接入

## 12. 当前结论和不确定项

已确认：

1. 顶层高速 DAC 外部端口包括 `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 99-104 行。
2. 当前 DAC 数据由 `asg_dat` 和 `pid_dat` 相加得到。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 410-412 行。
3. `dac_a` / `dac_b` 是 `dac_a_sum` / `dac_b_sum` 饱和后的 14-bit 结果。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 414-416 行。
4. `dac_dat_a` / `dac_dat_b` 做了 signed-to-unsigned / negative-slope 转换，并在 `dac_clk_1x` 下寄存。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 418-423 行。
5. `dac_dat_o` 最终通过 `ODDR oddr_dac_dat` 输出，`D1=dac_dat_b`、`D2=dac_dat_a`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 425-430 行。

不确定，需要人工确认：

1. `dac_a` 是否物理对应前面板 OUT1，`dac_b` 是否物理对应前面板 OUT2，需要结合硬件文档、XDC 约束、DAC 芯片连接或实测确认。
2. `laser_lock_core.error_o` 和 `laser_lock_core.control_o` 的位宽、缩放、极性和限幅尚未定义，需要后续架构设计确认。
3. 激光器执行器输入范围、允许极性、保护电路、慢反馈接口形式，需要结合实验硬件确认，不能只由 FPGA top 代码判断。
