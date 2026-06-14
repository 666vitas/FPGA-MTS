# FPGA/Verilog 新手术语表

## 0. 本文件作用

本文件把本项目里反复出现的关键术语用大白话解释一遍。

不需要背，读到不懂的词回来查就行。

## 1. 数字格式和位宽

| 术语 | 大白话 |
|---|---|
| bit / 位宽 | 一个数字用多少根线表示。14 bit 就是 14 根线，每根线可以是 0 或 1 |
| signed | 有正负号的数。signed 14-bit 范围是 -8192 到 +8191。写代码时用 `logic signed` |
| unsigned | 只有正数和 0 的数。写代码时不写 `signed` 就是 unsigned |
| two's complement | FPGA 里表示 signed 数的标准方式。最高位是 1 表示负数，是 0 表示正数 |
| MSB / LSB | Most Significant Bit 最高位 / Least Significant Bit 最低位 |
| 截位 | 从宽位宽取窄位宽，例如从 16-bit 取 [15:2] 就是丢掉最低 2-bit |
| 位宽扩展 | 窄位宽变宽位宽，例如 14-bit 扩展成 15-bit 防止加法溢出 |
| 溢出 | 两个数相加结果超出位宽能表示的范围，例如两个 14-bit 正数相加超过 +8191 |
| 饱和 / saturation | 溢出时把结果压到最大值或最小值，而不是让数字绕回（例如 +8200 被压成 +8191） |
| 符号扩展 / sign-extension | 把 signed 数扩展位宽时，用最高位填充新增的高位 |

## 2. 时钟和复位

| 术语 | 大白话 |
|---|---|
| clock / 时钟 | FPGA 的节拍器。每来一个上升沿，寄存器更新一次。本项目主时钟是 `adc_clk`，约 125 MHz |
| posedge / 上升沿 | 时钟从 0 跳到 1 的瞬间 |
| reset / 复位 | 让所有寄存器回到初始状态 |
| active-low reset | 低电平（0）表示复位中，高电平（1）表示正常工作。`adc_rstn` 就是这种 |
| active-high reset | 高电平（1）表示复位中。`dac_rst` 就是这种 |
| rstn | 命名里带 `n` 通常表示 active-low |
| 时钟域 | 用同一个 clock 的所有寄存器的集合。同一个时钟域内信号可以安全直连 |
| 跨时钟域 / CDC | 把信号从一个时钟域传到另一个时钟域，需要特殊处理，新手阶段**不要做** |
| PLL | Phase-Locked Loop，锁相环。把输入时钟加工成不同频率/相位的输出时钟 |
| BUFG | FPGA 里的全局时钟缓冲器，把时钟稳定分发到整个芯片。**不是普通导线，不能乱改** |
| pll_locked | PLL 的输出状态信号。PLL 稳定后此信号变 1，在此之前 `adc_rstn` 会保持为 0 |

## 3. 信号和总线

| 术语 | 大白话 |
|---|---|
| port / 端口 | 模块对外的输入输出接口，就像芯片的引脚 |
| input / output | input 是信号进入模块，output 是信号从模块出去 |
| wire | 组合逻辑连线，不经过寄存器 |
| reg / register / 寄存器 | 在时钟边沿更新、能记住上一个值的存储单元 |
| always_ff | SystemVerilog 里描述时序逻辑（寄存器）的写法：`always_ff @(posedge clk)` |
| always_comb | SystemVerilog 里描述组合逻辑的写法 |
| assign | 连续赋值，描述组合逻辑连线 |
| bus / 总线 | 一组相关信号的集合，例如 `adc_dat[1:0]` 表示两路 ADC 数据 |
| valid | 数据有效标志，告诉下游"当前数据可以用了"。本项目当前没有 valid 信号 |

## 4. ADC 和 DAC 相关

| 术语 | 大白话 |
|---|---|
| ADC | Analog to Digital Converter，把模拟电压变成 FPGA 里的数字值 |
| DAC | Digital to Analog Converter，把 FPGA 里的数字值变成模拟电压 |
| IN1 / IN2 | Red Pitaya 前面板的两个模拟输入口，对应 FPGA 内部 `adc_dat[0]` 和 `adc_dat[1]` |
| OUT1 / OUT2 | Red Pitaya 前面板的两个模拟输出口 |
| negative-slope | Red Pitaya ADC 原始数据的一种格式，最高位保留、低 13 位取反后就变成 signed two's complement |
| ODDR | FPGA 里的 DDR 输出单元，把数据按 DAC 芯片需要的高速时序送到引脚。**绝对不能乱改** |
| dac_a_sum / dac_b_sum | 官方 top 里 ASG 和 PID 的输出求和结果。自定义 `error_o` 将来要接入这里（saturation 之前） |

## 5. 项目自定义信号

| 术语 | 大白话 |
|---|---|
| pd_i | 你的 `laser_lock_core` 的 PD 光电探测器信号输入，来自 `adc_dat[0]`，14-bit signed |
| ref_i | 你的 `laser_lock_core` 的参考信号输入，来自 `adc_dat[1]`，14-bit signed |
| error_o | 你的 `laser_lock_core` 的解调误差信号输出，送到 OUT1，14-bit signed |
| control_o | 你的 `laser_lock_core` 的控制量输出，第一阶段固定为 0，14-bit signed |
| clk_i | 你的模块用的时钟，接 `adc_clk` |
| rstn_i | 你的模块用的复位，接 `adc_rstn`，active-low |

## 6. Vivado 操作

| 术语 | 大白话 |
|---|---|
| Vivado | Xilinx FPGA 开发软件，用来综合、布线、生成 bitstream |
| Synthesis / 综合 | 把 Verilog 代码翻译成 FPGA 内部逻辑单元 |
| Implementation / 实现 | 把逻辑单元放进具体 FPGA 位置并布线 |
| Bitstream / .bit 文件 | 可以加载到 FPGA 板子上的最终配置文件 |
| xvlog | Vivado 仿真器的编译命令 |
| xelab | Vivado 仿真器的 elaboration 命令 |
| xsim | Vivado 仿真器的运行命令 |
| XDC / SDC | 约束文件，定义引脚映射和时序要求。**新手不要乱改** |

## 7. 实验相关

| 术语 | 大白话 |
|---|---|
| PD / Photodetector | 光电探测器，把光信号变成电信号 |
| EOM | Electro-Optic Modulator，电光调制器，用来给激光加调制 |
| MTS | Modulation Transfer Spectroscopy，调制转移光谱，本项目的实验方法 |
| error signal / 误差信号 | mixer + LPF 之后得到的低频信号，送给 D2-125 做伺服控制 |
| D2-125 | 实验中使用的伺服控制器模块 |
| mixer / 混频器 | 把两个信号相乘的电路。模拟 mixer 是硬件芯片，数字 mixer 是 FPGA 里的乘法器 |
| LPF / 低通滤波器 | 让低频通过、阻挡高频的滤波器 |
| BPF / 带通滤波器 | 只让某一频率范围通过的滤波器 |

## 8. 你现在只需要记住

读到不懂的词，回到这个表查。查不到的发给我或者 GPT。
