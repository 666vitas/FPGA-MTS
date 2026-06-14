# Red Pitaya 官方 FPGA 工程中与激光稳频相关的代码地图

> 阅读范围：当前工作区根目录 `rtl/red_pitaya_top.sv`，以及 Vivado 工程导入目录 `project/redpitaya.srcs/sources_1/imports/RedPitaya-FPGA-master/rtl/...` 下被 top 实例化的官方模块源码。本文只做代码阅读和结构分析，不建议在第一阶段修改官方工程。

## 1. `red_pitaya_top.sv` 的总体作用

`red_pitaya_top.sv` 是整块 Red Pitaya FPGA 逻辑的“总接线板”。它一边接外部硬件引脚，例如 ADC、DAC、PWM DAC、扩展口、SATA/daisy、LED；另一边接 Zynq PS/ARM 和 DDR；中间把官方提供的几个功能模块接起来，包括示波器采集 `scope`、任意波形发生器 `asg`、PID、模拟杂项 `ams`、house keeping 和 daisy 通信。

大白话说：它本身不是激光稳频算法，而是把“ADC 进来的数据送到该去的模块”，再把“ASG/PID 等模块算出的 DAC 数据送到高速 DAC 引脚”。官方文件头也说明 top 的作用是连接 PS 和其他应用模块，且图里明确有 `ADC -> SCOPE/PID`、`ASG/PID -> DAC` 的路径。来源：`rtl/red_pitaya_top.sv` 第 1-3 行、第 8-50 行。

官方注释还说明，analog 部分会把 ADC 数据从 unsigned negative-slope 转成 two's complement，DAC 输出前会做类似转换；scope 把 ADC 数据存 RAM，ASG 从 RAM 给 DAC 发数据，MIMO PID 以 ADC 为输入、DAC 为输出。来源：`rtl/red_pitaya_top.sv` 第 42-47 行。

## 2. top 下主要模块作用

### `red_pitaya_pll`

作用：从外部 ADC 差分时钟生成 FPGA 内部使用的多路时钟，包括 ADC clock、DAC 1x/2x/2p clock、fast serial clock 和 PDM clock，并输出 `pll_locked`。top 中先用 `IBUFDS` 接收 `adc_clk_i`，再实例化 `red_pitaya_pll`，之后用 `BUFG` 生成 `adc_clk`、`dac_clk_1x`、`dac_clk_2x`、`dac_clk_2p`、`ser_clk`、`pwm_clk`。来源：`rtl/red_pitaya_top.sv` 第 218-241 行；`project/.../rtl/red_pitaya_pll.sv` 第 13-25 行、第 30-83 行。

对稳频的意义：强相关但第一阶段不要动。后续 `laser_lock_core` 应该优先工作在 `adc_clk` 域，避免额外跨时钟复杂度。

### `red_pitaya_ps`

作用：Zynq PS/ARM 的 wrapper，连接 DDR/MIO、输出 FCLK/reset，并通过 AXI slave 暴露一个简化的 system bus 给 PL 模块使用。top 把 `ps_sys` 连接给它，同时 scope 的 AXI 写通道也接入 PS。来源：`rtl/red_pitaya_top.sv` 第 275-325 行；`rtl/red_pitaya_ps.sv` 第 1-25 行、第 28-89 行。

对稳频的意义：中等相关。将来如果 `laser_lock_core` 需要软件配置寄存器，需要理解 PS/system bus；但第一阶段不建议改 PS wrapper。

### `sys_bus_interconnect`

作用：把 PS 发来的 `ps_sys` system bus 按地址区域拆成 8 个 slave bus：`sys[0]` 到 `sys[7]`。top 中 `SN=8`、`SW=20`，并且 `sys[6]`、`sys[7]` 目前接到 stub。来源：`rtl/red_pitaya_top.sv` 第 207-209 行、第 327-344 行；`project/.../rtl/sys_bus_interconnect.sv` 第 7-26 行、第 41-76 行。

对稳频的意义：强相关。将来给 `laser_lock_core` 加软件寄存器时，`sys[6]` 或 `sys[7]` 是候选空地址区，但具体地址映射还需要和上位机/驱动确认。

### `red_pitaya_scope`

作用：官方示波器采集模块，把 ADC CH A/B 数据经过可配置滤波、平均/抽取、触发逻辑后写入 RAM/DDR，供软件读取。top 中它接收 `adc_dat[0]` 和 `adc_dat[1]`。来源：`rtl/red_pitaya_top.sv` 第 513-547 行；`project/.../rtl/classic/red_pitaya_scope.v` 第 1-48 行、第 50-99 行、第 124-140 行。

对稳频的意义：强相关但更偏“观测/调试”。你的 PD 原始光强信号可以通过 scope 看见；将来锁频误差信号也建议能送入某个可观测路径。第一阶段不建议改 scope 内部。

### `red_pitaya_asg`

作用：官方任意波形发生器。软件往 buffer 写波形，ASG 按配置读表、缩放、加 offset，输出两路 14-bit DAC 数据 `dac_a_o`、`dac_b_o`。top 中它输出到 `asg_dat[0]`、`asg_dat[1]`，随后与 PID 输出相加。来源：`rtl/red_pitaya_top.sv` 第 549-571 行；`project/.../rtl/classic/red_pitaya_asg.v` 第 1-49 行、第 51-68 行、第 107-145 行；`project/.../rtl/classic/red_pitaya_asg_ch.v` 第 37-43 行、第 146-159 行。

对稳频的意义：强相关。MTS 需要调制源时，ASG 可能作为现成调制波形来源；但如果调制/解调都要在 PL 闭环完成，未来也可能绕过或替换一部分 ASG 功能。

### `red_pitaya_pid`

作用：官方 MIMO PID 控制器。它有两路输入 `dat_a_i/dat_b_i` 和两路输出 `dat_a_o/dat_b_o`，内部由四个 PID block 组成：`PID11/PID21/PID12/PID22`，输出前做交叉求和和饱和。top 中它的输入来自 `adc_dat[0]`、`adc_dat[1]`，输出到 `pid_dat[0]`、`pid_dat[1]`。来源：`rtl/red_pitaya_top.sv` 第 573-593 行；`project/.../rtl/classic/red_pitaya_pid.v` 第 17-48 行、第 52-69 行、第 85-189 行、第 191-225 行。

注意：这个 PID block 里所谓 error 是 `set_sp_i - dat_i`，不是 MTS/饱和吸收解调得到的误差信号。来源：`project/.../rtl/classic/red_pitaya_pid_block.v` 第 72-83 行。你的项目里，PD 采到的是光强信号，因此真正的锁频误差信号应先由 `laser_lock_core` 做带通、缩放、混频、解调等处理后得到，再决定是否送入 PID 或直接控制 DAC。

### `red_pitaya_ams`

作用：模拟杂项模块，用 system bus 配置 4 路 8-bit PWM/PDM DAC，同时原始说明提到 XADC/供电/温度/外部电压读数；当前这个源码片段主要实现 PWM DAC 配置寄存器。top 中 `red_pitaya_ams` 输出 `pdm_cfg[0..3]`，再接 `red_pitaya_pdm` 输出 `dac_pwm_o`。来源：`rtl/red_pitaya_top.sv` 第 346-381 行；`project/.../rtl/classic/red_pitaya_ams.v` 第 15-39 行、第 41-58 行、第 64-95 行。

对稳频的意义：弱到中等相关。若用慢速模拟控制或偏置，可关注 PWM DAC；高速 MTS 解调主链路暂时不用管。

### `red_pitaya_hk`

作用：house keeping，处理 FPGA ID/DNA、LED、扩展口方向/数据、`digital_loop`、`daisy_mode`、CAN 开关等全局配置。top 中 `digital_loop` 会影响 ADC 数据来源：开启时 ADC 数据被替换为 DAC 内部数据，用于数字回环。来源：`rtl/red_pitaya_top.sv` 第 432-471 行、第 481-510 行；`project/.../rtl/classic/red_pitaya_hk.v` 第 15-27 行、第 29-58 行、第 131-153 行。

对稳频的意义：中等相关。`digital_loop` 会改变 ADC 路径，调试时必须确认它关闭；扩展口/触发也可能用到。第一阶段不要乱改。

### `red_pitaya_daisy`

作用：通过 SATA 差分线和其他板卡做高速串行 daisy-chain 通信。top 当前把它用于 daisy 测试/触发相关逻辑，`par_dat` 还参与 `daisy_trig`。来源：`rtl/red_pitaya_top.sv` 第 595-638 行；`project/.../rtl/classic/red_pitaya_daisy.v` 第 17-52 行、第 57-94 行。

对稳频的意义：通常弱相关，除非未来要多板同步或外部触发联动。第一阶段可以暂时不管。

## 3. 与稳频项目的相关性分组

强相关：

- `red_pitaya_top.sv`：未来插入 `laser_lock_core` 的位置在这里决定。来源：`rtl/red_pitaya_top.sv` 第 392-430 行、第 517-593 行。
- ADC IO/`adc_dat` 路径：PD 光强原始数据入口。来源：`rtl/red_pitaya_top.sv` 第 94-98 行、第 392-404 行。
- DAC IO/`dac_a/dac_b` 路径：最终控制输出入口。来源：`rtl/red_pitaya_top.sv` 第 410-430 行。
- `red_pitaya_asg`：可能提供调制波形。来源：`rtl/red_pitaya_top.sv` 第 554-571 行。
- `red_pitaya_pid`：可作为解调后误差信号的后级控制器候选，但不是误差信号生成器。来源：`rtl/red_pitaya_top.sv` 第 577-593 行；`red_pitaya_pid_block.v` 第 72-83 行。
- `sys_bus_interconnect`：未来配置寄存器入口。来源：`rtl/red_pitaya_top.sv` 第 331-344 行。

中等相关：

- `red_pitaya_scope`：观察原始 PD、滤波后信号、误差信号的调试通道。来源：`rtl/red_pitaya_top.sv` 第 517-547 行。
- `red_pitaya_ps`：软件配置和数据搬运相关。来源：`rtl/red_pitaya_top.sv` 第 275-325 行。
- `red_pitaya_hk`：`digital_loop`、扩展口、触发配置相关。来源：`rtl/red_pitaya_top.sv` 第 445-471 行。
- `red_pitaya_ams`：慢速 PWM DAC/模拟辅助控制相关。来源：`rtl/red_pitaya_top.sv` 第 352-381 行。

暂时不用管：

- `red_pitaya_daisy`：除非要多板同步。来源：`rtl/red_pitaya_top.sv` 第 604-638 行。
- CAN、扩展口大部分 GPIO 细节：除非外部触发/状态信号需要。来源：`rtl/red_pitaya_top.sv` 第 481-510 行。
- PLL 内部参数：除非采样率/时钟结构要改。来源：`project/.../rtl/red_pitaya_pll.sv` 第 30-83 行。

## 4. ADC CH1/CH2 在 top 内部的信号

外部 ADC 入口：

- `adc_dat_i`：端口声明为 `input logic [MNA-1:0] [16-1:0] adc_dat_i`，默认 `MNA=2`，因此 CH1/CH2 每路 16 bit。声明没有 `signed`，按 SystemVerilog 规则应视为 unsigned logic。来源：`rtl/red_pitaya_top.sv` 第 52-57 行、第 94-98 行。
- 时钟输入为 `adc_clk_i[1:0]` 差分时钟，经 `IBUFDS`、PLL、`BUFG` 生成内部 `adc_clk`。来源：`rtl/red_pitaya_top.sv` 第 218-241 行。

截位后的 ADC 原始数据：

- `adc_dat_raw`：`logic [2-1:0] [14-1:0] adc_dat_raw`，两路 14 bit，声明没有 `signed`，是 unsigned logic。它取 `adc_dat_i[0][15:2]` 和 `adc_dat_i[1][15:2]`，最低 2 bit 被注释为 reserved for 16bit ADC。来源：`rtl/red_pitaya_top.sv` 第 392-398 行。

转换后的内部 ADC 数据：

- `adc_dat`：类型 `SBA_T [MNA-1:0] adc_dat`，而 `SBA_T = logic signed [14-1:0]`，所以 `adc_dat[0]`/`adc_dat[1]` 是 14 bit signed。来源：`rtl/red_pitaya_top.sv` 第 182-186 行。
- CH1：`adc_dat[0]`，由 `adc_dat_raw[0]` 在 `posedge adc_clk` 下转换得到；如果 `digital_loop` 开启，则由 `dac_a` 回灌。来源：`rtl/red_pitaya_top.sv` 第 400-404 行。
- CH2：`adc_dat[1]`，由 `adc_dat_raw[1]` 在 `posedge adc_clk` 下转换得到；如果 `digital_loop` 开启，则由 `dac_b` 回灌。来源：`rtl/red_pitaya_top.sv` 第 400-404 行。
- 时钟域：`adc_dat[]` 在 `always @(posedge adc_clk)` 中寄存，属于 `adc_clk` 域；复位为 `adc_rstn`，由 `frstn[0] & pll_locked` 在 `adc_clk` 下生成。来源：`rtl/red_pitaya_top.sv` 第 251-258 行、第 400-404 行。

去向：

- `adc_dat[0]`/`adc_dat[1]` 同时送入 `red_pitaya_scope` 的 `adc_a_i/adc_b_i`。来源：`rtl/red_pitaya_top.sv` 第 517-522 行。
- `adc_dat[0]`/`adc_dat[1]` 同时送入 `red_pitaya_pid` 的 `dat_a_i/dat_b_i`。来源：`rtl/red_pitaya_top.sv` 第 577-584 行。

## 5. DAC CH1/CH2 输出前的信号

ASG 输出：

- `asg_dat`：类型 `SBG_T [2-1:0] asg_dat`，`SBG_T = logic signed [14-1:0]`，两路 14 bit signed。来源：`rtl/red_pitaya_top.sv` 第 182-184 行、第 198-199 行。
- `asg_dat[0]`/`asg_dat[1]` 由 `red_pitaya_asg` 输出，实例端口注释标为 CH1/CH2。top 给 ASG 的 `dac_clk_i` 实际接的是 `adc_clk`，所以 ASG 工作在 `adc_clk` 域。来源：`rtl/red_pitaya_top.sv` 第 554-559 行。

PID 输出：

- `pid_dat`：类型 `SBA_T [2-1:0] pid_dat`，两路 14 bit signed。来源：`rtl/red_pitaya_top.sv` 第 182-186 行、第 201-202 行。
- `pid_dat[0]`/`pid_dat[1]` 由 `red_pitaya_pid` 输出，PID 时钟接 `adc_clk`。来源：`rtl/red_pitaya_top.sv` 第 577-584 行。

DAC 前求和与饱和：

- `dac_a_sum`/`dac_b_sum`：`logic signed [15-1:0]`，分别等于 `asg_dat[0] + pid_dat[0]`、`asg_dat[1] + pid_dat[1]`。来源：`rtl/red_pitaya_top.sv` 第 194-197 行、第 410-412 行。
- `dac_a`/`dac_b`：`logic [14-1:0]`，声明没有 `signed`，但承载的是 two's complement 格式下的 14-bit 饱和结果。来源：`rtl/red_pitaya_top.sv` 第 194-196 行、第 414-416 行。
- `dac_dat_a`/`dac_dat_b`：`logic [14-1:0]`，在 `posedge dac_clk_1x` 下把 `dac_a/dac_b` 做 signed-to-unsigned negative-slope 变换后寄存。来源：`rtl/red_pitaya_top.sv` 第 194-195 行、第 418-423 行。
- `dac_dat_o`：外部 DAC 14 bit combined data 输出端口，`ODDR oddr_dac_dat` 用 `dac_clk_1x` 双沿输出，`D1=dac_dat_b`、`D2=dac_dat_a`，因此 CH A/B 通过 DDR 复用到同一 14-bit DAC 数据总线。来源：`rtl/red_pitaya_top.sv` 第 99-104 行、第 425-430 行。

时钟域：

- `asg_dat` 和 `pid_dat` 在当前 top 连接下都随 `adc_clk` 模块时钟产生。来源：`rtl/red_pitaya_top.sv` 第 554-559 行、第 577-580 行。
- `dac_a_sum/dac_b_sum`、`dac_a/dac_b` 是组合逻辑结果，输入来自 `adc_clk` 域模块输出；`dac_dat_a/dac_dat_b` 在 `dac_clk_1x` 下寄存。来源：`rtl/red_pitaya_top.sv` 第 410-423 行。
- `dac_clk_1x` 来自 PLL 的 `clk_dac_1x`，top 注释写为 DAC clock 125 MHz；`adc_clk` 也来自同一 PLL。来源：`rtl/red_pitaya_top.sv` 第 221-239 行。

## 6. 官方工程当前 ADC 到 DAC 数据流

```text
外部 ADC 引脚
  adc_dat_i[0/1]  16-bit unsigned logic
      |
      | 取 [15:2]
      v
  adc_dat_raw[0/1]  14-bit unsigned logic
      |
      | posedge adc_clk；negative-slope -> two's complement
      v
  adc_dat[0/1]  14-bit signed, adc_clk 域
      |
      +---------------------> red_pitaya_scope
      |                       用于采集/触发/写 RAM/DDR 给软件看
      |
      +---------------------> red_pitaya_pid
                              官方 MIMO PID
                              |
                              v
                         pid_dat[0/1]

red_pitaya_asg
  软件波形 buffer -> 读表/缩放/offset
      |
      v
  asg_dat[0/1]

pid_dat[0/1] + asg_dat[0/1]
      |
      v
  dac_a_sum/dac_b_sum  15-bit signed
      |
      | 饱和
      v
  dac_a/dac_b  14-bit two's complement 数据
      |
      | posedge dac_clk_1x；signed -> unsigned negative-slope
      v
  dac_dat_a/dac_dat_b
      |
      | ODDR：D1=dac_dat_b, D2=dac_dat_a
      v
外部 DAC 引脚 dac_dat_o[13:0], dac_wrt_o, dac_sel_o, dac_clk_o
```

来源主线：ADC IO 与转换在 `rtl/red_pitaya_top.sv` 第 392-404 行；scope 连接在第 517-547 行；ASG 连接在第 554-571 行；PID 连接在第 577-593 行；DAC 求和、饱和和 ODDR 输出在第 410-430 行。

## 7. 未来插入 `laser_lock_core` 的候选位置

候选位置 A：ADC 转换后、分发给 scope/PID 前。

- 位置：`adc_dat[0/1]` 生成之后，也就是 `rtl/red_pitaya_top.sv` 第 400-404 行之后、scope/PID 实例之前。
- 优点：拿到的是已经转换成 14-bit signed two's complement 的 PD 光强信号，适合做带通、缩放、混频、解调。
- 典型用途：`laser_lock_core` 输入 `adc_dat[0]`/`adc_dat[1]`，输出误差信号、调制参考、诊断信号。
- 风险：如果要把误差信号送回 scope，需要规划替代/旁路 scope 的输入，避免丢失原始 PD 可观测性。

候选位置 B：PID 输入前。

- 位置：`red_pitaya_pid` 的 `.dat_a_i(adc_dat[0])`、`.dat_b_i(adc_dat[1])` 附近。来源：`rtl/red_pitaya_top.sv` 第 577-584 行。
- 思路：把 `laser_lock_core` 解调出的误差信号送给 PID，而不是把原始 PD 光强直接送给 PID。
- 注意：这是概念上很合理的位置，但需要确认 PID 的 setpoint、符号、增益缩放是否适合 MTS error。

候选位置 C：DAC 求和前，与 ASG/PID 并列或替代 PID。

- 位置：`dac_a_sum = asg_dat[0] + pid_dat[0]`、`dac_b_sum = asg_dat[1] + pid_dat[1]` 附近。来源：`rtl/red_pitaya_top.sv` 第 410-416 行。
- 思路：`laser_lock_core` 直接输出 DAC 控制量，参与或替代 `pid_dat`。
- 优点：闭环延迟短，控制路径清楚。
- 风险：需要重新定义 ASG 调制量、反馈控制量、DAC 通道分工，避免两个控制源抢同一路 DAC。

候选位置 D：system bus 空 slave 区。

- 位置：`sys[6]`、`sys[7]` 当前接 `sys_bus_stub`。来源：`rtl/red_pitaya_top.sv` 第 331-344 行。
- 思路：未来 `laser_lock_core` 的配置/status 寄存器可以挂在空 bus 区。
- 注意：不确定上位机地址空间是否已有软件约定，需要人工确认。

## 8. 目前绝对不要修改的地方

- 不要改 `red_pitaya_pll` 和时钟/reset 网络。原因：ADC/DAC/serial/PWM 全部依赖这些时钟，改动风险很大。来源：`rtl/red_pitaya_top.sv` 第 218-266 行；`project/.../rtl/red_pitaya_pll.sv` 第 30-83 行。
- 不要改 PS/DDR/MIO/AXI wrapper。原因：这关系到 Linux/ARM、DDR、AXI 数据搬运和软件寄存器访问。来源：`rtl/red_pitaya_top.sv` 第 275-325 行；`rtl/red_pitaya_ps.sv` 第 1-25 行。
- 不要改 ADC/DAC 物理 IO 的格式转换和 ODDR 输出。原因：这里涉及 Red Pitaya 板级 ADC/DAC 的编码、negative-slope、DDR 复用时序。来源：`rtl/red_pitaya_top.sv` 第 392-430 行。
- 不要改 `red_pitaya_scope` 内部。原因：它是第一阶段验证 PD 原始光强和后续误差信号的关键观测工具。来源：`project/.../rtl/classic/red_pitaya_scope.v` 第 1-48 行。
- 不要改 `red_pitaya_hk` 里的 `digital_loop` 默认行为。原因：它会影响 ADC 实际数据来源，调试时必须可控。来源：`project/.../rtl/classic/red_pitaya_hk.v` 第 131-153 行；`rtl/red_pitaya_top.sv` 第 400-404 行。
- 不要直接把原始 PD 光强当作最终误差信号接 PID。原因：官方 PID 的 error 只是 `set_sp_i - dat_i`，不是 MTS/饱和吸收解调误差信号。来源：`project/.../rtl/classic/red_pitaya_pid_block.v` 第 72-83 行。

## 9. 下一步阅读任务清单

1. 阅读 `red_pitaya_scope.v` 的寄存器映射和数据路径，确认能否同时观察原始 PD、带通后信号、解调后 error。重点看 `sys_addr` case、BRAM/AXI 写入路径。入口文件：`project/.../rtl/classic/red_pitaya_scope.v`，已确认模块头和输入滤波在第 50-140 行附近。
2. 阅读 `red_pitaya_asg.v` 和 `red_pitaya_asg_ch.v` 的寄存器映射，确认能否用 ASG 产生 MTS 调制参考，以及 ASG 输出符号/幅度范围。入口文件：`project/.../rtl/classic/red_pitaya_asg.v` 第 51-160 行；`red_pitaya_asg_ch.v` 第 146-159 行。
3. 阅读 `red_pitaya_pid.v` 和 `red_pitaya_pid_block.v` 的寄存器映射、符号缩放、饱和范围，判断它适合作为解调 error 后的慢环/快环控制器，还是需要自定义 PI/PID。入口文件：`project/.../rtl/classic/red_pitaya_pid.v` 第 191-260 行；`red_pitaya_pid_block.v` 第 72-180 行。
4. 阅读 system bus 地址映射和软件侧寄存器定义，确认 `sys[6]`/`sys[7]` 是否真的可用。硬件入口：`rtl/red_pitaya_top.sv` 第 331-344 行；`project/.../rtl/sys_bus_interconnect.sv` 第 41-76 行。
5. 查约束文件中 ADC/DAC 引脚和时钟约束，确认当前 top 对应的板卡型号、采样率和时钟。入口文件候选：`sdc/red_pitaya.xdc` 和 `project/redpitaya.srcs/constrs_1/imports/RedPitaya-FPGA-master/prj/v0.94/sdc/red_pitaya.xdc`。
6. 整理未来 `laser_lock_core` 的接口草案，但暂时不写 Verilog：输入应包括 `adc_clk`、`adc_rstn`、`adc_dat[0/1]`、可选 ASG/ref；输出应包括 `error`、`control`、debug/scope 观测信号、system bus 寄存器接口。

