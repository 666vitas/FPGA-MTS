# 01 Red Pitaya 官方 top 学习笔记

阅读对象：

- `rtl/red_pitaya_top.sv`
- `project/redpitaya.xpr`
- `rtl/red_pitaya_ps.sv`
- `project/redpitaya.srcs/sources_1/imports/RedPitaya-FPGA-master/rtl/...`

原则：本文件只做代码阅读和文档整理，不修改官方 RTL，不新增模块。

## 1. `red_pitaya_top.sv` 是什么？

`red_pitaya_top.sv` 是 Red Pitaya FPGA 设计的顶层模块。它叫 top，是因为它位于整个 PL 逻辑的最外层：一边连接板级外部引脚，例如 ADC、DAC、PWM DAC、XADC、扩展口、SATA daisy、LED；另一边连接 Zynq PS/ARM、DDR、MIO；中间实例化并连接官方功能模块。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 1-3 行注释 `Red Pitaya TOP module. It connects external pins and PS part with other application modules.`
- 位置/关键词：第 52 行 `module red_pitaya_top`
- 位置/关键词：第 68-119 行顶层端口，包含 PS、DDR、ADC、DAC、PWM DAC、XADC、扩展口、SATA、LED。

在 Vivado 工程中，它被设置为顶层模块。也就是说综合/实现时，Vivado 会从 `red_pitaya_top` 这个模块开始展开整个硬件设计。

证据：

- 文件：`project/redpitaya.xpr`
- 模块：工程配置，不是 HDL 模块
- 位置/关键词：约第 1080 行、第 1110 行 `TopModule` 的值为 `red_pitaya_top`

它连接的主要模块包括：

- `red_pitaya_pll`
- `red_pitaya_ps`
- `sys_bus_interconnect`
- `red_pitaya_ams`
- `red_pitaya_pdm`
- `red_pitaya_hk`
- `red_pitaya_scope`
- `red_pitaya_asg`
- `red_pitaya_pid`
- `red_pitaya_daisy`

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 221 行 `red_pitaya_pll pll`
- 位置/关键词：第 275 行 `red_pitaya_ps ps`
- 位置/关键词：第 331 行 `sys_bus_interconnect`
- 位置/关键词：第 352 行 `red_pitaya_ams i_ams`
- 位置/关键词：第 371 行 `red_pitaya_pdm pdm`
- 位置/关键词：第 445 行 `red_pitaya_hk i_hk`
- 位置/关键词：第 517 行 `red_pitaya_scope i_scope`
- 位置/关键词：第 554 行 `red_pitaya_asg i_asg`
- 位置/关键词：第 577 行 `red_pitaya_pid i_pid`
- 位置/关键词：第 604 行 `red_pitaya_daisy i_daisy`

## 2. 主要模块作用

### `red_pitaya_pll`

作用：从 ADC 差分时钟输入生成内部多路时钟，包括 ADC clock、DAC 1x/2x/2p clock、serial clock、PDM clock，并输出 PLL lock 状态。

连接关系：

- `adc_clk_i[1:0]` 先经过 `IBUFDS i_clk` 变成 `adc_clk_in`。
- `red_pitaya_pll` 输入 `adc_clk_in`，输出 `pll_adc_clk`、`pll_dac_clk_1x`、`pll_dac_clk_2x`、`pll_dac_clk_2p`、`pll_ser_clk`、`pll_pwm_clk`。
- 这些时钟再经过 `BUFG` 变成 `adc_clk`、`dac_clk_1x`、`dac_clk_2x`、`dac_clk_2p`、`ser_clk`、`pwm_clk`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 218-241 行 `IBUFDS`、`red_pitaya_pll`、`BUFG`
- 文件：`project/.../rtl/red_pitaya_pll.sv`
- 模块：`red_pitaya_pll`
- 位置/关键词：第 13-25 行端口 `clk_adc`、`clk_dac_1x`、`clk_dac_2x`、`clk_dac_2p`、`clk_ser`、`clk_pdm`、`pll_locked`

### `red_pitaya_ps`

作用：Zynq Processing System wrapper，连接 ARM/PS、DDR、MIO、FCLK/reset、GPIO、system bus 和 AXI master 通道。

证据：

- 文件：`rtl/red_pitaya_ps.sv`
- 模块：`red_pitaya_ps`
- 位置/关键词：第 1-3 行 `Processing System (PS) wrapper`
- 位置/关键词：第 22-25 行说明 PS wrapper 内含 AXI slave，并作为 custom system bus master
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 275-325 行实例 `red_pitaya_ps ps`

### `sys_bus_interconnect`

作用：把 PS 侧来的 `ps_sys` system bus 按地址拆成多个 slave bus。top 中配置为 8 个 slave 区域，`sys[0]` 到 `sys[7]`。其中 `sys[6]` 和 `sys[7]` 当前接 stub。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 207-209 行 `sys_bus_if ps_sys`、`sys [8-1:0]`
- 位置/关键词：第 327-344 行 `sys_bus_interconnect`，参数 `.SN(8)`、`.SW(20)`，以及 `sys_bus_stub`
- 文件：`project/.../rtl/sys_bus_interconnect.sv`
- 模块：`sys_bus_interconnect`
- 位置/关键词：第 7-26 行参数和端口，`bus_m` 到 `bus_s`
- 位置/关键词：第 41-76 行地址选择、读写分发和返回数据复用

### `red_pitaya_ams`

作用：analog mixed signal 模块。官方注释说它使用 XADC 和软件接口控制 PWM DAC；当前 top 中主要看到它通过 `sys[4]` 配置 `pdm_cfg[0..3]`，再由 `red_pitaya_pdm` 输出 `dac_pwm_o`。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_ams.v`
- 模块：`red_pitaya_ams`
- 位置/关键词：第 15-39 行 `Module using XADC and software interface for PWM DAC`
- 位置/关键词：第 41-58 行端口 `dac_a_o`、`dac_b_o`、`dac_c_o`、`dac_d_o`、`sys_*`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 350-381 行 `pdm_cfg`、`red_pitaya_ams i_ams`、`red_pitaya_pdm pdm`

不确定，需要人工确认：当前工程中 XADC 数据是否完整通过 `red_pitaya_ams` 暴露给软件，因为阅读到的 `red_pitaya_ams.v` 片段主要是 PWM DAC 寄存器逻辑。

### `red_pitaya_hk`

作用：house keeping。负责系统识别、DNA/ID、LED、扩展口方向和数据、`digital_loop`、`daisy_mode`、CAN 开关等全局配置。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_hk.v`
- 模块：`red_pitaya_hk`
- 位置/关键词：第 15-27 行说明 system identification、expansion connector、LED
- 位置/关键词：第 29-58 行端口 `digital_loop`、`daisy_mode_o`、`exp_*`、`can_on_o`、`sys_*`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 445-471 行实例 `red_pitaya_hk i_hk`
- 位置/关键词：第 400-404 行 `digital_loop` 会让 `adc_dat` 取 `dac_a/dac_b`，形成数字回环

### `red_pitaya_scope`

作用：官方示波器采集模块，把 ADC 数据采集到 RAM/DDR，软件之后可以读取；内部包含输入滤波、平均/抽取、触发和 buffer。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_scope.v`
- 模块：`red_pitaya_scope`
- 位置/关键词：第 1-5 行 `capturing ADC data into BRAMs`
- 位置/关键词：第 16-48 行说明 `DFILT1`、`AVG & DEC`、`TRIG`、`BUF`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 517-547 行实例 `red_pitaya_scope i_scope`，输入 `adc_dat[0]`、`adc_dat[1]`

### `red_pitaya_asg`

作用：arbitrary signal generator，任意波形发生器。软件把波形写入 buffer，ASG 读出后做缩放和 offset，输出到 DAC 路径，并提供触发通知。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_asg.v`
- 模块：`red_pitaya_asg`
- 位置/关键词：第 1-4 行 `arbitrary signal generator`
- 位置/关键词：第 15-49 行说明 buffer、FSM、trigger、输出缩放
- 位置/关键词：第 51-68 行端口 `dac_a_o`、`dac_b_o`、`dac_clk_i`、`trig_out_o`、`sys_*`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 554-571 行实例 `red_pitaya_asg i_asg`，输出 `asg_dat[0]`、`asg_dat[1]`

### `red_pitaya_pid`

作用：官方 MIMO PID 控制器。它接收两路 14-bit 输入 `dat_a_i/dat_b_i`，内部由四个 PID 子块构成，输出两路 14-bit 控制量。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_pid.v`
- 模块：`red_pitaya_pid`
- 位置/关键词：第 1-4 行 `MIMO PID controller`
- 位置/关键词：第 17-48 行说明 `PID11`、`PID21`、`PID12`、`PID22`、`SUM & SAT`
- 位置/关键词：第 52-69 行端口 `dat_a_i`、`dat_b_i`、`dat_a_o`、`dat_b_o`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 577-593 行实例 `red_pitaya_pid i_pid`，输入 `adc_dat[0/1]`，输出 `pid_dat[0/1]`

注意：在当前 top 中，PID 直接吃 ADC 转换后的信号。对 MTS/饱和吸收稳频来说，PD 原始光强不是最终误差信号，所以不能简单把这个连接理解成“官方已经完成 MTS error 生成”。这里的 MTS 解调链路尚未出现。

### `red_pitaya_daisy`

作用：通过 SATA/daisy 差分线和其他 Red Pitaya 板卡做串行连接，可用于多板通信、同步或测试。

证据：

- 文件：`project/.../rtl/classic/red_pitaya_daisy.v`
- 模块：`red_pitaya_daisy`
- 位置/关键词：第 17-52 行说明 multiple boards、fast serial lines、TX/RX/test
- 位置/关键词：第 57-94 行端口 `daisy_p_o`、`daisy_n_o`、`daisy_p_i`、`daisy_n_i`、`ser_clk_i`、`par_clk_i`、`par_dat_*`、`sys_*`
- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 595-638 行实例 `red_pitaya_daisy i_daisy`

## 3. 按稳频项目分类

### 强相关模块

- `red_pitaya_top`：未来 `laser_lock_core` 的插入位置会在 top 中决定。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，ADC/DAC/ASG/PID/scope 连接集中在第 392-430 行、第 517-593 行。
- ADC IO 相关逻辑：PD 光强信号进入 FPGA 的入口。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，关键词 `adc_dat_i`、`adc_dat_raw`、`adc_dat`，第 94-98 行、第 392-404 行。
- DAC IO 相关逻辑：控制量输出到激光器执行器的最终出口。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，关键词 `dac_a_sum`、`dac_b_sum`、`dac_dat_a`、`dac_dat_b`、`dac_dat_o`，第 410-430 行。
- `red_pitaya_pll`：决定 ADC/DAC 主时钟。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，关键词 `red_pitaya_pll`、`adc_clk`、`dac_clk_1x`，第 221-241 行。
- `sys_bus_interconnect`：未来自定义寄存器配置可能需要挂到 system bus。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，关键词 `sys[6]`、`sys[7]`、`sys_bus_stub`，第 331-344 行。

### 可能复用模块

- `red_pitaya_scope`：可复用作原始 PD 信号、解调误差信号、控制量的观测工具。证据：`rtl/red_pitaya_top.sv` 第 517-547 行；`red_pitaya_scope.v` 第 1-48 行。
- `red_pitaya_asg`：可能复用为 MTS 调制波形源或测试激励源。证据：`rtl/red_pitaya_top.sv` 第 554-571 行；`red_pitaya_asg.v` 第 15-49 行。
- `red_pitaya_pid`：可能复用为解调误差信号后的控制器，但不能直接把 PD 光强当 error。证据：`rtl/red_pitaya_top.sv` 第 577-593 行；`red_pitaya_pid.v` 第 17-69 行。
- `red_pitaya_ps`：可能复用 ARM/software 配置通道。证据：`rtl/red_pitaya_ps.sv` 第 22-25 行；`rtl/red_pitaya_top.sv` 第 275-325 行。
- `red_pitaya_hk`：可能复用扩展口、触发、`digital_loop` 调试开关。证据：`rtl/red_pitaya_top.sv` 第 445-510 行；`red_pitaya_hk.v` 第 29-58 行。
- `red_pitaya_ams`：可能复用慢速 PWM DAC 做偏置或慢控制。证据：`rtl/red_pitaya_top.sv` 第 350-381 行；`red_pitaya_ams.v` 第 41-58 行。

### 暂时不用管模块

- `red_pitaya_daisy`：除非未来需要多板同步、板间通信或 daisy 触发，否则第一阶段不用深入。证据：`rtl/red_pitaya_top.sv` 第 595-638 行；`red_pitaya_daisy.v` 第 17-52 行。
- CAN/扩展口大部分细节：除非实验接线需要外部触发或数字状态输出。证据：`rtl/red_pitaya_top.sv` 第 481-510 行。
- `red_pitaya_pdm` 细节：当前只知道它把 `pdm_cfg` 转成 `dac_pwm_o`。证据：`rtl/red_pitaya_top.sv` 第 371-381 行。不确定，需要人工确认是否会用于本稳频执行器。

## 4. top 中关键词相关信号

### `adc` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `adc_dat_i` | 顶层 ADC 数据输入，`[MNA-1:0][15:0]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 94-96 行 |
| `adc_clk_i` | 顶层 ADC 差分时钟输入 `{p,n}` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 96 行 |
| `adc_clk_o` | 可选 ADC clock source 输出，注释写 unused | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 97 行、第 387-388 行 |
| `adc_cdcs_o` | ADC clock duty cycle stabilizer 输出，固定为 1 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 98 行、第 390 行 |
| `adc_clk_in` | `IBUFDS` 后的 ADC 输入时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 155-157 行、第 219 行 |
| `pll_adc_clk` | PLL 输出的 ADC clock | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 157 行、第 226 行 |
| `adc_clk` | BUFG 后的内部 ADC 主时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 171 行、第 236 行 |
| `adc_rstn` | ADC 时钟域 active-low reset | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 171-172 行、第 256-258 行 |
| `adc_clk_daisy` | daisy RX 输出的并行时钟，也用于 `adc_clk_o` ODDR | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 173 行、第 387-388 行、第 620 行 |
| `adc_dat_raw` | 从 16-bit ADC 输入截出的 14-bit 原始数据 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 392-398 行 |
| `adc_dat` | 转换成 two's complement 后的内部 ADC 数据，类型为 `SBA_T` signed 14-bit | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 182-186 行、第 400-404 行 |
| `adc_a_i`/`adc_b_i` | scope 的 ADC 输入端口，接 `adc_dat[0/1]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 517-522 行 |

### `dac` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `dac_dat_o` | 顶层高速 DAC 14-bit combined data 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 99-104 行、第 430 行 |
| `dac_wrt_o` | DAC write 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 101 行、第 427 行 |
| `dac_sel_o` | DAC channel select 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 102 行、第 428 行 |
| `dac_clk_o` | DAC clock 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 103 行、第 426 行 |
| `dac_rst_o` | DAC reset 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 104 行、第 429 行 |
| `dac_pwm_o` | 4 路 1-bit PWM DAC 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 105-106 行、第 371-381 行 |
| `pll_dac_clk_1x/2x/2p` | PLL 生成的 DAC 相关时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 158-160 行、第 227-229 行 |
| `dac_clk_1x/2x/2p` | BUFG 后的 DAC 相关时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 188-191 行、第 237-239 行 |
| `dac_rst` | DAC IO 内部 active-high reset | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 192 行、第 260-262 行 |
| `dac_dat_a/dac_dat_b` | DAC A/B 输出寄存器，送入 ODDR | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 194 行、第 418-430 行 |
| `dac_a/dac_b` | ASG+PID 饱和后的 14-bit 内部 DAC 数据 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 195 行、第 414-416 行 |
| `dac_a_sum/dac_b_sum` | `asg_dat` 与 `pid_dat` 的 15-bit signed 求和 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 196 行、第 410-412 行 |
| `pdm_cfg` | AMS 输出给 PDM 的 4 路 8-bit 配置 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 350-381 行 |

### `clk` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `FIXED_IO_ps_clk` | PS 侧时钟相关固定 IO | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 68-72 行、第 275-279 行 |
| `fclk` | PS 输出的 4 路 fabric clock，注释含 125/250/50/200 MHz | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 131 行、第 298-300 行 |
| `adc_clk_in` | ADC 差分时钟输入缓冲后信号 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 155-157 行、第 219 行 |
| `pll_adc_clk` | PLL ADC clock 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 157 行、第 226 行 |
| `pll_dac_clk_1x/2x/2p` | PLL DAC clock 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 158-160 行、第 227-229 行 |
| `pll_ser_clk` | PLL fast serial clock 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 161 行、第 230 行 |
| `pll_pwm_clk` | PLL PWM/PDM clock 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 162 行、第 231 行 |
| `adc_clk` | 主要数据处理时钟，scope/asg/pid/hk/ams/daisy sys bus 都使用它 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 236 行、第 352-355 行、第 517-522 行、第 554-559 行、第 577-580 行 |
| `dac_clk_1x/2x/2p` | DAC IO 输出使用的时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 237-239 行、第 419-430 行 |
| `ser_clk` | daisy high speed serial clock | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 165 行、第 240 行、第 611 行 |
| `pwm_clk` | PWM reset 生成使用的时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 167 行、第 241 行、第 264-266 行 |
| `axi0_clk/axi1_clk` | scope 输出给 PS 的 AXI 写通道时钟 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 143-145 行、第 529 行 |
| `dly_clk` | daisy IDELAY 用的 200 MHz 时钟，来自 `fclk[3]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 600-612 行 |

### `rst` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `FIXED_IO_ps_srstb` | PS reset 相关固定 IO | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 68-72 行、第 275-279 行 |
| `frstn` | PS 输出的 fabric active-low reset | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 131-132 行、第 298-300 行 |
| `pll_locked` | PLL lock 状态，参与 reset 生成 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 163 行、第 221-233 行、第 256-266 行 |
| `adc_rstn` | ADC 域 active-low reset，`frstn[0] & pll_locked` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 171-172 行、第 256-258 行 |
| `dac_rst` | DAC IO active-high reset，`~frstn[0] \| ~pll_locked` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 192 行、第 260-262 行 |
| `pwm_rstn` | PWM active-low reset | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 167-168 行、第 264-266 行 |
| `axi0_rstn/axi1_rstn` | scope 输出给 PS 的 AXI reset | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 143-145 行、第 529-530 行 |
| `dac_rst_o` | 顶层 DAC reset 输出 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 104 行、第 429 行 |

### `pid` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `pid_dat` | PID 输出到 DAC 求和路径的两路 14-bit signed 数据 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 201-202 行、第 581-584 行 |
| `red_pitaya_pid i_pid` | 官方 MIMO PID 实例 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 573-593 行 |
| `dat_a_i/dat_b_i` | PID 输入，当前接 `adc_dat[0/1]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 577-584 行 |
| `dat_a_o/dat_b_o` | PID 输出，当前接 `pid_dat[0/1]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 577-584 行 |
| `dac_a_sum/dac_b_sum` | PID 和 ASG 在 DAC 前相加 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 410-412 行 |

### `asg` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `asg_dat` | ASG 输出到 DAC 求和路径的两路 14-bit signed 数据 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 198-199 行、第 554-557 行 |
| `trig_asg_out` | ASG trigger notification 输出，送给 scope/GPIO 触发选择 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 140 行、第 481 行、第 524 行、第 562 行 |
| `trig_ext_asg01` | scope 外部/ASG trigger 共享信号 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 141 行、第 525-526 行 |
| `red_pitaya_asg i_asg` | 官方 ASG 实例 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 549-571 行 |
| `dac_a_sum/dac_b_sum` | ASG 和 PID 在 DAC 前相加 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 410-412 行 |

### `scope` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `scope_trigo` | scope 输出的 daisy trigger，参与外部触发输出选择 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 174 行、第 481 行、第 527 行 |
| `red_pitaya_scope i_scope` | 官方示波器采集实例 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 513-547 行 |
| `adc_a_i/adc_b_i` | scope 输入，当前接 `adc_dat[0/1]` | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 517-522 行 |
| `axi0_*`/`axi1_*` | scope 到 PS/DDR 的 AXI 写通道 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 143-153 行、第 528-538 行 |
| `sys[1]` | scope 的 system bus 配置区 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 539-546 行 |

### `sys_bus` 相关

| 信号/关键词 | 含义 | 证据 |
|---|---|---|
| `ps_sys` | PS 输出的 master system bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 207-208 行、第 312-336 行 |
| `sys[8-1:0]` | 8 路 slave system bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 207-209 行 |
| `sys_bus_interconnect` | system bus 地址解码和复用模块 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 327-337 行 |
| `sys[0]` | house keeping bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 463-470 行 |
| `sys[1]` | scope bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 539-546 行 |
| `sys[2]` | ASG bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 563-570 行 |
| `sys[3]` | PID bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 585-592 行 |
| `sys[4]` | AMS bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 361-368 行 |
| `sys[5]` | daisy bus | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 627-637 行 |
| `sys[6]`/`sys[7]` | 当前接 `sys_bus_stub`，看起来未使用 | 文件 `rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 339-344 行 |

不确定，需要人工确认：`sys[6]`/`sys[7]` 在软件侧地址空间是否完全空闲，硬件 top 中它们接 stub，但上位机或驱动是否已有保留约定需要继续查软件和地址文档。

## 5. 对稳频项目的关键理解

1. 官方 top 当前的数据主线是：`adc_dat_i` -> `adc_dat_raw` -> `adc_dat` -> `scope` 和 `pid`；`asg_dat + pid_dat` -> `dac_a/dac_b` -> `dac_dat_a/dac_dat_b` -> `dac_dat_o`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 392-430 行、第 517-593 行。
2. ADC 数据在 top 中做了格式转换：从 ADC 原始 16-bit 取高 14-bit，再转换为 two's complement。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 392-404 行。
3. DAC 输出前会把 ASG 和 PID 相加并饱和，再做 signed-to-unsigned/negative-slope 转换。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 410-430 行。
4. 当前官方工程里没有看到 MTS/饱和吸收解调链路。也就是说，PD 光强信号进入 ADC 后，目前只是被送给 scope 和 PID；真正的误差信号生成仍需后续自定义设计。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 517-593 行；未看到 mixer、demod、lock-in 等模块关键词。不确定，需要人工确认是否其他未实例化文件中有类似功能，但当前 top 没有连接。
