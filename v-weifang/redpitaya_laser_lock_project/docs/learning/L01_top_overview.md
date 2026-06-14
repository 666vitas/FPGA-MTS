# L01_top_overview：red_pitaya_top.sv 总览

## 0. 本文件作用

本文件只做 L01：学习官方 `rtl\red_pitaya_top.sv` 的整体结构。

本章目标不是看懂每一行代码，而是先建立一张“地图”：知道 `red_pitaya_top.sv` 在 Red Pitaya FPGA 工程里像什么、连着哪些大模块、哪些区域以后可能和 MTS/激光稳频项目有关。

本章不深入 L02 ADC 细节，也不深入 L03 DAC 细节。

## 1. 阅读对象

本次只读一个官方文件：

```text
rtl\red_pitaya_top.sv
```

只读，不修改。

## 2. 实验定义

本项目后续想做的是 MTS 激光稳频中的 FPGA 数字信号处理：

```text
PD signal
REF signal
  -> Red Pitaya FPGA
  -> error signal
```

但在 L01 阶段，我们不接线、不写 `laser_lock_core`、不改官方 top。

现在只问一个问题：

```text
red_pitaya_top.sv 这个官方 top 文件，在整个 Red Pitaya FPGA 系统里负责什么？
```

## 3. 当前原则

| 原则 | 说明 |
|---|---|
| 只做 L01 | 只学习 top 总览 |
| 官方工程只读 | 不修改 `rtl\red_pitaya_top.sv` |
| 不写 Verilog | 不生成任何 RTL |
| 不实现 `laser_lock_core` | 本章只学习，不开发 |
| 不开始 L02/L03 | ADC/DAC 只讲大概位置，不追细节 |
| 面向新手 | 先讲系统位置，再讲模块，再讲信号 |

## 4. 大白话解释

`red_pitaya_top.sv` 很像 Red Pitaya FPGA 的“总接线板”。

可以把 Red Pitaya 想象成一台仪器，里面有很多零件：

- ADC：把外部模拟输入变成 FPGA 里的数字数据；
- DAC：把 FPGA 里的数字数据送回模拟输出；
- PLL/clock/reset：给所有硬件逻辑提供节拍和复位；
- PS/system bus：让 ARM/Linux 软件能控制 FPGA 里的模块；
- scope：像示波器采集模块，把 FPGA 里的数据存起来给软件看；
- ASG：任意波形发生器，可以产生输出波形；
- PID：官方已有的控制器；
- HK/GPIO/LED：板卡管理、扩展口、LED 等杂项功能。

`red_pitaya_top.sv` 的工作不是亲自完成所有功能，而是把这些零件连起来。它像一个总接线板：

```text
外部引脚
  <-> red_pitaya_top.sv
      <-> PLL / reset
      <-> PS / system bus
      <-> ADC IO
      <-> DAC IO
      <-> scope
      <-> ASG
      <-> PID
      <-> HK / GPIO / LED
      <-> daisy
```

所以后续如果要接入 MTS/激光稳频模块，不能随便把算法塞进 top。正确做法是：先理解这个总接线板，再设计一个独立的自定义模块，最后只在安全位置做接线方案。

## 5. 新手必须明白

### 5.1 top 文件不是算法文件

`red_pitaya_top.sv` 不是用来写 MTS 算法的地方。

它主要负责：

- 接外部 FPGA 引脚；
- 接 PS/DDR/AXI；
- 接 ADC/DAC；
- 接官方 scope/ASG/PID/HK；
- 管理 clock/reset；
- 把各模块的信号接在一起。

### 5.2 top 文件是系统入口

Vivado 综合整个 FPGA 设计时，需要一个最顶层模块。这里的顶层模块就是：

```text
module red_pitaya_top
```

它下面再实例化很多子模块，例如：

```text
red_pitaya_ps
red_pitaya_pll
red_pitaya_scope
red_pitaya_asg
red_pitaya_pid
red_pitaya_hk
```

### 5.3 对 MTS 项目来说，top 的意义是“找接线点”

我们现在不是要改 top，而是要从 top 里学会：

- ADC 数据大概从哪里进入；
- DAC 数据大概从哪里出去；
- clock/reset 大概从哪里来；
- 官方 scope/ASG/PID 怎么连接；
- 后续自定义 `laser_lock_core` 应该作为独立模块，从哪里读信号、往哪里送信号。

## 6. 分层讲解

### 6.1 第一层：系统总图

文件开头的官方注释已经说明了 `red_pitaya_top.sv` 的定位：

```text
Top module connects PS part with rest of Red Pitaya applications.
```

大白话：PS 是 ARM/Linux 那边，FPGA 里还有 scope、ASG、PID、ADC、DAC 等应用模块。top 负责把它们连起来。

### 6.2 第二层：外部端口

`red_pitaya_top` 的端口包括几大类：

| 端口类别 | 大概作用 | 对本项目的意义 |
|---|---|---|
| PS connections | 连接 Zynq PS 固定 IO | 当前不要改 |
| DDR | 连接外部 DDR | 当前不要改 |
| ADC | 外部 ADC 数据和时钟 | 后续 PD/REF 可能从这里进入 |
| DAC | 外部 DAC 数据、时钟、控制 | 后续 error signal 可能从这里输出 |
| PWM DAC | 低速 PWM DAC 输出 | 当前不是主线 |
| XADC | FPGA 片上模拟输入 | 当前不是主线 |
| Expansion connector | 扩展口 | 当前不是主线 |
| SATA/daisy | 板间连接 | 当前不是主线 |
| LED | LED 输出 | 可用于调试，但不是当前主线 |

### 6.3 第三层：内部信号

top 内部先声明很多线，例如：

| 信号类别 | 例子 | 大概作用 |
|---|---|---|
| clock/reset | `adc_clk`、`adc_rstn`、`dac_clk_1x` | 给逻辑提供节拍和复位 |
| ADC 数据 | `adc_dat` | FPGA 内部使用的 ADC 数据 |
| DAC 数据 | `dac_a`、`dac_b`、`dac_a_sum`、`dac_b_sum` | FPGA 内部送 DAC 的数据 |
| system bus | `ps_sys`、`sys` | PS 软件控制 FPGA 模块的通道 |
| ASG/PID 数据 | `asg_dat`、`pid_dat` | 官方 ASG/PID 的输出 |

这里先只认名字和大概分区，不展开位宽转换细节。

### 6.4 第四层：主要模块实例

top 里实例化了多个官方模块。它们像被插到总接线板上的功能卡。

| 模块实例 | 所在区域 | 大概作用 | 本项目暂时态度 |
|---|---|---|---|
| `red_pitaya_pll pll` | PLL 区域 | 产生 ADC/DAC/serial/PWM 等时钟 | 只读，不改 |
| `red_pitaya_ps ps` | PS 连接区域 | 连接 ARM/DDR/AXI/system bus | 只读，不改 |
| `sys_bus_interconnect` | system bus 区域 | 把 PS bus 分到多个模块 | 只读，不改 |
| `red_pitaya_ams i_ams` | Analog mixed signals | 管理 AMS/PWM 配置 | 当前不是主线 |
| `red_pitaya_pdm pdm` | PDM 区域 | 产生 PWM DAC 输出 | 当前不是主线 |
| `red_pitaya_hk i_hk` | House Keeping | LED、GPIO、digital_loop、daisy mode 等 | 只读，不改 |
| `red_pitaya_scope i_scope` | oscilloscope 区域 | 采集 `adc_dat[0]`、`adc_dat[1]` 给软件看 | 后续调试很有用 |
| `red_pitaya_asg i_asg` | ASG 区域 | 官方任意波形发生器 | 后续可能作为回退路径 |
| `red_pitaya_pid i_pid` | PID 区域 | 官方 PID 控制器 | 当前不做 FPGA PID |
| `red_pitaya_daisy i_daisy` | daisy 区域 | 板间高速链路 | 当前不是主线 |

## 7. 关键文件/信号/模块表

### 7.1 关键文件表

| 文件 | 作用 | 新手必须看懂 | 暂时可以不懂 | 不要乱改 |
|---|---|---|---|---|
| `rtl\red_pitaya_top.sv` | 官方 FPGA 顶层总接线文件 | 大模块分区、ADC/DAC/clock/reset/PS/scope/ASG/PID 大概位置 | 每个模块内部实现 | 整个文件当前只读 |

### 7.2 关键模块表

| 模块/实例 | 大概位置 | 大白话作用 | 和 MTS/稳频项目关系 |
|---|---|---|---|
| `red_pitaya_top` | 顶层模块 | 总接线板 | 未来只应该在这里做最小接线方案 |
| `red_pitaya_pll pll` | clock/reset 区域 | 产生全板 FPGA 时钟 | 后续自定义模块需要选对 clock/reset |
| `red_pitaya_ps ps` | PS 连接区域 | 连接 ARM/Linux | 后续参数控制可能经过 PS，但当前不改 |
| `sys_bus_interconnect` | system bus 区域 | 软件控制总线分发器 | 后续 gain/offset 可能用到，但当前不改 |
| `red_pitaya_scope i_scope` | oscilloscope 区域 | FPGA 内部示波器 | 后续观察 ADC/error 很有用 |
| `red_pitaya_asg i_asg` | ASG 区域 | 波形发生器 | 官方输出路径的一部分，后续要保留回退 |
| `red_pitaya_pid i_pid` | PID 区域 | 官方 PID | 当前不做 PID，只读 |
| `ODDR oddr_dac_*` | DAC IO 区域 | 把数据按 DAC 需要的时序送到引脚 | 绝对不要乱改 |

### 7.3 关键总览信号表

| 信号名 | 位宽/类型 | signed/unsigned | 来自哪里 | 送到哪里 | 本项目作用 |
|---|---|---|---|---|---|
| `adc_dat_i` | `[MNA-1:0][16-1:0]` | 未声明 signed | 外部 ADC 端口 | ADC IO 区域 | 后续 PD/REF 原始入口候选，细节留到 L02 |
| `adc_dat` | `SBA_T [MNA-1:0]` | `SBA_T` 是 signed 14 bit | ADC IO 转换后 | scope、PID 等 | 后续自定义 core 的候选输入，细节留到 L02 |
| `adc_clk` | 1 bit clock | 不适用 | PLL/BUFG | ADC、scope、ASG、PID 等 | 后续 custom core 候选时钟 |
| `adc_rstn` | 1 bit reset | 不适用 | reset 逻辑 | ADC 时钟域模块 | 后续 custom core 候选复位 |
| `asg_dat` | `SBG_T [2-1:0]` | signed 14 bit | `red_pitaya_asg` | DAC 求和路径 | 官方输出路径，后续应保留回退 |
| `pid_dat` | `SBA_T [2-1:0]` | signed 14 bit | `red_pitaya_pid` | DAC 求和路径 | 官方 PID 输出，当前不做 PID |
| `dac_a_sum`、`dac_b_sum` | signed 15 bit | signed | ASG/PID 求和 | DAC 限幅 | 后续 DAC 插入点可能相关，细节留到 L03 |
| `dac_dat_o` | 14 bit output | 未声明 signed | DAC ODDR | 外部 DAC | 最终 DAC 引脚输出，不要直接改 |

## 8. 证据

| 证据 | 位置 | 说明 |
|---|---|---|
| 文件开头注释 | `rtl\red_pitaya_top.sv` 第 1-43 行附近 | 说明 top 连接 PS、scope、ASG、PID、ADC、DAC、daisy |
| 顶层模块声明 | 第 52 行附近 | `module red_pitaya_top` |
| ADC/DAC 顶层端口 | 第 95-104 行附近 | 出现 `adc_dat_i`、`adc_clk_i`、`dac_dat_o`、`dac_wrt_o` 等 |
| local signals | 第 122 行后 | 声明内部 clock、ADC、DAC、system bus 等信号 |
| `SBA_T` / `SBG_T` | 第 182-186 行附近 | 定义 acquire/generate stream bus 类型 |
| PLL 区域 | 第 214-264 行附近 | `IBUFDS`、`red_pitaya_pll`、`BUFG`、`adc_rstn`、`dac_rst` |
| PS 区域 | 第 271-325 行附近 | `red_pitaya_ps ps` 连接 PS、DDR、AXI、system bus |
| system bus 区域 | 第 327-344 行附近 | `sys_bus_interconnect` 把 `ps_sys` 分到 `sys` |
| ADC IO 区域 | 第 383-404 行附近 | ADC 输入转换到 `adc_dat` |
| DAC IO 区域 | 第 406-430 行附近 | `dac_a_sum`、`dac_b_sum`、saturation、ODDR |
| House Keeping | 第 432-471 行附近 | `red_pitaya_hk i_hk` |
| scope | 第 512-547 行附近 | `red_pitaya_scope i_scope` 读取 `adc_dat[0]`、`adc_dat[1]` |
| ASG | 第 549-571 行附近 | `red_pitaya_asg i_asg` 输出 `asg_dat[0]`、`asg_dat[1]` |
| PID | 第 573-593 行附近 | `red_pitaya_pid i_pid` 读取 `adc_dat`，输出 `pid_dat` |
| Daisy | 第 595-639 行附近 | `red_pitaya_daisy i_daisy` |

## 9. 不要碰/不要改

L01 阶段不要修改任何官方代码。

尤其不要碰：

```text
rtl\red_pitaya_top.sv
red_pitaya_pll
red_pitaya_ps
sys_bus_interconnect
ADC IO
DAC IO
ODDR
PS/AXI/DDR
scope
ASG
PID
HK
XDC/SDC
```

新手特别要注意：`ODDR`、PLL、PS/AXI/DDR 这些是板级基础设施。它们不是 MTS 算法，不是新手阶段应该试着改的地方。

## 10. 已确认

- `red_pitaya_top.sv` 是官方 FPGA 顶层模块。
- 它连接外部引脚、PS、DDR、ADC、DAC、scope、ASG、PID、HK、daisy 等模块。
- top 文件开头官方注释已经把它描述成连接 PS 和 Red Pitaya 应用模块的顶层。
- ADC、DAC、clock/reset、PS/system bus、scope/ASG/PID 都能在 top 中找到明确区域。
- 本章只完成了 L01 总览，没有展开 L02 ADC 细节，也没有展开 L03 DAC 细节。

## 11. 不确定，需要人工确认

| 不确定项 | 为什么不确定 |
|---|---|
| `adc_dat[0]` 是否一定物理对应 Red Pitaya IN1 | L01 只看 top 总览，物理通道对应需要 L02 和板级资料/实验确认 |
| `adc_dat[1]` 是否一定物理对应 Red Pitaya IN2 | 同上 |
| DAC A/B 是否一定对应 OUT1/OUT2 | L01 不深入 DAC，需 L03 和板级资料/实验确认 |
| 当前工作区的 `rtl\red_pitaya_top.sv` 是否完全等同干净官方原版 | 本次只读当前文件；若需要原版对比，需后续单独做审查 |

## 12. 我现在只需要记住什么

现在只需要记住四句话：

1. `red_pitaya_top.sv` 是 Red Pitaya FPGA 的“总接线板”。
2. 它负责把 PS、ADC、DAC、clock/reset、scope、ASG、PID 等模块连起来。
3. MTS/稳频算法以后不应该散写在 top 里，而应该做成独立模块，再通过安全接线方案接入。
4. 当前只学习总览，不写 RTL，不改官方工程。

## 13. 下一步建议

下一步建议做 L02：

```text
learning\L02_adc_path.md
reports\REPORT_L02_adc_path.md
```

但只有在用户明确要求时才开始。

现在不要继续 L02，不要写 Verilog，不要修改官方工程。

## 14. 给 GPT 审查的问题

1. 这个 L01 总览是否足够解释 `red_pitaya_top.sv` 为什么像“总接线板”？
2. L01 是否已经足够，不需要再展开 ADC/DAC 细节？
3. 后续 L02 是否应重点确认 `adc_dat[0]`、`adc_dat[1]` 和 IN1/IN2 的关系？
4. 后续 L03 是否应重点确认 DAC A/B 和 OUT1/OUT2 的关系？
