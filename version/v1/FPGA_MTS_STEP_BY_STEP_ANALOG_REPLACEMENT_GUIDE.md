# FPGA + MTS 逐器件数字替代实验指南

## 2026-06-10 Step 4 更新：FPGA PI/PID 替代 D2-125

当前 Step 4 明确为：

```text
Step 4：FPGA PI/PID 替代 D2-125
```

Step 4 之前不再继续强推替代 `ZFL-500LN+`。当前主线是替代 `D2-125` 的基本 servo 功能，而不是替代全部模拟前级。

当前顺序：

1. 保留 `PD -> BPF -> ZFL -> ADC` 最小可用前级；
2. 使用已验证的 `FPGA mixer+LPF` 产生 error-like signal；
3. 先完成 `v2a/v2b/v2c`，只仿真或只接示波器；
4. 只有 `v2c` 通过后，才允许进入 `v2d` 低增益短时间闭环；
5. `digital gain` 只做幅度匹配和 DAC 输出缩放，不能替代 ADC 前低噪声放大。

## 2026-06-09 论文目标同步：先锁得住，再谈全自动优化

目标报告给出的研究方向是“全自动数字稳频参数优化”，但这不是让 AI 现在直接接管实验。更稳的路线是：

```text
FPGA 快速确定性内环
  -> 先产生可用 error signal
  -> 再接 D2-125 验证可锁性
  -> 再做 FPGA PID
  -> 再做自动重锁 FSM
  -> 最后做 AI 慢速监督调参
```

当前已经完成的是：

- `mixer_core` 等效 `ZFM-3+ mixer`；
- `lpf_core` 等效 mixer 后低频提取；
- 真实链路下已经看到 FPGA OUT1 error-like signal；
- `FPGA OUT1 -> D2-125` 后级响应已经看到约 `3.42 Vpp`。

当前还没有完成的是：

- 闭环锁定；
- FPGA PID；
- 自动重锁；
- 数据集 benchmark；
- AI 参数优化。

所以当前最小下一步是执行 `v1i_D2-125` 安全接入 SOP，而不是直接替代前级 BPF / 放大器，也不是直接写 AI。

## 2026-06-09 当前实现状态更新

当前已经实现：

- FPGA 替代 `ZFM-3+ mixer + mixer 后 LPF / 低频提取`；
- FPGA OUT1 可以作为 `D2-125 error input` 的候选信号；
- FPGA 直接输出基准约 `160 mVpp`；
- 三通/并联 REF 条件下 FPGA OUT1 可能下降到约 `30-120 mVpp`，该现象受 REF 分配、负载、相位和接线影响；
- D2-125 后级对 FPGA error signal 有明显响应，CH3 约 `3.42 Vpp`。

当前仍未实现：

- FPGA PID；
- 闭环锁定；
- 自动锁定；
- AI 优化；
- 完整替代 `D2-125`；
- 替代前级 BPF / `ZFL-500LN+`。

当前判断：

FPGA error-like signal 已经具备进入 `D2-125` 安全接入前置验证的价值，但还没有完成 FPGA 锁定。下一步不是直接闭环，也不是 PID/AI，而是确认 D2-125 输入安全、后级响应、极性、offset、削顶、噪声和多次扫描重复性。

本文是从当前 `v1c 已通过` 到后续完整 FPGA-MTS 稳频链路的总路线图。它的写法按“老师上课”的方式来：先看真实模拟链路，再看 FPGA 想替代什么，最后按阶段一个器件、一个功能地替代。

核心原则只有一句：

```text
每一版只替代一个明确的模拟链路位置，并且必须能用示波器证明这个位置确实工作。
```

当前允许做的是文档和后续开发准备；本文不修改 RTL，不运行 Vivado，不生成 bitstream，不上板。

## 1. 当前真实模拟链路

当前实验台真实 MTS 模拟链路应按下面顺序理解：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ RF amplifier
  -> ZFM-3+ mixer
  -> mixer 后 LPF / 后级带宽
  -> MTS error
  -> D2-125 Servo
  -> Laser
```

这条链路不是“随便串了几个盒子”。每个器件都解决一个很具体的问题。

### 1.1 PD

PD 是 photodetector，把光强变化变成模拟电压。对 MTS 来说，PD 输出里可能包含：

- 原子光谱背景；
- 扫描带来的慢变化；
- 噪声；
- 与调制相关的 `4.6 MHz` 分量；
- 其他高频杂散。

FPGA 不能凭空制造出好信号。如果 PD 里 `4.6 MHz` 分量很弱，或者在进入 ADC 前已经被噪声淹没，后面的数字处理只能把“信号和噪声一起处理”。

### 1.2 10 MHz LPF

`10 MHz LPF` 是 mixer 前的低通滤波器。它的作用是保留 `4.6 MHz` 附近的目标分量，同时压掉更高频的无用噪声。

对小白来说，可以这样想：

```text
10 MHz LPF 是进入 mixer 前的“高频垃圾拦截器”。
```

它不是 v1d 要做的 mixer 后 LPF。不要把这两个 LPF 混在一起。

### 1.3 1.8 MHz HPF

`1.8 MHz HPF` 是 mixer 前的高通滤波器。它的作用是去掉 DC、慢漂移和低频背景，同时让 `4.6 MHz` 通过。

`10 MHz LPF + 1.8 MHz HPF` 级联后，等效成一个大概的 pre-mixer BPF：

```text
1.8 MHz 到 10 MHz 的带通窗口
```

这个窗口的意义是：让 `4.6 MHz` 调制分量更突出地进入后级 mixer。

### 1.4 ZFL-500LN+ RF amplifier

`ZFL-500LN+` 是 Mini-Circuits 的 RF amplifier。当前记录中它的典型增益约 `24 dB`，换成电压增益约：

```text
10^(24/20) ≈ 15.8x
```

它的位置在 ADC / 模拟 mixer 前，所以它改善的是“进入后级之前的模拟信号幅度”。这点很重要：

```text
FPGA digital gain 只能放大 ADC 已经采到的数值。
如果 ADC 前信号已经太小或 SNR 太差，digital gain 不能恢复丢掉的 SNR。
```

所以后续 `digital gain` 只能说是“等效幅度缩放”，不能说完全替代低噪声模拟前放。

### 1.5 ZFM-3+ mixer

`ZFM-3+` 是 Mini-Circuits 的 Level 7 double-balanced mixer。当前 REF 是 `4.6 MHz`。

它做的事情是：

```text
PD_RF x 4.6 MHz REF
```

如果 PD 中有与 `4.6 MHz` 同步的分量，乘法后会产生：

```text
低频/基带项 + 9.2 MHz 高频项
```

当前 `v1c_mixer_only` 已经用 FPGA 的 signed digital multiplier 初步替代了这个位置：

```text
pd_i x ref_i -> raw mixer output -> OUT1
```

### 1.6 mixer 后 LPF / 后级带宽

mixer 后 LPF 的任务和前面的 `10 MHz LPF` 完全不同。它是在混频之后，用来滤掉 `2f` 高频项。

对当前真实 `4.6 MHz` 链路来说：

```text
需要压低 2f = 9.2 MHz
保留低频 / 基带 / error-like 分量
```

这正是 `v1d_mixer_lpf` 要替代的位置。

### 1.7 MTS error

MTS error 不是“只要有波形就行”。优质 error signal 应该具有：

- 清晰过零点；
- 过零点附近斜率大；
- 噪声小；
- offset 小；
- 幅度合适；
- 不削顶；
- 对重复扫描可重复；
- 后续能被 servo 使用。

`v1d` 只能得到 error-like low-frequency signal，不能直接宣称得到最终 MTS error。

### 1.8 D2-125 Servo

D2-125 是后续接收 MTS error 的外部 servo / PID。当前它的输入范围、输入阻抗、极性和带宽仍需确认。

因此当前规则是：

```text
D2-125 参数未测清楚前，不允许接入。
```

### 1.9 Laser

Laser 是最终被控对象。只有当前面已经得到安全、可重复、可接 servo 的 error signal 后，才进入真正锁激光阶段。

当前 v1d 之前都只是在做电子链路和信号处理验证。

## 2. 目标数字链路

长期目标数字链路是：

```text
PD
  -> Red Pitaya ADC
  -> digital 10 MHz LPF
  -> digital 1.8 MHz HPF
  -> digital gain
  -> digital mixer
  -> post-mixer LPF
  -> phase / I-Q correction
  -> output scaling
  -> OUT1
  -> D2-125 或 FPGA PID
```

这条数字链路可以逐段映射到真实模拟链路：

| 真实模拟器件 / 功能 | 数字替代模块 | 说明 |
|---|---|---|
| PD 输出进入后级 | Red Pitaya ADC / `IN1` | 采样 PD 电压，必须保护输入量程 |
| 10 MHz LPF | `digital_10m_lpf` 或 BPF 上截止 | mixer 前滤波，保留 4.6 MHz |
| 1.8 MHz HPF | `digital_1p8m_hpf` 或 BPF 下截止 | mixer 前滤波，去低频背景 |
| ZFL-500LN+ | `digital_gain_core` | 只能做 ADC 后缩放，不能恢复 ADC 前 SNR |
| ZFM-3+ mixer | `mixer_core.sv` | v1c 已实现 raw digital mixer |
| mixer 后 LPF | `lpf_core.sv` / `post_mixer_lpf_core` | v1d 要做，提取低频/基带 |
| 相位调节 | `iq_core` / phase register | 后续优化 error 斜率和背景 |
| 输出幅度管理 | `output_scaling` / `output_protect` | 防止 OUT1 削顶或太小 |
| D2-125 | 外部 servo 接口 | 必须先测输入范围和极性 |
| FPGA PID | `pid_core` | v2 以后，error 稳定后才做 |
| AI 自动锁频 | PC/ARM/状态机 + 识峰算法 | v5 以后，不替代基本物理链路 |

这里要特别分清三个“滤波”：

```text
10 MHz LPF / 1.8 MHz HPF:
  在 mixer 前，目的是让 4.6 MHz 分量干净地进 mixer。

post-mixer LPF:
  在 mixer 后，目的是去掉 9.2 MHz，留下低频 error-like 分量。

servo/PID loop filter:
  在 error signal 之后，目的是让激光稳定闭环。
```

这三个不能混写进同一个 v1d。

## 3. 当前已完成阶段

### 3.0 当前最新观察：v1e-A 真实链路 FPGA mixer+LPF 初测

`v1e-A_real_chain_mixer_replacement` 已经在真实链路下观察到 FPGA OUT1 的 error-like signal。当前不是“完全通过”，而是“已观察到，需要继续验证”。

当前保留的模拟前级：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ RF amplifier
```

当前 FPGA 替代：

```text
ZFM-3+ mixer
  -> mixer 后低频提取
```

当前 FPGA 链路：

```text
IN1 = 模拟前级处理后的 PD 调制信号
IN2 = 与 EOM 同源的 4.6 MHz REF
OUT1 = mixer_core + lpf_core 后的 error-like signal
```

当前示波器记录，截图 / 文件标记为 `mix-lpf-dui2`：

| 通道 | 信号 | 当前观测 |
|---|---|---|
| CH1 | scan/ramp | 约 `48.913 Hz`，约 `14.1 mVpp` |
| CH2 | PD / 饱和吸收相关信号 | 约 `131 mVpp` |
| CH3 | analog error reference | 约 `80 mVpp` |
| CH4 | FPGA OUT1 error-like signal | 约 `160-170 mVpp`，图中读数约 `169 mV` |

这一步重要，是因为它说明真实 PD 调制信号经过模拟前级后，进入 FPGA mixer+LPF，可以产生随 scan 和谱线结构变化的 error-like 输出。同源 `4.6 MHz REF` 对稳定输出非常重要，因为同步解调依赖 EOM 调制和 REF 的稳定相位关系；不同源 REF 会带来相位漂移和误差信号“呼吸”。

### 3.0.1 v1e-A 与原模拟链路的幅度对照

当前 `v1e-A` 只替代：

```text
ZFM-3+ mixer
  -> mixer 后 LPF / 低频提取
```

模拟 BPF 和前级放大仍然保留：

```text
10 MHz LPF
1.8 MHz HPF
ZFL-500LN+ amplifier
```

对照实验记录：

```text
FPGA OUT1 error-like signal ≈ 0.16 Vpp
原模拟链路 error signal ≈ 1.57 Vpp
幅度比例 ≈ 1.57 / 0.16 ≈ 9.8
```

这说明 FPGA 已经能在真实链路下产生 error-like signal，但当前幅度明显小于原模拟链路。下一步不是 PID，也不是接 D2-125，而是先做：

1. REF 相位扫描；
2. REF 幅度扫描；
3. CH3 / CH4 形状、极性、过零点和斜率对比；
4. `v1g digital gain / output scaling` 方案设计。

`digital gain` 的作用是把 ADC 已经采到并解调出来的数字结果放大到更合适的 OUT1 幅度。它不能恢复 ADC 前已经丢失的信噪比，也不能替代相位优化。

当前仍需补充：IN1 依赖性测试、IN2/REF 依赖性测试、REF 幅度扫描、REF 相位扫描、CH4 与 CH2/CH3 的时间对应关系、幅度和稳定性评估。

下一步不是直接接 D2-125，而是做 `v1e-A` 补充验证和必要的 `v1e-debug`。当前仍不能声称已经得到最终可锁定 MTS error signal。

### 3.0.2 v1e-B 三基准对照后的路线修正

最新三基准对照：

| 基准 | 链路 | Vpp | 结论 |
|---|---|---:|---|
| A | 模拟 mixer 直接输出，不经过 D2-125 | `0.46-0.47 Vpp` | 噪声大，有过零点但不够干净 |
| B | D2-125 后级输出 / 原模拟系统参考输出 | `1.57-1.8 Vpp` | 噪声小、形状好、过零点清晰 |
| C | FPGA OUT1，`mixer_core -> lpf_core` | `0.16 Vpp` | 噪声小、形状好、过零点清晰 |

这个对照修正了路线判断：

1. FPGA 已经初步替代了 `ZFM-3+ mixer + mixer 后 LPF / 低频提取`；
2. FPGA 暂时没有替代 `10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+ 放大器`；
3. FPGA 还没有替代 `D2-125 PID / servo`；
4. D2-125 后级可能提供了增益、滤波、offset 调整、带宽限制或输出缩放；
5. 下一步不立刻替代前级滤波器和放大器；
6. 下一步优先做 `digital gain`、`REF phase / I-Q optimization`、`D2-125 safety input`、再到 `FPGA PID`。

最终目标从“只生成 error-like signal”提升为：

```text
用 FPGA 板子完成 MTS 激光锁定功能。
```

实现顺序是：

```text
FPGA 生成 error signal
  -> FPGA error signal 驱动 D2-125
  -> FPGA 内部 PID 替代 D2-125
  -> 自动寻峰 / 重锁 FSM
  -> AI 优化
```

### 3.1 v1ab：IN1/IN2 直通已完成

`v1ab` 已经完成两条基础链路：

```text
IN1 -> OUT1
IN2 -> OUT1
```

这说明：

- `IN1 / adc_dat[0] / pd_i` 可以进入 FPGA；
- `IN2 / adc_dat[1] / ref_i` 可以进入 FPGA；
- DAC A / `OUT1` 路径可用；
- 自定义 bitstream 加载后确实生效。

这一步像是在确认“水管通了”。没有这一步，后面 mixer、LPF 都无从谈起。

### 3.2 v1c：digital mixer 已完成

`v1c_mixer_only` 已经真实上板通过。

实验事实：

- `IN1 = 100 kHz sine`；
- `IN2 = 100 kHz sine`；
- `OUT1` 看到约 `200 kHz`；
- `OUT1` 约 `20-22 mVpp`；
- 拔掉 `IN1` 后，`OUT1` 消失；
- `4.6 MHz x 4.6 MHz` 也能看到混频输出波形。

这说明 FPGA 内部的 digital mixer 已经不是纸面设计，而是真实工作：

```text
pd_i x ref_i -> scaled raw mixer output -> OUT1
```

但 `v1c` 没有 LPF，所以输出中包含 DC/低频和 `2f` 高频项，还不是最终 error。

### 3.3 v1d：mixer 后 LPF 已完成信号源差频上板测试

`v1d` 的目标是：

```text
mixer_core 输出
  -> post-mixer LPF
  -> 保留低频/差频/基带分量
  -> 抑制 2f 高频分量
  -> OUT1
```

`v1d` 仍然不做：

- pre-mixer 10 MHz LPF；
- pre-mixer 1.8 MHz HPF；
- digital gain；
- I/Q；
- PID；
- D2-125；
- 激光器；
- AI。

已完成结果：

```text
100 kHz x 102 kHz -> OUT1 约 1.992 kHz，周期约 502 us，Vpp 约 68.3 mV
100 kHz x 101 kHz -> OUT1 约 1 kHz
```

为什么这证明 v1d 工作：

```text
100 kHz x 102 kHz 会产生 |102 kHz - 100 kHz| = 2 kHz 差频项；
100 kHz x 101 kHz 会产生 |101 kHz - 100 kHz| = 1 kHz 差频项。
```

OUT1 上看到这些差频，说明 `mixer_core` 后面的 `lpf_core` 已经在板子上保留低频差频项，并压制较高频和频项。

但这仍然不是最终 MTS error，因为输入是干净信号源，不是真实 PD 饱和吸收 / MTS 信号。下一阶段 `v1e` 才进入真实 PD + `4.6 MHz REF` 测试。

## 4. 逐阶段替代路线

### v1d：替代 mixer 后 LPF / 低频提取功能

替代对象：

```text
ZFM-3+ mixer 后面的 LPF / error extraction
```

为什么要做：

`v1c` raw mixer 已经证明乘法工作，但 raw mixer 输出一定包含高频项。例如：

```text
100 kHz x 100 kHz -> DC + 200 kHz
100 kHz x 101 kHz -> 1 kHz + 201 kHz
4.6 MHz x 4.6 MHz -> DC/低频 + 9.2 MHz
```

如果没有 LPF，OUT1 上看到的是混合波形，不是干净的低频 error-like signal。

FPGA 模块：

- 新增 `lpf_core.sv`；
- 在 `laser_lock_core.sv` 中新增 `OUTPUT_MODE=3`；
- 保留 `OUTPUT_MODE=0/1/2`；
- `OUTPUT_MODE=2` 用于 raw mixer；
- `OUTPUT_MODE=3` 用于 `mixer + LPF`。

推荐第一版 LPF：

```text
y[n] = y[n-1] + ((x[n] - y[n-1]) >>> LPF_SHIFT)
```

建议默认：

```text
LPF_SHIFT = 12
输入 signed 14-bit
内部 state 至少 signed 32-bit
输出 signed 14-bit saturation
```

Python 仿真：

- 用 Python 生成 `100 kHz` 和 `101 kHz` 正弦；
- 相乘得到 raw mixer；
- 对 raw mixer 做一阶 IIR；
- 观察频谱中 `1 kHz` 是否保留，`201 kHz` 是否下降；
- 再仿真 `4.6 MHz x 4.6 MHz`，观察 `9.2 MHz` 是否被压低。

RTL testbench：

- `tb_lpf_core.sv`；
- `tb_laser_lock_core_v1d.sv`；
- 覆盖 reset、enable、阶跃、高频输入、正负输入、saturation；
- 确认 `OUTPUT_MODE=0/1/2` 不被破坏；
- 确认 `OUTPUT_MODE=3` 是 raw mixer 后接 LPF。

上板测试：

- 先 `OUTPUT_MODE=2`，确认 raw mixer 还正常；
- 再 `OUTPUT_MODE=3`，看 LPF 是否生效；
- 第一组关键测试：`IN1=100 kHz`，`IN2=101 kHz`；
- 第二组真实频率方向测试：`IN1=4.6 MHz`，`IN2=4.6 MHz`。

通过标准：

- `OUTPUT_MODE=2` 下仍能看到 raw mixer 特征；
- `OUTPUT_MODE=3` 下 `201 kHz` 被明显压低，主要看到 `1 kHz`；
- `4.6 MHz x 4.6 MHz` 时，`9.2 MHz` 被压低，主要剩 DC/低频；
- OUT1 不削顶；
- reset 和 enable 安全；
- 输出可重复。

不能做什么：

- 不做 `10 MHz LPF`；
- 不做 `1.8 MHz HPF`；
- 不做 digital gain；
- 不做 I/Q；
- 不做 PID；
- 不接 D2-125；
- 不接激光器；
- 不做 AI。

### v1e：真实 PD + REF 初步解调

替代对象：

```text
真实 PD + 真实 4.6 MHz REF 进入已完成的 mixer + LPF 链路
```

为什么要做：

v1d 用信号发生器证明 `mixer + LPF` 的电子功能。但真实 MTS 系统中，PD 信号不是理想正弦，它可能有背景、噪声、offset、幅度变化和相位问题。

v1e 的目的不是马上做完美 error，而是问一个更朴素的问题：

```text
真实 PD 进 IN1，真实 REF 进 IN2，经过 mixer + LPF 后，OUT1 有没有像 error 的低频响应？
```

FPGA 模块：

- 沿用 `mixer_core.sv`；
- 沿用 `lpf_core.sv`；
- 不新增 pre-mixer BPF；
- 不新增 digital gain；
- 可保留 `OUTPUT_MODE=2/3` 对照。

Python 仿真：

- 如果已有真实 PD 采样数据，可离线做 `PD x REF -> LPF`；
- 没有真实数据时，先用“4.6 MHz 正弦 + 慢变化包络 + 噪声”模拟；
- 观察 LPF 后是否能保留慢变化。

RTL testbench：

- 不一定新增大模块；
- 可新增真实风格 stimulus；
- 验证有 offset、噪声、小幅信号时链路不溢出、不顶死。

上板测试：

- 先确认 PD 输出进入 Red Pitaya 前的 Vpp；
- 先确认 REF 进入 IN2 前的 Vpp；
- 两路都必须在 Red Pitaya 安全范围内；
- OUT1 只接示波器；
- 观察扫描时是否有低频 error-like 响应。

通过标准：

- OUT1 对激光扫描有可重复响应；
- 波形不是纯噪声；
- 改变 REF / PD 接线时响应有合理变化；
- OUT1 不削顶；
- 仍不接 D2-125。

不能做什么：

- 不因为看到一点波形就说“已经 MTS error 成功”；
- 不直接接 D2-125；
- 不做闭环；
- 不用 digital gain 掩盖输入太小的问题。

### v1f：替代 10 MHz LPF + 1.8 MHz HPF

替代对象：

```text
10 MHz LPF + 1.8 MHz HPF
```

这两个器件合起来是 pre-mixer BPF，不是 v1d 的 post-mixer LPF。

为什么要做：

真实模拟链路在 mixer 前先做滤波，是为了让 `4.6 MHz` 调制分量干净地进入 mixer。没有这个步骤，PD 里的低频背景和高频噪声都会进入 mixer，最后污染 error。

FPGA 模块：

- `pre_mixer_lpf_core`，对应 `10 MHz LPF`；
- `pre_mixer_hpf_core`，对应 `1.8 MHz HPF`；
- 或合并成 `pre_mixer_bpf_core`；
- 输入来自 `pd_i`；
- 输出送到 mixer 的 PD 路径。

Python 仿真：

- 先设计 125 MS/s 下的数字滤波器；
- 检查 `4.6 MHz` 处幅度损失；
- 检查 `1.8 MHz` 以下抑制；
- 检查 `10 MHz` 以上抑制；
- 检查相位延迟和群延迟。

RTL testbench：

- 输入多频信号：低频、`4.6 MHz`、高于 `10 MHz`；
- 验证低频被压制；
- 验证 `4.6 MHz` 被保留；
- 验证高频被压制；
- 检查 fixed-point 系数、位宽、saturation。

上板测试：

- 可先用信号源扫频；
- 测 `1 MHz`、`4.6 MHz`、`12 MHz`；
- 比较 BPF 开关前后的 OUT1 或内部调试输出；
- 不要同时改 gain 和 mixer，先单独验证滤波。

通过标准：

- `4.6 MHz` 通过；
- 低频背景明显下降；
- 高于 `10 MHz` 的成分下降；
- 输出不削顶；
- 引入的相位/延迟可记录。

不能做什么：

- 不把 pre-mixer BPF 当作 post-mixer LPF；
- 不同时打开 digital gain；
- 不直接用它证明 error signal 已经好。

### v1g：替代/等效 ZFL-500LN+ 放大器的幅度缩放

替代对象：

```text
ZFL-500LN+ RF amplifier 的幅度作用
```

为什么要做：

真实 ZFL-500LN+ 的典型增益约 `24 dB`，电压增益约 `15.8x`。FPGA 后续可能需要数字缩放，让进入 mixer 或 OUT1 的信号幅度更合适。

但是必须讲清楚：

```text
digital gain 只能放大 ADC 已经采到的数字值。
它不能替代 ADC 前低噪声模拟放大对 SNR 的帮助。
```

FPGA 模块：

- `digital_gain_core.sv`；
- gain 可选：`x1, x2, x4, x8, x16`；
- 必须有 saturation；
- 必须能 bypass。

Python 仿真：

- 模拟小信号 + 噪声；
- 比较 ADC 前模拟放大和 ADC 后 digital gain 的差别；
- 检查 gain 后是否削顶；
- 检查噪声也会被一起放大。

RTL testbench：

- 正负输入；
- 最大输入；
- gain 切换；
- saturation；
- bypass；
- reset。

上板测试：

- 先用信号源固定输入；
- 逐级打开 `x1/x2/x4/x8/x16`；
- 示波器观察 OUT1 幅度；
- 确认不削顶；
- 记录每一级 Vpp。

通过标准：

- gain 比例正确；
- 正负号正确；
- 不出现 wrap-around；
- saturation 可控；
- bypass 后恢复原信号。

不能做什么：

- 不声称 digital gain 已完全替代 ZFL-500LN+；
- 不在 PD 直入 ADC SNR 未测前取消模拟前放；
- 不用高 gain 掩盖输入链路问题。

### v1h：相位调节 / I-Q 解调

替代对象：

```text
模拟 mixer 中不可控或难精确调节的解调相位
```

为什么要做：

同一个 PD 信号和 REF 相乘，REF 相位不同，低通后的结果会不同。相位选得好，error signal 的过零斜率大；相位选得不好，可能混入吸收背景，或者斜率变小。

I/Q 解调的思路是同时做两路：

```text
I = PD x cos(wt) -> LPF
Q = PD x sin(wt) -> LPF
```

然后通过选择 I、Q 或它们的组合，找到最好的 error signal。

FPGA 模块：

- `nco_core` 或外部 REF 相位处理；
- `iq_mixer_core`；
- `i_lpf_core`；
- `q_lpf_core`；
- `phase_select` 或 `iq_combine`。

Python 仿真：

- 构造带相位差的 PD 信号；
- 扫 phase；
- 观察 error 斜率、offset、RMS noise；
- 找最佳 I/Q 组合。

RTL testbench：

- 验证 sin/cos 正交；
- 验证 I/Q 正负号；
- 验证 phase 改变会改变输出；
- 验证 I/Q 输出都不溢出。

上板测试：

- 使用稳定信号源；
- 扫 phase；
- 记录 OUT1 的 Vpp、offset、斜率；
- 后续真实 PD 下找最佳 zero-crossing。

通过标准：

- 相位可控；
- I/Q 输出符合预期；
- 存在可重复的最佳相位；
- 输出不削顶。

不能做什么：

- 不在 v1d 就引入 I/Q；
- 不把 I/Q 幅值 `sqrt(I^2+Q^2)` 直接当 MTS error，因为锁频通常需要带符号过零 error；
- 不在 phase 未稳定前接 servo。

### v1i：OUT1 到 D2-125 的安全接口

替代对象：

```text
把 FPGA OUT1 输出安全送入 D2-125 error input
```

为什么要做：

前面所有阶段都只是示波器验证。真正进入锁频前，必须让 D2-125 接收到幅度、offset、极性、带宽都合适的 error signal。

必须先测 D2-125：

- 输入范围；
- 输入阻抗；
- 极性；
- 带宽；
- 推荐 error 幅度；
- 是否允许 DC offset；
- 最大安全输入。

FPGA 模块：

- `output_scaling_core`；
- `offset_trim_core`；
- `polarity_select`；
- `output_protect`；
- 可能需要外部模拟衰减或滤波。

Python 仿真：

- 模拟不同 scaling、offset、polarity；
- 检查 servo 看到的 error 是否过零；
- 检查噪声和削顶。

RTL testbench：

- output scaling；
- offset；
- polarity；
- saturation；
- enable safety；
- reset 输出 0。

上板测试：

- 先 OUT1 接示波器；
- 再 OUT1 接假负载或高阻测量；
- 确认幅度和 offset 安全；
- 最后才考虑接 D2-125；
- 接入后先不开激光闭环，只观察 D2-125 输入响应。

通过标准：

- OUT1 幅度在 D2-125 安全范围；
- offset 可控；
- 极性明确；
- 没有削顶；
- D2-125 输入端看到的波形和示波器一致。

不能做什么：

- 不在 D2-125 参数未知时接入；
- 不直接把 raw mixer 或未缩放 error 接 D2-125；
- 不在没有示波器确认时闭环。

### v2：FPGA PID

替代对象：

```text
D2-125 Servo / PID 的一部分或全部功能
```

为什么要做：

如果后续希望 Red Pitaya 自己完成闭环控制，就需要 FPGA PID。但 PID 不是解调链路的第一步。没有稳定 error signal，PID 只会放大问题。

进入条件：

- error signal 已经稳定；
- 过零点清晰；
- offset 和极性明确；
- 输出幅度安全；
- 激光执行器接口已清楚；
- 已知道目标闭环带宽。

FPGA 模块：

- `pid_core.sv`；
- `integrator`；
- `kp/ki/kd` 参数；
- anti-windup；
- output limit；
- enable / reset / freeze。

Python 仿真：

- 简化 plant；
- 扫 PID 参数；
- 看阶跃响应和稳定性；
- 检查积分饱和。

RTL testbench：

- P/I/D 分量；
- 积分限幅；
- reset；
- enable；
- 输出限幅。

上板测试：

- 先用电子假 plant；
- 再接真实执行器；
- 从很小 gain 开始；
- 示波器监测 error 和 control。

通过标准：

- 不振荡；
- 不积分跑飞；
- 输出受限；
- 能降低 error；
- 可重复锁定。

不能做什么：

- 不在 v1d/v1e 阶段做；
- 不在 error 不稳定时做；
- 不把 PID 当作修复坏 error 的工具。

### v5：AI 自动锁频

替代对象：

```text
人工识峰、判断失锁、重新扫描、自动重锁的操作流程
```

AI 不替代基本物理链路。AI 不能替代：

- PD；
- 滤波；
- mixer；
- LPF；
- error signal；
- servo 稳定性。

AI 能做的是：

- 识别扫描谱线；
- 判断当前是否失锁；
- 自动寻找合适锁点；
- 自动调整扫描范围；
- 自动选择 I/Q 相位候选；
- 自动重锁；
- 记录实验状态。

进入条件：

- 已经能产生稳定、可重复的 error signal；
- 已经能安全接 servo；
- 已经有足够多扫描数据；
- 已经定义什么叫好锁、失锁、坏谱线。

FPGA / 软件分工：

- FPGA 做实时链路；
- PC/ARM 做慢速识别和策略；
- AI 不进入 125 MHz 实时闭环核心。

通过标准：

- AI 能正确识别谱线；
- 能判断锁定状态；
- 能在失锁后执行安全重锁流程；
- 不会输出危险控制量。

不能做什么：

- 不在没有 error signal 时做 AI；
- 不让 AI 直接控制危险输出；
- 不把 AI 当作跳过物理调试的捷径。

## 5. 每阶段实验记录模板

每次实验都应记录同一套字段，避免以后忘记当时到底接了什么、测了什么。

| 阶段 | 替代器件 | FPGA 模块 | 输入 | 输出 | 示波器设置 | 通过标准 | 风险 |
|---|---|---|---|---|---|---|---|
| v1d | mixer 后 LPF | `lpf_core.sv` | 双路信号源 `100 kHz/101 kHz`，后续 `4.6 MHz/4.6 MHz` | OUT1 | 先看 raw mixer，再看 LPF；1 kHz 用 `200 us/div` 量级，200 kHz 用 `1-2 us/div` 量级 | LPF 后主要看到 1 kHz，201 kHz/9.2 MHz 被压低 | LPF 太窄导致 1 kHz 也变小；输出太小看不到 |
| v1e | 真实 PD + REF 初步解调 | `mixer_core + lpf_core` | 真实 PD 到 IN1，安全 REF 到 IN2 | OUT1 | 低频扫描时看 error-like 响应；必要时 AC/DC 耦合都看 | OUT1 随扫描有可重复低频响应 | PD/REF 幅度不安全；噪声过大 |
| v1f | 10 MHz LPF + 1.8 MHz HPF | `pre_mixer_bpf_core` | 多频信号或真实 PD | BPF 后调试输出 / OUT1 | 扫频记录 Vpp | 4.6 MHz 保留，低频和高频被压制 | 与 post-mixer LPF 混淆；相位延迟未记录 |
| v1g | ZFL-500LN+ 幅度缩放 | `digital_gain_core` | 已采样信号 | gain 后输出 | 固定输入，逐档 gain | x1/x2/x4/x8/x16 比例正确且不 wrap | 数字增益放大噪声；削顶 |
| v1h | 相位 / I-Q | `iq_mixer_core` | PD + REF 或 NCO | I/Q 或组合输出 | 扫 phase，记录 offset/Vpp/斜率 | 找到可重复最佳相位 | 相位不同步；把幅值 R 误当 error |
| v1i | OUT1 到 D2-125 | `output_scaling + protect` | 已验证 error | OUT1 到示波器，后续到 D2-125 | 先示波器确认 Vpp/offset/极性 | 幅度、offset、极性、安全范围明确 | 未测 D2-125 参数就接入 |
| v2 | FPGA PID | `pid_core.sv` | 稳定 error | control output | 同时看 error/control | 闭环稳定，不振荡 | PID 掩盖坏 error；积分跑飞 |
| v5 | AI 自动锁频 | PC/ARM 策略 + 状态机 | 扫描谱线、error、锁定状态 | 参数建议或自动重锁动作 | 记录状态和结果 | 能识峰、判失锁、重锁 | AI 越过安全联锁 |

建议每次实验后追加：

```text
日期：
阶段：
bitstream / commit / 文件版本：
OUTPUT_MODE：
IN1 信号：
IN2 信号：
OUT1 观察：
示波器 time/div：
示波器 volt/div：
是否削顶：
是否可重复：
结论：
下一步：
```

## 6. v1d 立即执行实验指南

本节是 `v1d` 写完 RTL、仿真 PASS、Generate Bitstream 之后才允许执行的上板指南。当前本文只写指南，不上板。

### 6.1 如何设置 OUTPUT_MODE=2

`OUTPUT_MODE=2` 是 raw mixer 对照模式：

```text
OUT1 = mixer_core(pd_i, ref_i)
```

它的作用是确认 v1c 基线仍然正常。

典型 top 参数应类似：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 2;
```

注意：

- 改参数后必须重新综合、实现、生成 bitstream；
- 不能拿旧 bitstream 说新模式生效；
- 本任务当前不允许实际运行 Vivado。

### 6.2 如何设置 OUTPUT_MODE=3

`OUTPUT_MODE=3` 是 v1d 新增的 mixer + LPF 模式：

```text
OUT1 = lpf_core(mixer_core(pd_i, ref_i))
```

典型 top 参数应类似：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

切换到 `OUTPUT_MODE=3` 前，必须已经用 testbench 证明：

- `OUTPUT_MODE=0/1/2` 没坏；
- `OUTPUT_MODE=3` 的 LPF 行为正确；
- reset 后输出安全；
- saturation 正常。

### 6.3 IN1=100 kHz、IN2=101 kHz 怎么接

接线：

```text
信号源 CH1 -> Red Pitaya IN1
信号源 CH2 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH4 或 CH1
信号源 CH1 或 CH2 同时接示波器参考通道
```

建议输入：

```text
IN1 = 100 kHz sine
IN2 = 101 kHz sine
幅度 = 100-500 mVpp
offset = 0 V
```

安全检查：

- 进入 Red Pitaya 前用示波器确认实际 Vpp；
- 不要直接输入超过 Red Pitaya 安全范围的信号；
- 不接真实 PD；
- 不接 D2-125。

### 6.4 示波器 time/div 和 volt/div 建议

看 raw mixer 高频项时：

```text
目标频率：201 kHz
周期：约 4.98 us
time/div：1 us/div 或 2 us/div
volt/div：20 mV/div 或 50 mV/div 起步
```

看 LPF 后 1 kHz 差频时：

```text
目标频率：1 kHz
周期：1 ms
time/div：100 us/div 到 200 us/div 起步
volt/div：10 mV/div、20 mV/div 或按实际幅度调整
```

如果输出太小：

- 先调示波器 volt/div；
- 再确认输入幅度；
- 再确认 bitstream 和 OUTPUT_MODE；
- 不要第一反应就改 RTL gain。

### 6.5 raw mixer 应该看到什么

在 `OUTPUT_MODE=2`，`IN1=100 kHz`，`IN2=101 kHz` 时，理论上：

```text
sin(2π100k t) x sin(2π101k t)
  -> 1 kHz 差频项
  -> 201 kHz 和频项
```

因为没有 LPF，示波器上可能看到比较快的波形，也可能叠加慢包络。

raw mixer 的作用是：

```text
证明乘法还活着。
```

### 6.6 LPF 后应该看到什么

在 `OUTPUT_MODE=3`，同样输入 `100 kHz` 和 `101 kHz` 时，LPF 后应主要看到：

```text
1 kHz
```

`201 kHz` 应明显变弱或被平滑掉。

这就是 v1d 的核心通过标准：

```text
raw mixer 有 1 kHz + 201 kHz；
LPF 后主要剩 1 kHz。
```

### 6.7 如果看不到 1 kHz，如何排查

按这个顺序排查，不要跳步：

1. 确认 `OUTPUT_MODE=2` 下 raw mixer 仍正常；
2. 确认加载的是最新 bitstream；
3. 确认 top 参数确实是 `OUTPUT_MODE=3`；
4. 确认 IN1 是 `100 kHz`，IN2 是 `101 kHz`；
5. 确认两路输入幅度在 `100-500 mVpp`，offset 为 `0 V`；
6. 示波器 time/div 改到 `100-200 us/div` 看 1 kHz；
7. volt/div 调到足够灵敏；
8. 检查 LPF 是否 reset 后一直没 enable；
9. 检查 `LPF_SHIFT` 是否太大，导致响应太慢或幅度太小；
10. 检查 saturation 是否把输出夹死；
11. 回到 `tb_lpf_core` 用同样频率重跑仿真。

常见误判：

- 用 `1 us/div` 看 1 kHz，会觉得“没有波形”；
- 用 `200 us/div` 看 raw 201 kHz，会觉得“很乱”；
- 输出只有几 mV 时，volt/div 太粗会看不到。

### 6.8 为什么不接 D2-125

因为 v1d 输出还只是 error-like low-frequency signal，不是最终 MTS error。

当前还缺：

- 真实 PD 输入验证；
- pre-mixer BPF；
- digital gain / 幅度标定；
- I/Q phase 优化；
- offset 调整；
- D2-125 输入范围；
- D2-125 极性；
- D2-125 阻抗；
- D2-125 带宽。

如果现在接 D2-125，风险是：

- 输入幅度不安全；
- 极性反了；
- offset 过大；
- 9.2 MHz 残留过多；
- servo 接收到的不是可用 error；
- 后续无法判断问题来自 FPGA、D2-125 还是激光器。

所以 v1d 的唯一输出对象是：

```text
示波器
```

## 7. 得到优质 MTS error 的最终标准

最终不是“OUT1 有波形”就结束。真正优质的 MTS error 至少应满足：

- 清晰过零点；
- 过零点附近斜率大；
- 噪声小；
- offset 小；
- 不削顶；
- 可重复；
- 可接 servo；
- 能锁定激光。

可以把这些标准分成三层。

信号形状层：

- 过零点位置稳定；
- 过零斜率足够大；
- 正负两侧形状合理；
- 没有明显削顶或饱和。

噪声和频谱层：

- RMS noise 小；
- `9.2 MHz` 残留足够低；
- 低频漂移可控；
- OUT1 噪声不会淹没 error。

闭环可用层：

- D2-125 或 FPGA PID 输入范围匹配；
- 极性明确；
- offset 可调；
- 闭环后能降低 error；
- 激光能稳定锁在目标跃迁附近。

## 8. 下一步开发任务

`v1d_mixer_lpf` 最小 RTL 开发和信号源差频上板测试已经完成。

`v1e-A / v1e-B` 已经完成真实链路 error-like signal 观察和三基准对照。当前记录为“真实链路误差信号对照已完成”，但不表示已经完成 FPGA 锁定。

已完成：

- `lpf_core.sv`
- `tb_lpf_core.sv`
- `tb_laser_lock_core_v1d.sv`
- `laser_lock_core.sv OUTPUT_MODE=3`
- `red_pitaya_top.sv LASER_LOCK_OUTPUT_MODE=3`
- `100 kHz x 102 kHz -> OUT1 约 1.992 kHz`
- `100 kHz x 101 kHz -> OUT1 约 1 kHz`

当前真实链路接线和观测：

```text
IN1 = 模拟前级处理后的 PD 调制信号
IN2 = 与 EOM 同源的 4.6 MHz REF，进入 Red Pitaya 前必须衰减到安全范围
OUT1 = 示波器观察 error-like low-frequency signal
```

当前结果：

- FPGA OUT1 已看到随 scan / PD 峰位置变化的 error-like 结构；
- FPGA OUT1 约 `0.16 Vpp`；
- 模拟 mixer 直接输出约 `0.46-0.47 Vpp`，但噪声较大；
- D2-125 后级输出约 `1.57-1.8 Vpp`，噪声小、形状好、过零点清晰；
- 同源 `4.6 MHz REF` 对稳定输出非常重要。

new-6.9 后的下一步开发顺序：

1. `v1i D2-125 safety input`：FPGA OUT1 输入 D2-125，先不开闭环，只观察响应和安全性；
2. `v1g digital gain / output scaling`：可选优化，只有 D2-125 输入响应不足且确认不饱和时才开发；
3. `v1h REF phase / I-Q optimization`：优化过零点、斜率和噪声；
4. 低增益短时间闭环验证：仍由 D2-125 负责 servo；
5. `v2 FPGA PID`：在 FPGA 内部逐步替代 D2-125 PID / servo；
6. `v3 auto-lock / relock FSM`：自动找峰、判断锁定状态、失锁重锁；
7. `v4 dataset + benchmark`：记录锁定、失锁、重锁和参数效果；
8. `v5 AI optimization`：基于数据集做锁定状态识别、自动参数优化和智能重锁。

暂时保留：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ 放大器`；
- `D2-125 PID / servo`。

v1d 已满足的仿真和上板条件：

```text
tb_lpf_core PASS
tb_laser_lock_core_v1d PASS
100 kHz x 102 kHz -> OUT1 约 1.992 kHz
100 kHz x 101 kHz -> OUT1 约 1 kHz
```

当前仍然：

```text
不允许接 D2-125
不允许直接闭环
不允许声称已经完成 FPGA 锁定
不允许 PID
不允许 AI
```

一句话总结下一步：

```text
v1e-A/v1e-B 已证明 FPGA error-like signal 有价值；new-6.9 已看到 D2-125 后级明显响应，下一步优先 v1i 安全验证，再按结果决定是否做 v1g 增益缩放和 v1h 相位优化。
```
