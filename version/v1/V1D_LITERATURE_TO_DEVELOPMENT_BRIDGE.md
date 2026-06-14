# V1D 文献到开发桥接说明

> 本文件是 v1d 的技术依据（"为什么这样设计"），包含文献推导、公式计算和参数选择理由。
> 操作步骤和实验 checklist 参见 [[FPGA_MTS_STEP_BY_STEP_ANALOG_REPLACEMENT_GUIDE]]。
> 当前状态参见 [[STATUS]]。

## 1. 当前版本目标

`v1d_mixer_lpf` 的目标是把已经通过上板验证的 raw mixer 输出，接入一个 post-mixer low-pass filter，并把低频/差频/基带分量送到 `OUT1` 示波器：

```text
IN1 / PD x IN2 / REF
  -> mixer_core
  -> post-mixer LPF
  -> OUT1
```

`v1d` 不是最终 MTS error signal。它只验证一个更小的问题：`PD x REF` 之后，FPGA 是否能把 mixer 后的低频/基带项提取出来，并压低同频混频产生的 `2f` 高频项。

因此 `v1d` 的成功标准不是“能锁激光”，也不是“已经得到高质量 MTS error”，而是：

- raw mixer 后的高频项被 LPF 明显平滑或压低；
- 低频/差频信号能从 `OUT1` 上被示波器看到；
- 输出仍然安全、可解释、可和 `OUTPUT_MODE=2` raw mixer 对照。

### 1.1 v1d 在真实模拟链路中的位置

当前实验台真实模拟链路是：

```text
PD 模拟电压信号
  -> 10 MHz Low Pass Filter
  -> 1.8 MHz High Pass Filter
  -> ZFL-500LN+ RF Amplifier
  -> ZFM-3+ Mixer, REF = 4.6 MHz
  -> mixer 后 LPF
  -> MTS Error Signal
  -> D2-125 Servo / PID
  -> Laser lock
```

目标数字替代链路的长期形态是：

```text
PD
  -> Red Pitaya ADC / IN1
  -> digital pre-mixer BPF
  -> digital gain / scaling
  -> digital mixer / lock-in with REF
  -> post-mixer LPF
  -> OUT1
  -> 后续再考虑 D2-125
```

但 `v1d` 只替代其中一个位置：

```text
ZFM-3+ mixer 后的 IF / mixed output
  -> mixer 后 LPF
```

也就是说，`v1d` 当前对应的是：

```text
已完成：ZFM-3+ mixer 的 FPGA 等效 raw mixer, v1c
本次：mixer 后 LPF 的 FPGA 等效, v1d
```

`10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+`、D2-125、激光器闭环都只作为边界条件写入本文，不在 `v1d` RTL 中实现。

## 2. 当前已完成基础

`v1ab` 已通过两路基础输入输出链路：

```text
IN1 -> OUT1
IN2 -> OUT1
```

这说明：

- `IN1 / adc_dat[0] / pd_i` 通路可用；
- `IN2 / adc_dat[1] / ref_i` 通路可用；
- `laser_lock_core` 能接收两路 ADC 数据；
- DAC A / `OUT1` 输出路径可用。

`v1c_mixer_only` 已通过真实上板测试：

- `IN1 = 100 kHz sine`，`IN2 = 100 kHz sine` 时，`OUT1` 出现约 `200 kHz` 成分；
- `OUT1` 幅度约 `20-22 mVpp`；
- 拔掉 `IN1` 后，`OUT1` 波形消失；
- `4.6 MHz x 4.6 MHz` 测试中，`OUT1` 也能看到混频输出波形。

这说明当前 `OUTPUT_MODE=2` 的 `mixer_core(pd_i, ref_i)` 已经不是单路直通，也不是示波器噪声，而是依赖 `IN1` 和 `IN2` 两路输入的 FPGA 数字混频结果。

### 2.1 当前真实链路参数和对 v1d 的约束

| 真实链路位置 | 当前记录参数 | 作用 | FPGA 对应模块 | v1d 是否实现 | 对 v1d 的直接约束 |
|---|---|---|---|---|---|
| PD 输出 | 模拟电压信号，具体 Vpp/SNR 待测 | 提供包含 4.6 MHz 调制信息的光电信号 | `IN1 / adc_dat[0] / pd_i` | 不新增处理 | v1d 测试先用信号源，不直接要求真实 PD |
| 10 MHz LPF | cutoff / passband 上限约 `10 MHz` | 抑制高于 10 MHz 的高频噪声，保留 4.6 MHz | 后续 `pre_mixer_lpf` 或 BPF 上截止 | 否 | 不能把它误认为 mixer 后 LPF |
| 1.8 MHz HPF | cutoff / passband 下限约 `1.8 MHz` | 去 DC、低频背景、慢漂移，保留 4.6 MHz | 后续 `pre_mixer_hpf` 或 BPF 下截止 | 否 | v1d 不负责去除 PD 低频背景 |
| 1.8-10 MHz BPF | 由 `10 MHz LPF + 1.8 MHz HPF` 级联形成 | 让 4.6 MHz 分量进入 mixer 前更突出 | 后续 `pre_mixer_bpf_core` | 否 | v1d 只能验证 mixer 后低通，不能证明前级 SNR 已足够 |
| ZFL-500LN+ | Mini-Circuits RF amplifier，典型增益约 `24 dB`，电压增益约 `15.8x` | ADC/mixer 前提高 RF 信号幅度 | 后续 `digital_gain_core` / scaling | 否 | digital gain 不能恢复 ADC 前已丢失的 SNR |
| ZFM-3+ mixer | Level 7 double-balanced mixer，LO 典型 `+7 dBm`，当前 REF `4.6 MHz` | 把 PD 中 4.6 MHz 同步分量搬移到低频，同时产生 2f | `mixer_core.sv` | v1c 已实现 | v1d 的输入就是 raw mixer 的 signed 14-bit 输出 |
| mixer 后 LPF | cutoff / 阶数 / 型号待测 | 去除 `2f = 9.2 MHz`，保留低频 error-like 分量 | `lpf_core.sv` | 是 | 这是 v1d 的唯一新增处理模块 |
| Red Pitaya ADC | STEMlab 125-14，`125 MS/s`，`14-bit`，输入需按约 `±1 V` 保护 | 采样 IN1/IN2 | 官方 ADC + `adc_dat[0/1]` | 已沿用 | 输入测试幅度应先用安全正弦，不直接上高幅 RF |
| Red Pitaya DAC OUT1 | 约 `±1 V` 输出范围，实际有效位和噪声需实测 | 输出 error-like signal 到示波器 | 官方 DAC A / OUT1 | 已沿用 | LPF 输出必须 signed 14-bit saturation |
| D2-125 Servo | 输入范围、阻抗、极性、带宽未确认 | 后续接收真正 MTS error 并闭环 | 后续外部接口 | 否 | v1d 严禁接入 D2-125 |

### 2.2 当前代码链路和真实器件映射

当前 v1c 已经确认的 FPGA 代码链路是：

```text
adc_dat[0] -> laser_lock_core.pd_i
adc_dat[1] -> laser_lock_core.ref_i
mixer_core(pd_i, ref_i)
  -> output_protect
  -> laser_error
  -> dac_a_sum_laser
  -> official DAC saturation / conversion
  -> OUT1
```

`v1d` 只应把这条链路改成：

```text
adc_dat[0] -> pd_i
adc_dat[1] -> ref_i
mixer_core(pd_i, ref_i)
  -> lpf_core
  -> output_protect
  -> laser_error
  -> dac_a_sum_laser
  -> official DAC saturation / conversion
  -> OUT1
```

工程边界：

- `mixer_core` 对应真实 `ZFM-3+ Mixer`；
- `lpf_core` 对应真实 `mixer 后 LPF`；
- `output_protect` 只做输出保护/寄存，不等价于完整滤波器；
- v1d 不应改 `red_pitaya_top.sv` 的官方 ADC/DAC/PLL/ODDR 接口；
- v1d 不应把 `10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+` 的替代逻辑混入本次修改。

### 2.3 v1c 实验事实对 v1d 参数的意义

v1c 的 `100 kHz x 100 kHz` 测试已经看到 `200 kHz`，这不是一个随便的现象，而是给 v1d 低通测试提供了基线：

```text
raw mixer 已经能产生 2f；
v1d 的 LPF 必须让这个 2f 在 OUTPUT_MODE=3 下明显变弱。
```

`100 kHz x 101 kHz` 是更适合 v1d 的验证方式：

```text
100 kHz x 101 kHz
  -> 1 kHz 差频项
  -> 201 kHz 和频项
```

如果 `OUTPUT_MODE=3` 正常，示波器应主要看到 `1 kHz`，而不是 `201 kHz`。这比 `100 kHz x 100 kHz` 更容易判断 LPF 是否“保留低频、压制高频”。

真实频率测试中：

```text
4.6 MHz x 4.6 MHz
  -> DC / 慢变项
  -> 9.2 MHz 高频项
```

因此 `v1d` 的 LPF 不能只在低频玩具测试中看起来有效，还必须在 `4.6 MHz` 同频测试中显著压低 `9.2 MHz`。

## 3. 文献给出的核心结论

### 结论 1：数字 lock-in / synchronous detection 的核心链路是 mixer + LPF

Linien、PyRPL 和 FPGA digital lock-in 三组文献都指向同一条最小链路：

```text
输入信号
  -> 与同频参考相乘 / IQ demodulation
  -> low-pass filter
  -> 低频 I/Q 或 error-like signal
```

Linien 把 PD 光谱信号送入 Red Pitaya ADC，在 FPGA 内完成 CORDIC/IQ 解调，并用 IIR 得到 error signal。PyRPL 把这个结构拆成 `IN1/IN2 -> IQ module -> low-pass -> OUT1/OUT2` 这类可路由模块。FPGA digital lock-in 论文则更直接地把 DDS、乘法器、CIC/FIR 低通写成数字锁相放大器 pipeline。

对 `v1d` 的工程含义：

- `v1c` 的 raw mixer 只能证明乘法器工作，还不能提取基带；
- raw mixer 后必须加入 post-mixer LPF；
- `v1d` 的代码目标应聚焦在 `mixer_core -> lpf_core -> OUT1`，不应同时扩展 BPF/gain/PID/AI。

### 结论 2：mixer 后输出包含低频项和 2f 高频项

同频正弦相乘时：

```text
sin(wt) x sin(wt) = 1/2 - 1/2 cos(2wt)
```

因此 `100 kHz x 100 kHz` 后会包含 DC/低频项和 `200 kHz` 高频项；这正好对应 v1c 上板中 `OUT1` 出现 `200 kHz` 的实验事实。

对于真实目标频率：

```text
PD_RF x REF
4.6 MHz x 4.6 MHz
  -> 低频/基带项 + 9.2 MHz 高频项
```

对 `v1d` 的工程含义：

- `OUTPUT_MODE=3` 的 LPF 必须压低 `9.2 MHz`；
- 在低频替代测试中，`100 kHz x 101 kHz` 理论上包含 `1 kHz` 差频项和 `201 kHz` 高频项；
- `v1d` 的示波器验收重点是：LPF 后主要看到 `1 kHz` 或低频/DC，而不是 raw mixer 中显著的 `201 kHz` 或 `9.2 MHz`。

### 结论 3：第一版 LPF 应该简单、稳定、可解释

Linien 和 PyRPL 都支持低阶 IIR / IQ low-pass 作为实时 Red Pitaya 解调链路。FPGA digital lock-in 论文给出的 CIC+FIR 路线滤波更干净，但包含 decimation 和较明显延迟，适合后续低噪声记录或慢速观测，不适合作为 `v1d` 第一版的最小实时输出。

对 `v1d` 的工程含义：

- 第一版推荐一阶 IIR / leaky integrator；
- CIC/FIR/decimation 不进入 `v1d` 第一版；
- `v1d` 先验证“能不能从 mixer 后提取低频项”，再进入后续滤波器优化。

### 结论 4：保留 raw mixer 输出模式很重要

文献中的 lock-in 链路都依赖可观察的中间信号：输入、乘法后、低通后。v1c 已经给出了 raw mixer 的真实上板基线。

对 `v1d` 的工程含义：

- `OUTPUT_MODE=2` 必须保留，用于 raw mixer 对照；
- `OUTPUT_MODE=3` 才新增为 `mixer + LPF`；
- 上板测试必须先用 `OUTPUT_MODE=2` 确认 raw mixer 行为，再切到 `OUTPUT_MODE=3` 判断 LPF 是否生效。

### 结论 5：v1d 不等于完整 MTS error

文献和真实链路记录都说明，优质 MTS error signal 不只是 `mixer + LPF`。还需要前级频带选择、足够 SNR、相位选择、offset 和输出幅度管理，后续还要经过 servo 验证。

对 `v1d` 的工程含义：

- 当前不做 PD 前级 `10 MHz LPF / 1.8 MHz HPF` 的数字替代；
- 当前不做 ZFL-500LN+ 等效 digital gain；
- 当前不做 I/Q 相位扫描；
- 当前不做 offset 调整；
- 当前不做输出增益标定；
- 当前不接 D2-125，不接激光器，不做闭环 servo；
- `v1d` 输出只能称为 `error-like low-frequency/baseband signal`。

## 4. 对 v1d 的具体设计决策

`v1d` 的第一版工程决策如下。

- 新增 `lpf_core.sv`，作为 `mixer_core` 后的 post-mixer LPF。
- LPF 采用一阶 IIR / leaky integrator。
- 差分公式：

```text
y[n] = y[n-1] + ((x[n] - y[n-1]) >>> LPF_SHIFT)
```

- `LPF_SHIFT` 建议默认初值为 `12`。
- 该初值的工程含义：在 `125 MS/s` 时给出 kHz 量级的平滑响应，适合先保留 `1 kHz` 差频，同时压低 `201 kHz` 和 `9.2 MHz`。后续可用 `10/11/12/13` 做仿真和上板对比。
- 一阶 IIR 的近似关系可按 `fc ≈ fs / (2π * 2^LPF_SHIFT)` 粗估：

| `LPF_SHIFT` | 粗略 cutoff 量级 | 对 v1d 的用途判断 |
|---|---:|---|
| `10` | 约 `19 kHz` | 响应快，201 kHz 抑制较弱，可作对照 |
| `11` | 约 `9.7 kHz` | 中等响应，适合比较 |
| `12` | 约 `4.9 kHz` | 建议默认初值，能保留 1 kHz 差频并压低 201 kHz |
| `13` | 约 `2.4 kHz` | 更平滑，响应更慢，可看 1 kHz 幅度是否开始变小 |

- 以 `LPF_SHIFT=12` 粗估，`201 kHz` 会比通带明显衰减，`9.2 MHz` 会被更强压低；真实抑制量仍要以仿真和示波器频谱为准。
- 内部 accumulator / state 位宽建议至少 `32-bit signed`，输入先 sign-extend 到内部位宽，再计算差值和反馈。
- `lpf_core` 输入为 signed 14-bit，输出为 signed 14-bit。
- 输出必须做 saturation，不能直接截断造成符号错误或不可控削顶。
- `lpf_core` 不直接吃 28-bit 乘法原始结果；第一版建议沿用 `mixer_core` 已缩放并 saturation 后的 signed 14-bit 输出，保证模块边界清楚。
- 若后续发现 LPF 前量化过重，再单独讨论 `mixer_core` 输出宽位宽到 `lpf_core` 的内部接口，不在 v1d 第一版中扩大范围。
- 保留现有 `OUTPUT_MODE=0/1/2`：
  - `0`: `IN1 / pd_i -> OUT1`
  - `1`: `IN2 / ref_i -> OUT1`
  - `2`: `IN1 x IN2 raw mixer -> OUT1`
- 新增 `OUTPUT_MODE=3`：
  - `3`: `IN1 x IN2 -> lpf_core -> OUT1`
- 不修改 Red Pitaya 官方底层 ADC/DAC/PLL/ODDR/PS/AXI/XDC。
- 不在 `v1d` 引入 BPF/gain/PID/IQ/AI/D2-125 相关逻辑。

## 5. v1d 仿真测试标准

`v1d` 写 RTL 后，至少必须通过以下仿真标准，才允许进入 bitstream 流程：

1. `tb_lpf_core` PASS；
2. `tb_laser_lock_core_v1d` PASS；
3. 阶跃输入时，LPF 输出按一阶 IIR 规律缓慢变化，而不是立即跳变；
4. 高频输入时，LPF 输出被明显平滑；
5. signed 正负输入正常，包括正到负、负到正的过零行为；
6. saturation 正常，内部 accumulator 或输出不会因截断产生错误符号。

`tb_laser_lock_core_v1d` 还应确认：

- `OUTPUT_MODE=0/1/2` 行为保持不变；
- `OUTPUT_MODE=3` 只在 raw mixer 后新增 LPF；
- reset 后输出为 0；
- enable 关闭时输出为 0；
- `control_o` 仍保持为 `14'sd0`。

## 6. v1d 上板测试标准

上板测试的共同安全前提：

- 先使用两路信号发生器正弦，不直接接真实 PD；
- IN1/IN2 第一次测试建议在 `100-500 mVpp` 范围内，`0 V offset`；
- 进入 Red Pitaya 前必须用示波器确认实际幅度；
- 严禁把未经衰减、可能超过 Red Pitaya 输入安全范围的 REF 或 mixer LO 直接接入 IN1/IN2；
- OUT1 只接示波器，不接 D2-125。

### 测试 A：raw mixer 对照

```text
OUTPUT_MODE = 2
IN1 = 100 kHz
IN2 = 100 kHz
建议幅度 = 100-500 mVpp, 0 V offset
```

预期：

```text
OUT1 有 200 kHz raw mixer 成分。
```

意义：

```text
确认 v1c 基线仍然存在，避免把输入、bitstream 或示波器设置问题误判为 LPF 问题。
```

### 测试 B：LPF 差频测试

```text
OUTPUT_MODE = 3
IN1 = 100 kHz
IN2 = 101 kHz
建议幅度 = 100-500 mVpp, 0 V offset
```

理论：

```text
raw mixer 包含 1 kHz + 201 kHz
```

预期：

```text
LPF 后 OUT1 主要看到 1 kHz；
201 kHz 被明显压低或平滑。
```

意义：

```text
这是 v1d 最关键的低频/差频提取测试。
```

### 测试 C：4.6 MHz 同频测试

```text
OUTPUT_MODE = 3
IN1 = 4.6 MHz
IN2 = 4.6 MHz
建议幅度 = 100-500 mVpp, 0 V offset
```

理论：

```text
raw mixer 包含低频/DC + 9.2 MHz
```

预期：

```text
9.2 MHz 被压制；
OUT1 主要剩低频/DC 或慢变分量。
```

意义：

```text
确认 v1d 与真实 MTS REF 频率方向一致，但仍不代表已经得到最终 MTS error signal。
```

## 7. 当前明确不做的内容

`v1d_mixer_lpf` 当前明确不做：

- 不做 `10 MHz LPF`；
- 不做 `1.8 MHz HPF`；
- 不做 `digital gain`；
- 不做 `I/Q`；
- 不做 `PID`；
- 不接 `D2-125`；
- 不接激光器；
- 不做 AI。

这些内容属于后续版本。当前如果把它们混入 `v1d`，会破坏最小验证边界，也会让示波器结果难以归因。

### 7.1 为什么这些内容虽然重要，但不能放进 v1d

| 不做内容 | 真实链路中的意义 | 为什么 v1d 不做 |
|---|---|---|
| `10 MHz LPF` | mixer 前高频噪声抑制，保留 4.6 MHz | 它是 pre-mixer filter，不是 mixer 后 LPF |
| `1.8 MHz HPF` | mixer 前去低频背景和慢漂移 | 它会改变进入 mixer 的信号，无法单独判断 post-mixer LPF |
| `digital gain` | 尝试等效 ZFL-500LN+ 的 ADC 后缩放 | 数字增益不能恢复 ADC 前 SNR，且会影响 saturation 判断 |
| `I/Q` | 后续优化解调相位和 error 斜率 | v1d 先验证单路 mixer + LPF，避免相位变量干扰 |
| `PID` | 闭环控制激光 | v1d 只输出示波器信号，不产生控制量 |
| `D2-125` | 外部 servo 接收真正 error signal | 输入范围/极性/带宽未确认，且 v1d 不是最终 error |
| 激光器 | 最终被控对象 | 当前只做电子链路验证 |
| AI | 后续自动识峰/锁定 | 没有稳定 error-like signal 前 AI 没有可靠输入 |

## 8. 文献链接

- [[Paper_数字解调_001_Linien_RedPitaya_FPGA_Laser_Locking]]
- [[Paper_数字解调_002_PyRPL_RedPitaya_Lockbox_IQ_PID]]
- [[Paper_数字解调_003_FPGA_Digital_Lockin_CIC_FIR]]
- [[Paper_数字解调_004_PyRPL_Open_Source_RedPitaya_Lockbox]]
- [[014_v1d_mixer_lpf_文献工程筛选报告]]
- [[020_真实模拟链路参数记录]]
- [[023_数字解调文献第一轮筛选报告_真实链路对照]]
- [[024_本轮处理记录_数字解调文献第一轮真实链路对照]]

## 9. 下一步 Codex 开发任务

下一步可以开始 `v1d_mixer_lpf` 的最小 RTL/TDD 开发：

- `lpf_core.sv`
- `tb_lpf_core.sv`
- `tb_laser_lock_core_v1d.sv`

下一条开发指令摘要：

```text
请进入 v1d_mixer_lpf 最小 TDD 开发。
只新增 post-mixer lpf_core.sv，并把 laser_lock_core 增加 OUTPUT_MODE=3。
保留 OUTPUT_MODE=0/1/2。
LPF 第一版使用一阶 IIR：
y[n] = y[n-1] + ((x[n] - y[n-1]) >>> LPF_SHIFT)
默认 LPF_SHIFT 建议 12，内部使用足够 guard bits，并输出 signed 14-bit saturation。
新增 tb_lpf_core.sv 和 tb_laser_lock_core_v1d.sv。
必须先运行仿真，PASS 后才允许 Generate Bitstream。
不要修改 Red Pitaya 官方底层 ADC/DAC/PLL/ODDR。
不要加入 BPF/gain/IQ/PID/AI。
不要接 D2-125，不要接激光器。
```

结论：

```text
可以开始写 lpf_core.sv，但必须先完成并通过仿真；
仿真 PASS 前不允许 Generate Bitstream；
bitstream 成功前不允许上板；
v1d 上板也只允许接示波器，不允许接 D2-125 或激光器。
```
