# 从 FPGA 误差信号到 FPGA 完成锁定的路线图

## 2026-06-10 v2 PI/PID 设计方案

当前主线进入 `v2 PI/PID` 方案准备阶段。`v2` 的替代对象是 `D2-125 Servo / PID` 的基本控制功能，而不是前级 `ZFL-500LN+`、BPF 或 AI 自动锁定。

当前仍然不允许直接闭环。只有 `v2c` 通过后，才允许进入 `v2d` 低增益短时间闭环。

## v2 PI/PID 文献依据简表

| 资料/论文 | 与 v2 相关的点 | 对本项目采用/不采用的决定 |
|---|---|---|
| Linien: Red Pitaya FPGA laser locking | Red Pitaya 上可做数字解调、IIR filtering、PID/DAC 输出；自动选锁点和参数优化属于更高层功能。 | v2 采用实时 FPGA servo 链路和低延迟 filtering/PID 思想；automatic lock point / machine learning 暂不用在 v2，保留到 v3/v5。 |
| PyRPL / Lockbox / IQ / PID | Red Pitaya 的 IQ、IIR、PID 和 Lockbox 模块说明了实时 DSP 路由、输出动态范围、低通带宽和状态机分层。 | v2 采用 enable、polarity、gain、output limit、safe output 等控制器接口；Lockbox 状态机保留到 v3。 |
| Digital laser frequency and intensity stabilization based on STEMlab | STEMlab/Red Pitaya 可作为 PI 控制平台，但输入/输出幅度、offset、DAC 噪声、延迟和带宽必须实测约束。 | v2 第一版优先 PI，不优先完整 PID；必须有 output_limit、anti-windup、safe output 和低增益测试路线。 |

## v2 第一版为什么采用 PI，而不是完整 PID

v2 第一版采用 `PI`：

- `P` 项负责对当前误差做即时响应；
- `I` 项负责消除静态误差；
- `D` 项容易放大 error signal 噪声，第一版上板风险更高；
- 当前目标是安全替代 `D2-125` 的基本 servo 功能，不是一次性完成复杂控制器；
- 已验证 FPGA mixer+LPF 产生的 error-like signal 可以让 `D2-125` 锁定，因此第一版重点是安全、可控、可回退；
- 先做 PI 可以减少参数维度，便于用户测试和 GPT/Codex/Claude Code 分工审查。

第一版必须包含：

- `enable_i`；
- `polarity_i`；
- `kp_i`；
- `ki_i`；
- signed 宽位 `integrator`；
- `anti-windup`；
- `output_limit_i`；
- `offset_i`；
- reset / disable 时的 safe output；
- 可选 debug：`p_term`、`i_term`、`sat_o`。

## v2a-v2d 分阶段测试路线

| 阶段 | 目标 | 允许接线 | 通过重点 |
|---|---|---|---|
| v2a | PI/PID RTL 方案与 testbench | 不接板子，只仿真 | signed、饱和、reset、enable、极性、anti-windup、output_limit、offset、safe output |
| v2b | 信号源模拟 error 输入测试 | PI 输出只接示波器，不接激光器 | 输出方向、限幅、enable、offset、无随机跳变 |
| v2c | 真实 FPGA error 输入，PI 输出只接示波器 | 使用真实 MTS error，输出仍不接激光器 | 无削顶、无异常漂移、无 windup、噪声可接受、关断安全 |
| v2d | 低增益短时间闭环 | 仅 v2c 通过后，低 `kp/ki` 短时闭环 | 能否锁、锁多久、是否饱和、是否发散、极性是否正确 |

硬边界：

- 当前不允许直接闭环；
- 当前不允许 AI；
- `v2d` 只有在 `v2c` 通过后才允许；
- `ZFL-500LN+` 暂时保留；
- `digital gain` 不能替代 ADC 前低噪声模拟放大。

## 2026-06-09 论文导向路线重构

当前路线必须服务于最终论文目标：

```text
基于 Red Pitaya 的全自动数字稳频参数优化系统
```

目标报告的核心判断是：只复现一个数字锁定器不够，真正有价值的是“FPGA 快速确定内环 + AI 慢速监督外环”。因此本项目路线重构为：

```text
v1: FPGA 生成 error signal，并完成 D2-125 安全接入验证
v2: FPGA PID / servo，逐步替代 D2-125
v3: lock / relock FSM，实现确定性自动锁定
v4: dataset + benchmark，建立可复现评价体系
v5: AI slow supervisory optimization
```

当前处于：

```text
v1i_D2-125 安全接入前置验证
```

当前不再把 `v1g digital gain` 当作唯一下一步。因为已经观察到 `FPGA OUT1 -> D2-125` 后 CH3 约 `3.42 Vpp` 的明显响应，所以最重要的是安全、极性、offset、削顶、噪声和依赖性测试。若 D2-125 输入响应不足，再回到 `v1g gain x2 / x4`。

## 2026-06-09 路线图更新：new-6.9 后的当前路线

当前路线调整为：

| 阶段 | 状态 | 说明 |
|---|---|---|
| A. FPGA 生成 error-like signal | 已完成 | FPGA 直接输出基准约 `160 mVpp` |
| B. FPGA OUT1 输入 D2-125 后级响应 | 已看到 | D2-125 后级输出 CH3 约 `3.42 Vpp`，初步成功 |
| C. D2-125 安全接入检查 | 下一步 | 只观察响应，不直接闭环 |
| D. D2-125 + FPGA error 低增益短时间锁定 | 后续 | 安全检查、极性、offset、重复性通过后才允许 |
| E. FPGA PID 替代 D2-125 | v2，未开始 | 不用 PID 修复尚未确认的 error signal |

FPGA 锁定路线中，误差信号质量指标优先级为：

1. 过零点清晰度；
2. 零点附近斜率；
3. 噪声；
4. 多次扫描重复性；
5. 与 PD / 谱线位置对应；
6. D2-125 响应；
7. `Vpp` 只是辅助指标。

当前重要判断：

- FPGA 直接输出约 `160 mVpp` 已经是可用候选 error signal；
- 三通/并联 REF 条件下 FPGA OUT1 降到 `30-120 mVpp` 不代表 FPGA 失败；
- FPGA OUT1 输入 D2-125 后 CH3 约 `3.42 Vpp`，说明 D2-125 后级对 FPGA error 有明显响应；
- 当前仍然没有完成 FPGA 锁定；
- 当前仍然不允许直接闭环；
- 当前仍然不允许启动 PID/AI。

## 1. 当前状态

当前 FPGA 已经能在真实链路中生成 error-like signal。

当前真实链路是：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ 放大器
  -> Red Pitaya IN1

4.6 MHz REF
  -> Red Pitaya IN2

FPGA:
  IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

当前 FPGA 程序参数：

```systemverilog
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 3
```

当前 FPGA OUT1 观测：

- Vpp 约 `0.16 Vpp`；
- 噪声小；
- 形状好；
- 过零点清晰；
- 和模拟 mixer 直接输出对应。

三组基准对照：

| 基准 | 信号 | Vpp | 观察 |
|---|---|---:|---|
| A | 模拟 mixer 直接输出 | `0.46-0.47 Vpp` | 噪声大，有过零点但不够干净 |
| B | D2-125 后级输出 | `1.57-1.8 Vpp` | 噪声小，形状好，过零点清晰 |
| C | FPGA OUT1 | `0.16 Vpp` | 噪声小，形状好，过零点清晰 |

这说明 FPGA 已经初步完成了 `ZFM-3+ mixer + mixer 后 LPF / 低频提取` 的数字替代，但还没有完成激光锁定。

## 2. 为什么不能立刻替代 D2-125

D2-125 不是一根普通线，也不只是一个显示器。它可能包含：

- 输入增益；
- 滤波；
- offset 调整；
- PID；
- 输出缩放；
- servo 输出到激光器。

当前 FPGA 只替代了 error generation 的一部分：

```text
PD 调制信号 x 4.6 MHz REF
  -> 低频 error-like signal
```

当前 FPGA 还没有替代：

```text
D2-125 PID / servo
```

所以不能直接说“FPGA 已经能锁定”，也不能直接把 FPGA OUT1 接 D2-125 后马上闭环。正确做法是先让 FPGA error signal 通过 D2-125 原有伺服系统验证可锁性，再逐步把 D2-125 的控制功能搬进 FPGA。

## 3. FPGA 完成锁定的分阶段路线

### 阶段 1：v1g digital gain / output scaling

历史说明：本节是 2026-06-01 阶段的路线。new-6.9 后已经观察到 `FPGA OUT1 -> D2-125` 后级约 `3.42 Vpp` 响应，因此当前执行优先级改为 `v1i` 安全验证；`v1g` 保留为可选优化。

目标：

```text
FPGA OUT1: 0.16 Vpp -> 0.5-1.0 Vpp
```

建议测试：

```text
gain x2 -> 约 0.32 Vpp
gain x4 -> 约 0.64 Vpp
gain x8 -> 约 1.28 Vpp
```

优先从 `gain x4` 开始，因为它能把 `0.16 Vpp` 提高到约 `0.64 Vpp`，同时比 `x8` 更不容易削顶。

### 阶段 2：v1h phase / I-Q optimization

目标：

找到误差信号斜率最大、过零点最清晰、噪声最低的 REF 相位。

如果单相位 REF 不够稳定，后续考虑 I/Q 数字解调：

```text
I = PD x cos(wt) -> LPF
Q = PD x sin(wt) -> LPF
```

然后从 I/Q 中选择最适合锁定的组合。

### 阶段 3：v1i FPGA OUT1 -> D2-125 error input

目标：

```text
FPGA OUT1 -> D2-125 error input
```

第一步只观察 D2-125 对 FPGA error 的响应，不直接闭环锁定。

必须先确认：

- FPGA OUT1 幅度安全；
- offset 合适；
- 极性明确；
- 不削顶；
- D2-125 error input 允许范围确认；
- D2-125 output 暂不接激光器，只观察响应。

确认安全后，再尝试让 D2-125 使用 FPGA error signal 进行锁定。

### 阶段 4：v2 FPGA PID

目标：

在 FPGA 内部实现 PID / servo，逐步替代 D2-125。

进入条件：

- D2-125 能用 FPGA error signal 锁定；
- 已记录锁定参数；
- 知道需要的 servo 极性、增益、带宽；
- FPGA error signal 稳定、可重复。

### 阶段 5：v3 auto-lock / relock FSM

目标：

实现：

- 自动找峰；
- 判断锁定状态；
- 失锁重扫；
- 自动重锁。

这一步是确定性状态机，不是 AI。

### 阶段 6：v5 AI optimization

目标：

基于数据集做：

- 锁定状态识别；
- 自动参数优化；
- 智能重锁。

AI 不替代基本物理链路，也不跳过安全联锁。

## 4. 进入 D2-125 安全接入前的条件

必须满足：

- FPGA OUT1 在 D2-125 error input 可接受范围内；
- 如果当前约 `160 mVpp` 已能让 D2-125 后级产生清晰响应，则不强制先放大到 `0.5-1.0 Vpp`；
- 不削顶；
- 噪声低；
- 过零点清晰；
- 极性确认；
- offset 合适；
- D2-125 error input 允许；
- 先不开闭环，只看响应。

如果任何一项不满足，不允许接 D2-125。

历史说明：早期曾把 `0.5-1.0 Vpp` 当作接入前目标幅度。new-6.9 后已经观察到 `FPGA OUT1 -> D2-125` 后级约 `3.42 Vpp` 的响应，所以当前判断应以 D2-125 实测响应、是否饱和、过零点、噪声和安全范围为准，而不是单纯追求更大 FPGA OUT1 Vpp。

## 5. 进入 FPGA PID 前的条件

必须满足：

- D2-125 能用 FPGA error signal 锁定；
- 已记录锁定参数；
- 知道需要的 servo 极性、增益、带宽；
- FPGA PID 才开始替代 D2-125。

也就是说，FPGA PID 不是拿来修复坏 error signal 的工具。它应该建立在已经可用、可重复、能驱动 D2-125 的 error signal 之上。

## 6. 前级滤波和放大器替代时机

当前暂时不替代：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ 放大器`。

只有在：

1. FPGA error signal 经 D2-125 能尝试锁定；或
2. FPGA PID 初步跑通；

之后，再逐步替代前级：

1. 先替代 `ZFL-500LN+ 放大器`，用 digital gain；
2. 再替代 `1.8 MHz HPF`；
3. 最后替代 `10 MHz LPF`。

这样做的原因是：当前真实模拟前级已经能提供可用的 PD 调制信号。过早替代前级会同时引入太多变量，让问题无法定位。
