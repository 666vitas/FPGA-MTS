# 实验测试指南

## 0. 本文件作用

本文件指导上板实验。它不是 RTL 设计文档，而是告诉你信号源、Red Pitaya、示波器应该怎么接，哪些线不能接，什么现象算通过。

总原则：

```text
OUT1 先接示波器。
不接 D2-125，直到 v1g。
不接激光器反馈。
不让 FPGA 驱动 EOM。
输入必须先测幅度。
当前 v1ab-1 和 v1ab-2 已通过，下一步可以准备 v1c_mixer_only。
```

当前进度：

```text
v1ab RTL 已生成。
testbench 已通过。
Vivado synthesis / implementation / bitstream 已成功。
.bit 已转换为 .bit.bin。
.bit.bin 已上传到 Red Pitaya。
fpgautil -b /root/red_pitaya_top.bit.bin 已加载成功。
终端显示 BIN FILE loaded through FPGA manager successfully。
v1ab-1: IN1 -> OUT1 已真实上板通过。
v1ab-2: IN2 -> OUT1 已真实上板通过。
```

所以当前可以进入 `v1c_mixer_only` 的准备和开发阶段，但仍然不是接真实 PD/REF/D2-125，也不是做完整 MTS error。

## 真实模拟链路与 FPGA 等效参数

当前实验台真实模拟链路是：

```text
PD signal
  -> 10 MHz Low Pass Filter
  -> 1.8 MHz High Pass Filter
  -> Mini-Circuits ZFL-500LN+ RF Amplifier
  -> Mini-Circuits ZFM-3+ Mixer
       REF input = 4.6 MHz sine from signal generator
  -> IF / mixed output
  -> servo / D2-125 error input
```

这条链路不是抽象图，而是当前实验台真实接线。FPGA 后续每一步测试都要问一句：我正在替代哪个真实器件？

| 真实链路 | 作用 | FPGA 等效 | 测试阶段 |
|---|---|---|---|
| `10 MHz Low Pass Filter` | 去掉高于 `10 MHz` 的噪声和无用高频分量 | digital LPF / BPF 上边界，cutoff ≈ `10 MHz` | `v1f_bpf_gain_enable` |
| `1.8 MHz High Pass Filter` | 去掉 DC、低频扫描背景、低频漂移 | digital HPF / BPF 下边界，cutoff ≈ `1.8 MHz` | `v1f_bpf_gain_enable` |
| `10 MHz LPF + 1.8 MHz HPF` | 形成约 `1.8-10 MHz` 的带通链路，保留 `4.6 MHz` 调制相关成分 | `bpf_core.sv` | `v1f_bpf_gain_enable` |
| `ZFL-500LN+ amplifier` | 约 `24 dB` 增益，电压增益约 `15.85`，放大目标频带信号 | `digital_gain.sv`，初始 `×1, ×2, ×4, ×8, ×16`，必须防削顶 | `v1f_bpf_gain_enable` |
| `ZFM-3+ mixer` | 与 `4.6 MHz REF` 相乘，把相干调制成分搬到低频 | `mixer_core.sv`，signed `14-bit × 14-bit -> 28-bit -> 14-bit` | `v1c_mixer_only` |
| mixer 后低通 | 去掉 `2f` 和高频项，保留慢变 error signal | `lpf_core.sv` | `v1d_mixer_lpf` |
| `D2-125 error input` | 接收安全的 error signal | `OUT1` 安全输出和保护 | `v1g_error_to_D2_125` |

必须后续标定的实验量：

1. PD 原始输出 `Vpp`；
2. `10 MHz LPF` 后 `Vpp`；
3. `1.8 MHz HPF` 后 `Vpp`；
4. `ZFL-500LN+` 放大后 `Vpp`；
5. mixer RF 输入 `Vpp`；
6. mixer LO / REF 输入 `Vpp`；
7. mixer IF 输出 `Vpp` 和 offset；
8. `D2-125 error input` 安全范围；
9. Red Pitaya `IN1/IN2` 实际输入幅度；
10. Red Pitaya `OUT1` 输出幅度；
11. FPGA 数字 gain 后是否削顶；
12. error signal 零点斜率和噪声 RMS。

## Step 1：v1ab-1：IN1 -> OUT1

目标：

```text
IN1 -> adc_dat[0] -> pd_i -> error_o -> OUT1
```

bitstream 参数：

```text
USE_LASER_LOCK_CORE = 1
LASER_LOCK_OUTPUT_MODE = 0
```

接线：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

信号：

```text
1 kHz sine
100 mVpp
0 V offset
```

成功标准：

- `OUT1` 有同频波形；
- 幅度可以不同；
- 极性可以反相；
- 不削顶；
- 不顶死；
- `OUT2` 无异常大信号。

失败时先查：

- 信号发生器是否真的输出；
- `IN1` 是否接对；
- 示波器触发是否正确；
- bitstream 是否对应 `OUTPUT_MODE=0`；
- Vivado 是否加入 `laser_lock_core.sv` 和 `output_protect.sv`。

## Step 2：v1ab-2：IN2 -> OUT1

前提：

```text
Step 1: IN1 -> OUT1 已经真实上板通过。
```

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

目标：

```text
IN2 -> adc_dat[1] -> ref_i -> error_o -> OUT1
```

bitstream 参数：

```text
USE_LASER_LOCK_CORE = 1
LASER_LOCK_OUTPUT_MODE = 1
```

接线：

```text
4.6 MHz REF 安全幅度 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF -> 示波器 CH2
```

信号：

```text
4.6 MHz sine
100-500 mVpp
0 V offset
```

禁止：

```text
6.32 Vpp 直接进 IN2。
不要第一次就直接 ±1 V。
```

成功标准：

- `OUT1` 能看到 4.6 MHz 同频波形；
- `IN2` 输入幅度安全；
- 不削顶；
- 不长时间顶死。

失败时先查：

- `REF` 是否真的经过衰减；
- 示波器是否能在进板前看到 `REF`；
- `OUTPUT_MODE` 是否为 1；
- `IN2` 和 `IN1` 是否接反。

## Step 3：进入 v1c 前的门槛

只有以下两项都通过，才允许进入 `v1c_mixer_only`：

```text
v1ab-1: IN1 -> OUT1 通过
v1ab-2: IN2 -> OUT1 通过
```

如果只完成了 bitstream 加载，但没有示波器波形验证，不算通过。

如果只通过 IN1，不允许进入 mixer；还必须验证 REF 输入候选通路 `IN2 -> OUT1`。

当前状态：

```text
v1ab-1: IN1 -> OUT1 已通过。
v1ab-2: IN2 -> OUT1 已通过。
允许进入 v1c_mixer_only。
```

## 后续 mixer 测试

适用版本：

```text
v1c_mixer_only
```

接线：

```text
信号发生器 CH1 -> Red Pitaya IN1
信号发生器 CH2 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
IN1 或 IN2 参考信号 -> 示波器 CH2
```

建议：

- 先用低幅度；
- 先用较低频同频信号，例如 `100 kHz / 100 kHz`；
- 两路信号都要在进板前用示波器确认；
- 第一次不要接真实 PD；
- 第一次不要直接使用真实实验链路的 4.6 MHz REF 大幅度信号；
- 不接 D2-125。

推荐测试顺序：

测试 A：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
```

目的：用低频、低幅度、容易看懂的两路同频信号确认数字乘法链路。

测试 B：

```text
IN1 = 4.6 MHz sine, 100 mVpp, 0 V offset
IN2 = 4.6 MHz sine, 100 mVpp, 0 V offset
```

目的：确认接近 MTS REF 频率时 mixer 输出仍然可观察、不削顶、不顶死。

测试 C：

```text
真实 PD + 安全衰减后的 4.6 MHz REF
```

这一步属于后续 `v1e_real_pd_ref`，不要在 `v1c` 第一轮就做。

看什么：

- `OUT1` 是否随两路输入变化；
- 是否出现长期满幅；
- 改变一路相位或幅度时输出是否变化。

## 后续 LPF 测试

适用版本：

```text
v1d_mixer_lpf
```

测试方法：

- 先用信号发生器模拟输入；
- 观察 `OUT1` 是否比 v1c 更平滑；
- 改变 `IN1/IN2` 的相位或幅度，观察低频输出是否变化；
- 记录输出幅度和 offset。

成功标准：

- 输出不再主要是高频乘法波形；
- 低频变化可解释；
- 不顶死；
- 不接 D2-125。

## 后续 real PD 测试

适用版本：

```text
v1e_real_pd_ref
```

接线：

```text
PD signal -> Red Pitaya IN1
安全衰减后的 4.6 MHz REF -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
模拟链路 error 或 REF -> 示波器 CH2
```

测试前必须确认：

- `PD` 幅度安全；
- `REF` 为 `4.6 MHz sine, 0 V offset`；
- `REF` 幅度安全，目标在 `±1 V` 内；
- 第一次建议 `100 mVpp` 到 `500 mVpp`；
- `REF` 不是 6.32 Vpp 直接接入；
- `OUT1` 只接示波器。

成功标准：

- `OUT1` 出现随实验调谐变化的 `error-like signal`；
- 幅度安全；
- offset 安全；
- 不接激光器反馈。

## 安全原则

必须遵守：

- `OUT1` 先示波器；
- 不接 `D2-125`，直到 `v1g`；
- 不接激光器反馈；
- 不让 FPGA 驱动 `EOM`；
- 输入必须先测幅度；
- `6.32 Vpp REF` 禁止直接进 `IN2`；
- `4.6 MHz REF` 第一次进 `IN2` 建议先 `100 mVpp` 到 `500 mVpp`；
- 未到 `v1e` 不接真实 `PD/REF`；
- 未到 `v1g` 不接 `D2-125`；
- 每个版本失败时先回退到上一版本；
- 不确认安全幅度，不进入下一步。

一句话记忆：

```text
先看见，后连接；先示波器，后 D2-125；先开环，后闭环。
```
