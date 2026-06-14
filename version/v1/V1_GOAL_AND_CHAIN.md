# V1_GOAL_AND_CHAIN

## 2026-06-10 v2 目标链路更新

当前进入 `v2 PI/PID` 方案准备阶段后，目标链路应按下面理解：

```text
PD -> BPF -> ZFL -> ADC -> FPGA mixer+LPF -> FPGA PI/PID -> DAC -> 激光器反馈
```

其中：

- `ZFL-500LN+` 暂时保留；
- `digital gain` 只做 ADC 后幅度匹配和 DAC 输出缩放，不能替代 `ZFL-500LN+`；
- 当 ADC 前 SNR 不足时，FPGA 内部 `digital gain` 不能恢复已经丢失的信噪比；
- `v2` 当前目标是替代 `D2-125` 的基本 servo 功能，而不是替代全部模拟前级；
- 当前仍不允许直接闭环，必须先完成 v2a/v2b/v2c。

## 2026-06-09 论文目标下的 v1-v5 主线重构

本项目最终论文目标是：

```text
基于 Red Pitaya 的全自动数字稳频参数优化系统
```

因此 v1 不是最终目标，而是整套论文系统的第一层：先把 error signal 做成可用、可接、可验证的物理信号。完整路线为：

| 阶段 | 论文/工程目标 | 当前状态 |
|---|---|---|
| v1 | FPGA error signal generation + D2-125 access verification | 当前处于 `v1i` 前置安全验证 |
| v2 | FPGA PID / servo replacing D2-125 | 未开始 |
| v3 | lock / relock FSM | 未开始 |
| v4 | dataset + benchmark | 未开始 |
| v5 | AI slow supervisory optimization | 未开始 |

关键分层：

```text
FPGA = fast deterministic inner loop
AI   = slow supervisory outer loop
```

当前最小目标不是 AI，也不是 FPGA PID，而是确认：

```text
FPGA OUT1 error-like signal
  -> D2-125 error input
  -> D2-125 后级稳定响应
```

只有 D2-125 安全接入、极性、offset、削顶、噪声、依赖性和可重复性验证通过后，才允许准备低增益短时间闭环。

## 2026-06-09 当前阶段状态更新

当前最新状态：

| 阶段 | 状态 |
|---|---|
| v1d | 已通过 |
| v1e | 真实链路 FPGA error-like signal 已看到，直接输出基准约 `160 mVpp` |
| v1i 前置验证 | FPGA OUT1 输入 D2-125 后，D2-125 后级输出约 `3.42 Vpp` |
| v1i 正式 D2-125 安全接入 | 下一步 |
| v2 FPGA PID | 未开始 |
| v3 auto-lock | 未开始 |
| v5 AI | 未开始 |

当前重要边界：

- FPGA 已经替代 `ZFM-3+ mixer + mixer 后 LPF / 低频提取`；
- FPGA 尚未替代带通滤波器、`ZFL-500LN+`、`D2-125 PID / servo`；
- `FPGA OUT1 -> D2-125` 后级响应约 `3.42 Vpp` 是积极结果，但仍然不是闭环锁定完成；
- 下一步是 `D2-125` 安全接入检查和低风险响应验证；
- 当前不允许直接闭环，不允许 PID/AI。

## 0. 本文件作用

本文件是 v1 的目标和链路主线，也是版本路线表、模块-器件映射表、D2-125 安全规则的唯一权威来源。当前状态参见 [[STATUS]]。

## 1. V1 总目标

最终目标是用 Red Pitaya STEMlab 125-14 / FPGA 板子完成 MTS 激光锁定功能。

这个总目标分成两条主线：

1. FPGA 先生成稳定、清晰、幅度合适的 error signal；
2. FPGA 再逐步替代 D2-125 的 PID / servo 控制链路。

换句话说，v1 的重点是 error signal generation；v2 以后才逐步进入 FPGA PID / servo。v1 的终点不是“已经锁住”，而是得到经过示波器和 D2-125 安全接入验证的 error signal。

分解目标：

- A. FPGA 生成 error signal；
- B. FPGA error signal 驱动 D2-125；
- C. FPGA 内部 PID 替代 D2-125；
- D. 自动锁定；
- E. AI 优化。

## 2. 真实实验链路与数字对应

```
真实模拟链路：
PD → 10 MHz LPF → 1.8 MHz HPF → ZFL-500LN+ → ZFM-3+ Mixer (× 4.6 MHz REF) → mixer 后 LPF → D2-125

目标数字链路：
PD → Red Pitaya ADC → digital BPF → digital gain → digital mixer → post-mixer LPF → OUT1 → D2-125
```

## 3. 模块-器件一一对应表（唯一权威版本）

| 真实器件 | FPGA 模块 | 阶段 | 状态 |
|---|---|---|---|
| ZFM-3+ Mixer | `mixer_core.sv` | v1c | ✅ 已通过 |
| mixer 后 LPF | `lpf_core.sv` | v1d | ✅ 仿真和信号源差频上板测试已通过 |
| 10 MHz LPF + 1.8 MHz HPF | `bpf_core.sv` / pre-mixer filter | v1f | 未开始 |
| ZFL-500LN+ (~24 dB) | `digital_gain.sv` | v1g | 未开始 |
| 相位调节 | phase register / IQ demod | v1h | 未开始 |
| OUT1 安全输出 | `output_protect.sv` | v1ab | ✅ 已就位 |
| D2-125 Servo | 外部接口（非 FPGA 模块） | v1i | 未开始 |
| FPGA PID | `pid_core.sv` | v2 | 未开始 |
| AI 自动锁频 | PC/ARM/状态机 | v5 | 未开始 |

## 4. V1 分阶段路线（唯一权威版本）

| 阶段 | 目标 | 替代器件 | 状态 |
|---|---|---|---|
| v1ab | IN1/IN2 → OUT1 通路验证 | （无，验证硬件基础） | ✅ 已通过 |
| v1c | raw digital mixer | ZFM-3+ | ✅ 已通过 |
| v1d | mixer 后 LPF | mixer 后 LPF | ✅ 仿真和信号源差频上板测试已通过 |
| v1e-A | 保留模拟前级，FPGA 替代 ZFM-3+ + mixer 后 LPF 初测 | ZFM-3+ + 后级 LPF 整体 | 已看到真实链路 FPGA error-like signal |
| v1e-B | 模拟 mixer、D2-125、FPGA OUT1 三基准对照 | 系统对照 | 已记录 |
| v1f | pre-mixer BPF | 10 MHz LPF + 1.8 MHz HPF | 未开始 |
| v1g | digital gain / output scaling | 输出增益/缩放 | 下一步 |
| v1h | I-Q / phase correction | 相位调节 | 未开始 |
| v1i | OUT1 → D2-125 安全接口 | 信号线 | 未开始 |

后续：v2 (FPGA PID) → v3 (sweep) → v4 (lock/relock FSM) → v5 (AI)。

## 5. v1d 当前开发边界

v1d 已经完成信号源差频上板测试：`raw mixer → LPF → OUT1`。

已验证：

```text
100 kHz x 102 kHz -> OUT1 约 1.992 kHz
100 kHz x 101 kHz -> OUT1 约 1 kHz
```

这说明 mixer 后 LPF 能保留低频 / 差频 / 基带分量，并压制较高频的和频分量。

v1d 仍然不接真实 PD，不接 D2-125。

禁止：做 pre-mixer BPF、digital gain、I/Q、PID、AI、声称得到最终 MTS error。

历史状态：v1d 信号源差频测试通过后，下一阶段是 v1e。当前已经进入 `v1e-A_real_chain_mixer_replacement` 初测，并在真实链路下观察到 FPGA OUT1 error-like signal。

## 5.1 v1e-A 当前状态：真实链路 error-like signal 初测中

`v1e-A_real_chain_mixer_replacement` 的目标是先保留模拟前级：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
```

同时用 Red Pitaya FPGA 替代：

```text
ZFM-3+ mixer
  -> mixer 后低频提取
```

当前 FPGA 参数：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

当前数据流：

```text
IN1 = 模拟前级处理后的 PD 调制信号
IN2 = 与 EOM 同源的 4.6 MHz REF
OUT1 = mixer_core + lpf_core 后的 error-like signal
```

当前已经观察到：

```text
CH1 scan/ramp: 约 48.913 Hz，约 14.1 mVpp
CH2 PD/饱和吸收相关信号: 约 131 mVpp
CH3 analog error reference: 约 80 mVpp
CH4 FPGA OUT1: 约 160-170 mVpp，截图读数约 169 mV
截图 / 文件标记: mix-lpf-dui2
```

这个结果说明真实链路下 FPGA mixer+LPF 已经能产生随 scan / PD 峰位置变化的 error-like 结构。它是重要进展，但不是完全通过。当前还必须补充 IN1/IN2 依赖性测试、REF 幅度扫描、REF 相位扫描、稳定性和可重复性记录。

当前仍然禁止接 D2-125、闭环锁定、PID、AI，也不能声称已经得到最终可锁定 MTS error signal。

### 5.2 v1e-A 对照结论与 v1g 准备

最新三基准对照实验进一步确认：

```text
基准 A：模拟 mixer 直接输出约 0.46-0.47 Vpp，噪声大，有过零点但不够干净
基准 B：D2-125 后级输出约 1.57-1.8 Vpp，噪声小、形状好、过零点清晰
基准 C：FPGA OUT1 约 0.16 Vpp，噪声小、形状好、过零点清晰，并与模拟 mixer 输出对应
```

这说明当前 FPGA 已经替代了：

```text
ZFM-3+ mixer
  -> mixer 后低频提取 / LPF
```

但当前没有替代：

```text
10 MHz LPF
1.8 MHz HPF
ZFL-500LN+ amplifier
D2-125
PID
AI
```

当前主要差距不是“有没有 error-like signal”，而是“如何把这个好的 error-like signal 安全地交给锁定系统”。new-6.9 后已经观察到 `FPGA OUT1 -> D2-125` 后级约 `3.42 Vpp` 响应，所以当前优先级改为 `v1i_D2-125` 安全接入前置验证。`v1g_digital_gain_output_scaling` 保留为可选优化：只有当 D2-125 输入响应不足、且确认不会饱和时，才开发 `gain x2 / x4`。

后续路线：

1. v1i：FPGA OUT1 -> D2-125 error input 安全接入前置验证；
2. v1g：digital gain / output scaling，可选优化；
3. v1h：REF 相位扫描 / I-Q 优化；
4. v2：FPGA PID 替代 D2-125；
5. v3：自动寻峰 / 重锁 FSM；
6. v4：数据集与 benchmark；
7. v5：AI 慢速监督优化。

`v1i_d2_125_safety` 当前处于前置验证阶段；`v2_pid` 仍未开始；`v5_ai` 仍未开始。

前级 `10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+ 放大器` 暂时不替代。等 FPGA error signal 经 D2-125 能尝试锁定，或 FPGA PID 初步跑通后，再逐步替代前级滤波和放大。

## 6. D2-125 安全接入规则（唯一权威版本）

D2-125 是外部激光伺服控制器。接入前必须确认以下全部参数：

- 输入电压范围（error input 可接受的最大/最小电压）
- 输入阻抗
- 极性（正误差电压对应激光频率偏高还是偏低）
- 带宽
- 是否需要外部衰减或放大
- 允许最大输入电压（超过可能损坏）

**接入硬边界**：

1. 以上参数全部确认前，**严禁接入 D2-125**
2. 接入前必须先用示波器确认 OUT1 幅度、offset、噪声、极性全部安全
3. 接入时严格按此顺序：断开 D2-125 原模拟输入 → 确认 D2-125 输出无异常 → 接入 FPGA OUT1 → 观察 D2-125 error monitor
4. 接入后如果出现振荡、饱和或异常输出，**立刻断开**
5. v1i 只允许 OUT1 → D2-125 error input；不允许 FPGA 直接控制激光器反馈

此规则适用于 v1i 及所有后续阶段。D2-125 接入的相关决策必须经过用户和 GPT 双重审查。

## 7. V1 成功标准

1. v1c：数字 mixer 能工作（✅）
2. v1d：mixer 后 LPF 能提取低频/差频/基带分量（✅ 信号源差频上板测试已通过）
3. v1e-A：真实链路下已观察到 error-like signal（补充依赖性、幅度、相位、稳定性验证中）
4. v1f：pre-mixer BPF 改善信号质量
5. v1g：gain/scaling 使输出幅度合适
6. v1h：phase/I-Q 优化 error 形状
7. v1i：OUT1 安全接入 D2-125
