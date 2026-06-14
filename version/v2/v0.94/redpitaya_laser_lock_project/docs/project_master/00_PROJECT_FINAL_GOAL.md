# 项目最终目标说明

## 0. 本文件作用

本文件说明整个 Red Pitaya MTS FPGA 激光稳频项目的最终目标。它不是某个阶段的临时记录，也不是某一次 Vivado 操作报告，而是后续所有版本路线的总方向。

以后如果文档太多、看不清主线，先回到本文件。它回答三个问题：

- 我们最终想替代哪一段模拟链路；
- v1 最终要完成哪条 PD/REF 数字 MTS error 链路；
- 当前 v1ab 先做什么、不做什么；
- 为什么现在最重要的是先完成 `IN1 -> OUT1` 和 `IN2 -> OUT1` 的硬件链路验证。

## 1. 实验背景

当前实验是 MTS 调制转移光谱稳频。真实实验中，光电探测器 `PD` 输出的信号先经过模拟 RF 链路，再得到误差信号送入 `D2-125`。

真实模拟链路可以整理为：

```text
PD
  -> 10 MHz Low Pass Filter
  -> 1.8 MHz High Pass Filter
  -> Mini-Circuits ZFL-500LN+ RF Amplifier
  -> Mini-Circuits ZFM-3+ Mixer
       REF input = 4.6 MHz sine from signal generator
  -> IF / mixed output
  -> servo / D2-125 error input
```

这不是抽象框图，而是当前实验台真实接线。后续 FPGA 设计必须尽量把每个数字模块对应到一个真实模拟器件或真实实验功能。

对新手来说，可以先把这条链路理解成：

```text
PD 光信号
  -> 通过 10 MHz LPF 和 1.8 MHz HPF 形成约 1.8 MHz 到 10 MHz 的有效带通链路
  -> 放大
  -> 和 4.6 MHz REF 相乘解调
  -> 低通滤波得到慢变化误差信号
  -> 交给伺服控制器 D2-125
```

## 2. FPGA v1 最终替代目标

v1 的最终目标是用 Red Pitaya FPGA 替代模拟链路中的滤波、放大、混频、低通和 error 输出部分。

```text
PD -> IN1
REF 4.6 MHz -> IN2

FPGA 内部：
adc_dat[0]
  -> DC remove / digital BPF / gain
adc_dat[1]
  -> REF input / optional phase adjustment
mixer
  -> LPF
  -> output scaling / limit
  -> error_o
  -> OUT1
```

也可以写成更接近实验语言的目标链路：

```text
PD signal
  -> FPGA IN1
4.6 MHz REF
  -> FPGA IN2

PD digital signal
  -> DC remove / digital BPF / gain
  -> mixer with REF
  -> LPF
  -> error signal
  -> OUT1
```

注意：`OUT1 -> D2-125 error input` 不是 v1ab 的事情，而是 `v1g_error_to_D2_125` 的事情。

v1 前半阶段不替代：

- `EOM drive`；
- `D2-125 PID`；
- `laser actuator`；
- `sweep`；
- `AI`。

也就是说，v1 的最终目标是先让 FPGA 产生可观察、可解释、幅度安全的 MTS `error-like signal`。它还不是完整锁频系统，更不是自动锁频系统。

## 2.1 真实模拟器件与 FPGA 等效关系

| 真实模拟链路器件/功能 | 当前已知参数 | FPGA 等效设计 |
|---|---|---|
| `10 MHz Low Pass Filter` | 保留 DC 到约 `10 MHz`，抑制更高频噪声；具体型号待补拍确认 | `digital LPF` 或 `BPF` 上边界，cutoff ≈ `10 MHz` |
| `1.8 MHz High Pass Filter` | 标注 `HIGH PASS FILTER 1.8 MHz`，输入 `50 Ω`，输出 `>=100 kΩ` | `digital HPF` 或 `BPF` 下边界，cutoff ≈ `1.8 MHz` |
| 等效带通链路 | `10 MHz LPF + 1.8 MHz HPF`，约 `1.8 MHz` 到 `10 MHz` | `bpf_core.sv`，passband roughly `1.8-10 MHz` |
| `ZFL-500LN+ RF Amplifier` | Mini-Circuits，约 `0.1-500 MHz`，典型增益约 `24 dB`，电压增益约 `15.85`，供电 `15 V` | `digital_gain.sv`，初始可选 `×1, ×2, ×4, ×8, ×16`，必须有 saturation / clipping protection |
| `ZFM-3+ Mixer` | Mini-Circuits Level 7 double-balanced mixer，LO 标称 `+7 dBm`，当前 REF 为 `4.6 MHz sine` | `mixer_core.sv`，signed `14-bit × 14-bit -> 28-bit`，再 scaling / saturation 回 signed `14-bit` |
| mixer 后低通 / error extraction | 去掉 `2f` 和高频项，保留慢变 error signal | `lpf_core.sv`，cutoff 需要根据 error signal 带宽和扫描/锁定需求确定，不能拍脑袋固定 |
| OUT1 到 D2-125 前保护 | 防止过幅、offset 异常、reset 异常输出 | `output_protect.sv` 和后续限幅/enable 保护 |

教学提醒：数字 gain 不能恢复 ADC 前已经丢失的信噪比。如果 PD 信号进入 Red Pitaya 前已经太小或被噪声淹没，FPGA 里把数字乘以 `16` 只会把信号和噪声一起放大。

当前 `v1ab_passthrough_debug` 已经完成真实上板验证。v1ab 不是 MTS error，v1ab 只验证输入输出硬件链路：

```text
OUTPUT_MODE=0:
IN1 -> ADC -> laser_lock_core -> OUT1

OUTPUT_MODE=1:
IN2 -> ADC -> laser_lock_core -> OUT1
```

当前两项结果已经通过：

```text
v1ab-1: IN1 -> OUT1，上板通过
v1ab-2: IN2 -> OUT1，上板通过
```

因此现在允许进入 `v1c_mixer_only` 的计划和代码开发阶段。但 `v1c` 只做数字乘法，不做 LPF/BPF/gain，不接 D2-125，也不能声称已经产生完整 MTS error。

## 3. 已知实验参数

当前已知或已作为阶段规划使用的参数：

| 参数 | 当前整理 |
|---|---|
| `EOM / MTS` 调制频率 | `4.6 MHz` |
| `EOM` 驱动幅度 | 约 `8.93 Vpp`，由外部信号发生器提供 |
| 原模拟 mixer `REF` | 约 `6.32 Vpp`，不能直接进 Red Pitaya `IN2` |
| Red Pitaya `IN2` 的 `REF` | `4.6 MHz sine, 0 V offset`，进板前必须衰减到安全范围，目标在 `±1 V` 内 |
| 第一次 `IN2` 测试建议 | 不要第一次就满幅，建议先 `100 mVpp` 到 `500 mVpp` |
| 模拟滤波/放大链路 | 约 `10 MHz low-pass + 1.8 MHz high-pass + RF amplifier` |
| 扫频 | 约 `50 Hz`、约 `400 mVpp`，第一阶段不做 sweep |

安全提醒：

```text
6.32 Vpp REF 禁止直接进入 Red Pitaya IN2。
EOM 8.93 Vpp 驱动也不是 Red Pitaya 输入信号。
第一次 REF 进 IN2 时，不要直接打到 ±1 V，更不能把原模拟 mixer REF 直接接入。
```

## 4. 最终系统路线

整个项目按阶段推进：

| 阶段 | 目标 |
|---|---|
| 阶段 | 目标 |
|---|---|
| `v1ab_passthrough_debug` | 验证 `IN1/IN2` 输入和 `OUT1` 输出硬件通路 |
| `v1c_mixer_only` | `pd_i * ref_i -> scaled error_o -> OUT1` |
| `v1d_mixer_lpf` | `pd_i * ref_i -> LPF -> error-like low frequency output` |
| `v1e_real_pd_ref` | 真实 `PD + 外部 4.6 MHz REF -> mixer + LPF -> error-like signal` |
| `v1f_bpf_gain_enable` | 加入数字 `1.8 MHz HPF + 10 MHz LPF + selectable digital gain`，严格对应 `10 MHz LPF + 1.8 MHz HPF + ZFL-500LN+ RF amplifier` |
| `v1g_error_to_D2_125` | `OUT1 -> D2-125 error input`，必须先由示波器确认安全 |
| `v2_fpga_pid` | FPGA PID |
| `v3_fpga_sweep` | FPGA sweep / scan，约 `50 Hz`、约 `400 mVpp` |
| `v4_lock_relock_fsm` | lock / relock FSM |
| `v5_ai_assisted_locking` | AI peak recognition / lock state detection / auto relock |

每个小版本只验证一个新能力，避免一次改太多导致出错后无法定位。

## 5. 当前最重要原则

当前最重要原则已经更新为：

```text
v1ab IN1->OUT1 和 IN2->OUT1 已通过，
现在可以进入 v1c mixer_only，
最终 v1 才完成 PD/REF 数字 MTS error signal。
```

更具体地说：

- `OUT1` 先接示波器；
- 不急着接 `D2-125`；
- 不急着接真实 `PD`；
- 不急着接真实实验 REF；
- 不接激光器反馈；
- 不让 FPGA 驱动 `EOM`；
- `v1c` 只做 mixer，不做 LPF/BPF/gain；
- 不做 PID；
- 不做 sweep；
- 不做 AI。

如果 `OUT1` 上连 `IN1 -> OUT1` 和 `IN2 -> OUT1` 的基础波形都没有，后面的 mixer、LPF、PID、自动重锁、AI 都没有可靠基础。
