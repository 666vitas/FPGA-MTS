# LESSON_v1ab_passthrough_debug

## 0. 本版本一句话目标

v1ab 不是 MTS error。

v1ab 的目标是验证 Red Pitaya 的最小输入输出链路：

```text
IN1 -> ADC -> FPGA core -> DAC -> OUT1
```

也就是说，本版本先不追求“激光稳频误差信号”，而是先回答一个最基础的问题：

> 一个安全的小信号从 Red Pitaya IN1 输入后，能不能经过 FPGA 内部逻辑，再从 OUT1 输出？

如果这个问题没有验证通过，后面的 mixer、LPF、BPF、PID、sweep 和 AI 都没有可靠基础。

当前最新状态：

```text
v1ab RTL 已生成。
testbench 已通过。
Vivado synthesis / implementation / bitstream 已成功。
.bit 已转换为 .bit.bin。
.bit.bin 已上传到 Red Pitaya。
fpgautil -b /root/red_pitaya_top.bit.bin 已加载成功。
终端显示 BIN FILE loaded through FPGA manager successfully。
当前还没有实际接信号发生器和示波器完成物理测试。
```

所以当前下一步不是写 mixer，而是做 `v1ab IN1 -> OUT1` 实验验证。

## 1. 它对应 MTS 实验链路的哪一段

最终希望实现的 MTS 调制转移光谱数字链路是：

```text
PD -> BPF -> gain -> mixer -> LPF -> error -> D2-125
```

在真实实验里，PD 信号代表光电探测器输出，REF 是 4.6 MHz 调制参考，mixer 和 LPF 共同产生 error signal，最后 error signal 送入 D2-125 或后续数字 PID。

但 v1ab 只验证最前面和最后面的硬件通路：

```text
PD/信号输入 -> IN1 -> FPGA -> OUT1
```

也可以理解为：

```text
信号发生器模拟 PD -> Red Pitaya IN1 -> FPGA passthrough -> Red Pitaya OUT1 -> 示波器
```

当前不做：

- mixer；
- LPF；
- BPF；
- PID；
- sweep；
- AI；
- D2-125 接入。

这一步的实验意义是：先确认 Red Pitaya 的 ADC 输入、FPGA 内部连线、DAC 输出和 bitstream 加载链路是活的。

v1 最终目标会继续走向：

```text
PD -> IN1
REF 4.6 MHz -> IN2

adc_dat[0] -> DC remove / digital BPF / gain
adc_dat[1] -> REF input / optional phase adjustment
mixer -> LPF -> output scaling / limit -> error_o -> OUT1
```

但这不是 v1ab。v1ab 只验证 `adc_dat[0]` 和 `adc_dat[1]` 这两路输入候选是否能从 OUT1 看见。

## 2. v1ab 的 FPGA 数据通路

v1ab 的 IN1 到 OUT1 数据通路可以画成：

```text
IN1
  -> ADC
  -> adc_dat[0]
  -> laser_lock_core.pd_i
  -> error_o
  -> dac_a_sum
  -> 官方 DAC saturation
  -> signed-to-unsigned / negative-slope conversion
  -> ODDR
  -> OUT1
```

逐个解释：

`IN1`

这是 Red Pitaya 前面板的模拟输入接口。信号发生器输出的 1 kHz、100 mVpp 正弦波接到这里。

`ADC`

ADC 是 analog-to-digital converter，也就是模数转换器。它把 IN1 上连续变化的模拟电压，转换成 FPGA 里可以处理的数字采样值。

`adc_dat[0]`

这是官方 top 里表示 ADC 第 0 路数据的信号。当前项目把它当作 IN1 的候选数字数据。它不是电压本身，而是电压经过 ADC 采样后的 signed 14-bit 数字量。

`laser_lock_core.pd_i`

这是 `laser_lock_core.sv` 的 PD 输入端口。v1ab 里，`pd_i` 接收 `adc_dat[0]`。名字叫 PD，是因为未来真实实验中 IN1 会接 PD 信号；但现在第一次测试时，用信号发生器来模拟这个输入。

`error_o`

这是 `laser_lock_core` 输出给外部的 error 信号。v1ab 里它还不是真正的 MTS error，只是把 `pd_i` 或 `ref_i` 透传出来，用来验证通路。

`dac_a_sum`

这是进入 DAC A，也就是 OUT1 路径前的一个内部求和信号。官方工程原来会把 ASG 和 PID 的数据加到这里。v1ab 里，在 `USE_LASER_LOCK_CORE=1` 时，把 `laser_error` 接入 `dac_a_sum`，让 OUT1 输出 FPGA core 的结果。

`官方 DAC saturation`

DAC 后级有官方已有的限幅逻辑。它的作用是避免内部数值超出 DAC 可以表达的范围。v1ab 不重写这段官方结构，而是尽量沿用它。

`signed-to-unsigned / negative-slope conversion`

Red Pitaya 官方 DAC 路径里有符号数到 DAC 输出格式的转换，还包含板级 DAC 的极性处理。新手要记住：FPGA 内部的 signed 数字，不会直接等于 BNC 上看到的电压，后面还有格式和极性转换。

`ODDR`

ODDR 是 FPGA 里用于高速输出的专用资源。DAC 数字数据最后通过这类高速 IO 结构送到板上的 DAC 芯片。v1ab 不修改 ODDR。

`OUT1`

这是 Red Pitaya 前面板的模拟输出接口。第一次实验时，OUT1 只接示波器，不接 D2-125，不接激光器反馈。

## 3. 新手必须理解的 FPGA 概念

1. FPGA 不是运行 Python

Python 是一条语句一条语句执行的程序。FPGA 不是这样工作。FPGA 是把你的 Verilog 变成硬件电路。配置完成后，很多逻辑是并行存在、同时工作的。

2. Verilog 描述的是硬件连接

Verilog 不是在写“软件流程”，而是在描述寄存器、组合逻辑、选择器、加法器、乘法器、连线这些硬件结构。比如一个 `assign` 可能对应一组真实的 FPGA 连线和 LUT。

3. `assign` 在硬件上是什么意思

例如：

```systemverilog
assign control_o = 14'sd0;
```

它不是“运行时给变量赋值一次”，而是把 `control_o` 这 14 根输出线固定接到数字 0。只要 FPGA 正在工作，这个连接就一直存在。

4. signed 14-bit 是什么

Red Pitaya ADC/DAC 数据常用 14-bit 有符号数表示。signed 14-bit 可以表示正数、负数和 0。它不是十进制电压，而是电压采样后的数字编码。正负号对应输入信号相对 0 V 的方向。

5. ADC 输入为什么变成数字量

FPGA 不能直接处理模拟电压。IN1 上的电压必须先经过 ADC，变成每个时钟周期更新一次的数字采样值，FPGA 才能做滤波、乘法、PID 等数字处理。

6. DAC 输出为什么不是直接 `assign` 到 BNC

OUT1 是模拟输出，它来自板上的 DAC 芯片。FPGA 需要先把内部 signed 数字送入官方 DAC 数据路径，再经过限幅、格式转换、高速输出接口和 DAC 芯片，最后才变成 BNC 上的模拟电压。

7. clock / reset 为什么重要

clock 决定寄存器什么时候更新，reset 决定系统上电或复位时进入什么初始状态。没有稳定时钟，数字逻辑不会按预期工作；没有可靠 reset，输出可能从未知状态开始。

8. bitstream 是什么

bitstream 是 Vivado 根据 Verilog 和约束生成的 FPGA 配置文件。它告诉 FPGA 内部的 LUT、触发器、连线、IO 资源应该如何连接，最终形成你设计的硬件。

9. `bit.bin` 加载后为什么断电会丢失

通过 `fpgautil` 加载的 FPGA 配置通常是临时加载到 FPGA 配置存储中的。Red Pitaya 断电或重启后，FPGA 会失去这次配置，需要重新加载 `bit.bin`。

10. 为什么 v1ab 通过后才能做 mixer

mixer 要同时依赖 PD 输入、REF 输入、FPGA 乘法逻辑和 DAC 输出。若 IN1/IN2 或 OUT1 基础通路不通，mixer 即使写对了，也无法判断问题出在乘法器还是板级输入输出链路。

## 4. 本版本涉及哪些代码文件

### `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv`

它是干什么的：

这是 Red Pitaya FPGA 工程的顶层文件，可以理解成“总接线板”。ADC、DAC、PLL、PS、AXI、官方模块和 `laser_lock_core` 都在这里连接。

我必须看懂哪里：

- `USE_LASER_LOCK_CORE`；
- `LASER_LOCK_OUTPUT_MODE`；
- `adc_dat[0]` 如何接到 `pd_i`；
- `adc_dat[1]` 如何接到 `ref_i`；
- `i_laser_lock_core` 实例；
- `laser_error` 如何进入 `dac_a_sum`；
- `dac_b_sum` 目前保持官方路径。

哪些地方暂时可以不懂：

- PS/AXI/DDR；
- XADC/AMS；
- PLL 细节；
- ODDR 细节；
- 官方示波器和信号发生器模块的完整内部结构。

哪些地方千万不要改：

- ADC IO；
- PLL / BUFG；
- ODDR；
- `dac_dat_o` / `dac_wrt_o` / `dac_sel_o` / `dac_clk_o` / `dac_rst_o`；
- PS/AXI/DDR；
- XDC/约束相关引用。

### `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv`

它是干什么的：

这是项目自己的核心模块。未来 BPF、mixer、LPF、PID 等数字稳频功能会逐步放到这个方向上。v1ab 里它只做 passthrough debug。

我必须看懂哪里：

- `pd_i` 是 PD/IN1 数据输入；
- `ref_i` 是 REF/IN2 数据输入；
- `error_o` 是输出给 OUT1 路径的信号；
- `control_o` 未来可能用于 OUT2/PID 控制，但 v1ab 固定为 0；
- `OUTPUT_MODE=0` 选择 `pd_i`；
- `OUTPUT_MODE=1` 选择 `ref_i`。

哪些地方暂时可以不懂：

- 以后 mixer 和滤波器怎么写；
- 定点乘法缩放；
- PID 控制。

哪些地方千万不要改：

- 当前已经通过 bitstream 的 v1ab 逻辑；
- 端口名；
- 位宽；
- reset/enable 的基本行为。

### `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv`

它是干什么的：

这是输出保护模块。v1ab 里它的功能很简单：reset 或未使能时输出 0，使能后输出输入数据。

我必须看懂哪里：

- `clk_i` 是寄存器更新的时钟；
- `rstn_i` 是低有效复位；
- `enable_i` 为 0 时输出 0；
- `data_i` 通过寄存器到 `data_o`。

哪些地方暂时可以不懂：

- 未来更复杂的限幅、斜率限制、软启动保护。

哪些地方千万不要改：

- reset 时输出 0 的安全行为；
- 位宽；
- 时钟域。

### `E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_laser_lock_core_v1ab.sv`

它是干什么的：

这是 v1ab 的 testbench，用来在仿真里验证 `laser_lock_core` 的基本行为。

我必须看懂哪里：

- 它分别测试 `OUTPUT_MODE=0` 和 `OUTPUT_MODE=1`；
- 它检查 reset 后输出是否为 0；
- 它检查 `pd_i` 是否能到 `error_o`；
- 它检查 `ref_i` 是否能到 `error_o`；
- 它检查 `control_o` 是否固定为 0。

哪些地方暂时可以不懂：

- testbench 的完整 SystemVerilog 写法；
- 仿真器命令；
- 后续更复杂的波形自检。

哪些地方千万不要改：

- 已经用于说明 v1ab 行为的基本检查；
- 与 RTL 端口对应的连接。

## 5. 逐段解释 v1ab 代码逻辑

1. `OUTPUT_MODE = 0` 时为什么是 `pd_i -> error_o`

`OUTPUT_MODE=0` 表示当前选择 PD 输入路径。由于 `pd_i` 在 top 中接的是 `adc_dat[0]`，而 `adc_dat[0]` 对应 IN1 候选数据，所以这时的目标是：

```text
IN1 -> adc_dat[0] -> pd_i -> error_o -> OUT1
```

这不是在产生 error signal，而是在检查 IN1 输入通路能不能走到 OUT1。

2. `OUTPUT_MODE = 1` 时为什么是 `ref_i -> error_o`

`OUTPUT_MODE=1` 表示当前选择 REF 输入路径。由于 `ref_i` 在 top 中接的是 `adc_dat[1]`，所以这时目标变成：

```text
IN2 -> adc_dat[1] -> ref_i -> error_o -> OUT1
```

这一步通常放在 IN1 测试通过之后，用来确认未来外部 4.6 MHz REF 从 IN2 进入 FPGA 的路径是否正常。

3. `control_o = 14'sd0` 在硬件上是什么意思

`control_o` 未来可能用于 PID 控制输出，也可能走 OUT2 方向。但 v1ab 不做 PID，所以把它固定为 0。

硬件上，这等价于把 `control_o` 的 14 根线固定接到 0。这样做的好处是：OUT2 或未来控制路径不会输出不可预期的控制量。

4. `output_protect` 为什么 reset 时输出 0

板子上电、加载 bitstream、复位释放之前，内部寄存器可能处于不确定状态。对激光稳频系统来说，不确定输出是危险的。

所以 `output_protect` 在 reset 时输出 0，意思是先把输出压到安全状态，等系统正常工作后再输出输入数据。

5. 为什么现在不做 saturation

v1ab 的任务是验证通路，不是做最终保护策略。官方 DAC 路径后面已经有原有 saturation 结构，本版本尽量保留官方路径，不在 `laser_lock_core` 里增加新的限幅逻辑。

这样可以减少变量：如果 OUT1 没信号，我们优先排查输入、top 连接、bitstream、DAC 路径，而不是同时怀疑一个新写的复杂限幅模块。

6. 为什么 `error_o` 接到 `dac_a_sum`，而不是 `dac_dat_o`

`dac_dat_o` 是靠近 FPGA IO 和 DAC 芯片的低层高速输出信号，后面关系到 ODDR、DAC 时钟、数据格式和板级接口。

v1ab 不直接改 `dac_dat_o`，而是把 `error_o` 接到更上游的 `dac_a_sum`，让它继续经过官方已有的 DAC saturation、格式转换和 ODDR 输出结构。

这是一种更保守的接入方式：只改项目需要接入的位置，尽量不碰官方高速 DAC 后级。

## 6. Vivado 已经完成了什么

1. Add Sources 是什么

Add Sources 是把设计文件加入 Vivado 工程的 Sources 列表。文件存在于磁盘目录中，不代表 Vivado 会综合它。只有 Vivado 工程 Sources 里能看到的设计文件，才会参与综合。

2. Run Synthesis 做了什么

Run Synthesis 是把 SystemVerilog/Verilog 设计转换成 FPGA 可以实现的硬件网络，例如 LUT、触发器、加法器、选择器、DSP 等。若 Synthesis 失败，通常说明代码语法、模块连接、端口、位宽或综合规则有问题。

3. Run Implementation 做了什么

Run Implementation 是把综合后的硬件网络放到具体 FPGA 资源上，并完成布局布线。它要决定每个逻辑单元放在哪里、信号线怎么连、时序能不能满足。

4. Generate Bitstream 做了什么

Generate Bitstream 是把 Implementation 的结果转换成 FPGA 配置文件。这个文件加载到 FPGA 后，FPGA 内部才会真的变成我们设计的硬件。

5. 为什么 bitstream 成功不代表实验一定成功

bitstream 成功只能说明 Vivado 能把设计变成 FPGA 配置，并且实现阶段没有阻塞性错误。它不能证明外部接线正确、输入信号安全、示波器设置正确，也不能证明 OUT1 上一定有你想看的波形。

6. 为什么还需要示波器验证

FPGA 最终服务的是实验链路。示波器是连接“数字设计”和“真实模拟世界”的检查工具。只有示波器看到 OUT1 上有正确频率的波形，才能说明 v1ab 的板级输入输出链路真正通过。

## 7. `bit.bin` 加载到板子意味着什么

命令：

```bash
fpgautil -b /root/red_pitaya_top.bit.bin
```

意思是让 Red Pitaya Linux 系统通过 FPGA manager，把 `/root/red_pitaya_top.bit.bin` 这个 FPGA 配置文件加载到 FPGA 里。

终端显示：

```text
BIN FILE loaded through FPGA manager successfully
```

说明 FPGA 已经临时加载了这份配置。这里的“临时”很重要：它表示当前通电状态下 FPGA 已经按这份 bitstream 工作，但断电或重启后通常会丢失，需要重新执行 `fpgautil`。

测试期间不要打开可能重新配置 FPGA 的官方网页应用。某些 Red Pitaya 官方应用会加载自己的 FPGA bitstream，一旦覆盖当前配置，你刚刚加载的 v1ab 设计就不再运行。

## 8. 现在还没测试时，我应该做什么

测试前检查清单：

- 板子继续通电；
- 不打开官方网页应用；
- 不接 D2-125；
- 不接真实 PD；
- 不接 EOM；
- 不接激光器反馈；
- 只接信号发生器和示波器；
- 确认信号发生器参数安全；
- 确认信号发生器输出先在示波器上看过；
- 确认 OUT1 先只接示波器 CH1。

这一步的原则是：先用最简单、最安全、最可控的信号证明通路，再进入真实实验信号。

当前必须按下面顺序做：

```text
Step 1: v1ab-1 IN1 -> OUT1
Step 2: v1ab-2 IN2 -> OUT1
Step 3: 两步都通过后，才进入 v1c_mixer_only
```

## 9. v1ab 第一次实验：IN1 -> OUT1

这是当前马上要做的 Step 1。

接线：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

信号发生器参数：

```text
waveform: sine
frequency: 1 kHz
amplitude: 100 mVpp
offset: 0 V
```

示波器建议：

```text
CH1: OUT1
CH2: 输入参考
触发源: CH2
时间尺度: 200 us/div 或 500 us/div
电压尺度: 50 mV/div 或 100 mV/div
```

为什么用 1 kHz：

1 kHz 很慢，示波器容易看，线缆和带宽要求低，也不会混入 4.6 MHz REF、mixer 或滤波器等后续复杂因素。

为什么用 100 mVpp：

这是一个保守的小信号，适合第一次验证输入输出链路。第一步不要追求大幅度，先确认有无、频率和基本形状。

## 9.1 v1ab 第二次实验：IN2 -> OUT1

只有 `IN1 -> OUT1` 已经通过，才做这一步。

需要重新设置：

```text
LASER_LOCK_OUTPUT_MODE = 1
```

并重新：

```text
Generate Bitstream
转 .bit.bin
scp 上传
fpgautil 加载
```

接线：

```text
4.6 MHz REF 安全幅度 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF 同时 -> 示波器 CH2
```

信号：

```text
4.6 MHz sine
建议先 100 mVpp 到 500 mVpp
0 V offset
不要第一次就直接 ±1 V
严禁 6.32 Vpp 直接进 IN2
```

目的：

```text
证明 REF 能进入 FPGA，后续 mixer 有参考输入。
```

## 10. 示波器上应该看到什么

成功现象：

- OUT1 上有 1 kHz 同频波形；
- CH1 和 CH2 频率一致；
- 波形不是一直贴在上限或下限。

允许出现：

- 幅度不同；
- 反相；
- 有延迟；
- 有噪声；
- 波形比输入略有变形。

这些现象不一定代表失败。因为 ADC/DAC 路径、官方 DAC 极性、格式转换和板级模拟链路都可能引入比例、极性和延迟变化。

失败现象：

- OUT1 没信号；
- OUT1 是固定直流；
- OUT1 直流顶死；
- OUT1 严重削顶；
- OUT1/OUT2 都没反应。

如果失败，不要立刻改代码。先按照下一节分层排查。

## 11. 如果没有信号，如何分层排查

### 1. bitstream 加载问题

检查：

- Red Pitaya 是否仍然通电；
- 是否执行过 `fpgautil -b /root/red_pitaya_top.bit.bin`；
- 终端是否显示 `BIN FILE loaded through FPGA manager successfully`；
- 加载之后是否重启过或断电过；
- 是否打开过可能覆盖 FPGA 的官方网页应用。

判断：

如果断电、重启或打开官方应用，当前 FPGA 里可能已经不是 v1ab bitstream，需要重新加载。

### 2. Vivado 版本/bit 文件问题

检查：

- 当前加载的 `.bit.bin` 是否来自 v1ab 最新成功的 bitstream；
- 是否误加载了 `USE_LASER_LOCK_CORE=0` 的回退 bitstream；
- `LASER_LOCK_OUTPUT_MODE` 是否为 0；
- 文件名和生成时间是否与本次工程一致。

判断：

如果 bit 文件不是当前 v1ab 的 `USE_LASER_LOCK_CORE=1`、`LASER_LOCK_OUTPUT_MODE=0` 版本，即使加载成功，也不会得到预期 IN1 -> OUT1 行为。

如果正在测试 `IN2 -> OUT1`，则要确认加载的是重新生成后的 `LASER_LOCK_OUTPUT_MODE=1` 版本。

### 3. 代码/参数问题

检查：

- `USE_LASER_LOCK_CORE = 1'b1`；
- `LASER_LOCK_OUTPUT_MODE = 0`；
- `laser_lock_core.sv` 和 `output_protect.sv` 已加入 Vivado Sources；
- `i_laser_lock_core` 出现在 `red_pitaya_top` 层级下；
- `error_o` 进入 DAC A 路径；
- DAC B 保持官方路径。

判断：

代码参数错误通常表现为 bitstream 能加载，但 OUT1 不是预期通路。此时要先查参数和 Vivado Sources，不要直接进入 v1c。

### 4. Red Pitaya 板子/IP/SSH 问题

检查：

- SSH 是否还能连接；
- 板子 IP 是否正确；
- 电源是否稳定；
- Red Pitaya 是否异常重启；
- Linux 终端是否还能执行命令。

判断：

如果板子掉线或重启，FPGA 配置可能丢失，实验现象也会消失。

### 5. 信号发生器/示波器接线问题

检查：

- 信号发生器输出是否真的打开；
- CH2 是否能看到输入参考；
- 信号发生器 OUT 是否接到 IN1；
- OUT1 是否接到 CH1；
- BNC 线是否正常；
- 示波器是否 AC/DC 耦合设置合适；
- 示波器触发源是否选 CH2；
- 电压档和时间档是否合理。

判断：

如果 CH2 都看不到 1 kHz 输入，说明问题不在 FPGA，而在信号发生器、线缆或示波器设置。

### 6. 实验物理信号问题

当前 v1ab 第一次测试不接真实 PD、不接 EOM、不接 D2-125、不接激光器反馈，所以理论上不应该把失败归因于 MTS 物理信号。

只有后续接入真实 PD/REF 时，才需要检查：

- PD 是否有光；
- MTS 调制是否存在；
- 4.6 MHz REF 幅度是否安全；
- 扫频是否打开；
- 光路是否在正确工作点附近。

## 12. 本版本学完后我应该掌握什么

完成 v1ab 后，你应该能够：

1. 解释 IN1 上的模拟电压如何通过 ADC 进入 FPGA；
2. 解释 `adc_dat[0]` 和 `pd_i` 的关系；
3. 解释 `error_o` 为什么走 DAC A / OUT1；
4. 解释 Vivado 的 Synthesis、Implementation、Generate Bitstream 三步分别做什么；
5. 解释 `bit.bin` 为什么断电或重启后会丢失；
6. 独立完成 IN1 -> OUT1 的示波器测试；
7. 判断 OUT1 没信号时应该先查 bitstream、参数、接线还是板子状态；
8. 说明为什么 v1ab 不是 MTS error；
9. 说明为什么不能一开始就接 D2-125；
10. 说明为什么 IN1/IN2 通过后才适合进入 mixer。

## 13. 进入 v1c 前的门槛

只有当以下两项都通过，才允许进入 `v1c_mixer_only`：

```text
v1ab IN1 -> OUT1 通过
v1ab IN2 -> OUT1 通过
```

IN1 -> OUT1 通过说明 PD 输入候选通路和 OUT1 输出通路基本正常。

IN2 -> OUT1 通过说明外部 REF 输入候选通路基本正常。

mixer 需要同时依赖 PD 和 REF。少验证任何一路，后续看到异常都很难判断问题来源。

当前答案很明确：

```text
现在不允许进入 v1c。
必须先完成 v1ab IN1->OUT1 和 IN2->OUT1。
```

## 14. 学习成果检查题

1. 为什么 v1ab 不是 MTS error？
2. 为什么不能直接接 D2-125？
3. 为什么 `error_o` 不直接驱动 `dac_dat_o`？
4. 为什么 OUT1 可能反相？
5. `.bit` 和 `.bit.bin` 有什么区别？
6. 为什么断电后需要重新执行 `fpgautil`？
7. 为什么 IN1 通过后还要测 IN2？
8. Vivado Synthesis 和 Implementation 有什么区别？
9. `output_protect` 的作用是什么？
10. 为什么进入 v1c 前必须先验证 IN1/IN2？

如果这些问题能用自己的话讲清楚，说明你不是只完成了一个 bitstream，而是真的掌握了 v1ab 这个阶段。

## 15. 给 GPT 审查的问题

建议把本次测试结果和以下问题发给 GPT 审查：

1. v1ab 的 IN1 -> OUT1 测试现象是否符合 passthrough debug 预期？
2. OUT1 幅度与输入不同是否正常，是否需要立刻标定？
3. 如果 OUT1 反相，是否符合 Red Pitaya DAC 官方路径的可能行为？
4. 如果 OUT1 有直流偏置，应该优先查 DAC 路径、示波器耦合，还是输入 offset？
5. 如果 IN1 通过、IN2 不通过，下一步应该检查 `LASER_LOCK_OUTPUT_MODE` 还是外部 REF 接线？
6. 是否可以在 IN1 -> OUT1 通过后立即测试 IN2 -> OUT1？
7. 进入 v1c 前，还需要补充哪些仿真或板级记录？
8. 当前是否仍应禁止接 D2-125？
9. 当前是否仍应禁止真实 PD、EOM 和激光器反馈接入？
10. v1c mixer 第一次上板是否应该先用低频同频信号，而不是直接 4.6 MHz？
