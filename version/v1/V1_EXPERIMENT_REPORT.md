# V1_EXPERIMENT_REPORT

## 2026-06-10 当前阶段判断：保留 ZFL，集中替代 D2-125

由于无 `ZFL-500LN+` 时没有可用误差信号，`ZFL-500LN+` 暂时作为最小模拟前级保留；下一步集中替代 `D2-125`。

当前关键事实：

- `FPGA mixer+LPF -> D2-125` 已经验证可锁定，说明 FPGA 生成的 error-like signal 具备闭环可用性；
- 锁定时噪声不大，无明显削顶；
- `digital gain` 不能替代 ADC 前低噪声放大；
- 当前主线是 `v2 FPGA PI/PID` 替代 `D2-125`，不是继续替代前级 `ZFL-500LN+`；
- 当前仍不允许直接闭环，不允许 AI。

## 2026-06-09 当前权威判读：从实验结果走向论文路线

当前项目总目标已经对齐为：

```text
基于 Red Pitaya 的全自动数字稳频参数优化系统
```

当前工程现实是：

```text
FPGA 已经初步完成 ZFM-3+ mixer + mixer 后 LPF / 低频提取的数字替代。
FPGA 尚未替代 D2-125 PID / servo。
FPGA 尚未实现闭环锁定。
AI 尚未开始。
```

目标报告给出的路线是分层系统：

```text
FPGA = 快速确定性内环
AI   = 慢速监督外环
```

因此当前 `new-6.9` 三组实验的意义不是“马上做 AI”，也不是“马上写 PID”，而是确认 FPGA error-like signal 已经值得进入 `D2-125` 安全接入前置验证。

### new-6.9 三组关键实验

| 测试 | 链路 | 观测 | 当前判断 |
|---|---|---|---|
| A | FPGA 直接输出 | FPGA OUT1 error-like signal 约 `160 mVpp` | FPGA 已能在真实链路下产生 error-like 输出 |
| B | 三通 / 并联 REF 条件 | FPGA OUT1 可能下降到约 `30-120 mVpp` | 该现象受 REF 分配、负载、相位和接线影响，不能单独判断 FPGA 失败 |
| C | FPGA OUT1 输入 D2-125 | D2-125 后级输出 CH3 约 `3.42 Vpp` | D2-125 对 FPGA error input 有明显响应，但还不是闭环锁定 |

### 关于 CH2 与 FPGA OUT1 幅度的说明

当前观察到 CH2 饱和吸收 / PD 相关信号约 `470-800 mVpp`。CH2 与 FPGA OUT1 不能直接按 Vpp 比较，因为：

1. CH2 是 PD / 饱和吸收相关通道；
2. FPGA OUT1 是经过 mixer+LPF 后的 error-like 输出；
3. 二者物理含义不同；
4. FPGA OUT1 的评价重点是过零点、斜率、噪声、重复性和能否安全驱动 D2-125。

### 当前结论

当前结果足以进入：

```text
v1i_D2-125 安全接入前置验证
```

但当前仍不允许：

- 直接闭环；
- 直接把 D2-125 输出接激光器反馈；
- 进入 FPGA PID；
- 进入 AI；
- 盲目增加 digital gain。

下一步实验记录应按：

```text
E:\new\fpga_lock\v94\version\v1\V1I_D2_125_SAFETY_TEST_SOP.md
```

执行和填写。

## 2026-06-09 new-6.9：三组测试对比记录

### 1. 当前真实链路背景

当前已经更换实验平台，并且气室已经加热。真实链路仍然保留模拟前级：

```text
PD
  -> 带通滤波器
  -> ZFL-500LN+ 放大器
  -> Red Pitaya IN1

同源 4.6 MHz REF
  -> Red Pitaya IN2

FPGA:
  IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

当前 FPGA 替代的是：

```text
ZFM-3+ mixer
  -> mixer 后 LPF / 低频提取
```

当前 FPGA 尚未替代带通滤波器、`ZFL-500LN+` 放大器、`D2-125 PID / servo` 和闭环锁定功能。

### 2. 测试 A：FPGA 直接输出误差信号，约 160 mVpp

实验接法：

```text
PD -> 带通滤波器 -> ZFL-500LN+ 放大器 -> Red Pitaya IN1
4.6 MHz REF -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器
```

不经过 `D2-125`。

实验现象：

在不接入 `D2-125`，仅使用 FPGA 完成 `mixer+LPF` 的情况下，Red Pitaya `OUT1` 可以得到 error-like signal，`Vpp` 约 `160 mVpp`。

实验意义：

1. FPGA 板子本身已经能够在真实 PD 链路下生成 error-like signal；
2. `160 mVpp` 是“FPGA 直接输出”的基准结果；
3. 该信号虽然幅度不大，但已经具有谱线相关结构；
4. 后续判断 FPGA 是否成功，不应只看 `Vpp`，而应看是否和 PD 峰位置对应、是否有清晰过零点、噪声是否低、是否能驱动 `D2-125` 后级产生响应。

### 3. 测试 B：三通/并联 REF 条件下，FPGA OUT1 约 30-120 mVpp

实验接法：

同一个 `4.6 MHz REF` 通过三通或并联方式，同时分给模拟链路 / `D2-125` 相关链路和 Red Pitaya `IN2`。PD 仍然经过带通滤波器和 `ZFL-500LN+` 放大器进入 `IN1`。

实验现象：

在三通 / 并联 REF 条件下，FPGA `OUT1` 直接输出可能下降到约 `30-120 mVpp`。

实验意义和解释：

1. 该结果不应单独作为 FPGA 能力上限；
2. 三通/并联 REF 可能改变进入 Red Pitaya `IN2` 的 REF 幅度和相位；
3. 普通三通不是理想功分器，会受到负载、阻抗、线缆、示波器和模拟 mixer 输入影响；
4. FPGA `OUT1` 变小，很可能与 REF 被加载、分压、相位变化有关；
5. 后续正式实验应尽量使用同一台双通道信号源同步输出，或正规 `50 ohm` 功分器，并实测 Red Pitaya `IN2` 端 REF 实际 `Vpp`；
6. 不要因为三通条件下 CH4 只有 `30-120 mVpp` 就判断 FPGA 失败。

### 4. 测试 C：FPGA OUT1 输入 D2-125 后，D2-125 后级输出 CH3 约 3.42 Vpp

实验接法：

```text
PD -> 带通滤波器 -> ZFL-500LN+ 放大器 -> Red Pitaya IN1
4.6 MHz REF -> Red Pitaya IN2

FPGA:
  IN1 x IN2 -> mixer_core -> lpf_core -> OUT1

Red Pitaya OUT1
  -> D2-125 error input / 后级输入
  -> D2-125 后级输出
  -> 示波器 CH3
```

示波器通道说明：

| 通道 | 颜色 | 观测对象 | 记录 |
|---|---|---|---|
| CH1 | 黄色 | scan/ramp | 频率约 `48.962 Hz`，`Vpp` 约 `38.4 mV` |
| CH2 | 绿色 | PD / 饱和吸收相关信号 | `Vpp` 可达约 `470-800 mV` |
| CH3 | 蓝色 | FPGA OUT1 输入 D2-125 后的后级输出 | `Vpp` 约 `3.42 V` |
| CH4 | 红色 | 直接观测到的板子输出 / 相关小信号 | 部分测试约 `30-120 mVpp`，受 REF 分配、三通负载、相位、接线和示波器设置影响 |

实验意义：

1. FPGA 生成的 error-like signal 虽然直接 `OUT1` 幅度较小，但已经能够驱动 `D2-125` 后级产生明显响应；
2. `D2-125` 后级输出约 `3.42 Vpp`，说明 `D2-125` 对 FPGA error 输入有增益、滤波、offset/servo 处理或输出缩放作用；
3. 这是 `v1i_D2-125` 安全接入前置验证的积极结果；
4. 但当前不能写成“已经完成 FPGA 锁定”。

当前不能声称已锁定的原因：

- 目前只是看到 `D2-125` 后级响应；
- 还没有确认闭环极性；
- 还没有确认 `D2-125` 输出到激光器反馈端的安全性；
- 还没有做低增益闭环；
- 还没有验证锁定稳定性；
- 还没有失锁保护；
- 还没有 FPGA PID。

推荐结论写法：

```text
FPGA OUT1 -> D2-125 后级响应测试初步成功，但仍属于 v1i 前置安全验证，不是闭环锁定完成。
```

### 5. 三层级对比表

| 层级 | 接法 | 观测幅度 | 意义 |
|---|---|---|---|
| FPGA 直接输出 | `PD->BPF->ZFL->IN1`，`REF->IN2`，`OUT1->示波器` | 约 `160 mVpp` | 板子 `mixer+LPF` 直接生成 error-like signal 的基准 |
| 三通/并联 REF 条件下 FPGA 输出 | REF 同时分给模拟链路和 FPGA，`OUT1->示波器` | 约 `30-120 mVpp` | 受 REF 分配、负载、相位、接线影响，不代表 FPGA 能力上限 |
| FPGA OUT1 输入 D2-125 后级 | `OUT1->D2-125->示波器 CH3` | 约 `3.42 Vpp` | D2-125 对 FPGA error signal 有明显后级响应，说明可进入 D2-125 安全接入前置验证 |

### 6. 当前限制

当前仍然没有完成 FPGA 锁定。当前也不允许直接闭环，不允许启动 PID/AI，不允许立刻替代前级 BPF / `ZFL-500LN+`。

## CH2 饱和吸收信号与 CH4 FPGA error signal 幅度差异分析

当前观察：

- CH2 绿色：PD / 饱和吸收相关信号，`Vpp` 约 `470-800 mV`；
- CH4 / FPGA OUT1：Red Pitaya 输出的 FPGA `mixer+LPF` 误差信号，常见约 `120 mVpp` 左右；部分测试在使用三通分 REF 或接线条件变化时可降至约 `30-40 mVpp`。

必须明确：

CH2 的 PD / 饱和吸收信号 `Vpp` 不能和 CH4 的 FPGA error `Vpp` 直接比较。

原因是 CH2 是光强/吸收包络信号，包含 DC 背景、扫描背景、饱和吸收峰、光强变化和低频包络。CH4 是 FPGA 对 PD 中 `4.6 MHz` 调制相关分量进行同步解调后得到的低频 error-like signal，不是把整个 PD 光强包络直接放大输出。

当前 FPGA 完成的是：

```text
IN1 中的 4.6 MHz 调制相关分量
  x IN2 的 4.6 MHz REF
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1 error-like signal
```

即使 CH2 饱和吸收信号有 `470-800 mVpp`，FPGA OUT1 只有约 `120 mVpp` 也是合理的。真正决定 FPGA OUT1 幅度的是 IN1 中实际 `4.6 MHz` 调制分量幅度、IN2 REF 实际幅度、REF 相位、`mixer_core` 缩放、`lpf_core` 低通后幅度、`output_protect` / DAC 输出映射、三通 REF 加载、digital gain 状态、示波器阻抗和接线状态。

当前判断：

FPGA OUT1 约 `120 mVpp` 并不代表失败。更重要的是：

- CH4 是否和 CH2 谱线位置对应；
- CH4 是否有清晰过零点；
- CH4 是否噪声低；
- CH4 是否能驱动 `D2-125` 后级产生稳定响应；
- CH4 输入 `D2-125` 后是否能得到清晰后级误差信号。

### 下一步

下一步不是直接闭环，也不是启动 PID/AI，而是进入 `v1i_D2-125` 安全接入前置验证：确认 `Red Pitaya OUT1 -> D2-125 error input` 的电压范围、offset 和极性，检查 D2-125 后级输出 CH3 是否削顶、是否有清晰过零点、噪声是否可接受，检查 CH3 与 CH2 PD 峰位置是否对应，并确认多次扫描重复性。

## 2026-06-01 v1e-B 三基准对照实验：模拟 mixer、D2-125、FPGA OUT1

### 1. 当前真实链路

当前 PD 信号不是原始 PD 直接进入 FPGA。真实链路是：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ 放大器
  -> Red Pitaya IN1
```

外部参考链路是：

```text
4.6 MHz REF
  -> Red Pitaya IN2
```

当前 FPGA 内部链路是：

```text
IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

当前 FPGA 程序参数：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

所以当前 FPGA 替代的是：

```text
ZFM-3+ mixer
  -> mixer 后 LPF / 低频提取
```

当前 FPGA 暂时没有替代：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ 放大器`；
- `D2-125 PID / servo`。

### 2. 基准 A：模拟 mixer 直接输出

链路：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ 放大器
  -> 原模拟 mixer
  -> 直接接示波器
```

不经过 D2-125。

实验结果：

| 项目 | 结果 |
|---|---|
| Vpp | 约 `0.46-0.47 Vpp` |
| 噪声 | 大 |
| 是否有清晰过零点 | 有，但不清晰，噪声较大 |
| 是否和 PD 峰对应 | 有 |

结论：

模拟 mixer 直接输出本身噪声较大，过零点存在但不够干净。这说明“模拟 mixer 直接出来”并不等于“已经适合锁定”，后级处理非常重要。

### 3. 基准 B：D2-125 后级输出

链路：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ 放大器
  -> 原模拟 mixer
  -> D2-125 后级输出 / 原模拟系统参考输出
  -> 示波器
```

实验结果：

| 项目 | 结果 |
|---|---|
| Vpp | 约 `1.57-1.8 Vpp` |
| 噪声 | 小 |
| 形状 | 好 |
| 过零点 | 清晰 |

结论：

D2-125 或其后级链路不仅承担 servo 功能，也可能提供了增益、滤波、offset 调整、带宽限制或输出缩放作用。它让误差信号变得更大、更干净、更适合锁定。

### 4. 基准 C：FPGA 输出

链路：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ 放大器
  -> Red Pitaya IN1

同源 4.6 MHz REF
  -> Red Pitaya IN2

FPGA:
  mixer_core
  -> lpf_core
  -> OUT1
```

实验结果：

| 项目 | 结果 |
|---|---|
| Vpp | 约 `0.16 Vpp` |
| 噪声 | 小 |
| 形状 | 好 |
| 过零点 | 清晰 |
| 和模拟 mixer 直接输出是否对应 | 是，对应 |

结论：

FPGA 已经能够在真实链路中产生 error-like signal。该信号幅度小于模拟 mixer 直接输出约 `3` 倍，小于 D2-125 后级输出约 `10` 倍。但 FPGA 输出噪声小、形状好、过零点清晰，是非常有价值的误差信号基础。

### 5. 三者对比表

| 基准 | 链路 | Vpp | 噪声 | 形状/过零点 | 当前意义 |
|---|---|---:|---|---|---|
| A | 模拟 mixer 直接输出 | `0.46-0.47 Vpp` | 大 | 有过零点但不够干净 | 原 mixer 本身输出参考 |
| B | D2-125 后级输出 | `1.57-1.8 Vpp` | 小 | 形状好，过零点清晰 | 原系统可锁定参考 |
| C | FPGA OUT1 | `0.16 Vpp` | 小 | 形状好，过零点清晰 | FPGA error signal 基础 |

### 6. 对最终 FPGA 锁定的意义

当前 FPGA 已经初步完成：

```text
ZFM-3+ mixer
  -> mixer 后 LPF / 低频提取
```

但当前 FPGA 还没有完成：

```text
D2-125 PID / servo 替代
```

因此正确路线不是立刻跳到 FPGA PID，也不是立刻声称 FPGA 已经能锁定，而是：

1. 先让 FPGA 生成稳定、清晰、幅度合适的 error signal；
2. 再让 FPGA OUT1 接入 D2-125 error input，让 D2-125 暂时继续负责 servo；
3. 验证 FPGA 误差信号能否驱动原有锁定系统；
4. 最后再在 FPGA 内部实现 PID，逐步替代 D2-125 的 servo/PID 功能。

### 7. 当前限制

当前不能说已经完成 FPGA 锁定，原因是：

- FPGA OUT1 尚未接入 D2-125；
- D2-125 对 FPGA error 的响应尚未测试；
- FPGA 还没有 PID / servo；
- FPGA 还没有自动寻峰、重锁 FSM；
- 还没有 AI；
- 前级 `10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+ 放大器` 仍然保留。

### 8. 下一步实验

下一步按锁定路线推进：

1. `v1g digital gain / output scaling`：把 FPGA OUT1 从约 `0.16 Vpp` 提高到 `0.5-1.0 Vpp`；
2. `v1h REF phase / I-Q optimization`：优化过零点、斜率和噪声；
3. `v1i D2-125 safety input`：FPGA OUT1 输入 D2-125，先不开闭环，只观察响应；
4. `v2 FPGA PID`：在 FPGA 内部逐步替代 D2-125 PID / servo；
5. `v3 auto-lock / relock FSM`：自动找峰、判断锁定状态、失锁重锁；
6. `v5 AI optimization`：基于数据集做锁定状态识别、自动参数优化和智能重锁。

## 2026-05-31 v1e-A FPGA 替代 mixer+LPF 与模拟链路对照实验

### 1. 实验条件

本次实验仍属于 `v1e-A_real_chain_mixer_replacement`。目标是把 FPGA 真实链路输出和原模拟链路输出放在一起比较，判断 FPGA 当前主要差距在哪里。

信号源和接线条件：

- 信号发生器同时给 EOM 和 Red Pitaya `IN2` REF 提供同源 `4.6 MHz sine`；
- REF 和 EOM 均约为 `±1 V / 2 Vpp`；
- PD 信号不是原始 PD 直接进板；
- PD 信号先经过模拟前级：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
  -> Red Pitaya IN1
```

Red Pitaya `IN2` 接外部同源 `4.6 MHz REF`。

当前 FPGA 参数：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

FPGA 内部链路：

```text
IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

### 2. 图 1：FPGA 替代 mixer + LPF 实验结果

图 1 文件 / 说明：

```text
经过混频 + LPF，板子输出误差信号
```

本图中 Red Pitaya 替代原模拟链路中的：

- `ZFM-3+ mixer`；
- mixer 后低频提取 / LPF。

仍然保留模拟前级：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ amplifier`。

观测结果：

| 通道 | 信号 | 说明 |
|---|---|---|
| CH1 | scan/ramp | 扫描参考 |
| CH2 | PD / 饱和吸收相关信号 | 经过模拟前级之前/相关监测信号 |
| CH3 | 本图中不作为主要判断 | 可作为辅助参考 |
| CH4 | Red Pitaya OUT1 | FPGA mixer+LPF 后输出的 error-like signal |

FPGA OUT1 约为：

```text
0.16 Vpp
```

该信号与 scan / PD 峰结构有对应关系，说明 FPGA 已经能够在真实链路下产生 error-like signal。

### 3. 图 2：原模拟链路对照实验结果

图 2 文件 / 说明：

```text
走模拟链路的误差信号
```

原模拟链路为：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
  -> ZFM-3+ mixer
  -> D2-125 / 模拟后级
```

观测结果：

```text
模拟链路 error signal 约 1.57 Vpp
```

这个模拟 error signal 是当前 FPGA 替代链路的幅度和形状对照基准。

### 4. 幅度对比

```text
FPGA 替代链路 OUT1 约 0.16 Vpp
原模拟链路 error 约 1.57 Vpp
幅度比例 = 1.57 / 0.16 ≈ 9.8
```

也就是说，当前 FPGA OUT1 的 error-like 信号已经出现，但幅度大约只有模拟链路对照的十分之一。

### 5. 对比结论

1. FPGA 已经完成真实链路下 mixer+LPF 的功能验证；
2. FPGA OUT1 幅度明显小于原模拟链路；
3. 幅度差异主要可能来自：
   - FPGA digital mixer 缩放；
   - `lpf_core` 只做低通，不做放大；
   - `output_protect` 保守输出；
   - 当前还没有 digital gain / output scaling；
   - 模拟链路 `ZFM-3+` 与后级可能存在额外转换增益或放大。

### 6. 当前没有替代什么

当前 FPGA 替代的是 `ZFM-3+ mixer + mixer 后 LPF`。当前没有替代：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ amplifier`；
- D2-125；
- PID；
- AI。

### 7. 为什么不能只看 Vpp 判断能不能锁

当前 FPGA 输出只有约 `0.16 Vpp`，这说明幅度偏小，但不能直接推出“不能高精度锁定”。锁定质量还取决于：

- 过零点是否清晰；
- 过零点附近斜率是否足够大；
- 噪声 RMS 是否小；
- offset 是否可控；
- 极性是否正确；
- 扫描重复时结构是否稳定。

所以 Vpp 是重要指标，但不是唯一指标。

### 8. 当前限制

当前仍不能直接接 D2-125，原因是：

1. FPGA OUT1 幅度、过零点、噪声和输出安全范围还未完成评估；
2. REF 相位还未扫描；
3. REF 幅度响应还未记录；
4. CH3/CH4 的峰位置、过零点、极性、斜率还未系统比较；
5. v1g digital gain / output scaling 还只是方案阶段。

### 9. 下一步

下一步不是 PID，也不是 AI，而是：

1. REF 相位扫描：`0°、30°、60°、90°、100°、120°、150°、180°`；
2. REF 幅度扫描：`0.3 Vpp、0.5 Vpp、0.8 Vpp、1.0 Vpp`；
3. CH3/CH4 对比：比较模拟 error 和 FPGA error 的峰位置、过零点、极性、斜率；
4. 准备 `v1g digital gain / output scaling` 方案；
5. 方案目标：把 FPGA OUT1 从约 `0.16 Vpp` 提高到 `0.6-1.0 Vpp`，同时不削顶、不饱和。

## 2026-05-30 v1e-A 真实链路 FPGA mixer+LPF 初测记录

### 1. 实验目标

本次阶段记为 `v1e-A_real_chain_mixer_replacement`。

目标不是直接完成激光锁频，而是在真实 MTS 实验链路中先验证一个关键问题：

```text
真实 PD 调制信号经过模拟前级后，
进入 Red Pitaya FPGA 的 mixer_core + lpf_core，
OUT1 是否能出现随 scan / PD 谱线结构变化的 error-like signal。
```

### 2. 保留的模拟前级

本次没有直接把 PD 原始信号送入 FPGA，也没有替代全部模拟链路。当前保留的模拟前级是：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ RF amplifier
```

这些模拟器件继续负责在 ADC 前提取和放大与 `4.6 MHz` 调制相关的 RF 成分。

### 3. FPGA 替代的部分

本次 Red Pitaya FPGA 替代的是：

```text
ZFM-3+ mixer
  -> mixer 后低频提取
```

当前 FPGA 程序参数为：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

`OUTPUT_MODE=3` 的含义是：

```text
IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

### 4. 接线方式

```text
IN1 = 模拟前级处理后的 PD 调制信号
IN2 = 与 EOM 同源的 4.6 MHz REF
OUT1 = FPGA mixer_core + lpf_core 后的 error-like signal
```

这里“同源 REF”非常重要。同步解调依赖 EOM 调制和 REF 之间稳定的相位关系；如果 REF 不同源或相位漂移，OUT1 上的 error-like 信号会出现漂移、呼吸或不稳定。

### 5. 四通道示波器分配与观测数据

截图 / 文件标记：`mix-lpf-dui2`

| 通道 | 颜色 | 信号 | 当前观测 |
|---|---|---|---|
| CH1 | 黄色 | scan / ramp | 频率约 `48.913 Hz`，Vpp 约 `14.1 mV` |
| CH2 | 绿色 | PD / 饱和吸收相关信号 | Vpp 约 `131 mV` |
| CH3 | 蓝色 | 模拟链路参考 / analog error reference | Vpp 约 `80 mV` |
| CH4 | 红色 | FPGA OUT1 error-like signal | Vpp 约 `160-170 mV`，图中读数约 `169 mV` |

### 6. 当前实验现象

1. FPGA OUT1 已经能看到与 scan / PD 峰位置相关的 error-like 结构。
2. CH4 红色波形不是随机噪声，而是随扫描周期重复出现。
3. 使用同源 `4.6 MHz REF` 后，之前的“呼吸现象”明显改善或消失。
4. 当前 FPGA OUT1 幅度约 `160-170 mVpp`。
5. 当前幅度仍低于后续直接接 servo 可能需要的幅度。

### 7. 为什么这个结果重要

这说明真实 PD 调制信号经过模拟前级后，进入 FPGA 的 `mixer_core + lpf_core`，已经可以产生随 scan 和谱线结构变化的低频输出。换句话说，FPGA 不再只是通过信号源正弦的教学测试，而是开始接触真实 MTS 光谱链路。

对小白来说，这一步的意义是：

```text
v1d 证明“电子乘法 + 低通”会工作；
v1e-A 证明“真实实验信号进来以后，这条 FPGA 链路也能看到像 error 的结构”。
```

### 8. 当前限制

当前不能直接说已经得到最终可锁定 MTS error signal，原因是：

1. CH4 幅度目前约 `160-170 mVpp`，还需要确认是否满足后续 servo 输入需求；
2. 还没有完成 IN1 依赖性测试；
3. 还没有完成 IN2 / REF 依赖性测试；
4. 还没有完成 REF 幅度扫描；
5. 还没有完成 REF 相位扫描；
6. 还没有确认 CH4 与 CH2 / CH3 的稳定时间对应关系；
7. 还没有完成 D2-125 输入范围、极性、offset、安全接入评估。

因此当前仍然禁止：

- 不接 D2-125；
- 不闭环锁定；
- 不做 PID；
- 不做 AI；
- 不声称已经得到最终 MTS error signal。

### 9. 下一步验证

下一步不是 PID，也不是 AI，而是继续完成 `v1e-A` 补充验证：

1. 保存 `mix-lpf-dui2` 截图和对应 CSV；
2. 做 IN1 依赖性测试：拔掉 IN1，观察 CH4 是否消失或变成无相关噪声；
3. 做 IN2 / REF 依赖性测试：拔掉 IN2，观察 CH4 是否明显变化；
4. 做 REF 幅度扫描：观察 CH4 幅度是否随 REF 幅度变化；
5. 做 REF 相位扫描：寻找 CH4 结构最清晰、斜率最大、噪声最小的相位；
6. 记录 CH4 与 CH2 / CH3 的时间对应关系；
7. 评估是否需要 `v1e-debug`：例如调整 `LPF_SHIFT` 或增加受控 digital gain。

## 2026-05-27 v1d_mixer_lpf 上板实验记录

### 1. 实验日期

2026-05-27

### 2. 程序模式

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

`OUTPUT_MODE=3` 表示 OUT1 输出 mixer 后低通结果：

```text
IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

### 3. 前置验证

```text
tb_lpf_core PASS
tb_laser_lock_core_v1d PASS
```

说明 `lpf_core` 单模块仿真和 `laser_lock_core` v1d 集成仿真已经通过。

### 4. 测试 A：100 kHz x 102 kHz

输入条件：

```text
IN1 = 100 kHz sine, 500 mVpp, 0 V offset
IN2 = 102 kHz sine, 500 mVpp, 0 V offset
```

理论：

```text
差频 = |102 kHz - 100 kHz| = 2 kHz
```

示波器 OUT1 观测：

```text
频率约 1.992 kHz
周期约 502 us
Vpp 约 68.3 mV
```

结论：符合 `2 kHz` 差频预期。

### 5. 测试 B：100 kHz x 101 kHz

输入条件：

```text
IN1 = 100 kHz sine, 500 mVpp, 0 V offset
IN2 = 101 kHz sine, 500 mVpp, 0 V offset
```

理论：

```text
差频 = |101 kHz - 100 kHz| = 1 kHz
```

示波器 OUT1 观测：

```text
OUT1 已看到 1 kHz 左右差频信号
```

结论：符合 `1 kHz` 差频预期。

### 6. 为什么这说明 v1d 成功

数字 mixer 会同时产生差频项和和频项。以 `100 kHz x 102 kHz` 为例：

```text
差频项 = |102 kHz - 100 kHz| = 2 kHz
和频项 = 102 kHz + 100 kHz = 202 kHz
```

v1d 的 `lpf_core` 是 mixer 后 LPF，它的任务是保留低频 / 差频 / 基带分量，并压制较高频的和频分量。现在 OUT1 能看到约 `2 kHz` 和约 `1 kHz` 差频，说明 FPGA 已经在真实 Red Pitaya 上完成：

```text
IN1/测试信号 x IN2/REF
  -> mixer
  -> post-mixer LPF
  -> OUT1 差频输出
```

因此 `v1d_mixer_lpf` 可以记录为：信号源差频上板测试通过。

### 7. 当前限制

这还不是最终 MTS error signal。原因是：

- 当前输入是干净信号源正弦，不是真实 PD 饱和吸收 / MTS 信号；
- 当前没有接真实 `4.6 MHz REF` 与真实 PD 同时测试；
- 当前没有 pre-mixer `10 MHz LPF + 1.8 MHz HPF`；
- 当前没有 digital gain；
- 当前没有相位 / I-Q 调整；
- 当前没有 D2-125 安全接口验证；
- 当前没有激光闭环。

### 8. 下一步

下一阶段是 `v1e_real_pd_ref`：

```text
IN1 = 真实 PD 饱和吸收 / MTS 信号
IN2 = 4.6 MHz REF，进入 Red Pitaya 前必须衰减到安全范围
OUT1 = 观察 error-like low-frequency signal
```

进入 v1e 前建议先保存本次 v1d 的示波器截图和 CSV，并补充拔掉 IN1 / IN2 的依赖性测试记录，如果尚未完成。

仍然禁止直接接 D2-125、闭环锁定、PID、AI。

## 2026-05-27 v1d Generate Bitstream 前检查记录

### 1. 当前阶段

当前阶段是 `v1d_mixer_lpf`。`v1d` 的目标是验证 mixer 后低通：

```text
IN1 / test signal
IN2 / REF
  -> mixer_core
  -> lpf_core
  -> OUT1
```

它替代的是模拟 mixer 后用于提取低频 / 差频 / 基带分量的低通功能，不是 10 MHz LPF，也不是 1.8 MHz HPF。

### 2. 已完成的仿真前提

```text
tb_lpf_core PASS
tb_laser_lock_core_v1d PASS
```

### 3. 本次代码状态确认

`red_pitaya_top.sv` 已确认并设置为：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

`OUTPUT_MODE=3` 表示 `OUT1` 输出：

```text
mixer_core(pd_i, ref_i)
  -> lpf_core
  -> output_protect
```

### 4. 下一步实验前流程

现在可以准备在 Vivado 中执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

Generate Bitstream 和 timing 通过之后，仍然不能接真实 PD，也不能接 D2-125。第一轮 v1d 上板实验必须使用安全的双路信号源：

```text
IN1 = 100 kHz sine, 200-500 mVpp, 0 V offset
IN2 = 101 kHz sine, 200-500 mVpp, 0 V offset
OUT1 -> oscilloscope
```

预期 `OUT1` 主要看到约 `1 kHz` 差频，周期约 `1 ms`，`201 kHz` 和频分量应明显被压制。

### 5. 仍然不能说明什么

当前即使 v1d bitstream 通过，也仍然不能说明已经得到最终 MTS error signal，因为：

- 当前没有接真实 PD；
- 当前没有 pre-mixer `10 MHz LPF + 1.8 MHz HPF`；
- 当前没有 digital gain；
- 当前没有相位 / I-Q 调整；
- 当前没有 D2-125 安全接口验证；
- 当前没有激光闭环。

真实 PD + `4.6 MHz REF` 从 `v1e` 才开始；D2-125 从 `v1i` 才考虑。

> 当前状态以 [[STATUS]] 为准。本文件保留 v1ab/v1c 的实验证据和历史记录。

## 2026-05-27 v1d_mixer_lpf 受控代码开发记录

当前阶段：

```text
v1c_mixer_only 已通过；
v1d_mixer_lpf 已开始受控 RTL 开发。
```

本次开发目标：

```text
IN1 / PD or test signal
IN2 / REF
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

本次新增：

```text
E:\new\fpga_lock\v94\v0.94\rtl\lpf_core.sv
E:\new\fpga_lock\v94\v0.94\sim\tb_lpf_core.sv
E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v1d.sv
```

本次修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

关键变化：

```text
OUTPUT_MODE=0: IN1 / pd_i -> OUT1
OUTPUT_MODE=1: IN2 / ref_i -> OUT1
OUTPUT_MODE=2: raw mixer output -> OUT1
OUTPUT_MODE=3: mixer + post-mixer LPF output -> OUT1
```

当前还不能上板。必须先通过：

```text
PASS: tb_lpf_core
PASS: tb_laser_lock_core_v1d
```

通过仿真后才允许继续 `Generate Bitstream`。bitstream timing 通过后，才允许进入 v1d 上板测试。

v1d 第一轮上板实验计划：

```text
IN1 = 100 kHz sine, 200-500 mVpp, 0 V offset
IN2 = 101 kHz sine, 200-500 mVpp, 0 V offset
```

理论结果：

```text
100 kHz x 101 kHz = 1 kHz 差频 + 201 kHz 和频
```

`OUTPUT_MODE=2` 应看到 raw mixer，高频纹波明显。  
`OUTPUT_MODE=3` 应主要看到约 `1 kHz`，周期约 `1 ms`，`201 kHz` 应明显被压制。

重要边界：

- v1d 不是最终 MTS error；
- v1d 不接真实 PD；
- v1d 不接 D2-125；
- v1e 才开始接真实 PD + `4.6 MHz REF`。

## 当前最新状态与历史记录标注

当前最新状态以 2026-05-21 的 `v1c_mixer_only 上板测试结果：初步通过` 为准。

本文后面保留了 v1ab、v1c 开发前、v1c 早期无波形排查等历史记录。凡是旧段落中出现：

```text
当前还没有 mixer
当前准备进入 v1ab-2
当前不允许进入 v1c
当前准备 v1c 上板测试
```

这类表述，都应理解为当时阶段的历史记录，不代表当前最新状态。当前最新状态是：

```text
v1c_mixer_only 已经真实上板初步通过；
允许准备 v1d_mixer_lpf；
本次不写 RTL。
```

## 2026-05-21 v1c_mixer_only 上板测试结果：初步通过

### 1. 测试背景

当前版本：

```text
v1c_mixer_only
```

当前 FPGA 设置：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 2;
```

含义：

```text
OUT1 输出 mixer_core(pd_i, ref_i) 的结果。
```

前置验证：

1. `tb_mixer_core` 已通过；
2. `tb_laser_lock_core_v1c` 已通过；
3. Vivado `Generate Bitstream` 成功；
4. Timing 通过，`WNS` 为正，`Failing Endpoints = 0`；
5. 已生成 `.bit.bin` 并通过 `fpgautil` 加载到 Red Pitaya。

### 2. 实验接线

```text
IN1 接信号发生器正弦信号；
IN2 接信号发生器正弦信号；
OUT1 接示波器 CH4。
```

### 3. 测试一：100 kHz x 100 kHz

输入条件：

```text
IN1 = 100 kHz sine，约 200 mVpp，0 V offset；
IN2 = 100 kHz sine，约 200 mVpp，0 V offset。
```

观察结果：

```text
OUT1 / CH4 可以看到明显波形；
CH4 Vpp 约为 20-22 mV；
使用 cursor 测量相邻峰间距，Delta X 约为 5 us；
对应频率约为 200 kHz。
```

理论解释：

对于同频正弦相乘：

```text
sin(wt) x sin(wt) = 1/2 - 1/2 cos(2wt)
```

因此 `100 kHz x 100 kHz` 后，输出应包含 DC 分量和 `200 kHz` 分量。实验中 cursor 测得 `5 us`，对应 `200 kHz`，与理论一致。

### 4. 输入依赖验证

实验现象：

```text
拔掉 IN1 后，OUT1 / CH4 波形消失。
```

结论：

```text
OUT1 不是单路直通，也不是示波器噪声；
OUT1 依赖 IN1 与 IN2 两路输入；
说明 FPGA 内部 mixer_core 的乘法输出已经真实上板工作。
```

### 5. 补充测试：4.6 MHz x 4.6 MHz

除 `100 kHz x 100 kHz` 测试外，实验中也进行了接近真实 MTS REF 频率的测试。

测试条件：

```text
IN1 = 4.6 MHz sine
IN2 = 4.6 MHz sine
OUT1 接示波器
```

观察结果：

```text
OUT1 可以看到输出波形。
```

理论解释：

`4.6 MHz x 4.6 MHz` 的理想混频结果包含：

1. DC / 低频项；
2. `9.2 MHz` 高频项。

因此 `v1c` 阶段看到高频混频波形是合理的。当前 `v1c` 没有 mixer 后 LPF，因此不会得到干净的低频 error-like signal。

关于相邻峰高度不一致：

在 `4.6 MHz` 测试时，相邻峰高度可能不完全一致，可能原因包括：

1. ADC/DAC 采样点与 `4.6 MHz / 9.2 MHz` 波形峰值不完全对齐；
2. 示波器采样、触发和显示插值带来视觉差异；
3. 两路 `4.6 MHz` 存在相位差或线缆延迟；
4. 输入存在微小 DC offset，导致 `4.6 MHz` 残留项；
5. 当前没有 LPF，多种频率分量叠加。

结论：

`4.6 MHz x 4.6 MHz` 能看到 `OUT1` 波形，进一步说明 `v1c_mixer_only` 在接近真实 MTS REF 频率下也能工作。但当前仍不是 MTS error signal。下一步仍应进入 `v1d_mixer_lpf`。

### 6. 关于相邻峰高度不一致的记录

实验中观察到相邻峰高度不完全一致，尤其在高频测试时更加明显。

可能原因包括：

1. `IN1` 和 `IN2` 存在相位差、线缆延迟或同步误差；
2. 信号源输出存在轻微 DC offset；
3. `v1c` 当前没有 post-LPF，输出同时包含 DC、`2f`、可能的 `f` 分量和噪声；
4. `4.6 MHz` 高频测试时，ADC/DAC 采样点、示波器采样和显示插值会使峰值显示不完全一致；
5. 当前 `OUT1` 幅度只有几十 mV，噪声和量化误差占比不可忽略。

判断：

相邻峰高度不一致不影响当前 `v1c` 的主要结论。当前 `v1c` 的核心判据是：

1. 是否出现符合乘法规律的 `2f` 成分；
2. 是否依赖 `IN1` 和 `IN2` 两路输入；
3. 输出幅度是否随输入幅度变化。

### 7. 当前结论

```text
v1c_mixer_only 上板测试初步通过。
```

通过依据：

1. `100 kHz x 100 kHz` 后，`OUT1` 出现 `200 kHz` 成分；
2. `OUT1` 幅度约 `20-22 mVpp`，与理论量级一致；
3. 拔掉 `IN1` 后，`OUT1` 波形消失；
4. 说明 FPGA 内部数字 mixer 已经真实工作。

### 8. 仍需注意

当前结果不能说明已经得到 MTS error signal。

原因：

1. 当前没有 mixer 后 LPF；
2. 当前没有 `1.8 MHz` HPF；
3. 当前没有 `10 MHz` LPF；
4. 当前没有 digital gain；
5. 当前没有相位调节；
6. 当前不能接 `D2-125`；
7. 当前不能接激光器反馈。

### 9. 下一步建议

下一步可以准备 `v1d_mixer_lpf`。

`v1d` 目标：

```text
mixer_core 输出
  -> post-mixer LPF
  -> 保留低频/基带分量
  -> 抑制 2f 高频分量
```

`v1d` 仍然不接 `D2-125`。  
`v1d` 仍然不声称已经完成 MTS error。

## 2026-05-21 v1c 上板 OUT1 暂无明显波形排查记录

当前现象：

```text
v1c_mixer_only 已完成仿真和 Vivado bitstream。
信号发生器输出已在示波器上确认有波形。
IN1、IN2 接入 sine 后，Red Pitaya OUT1 暂时没有明显波形。
```

只读代码审查结论：

- `red_pitaya_top.sv` 当前应为 `USE_LASER_LOCK_CORE = 1'b1`；
- `red_pitaya_top.sv` 当前应为 `LASER_LOCK_OUTPUT_MODE = 2`；
- `i_laser_lock_core` 的 `pd_i` 来自 `adc_dat[0]`；
- `i_laser_lock_core` 的 `ref_i` 来自 `adc_dat[1]`；
- `laser_lock_core` 在 `OUTPUT_MODE = 2` 时选择 `mixer_core(pd_i, ref_i)`；
- `laser_error` 进入 DAC A / `OUT1` 路径，并在官方 DAC saturation 前接入；
- 没有直接驱动 `dac_dat_o`；
- DAC B 仍保持官方路径；
- `output_protect` 的 `enable_i` 固定为 `1'b1`，不会主动关掉 mixer 输出。

因此，当前更优先怀疑：

```text
1. mixer-only 输出幅度太小；
2. 示波器电压档位/触发/耦合设置不合适；
3. 板上加载的 bit.bin 不是最新 OUTPUT_MODE=2 版本；
4. Red Pitaya 重启或官方网页应用覆盖了自定义 FPGA。
```

幅度估算：

```text
假设 Red Pitaya ±1 V -> signed 14-bit 约 ±8191。

IN1 = 100 mVpp sine，峰值 50 mV -> code 约 409。
IN2 = 100 mVpp sine，峰值 50 mV -> code 约 409。
409 * 409 >>> 13 ≈ 20 code。
20 / 8191 * 1 V ≈ 2.4 mV。
```

这说明 `100 mVpp x 100 mVpp` 的 mixer-only 输出非常小，普通 `100 mV/div` 或更粗档位下可能看起来像没有波形。

如果改为：

```text
IN1 = 500 mVpp sine，峰值 250 mV -> code 约 2048。
IN2 = 500 mVpp sine，峰值 250 mV -> code 约 2048。
2048 * 2048 >>> 13 = 512 code。
512 / 8191 * 1 V ≈ 62.5 mV。
```

因此下一轮建议先用两路干净正弦：

```text
IN1 = 100 kHz sine, 500 mVpp, 0 V offset
IN2 = 100 kHz sine, 500 mVpp, 0 V offset
OUT1 -> oscilloscope
CH1 = 20 mV/div 或 50 mV/div
Time/div = 1 us/div 或 2 us/div
Trigger Source = IN1 或 IN2 参考通道
```

预期：

```text
100 kHz x 100 kHz 后，OUT1 应包含 DC / 低频相关分量和 200 kHz 分量。
拔掉 IN1 或 IN2 任一路，OUT1 应明显减小或接近 0。
```

当前不建议马上改 `SHIFT`。应先用 `500 mVpp` 输入和更灵敏的示波器档位测试。如果仍无波形，再考虑在用户确认后做临时 debug 版本，例如把 `SHIFT=13` 改为 `SHIFT=10` 或 `SHIFT=8` 来放大 mixer-only 输出。临时 debug 版本必须单独记录，不能当作最终 v1c 设计。

## 2026-05-20 v1c_mixer_only 最新进度记录

本节记录当前 v1c 的最新状态，优先级高于本文中较早的“准备 v1c”“尚未 bitstream”等历史段落。

已确认完成：

1. `v1ab-1: IN1 -> OUT1` 已经真实上板通过；
2. `v1ab-2: IN2 -> OUT1` 已经真实上板通过；
3. `v1c: tb_mixer_core` 已通过；
4. `v1c: tb_laser_lock_core_v1c` 已通过；
5. Vivado 已经成功 `Generate Bitstream`；
6. 当前 `red_pitaya_top.sv` 应保持：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 2;
```

`LASER_LOCK_OUTPUT_MODE = 2` 表示 `OUT1` 输出 `mixer_core(pd_i, ref_i)` 的结果。也就是说，FPGA 现在不再做 `IN1` 直通或 `IN2` 直通，而是把 `IN1 / pd_i` 与 `IN2 / ref_i` 在 FPGA 内部相乘，然后把 mixer-only 输出送到 DAC A / `OUT1`。

当前可以准备进行 `v1c_mixer_only` 上板测试，但测试边界必须非常清楚：

- 当前只是 mixer-only；
- 当前没有 LPF；
- 当前没有 BPF/gain；
- 当前不是最终 MTS error signal；
- 当前不允许接 `D2-125`；
- 当前不允许接激光器反馈；
- 上板测试必须先用两路干净正弦，不要直接接真实 PD。

推荐第一轮上板输入：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
OUT1 -> oscilloscope
```

预期现象：两个同频正弦相乘后，`OUT1` 应该表现出 mixer-only 的乘法特征，包含 DC/低频相关分量和二倍频分量。因为还没有 LPF，所以不要期待看到干净的 error signal。

## 2026-05-20 当前最新状态

本节是当前最新状态，优先级高于本文中较早阶段留下的“待执行”“当前不允许进入 v1c”等历史段落。

当前真实上板结果：

```text
v1ab-1: IN1 -> OUT1 已通过。
v1ab-2: IN2 -> OUT1 已通过。
```

这说明：

1. `IN1 / adc_dat[0]` 通路可用；
2. `IN2 / adc_dat[1]` 通路可用；
3. `laser_lock_core` 已能接收两路 ADC 数据；
4. DAC A / `OUT1` 输出路径可用；
5. `bit.bin` 加载到 FPGA 后真实生效；
6. 当前允许准备进入 `v1c_mixer_only`。

但必须强调：

- 当前还没有 mixer；
- 当前还没有 LPF；
- 当前还没有 BPF/gain；
- 当前还没有真正 MTS error；
- 当前不能接 `D2-125`；
- 当前不能声称已经实现稳频；
- `v1c` 只允许做 mixer，不允许同时做 LPF/BPF/gain/PID/AI。

## 0. V1 总目标

V1 的最终目标是把 Red Pitaya FPGA 放到 MTS 调制转移光谱稳频链路中，逐步替代原来的部分模拟信号处理链路。

最终希望的实验接线是：

```text
IN1 接 PD 信号
IN2 接 4.6 MHz REF 信号
```

FPGA 内部逐步实现：

```text
PD -> 数字滤波 / gain -> mixer with REF -> LPF -> error signal -> OUT1
```

但是当前 `v1ab_passthrough_debug` 阶段不是 MTS error。它只是验证 Red Pitaya 的输入输出硬件通路是否真的能跑通。

对 FPGA 新手来说，当前不要把 `OUT1` 上看到的同频波形理解成“已经产生了 MTS 误差信号”。它只说明最基础的链路：

```text
模拟输入 -> ADC -> FPGA core -> DAC -> 模拟输出
```

已经开始工作。

## 1. V1 阶段拆分

`v1ab_passthrough_debug`：

验证 `IN1/IN2` 到 `OUT1` 的硬件通路。当前只做直通调试，不做 mixer、LPF、BPF、PID。

`v1c_mixer_only`：

验证 `pd_i * ref_i` 数字混频。第一次测试应先用安全、可控的低频同频信号，不直接接真实 PD 和真实 4.6 MHz REF。

`v1d_mixer_lpf`：

验证 `mixer + LPF`，得到 `error-like low-frequency signal`。这里才开始接近 lock-in 解调的基本形式。

`v1e_real_pd_ref`：

接真实 `PD + 4.6 MHz REF`，观察真实实验链路下的 FPGA `error-like signal`。

`v1f_bpf_gain_enable`：

加入数字 `BPF / gain`，目标替代原模拟链路中的：

```text
10 MHz LPF + 1.8 MHz HPF + RF amplifier
```

数字滤波器系数不能直接照搬模拟滤波器参数，必须根据 ADC 采样率、目标中心频率、带宽和定点位宽设计。

`v1g_error_to_D2_125`：

`OUT1` 接 `D2-125 error input`。只有示波器确认 `OUT1` 幅度、offset、极性和安全性后，才允许接 D2-125。

## 2. 当前代码版本信息

当前 `v1ab` 使用的关键文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

`v1ab-1` 上板通过时使用的参数：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 0
```

解释：

```text
OUTPUT_MODE=0 表示 IN1 / pd_i -> OUT1。
```

也就是说，Red Pitaya `IN1` 进入 ADC 后变成 `adc_dat[0]`，再接入 `laser_lock_core.pd_i`，经过 `error_o` 输出到 DAC A / OUT1。

当前准备进入 `v1ab-2`，代码已切换为：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 1
```

解释：

```text
OUTPUT_MODE=1 表示 IN2 / ref_i -> OUT1。
```

## 3. bitstream / bit.bin 加载记录

`v1ab-1` 已完成 Vivado 流程：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

`.bit` 已转换成 `.bit.bin`。

板子加载命令：

```bash
fpgautil -b /root/red_pitaya_top.bit.bin
```

加载成功信息：

```text
BIN FILE loaded through FPGA manager successfully
```

说明：

这表示 FPGA 已经被临时配置为对应的 bitstream。这个配置不是永久写入板子。Red Pitaya 断电、重启，或者打开可能覆盖 FPGA 的官方网页应用后，都需要重新用 `fpgautil` 加载目标 `.bit.bin`。

## 4. 实验记录：v1ab-1 IN1 -> OUT1

### 4.1 实验目标

验证：

```text
信号发生器 -> IN1 -> ADC -> FPGA -> DAC -> OUT1 -> 示波器
```

这一步的物理意义是证明 Red Pitaya 的 ADC 输入、FPGA 内部最小 core、DAC 输出和 OUT1 BNC 之间的最小链路已经能工作。

### 4.2 实验接线

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器参考通道
```

### 4.3 实验参数

本节保留为可填写实验记录格式：

```text
信号类型：
频率：
输入 Vpp：
Offset：
示波器 CH1：
示波器 CH2/CH4：
时间尺度：
电压尺度：
```

根据当前实验结果记录：

```text
OUT1 可以看到与输入同频的波形。
```

### 4.4 实验结果

结论：

```text
v1ab-1：IN1 -> OUT1 通过。
```

### 4.5 这个结果说明什么

这个结果非常重要，但要正确理解。

它说明：

1. `bit.bin` 已成功加载到 FPGA；
2. `USE_LASER_LOCK_CORE = 1'b1` 生效；
3. `LASER_LOCK_OUTPUT_MODE = 0` 生效；
4. `IN1 / adc_dat[0]` 能进入 `laser_lock_core`；
5. `laser_lock_core` 的 `error_o` 能进入 DAC A / OUT1；
6. Red Pitaya 的 `ADC -> FPGA core -> DAC -> OUT1` 最小链路已经跑通。

教学解释：

这不是 MTS error。它证明的是“路通了”。后续 mixer、LPF、BPF、gain、真实 PD/REF 和 D2-125 接入，都必须建立在这个最小链路已经可靠的基础上。

### 4.6 当前还不能说明什么

当前结果不能说明：

- 已经完成 MTS 解调；
- `IN2 REF` 通路已经通过；
- mixer 已经工作；
- LPF 已经工作；
- BPF / gain 已经工作；
- 可以接 `D2-125`；
- 可以接激光器反馈；
- 可以直接锁频。

## 5. 下一步计划：v1ab-2 IN2 -> OUT1

下一步要验证：

```text
IN2 / ref_i -> OUT1
```

目的：

确认外部 `4.6 MHz REF` 可以安全进入 Red Pitaya `IN2`，经过 ADC 和 FPGA core 后从 `OUT1` 看到，为后续 `v1c_mixer_only` 做准备。

当前仍不做：

- mixer；
- LPF；
- BPF；
- PID；
- AI；
- D2-125 接入；
- EOM 驱动替代。

## 6. 待执行实验：v1ab-2 IN2 -> OUT1

### 6.1 代码状态

当前代码状态：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 1
```

解释：

```text
OUTPUT_MODE=1 表示 IN2 / ref_i -> OUT1。
```

### 6.2 Vivado 操作

修改代码后必须重新执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

然后将 `.bit` 转换为 `.bit.bin`。

注意：不能继续使用 `OUTPUT_MODE=0` 的旧 `.bit.bin` 去测试 `IN2 -> OUT1`，否则测试目标和 bitstream 不一致。

### 6.3 上传和加载

上传到 Red Pitaya：

```bash
scp red_pitaya_top.bit.bin root@rp-f0cb13.local:/root/
```

加载：

```bash
ssh root@rp-f0cb13.local
fpgautil -b /root/red_pitaya_top.bit.bin
```

看到：

```text
BIN FILE loaded through FPGA manager successfully
```

才说明新版本已经加载。

### 6.4 实验接线

```text
4.6 MHz REF 安全幅度 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF 同时 -> 示波器参考通道
```

当前不是：

```text
IN2 -> OUT2
```

OUT2 不作为本次 REF 直通判断依据。

### 6.5 REF 信号参数

建议第一次测试：

```text
4.6 MHz sine
100 mVpp 到 500 mVpp
0 V offset
```

必须强调：

```text
不要第一次直接输入 ±1 V。
严禁 6.32 Vpp 直接进入 IN2。
必须先用示波器确认进入 IN2 前的实际幅度。
```

### 6.6 成功标准

成功：

```text
OUT1 上可以看到 4.6 MHz 同频正弦波。
```

允许：

- 幅度不同；
- 反相；
- 有相位差；
- 有一定噪声。

失败：

- `OUT1` 没信号；
- `OUT1` 直流顶死；
- `OUT1` 严重削顶；
- `OUT1/OUT2` 都无反应。

### 6.7 如果失败，排查顺序

1. 确认 `bit.bin` 是 `OUTPUT_MODE=1` 的新版本；
2. 确认 `fpgautil` 已重新加载；
3. 确认没有打开 Red Pitaya 官方网页应用覆盖 FPGA；
4. 确认 REF 确实接到 `IN2`；
5. 用示波器直接量 `IN2` 前端信号；
6. 确认 REF 幅度在安全范围；
7. 同时检查 `OUT1` 和 `OUT2`，但通过标准只看 `OUT1`；
8. 确认示波器带宽、触发源和时间尺度适合 `4.6 MHz`；
9. 必要时先用较低频率，例如 `100 kHz`，测试 `IN2` 通路；
10. 如果仍失败，把示波器截图和当前 `red_pitaya_top.sv` 参数发给 GPT。

## 7. 是否允许进入 v1c

当前不允许进入 `v1c`。

只有当：

```text
v1ab-1 IN1 -> OUT1 通过；
v1ab-2 IN2 -> OUT1 通过；
```

才允许进入：

```text
v1c_mixer_only
```

当前状态：

```text
v1ab-1 已通过；
v1ab-2 待测试。
```

---

## v1ab-2 实验记录：IN2 -> OUT1

### 实验目标

验证 Red Pitaya `IN2` 输入通路是否可用：

```text
IN2
  -> ADC
  -> adc_dat[1]
  -> laser_lock_core.ref_i
  -> error_o
  -> dac_a_sum
  -> DAC A
  -> OUT1
```

### 代码状态

当前测试时使用的参数：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 1
```

说明：

```text
OUTPUT_MODE=1 表示 OUT1 显示 IN2 / ref_i 通路。
```

### 实验接线

```text
4.6 MHz REF 信号 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
REF 输入参考 -> 示波器另一通道
```

### 实验现象

记录：

```text
IN2 -> OUT1 已经看到通路波形。
```

### 实验结论

```text
v1ab-2：IN2 -> OUT1 通过。
```

### 这个结果说明什么

这个结果说明：

1. `IN2` 对应的 ADC 数据 `adc_dat[1]` 可以进入 FPGA；
2. `laser_lock_core` 的 `ref_i` 通路有效；
3. `OUT1` 可以显示来自 `IN2` 的信号；
4. 后续 `mixer_core` 可以使用 `pd_i` 和 `ref_i` 两路信号；
5. `v1c_mixer_only` 的前提条件已经满足。

教学解释：

`v1ab-1` 证明了 `IN1 / pd_i` 通路可用，`v1ab-2` 证明了 `IN2 / ref_i` 通路可用。数字 mixer 至少需要两路输入：一路 PD，一路 REF。现在这两路都已经能进入 FPGA，并能通过 DAC A / OUT1 被示波器看到，所以可以进入下一阶段的 mixer 开发。

### 当前还不能说明什么

当前结果不能说明：

1. 这还不是 MTS error；
2. 这还不是混频信号；
3. 这还没有经过 LPF；
4. 这还没有经过数字 BPF/gain；
5. 这还不能直接接 `D2-125`；
6. 这还不能用于激光锁频。

## 当前 V1 状态总结

已完成：

- `v1ab-1：IN1 -> OUT1`，通过；
- `v1ab-2：IN2 -> OUT1`，通过。

下一步允许进入：

- `v1c_mixer_only`。

但 `v1c` 的目标只是验证：

```text
pd_i * ref_i -> scaled mixed output -> OUT1
```

`v1c` 仍然不是完整 MTS error signal。

当前仍然不能：

- 接 `D2-125`；
- 接激光器反馈；
- 声称已经完成锁频；
- 声称已经完成完整 MTS 解调。

## 下一阶段：v1c_mixer_only 计划

### v1c 目标

实现 FPGA 内部数字乘法：

```text
pd_i * ref_i -> mixed_signal -> 缩放 -> error_o -> OUT1
```

其中：

```text
pd_i  来自 IN1 / adc_dat[0]
ref_i 来自 IN2 / adc_dat[1]
```

### v1c 不是做什么

`v1c` 不做：

- LPF；
- BPF；
- gain；
- PID；
- scan；
- AI；
- D2-125 输出；
- 真实锁频。

### v1c 为什么重要

MTS 数字解调的核心第一步，是将 PD 信号中的调制成分与参考信号相乘。

这对应真实模拟链路中的：

```text
mixer with 4.6 MHz REF
```

但是，没有 LPF 时，乘法输出仍然会包含 DC、低频分量和 `2f` 分量。因此 `v1c` 的输出还不是真正干净的 error signal。

对新手来说，可以这样理解：

```text
v1c 是“证明数字乘法器能工作”，不是“证明已经能锁激光”。
```

### v1c 推荐测试顺序

不要一开始直接用真实 PD 和 4.6 MHz REF。

推荐先用信号发生器双路测试。

测试 A：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
观察 OUT1 是否出现乘法后的低频/二倍频特征。
```

测试 B：

```text
IN1 = 4.6 MHz sine, 100 mVpp
IN2 = 4.6 MHz sine, 100 mVpp
观察 OUT1 是否有 mixer 输出特征。
```

测试 C：

```text
再考虑真实 PD + 4.6 MHz REF。
```

### v1c 需要新增/修改的 RTL

预计新增：

```text
E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv
```

预计修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

原则：

1. 不修改 `red_pitaya_top.sv` 的 ODDR、PLL、ADC IO、DAC IO、PS/AXI、XDC；
2. 不修改 `output_protect.sv`，除非需要明确说明；
3. `mixer_core` 只在 `adc_clk` 时钟域工作；
4. 输入是 signed 14-bit；
5. 乘法结果是 signed 28-bit；
6. 必须设计缩放方式回到 signed 14-bit；
7. 必须考虑溢出和限幅；
8. 必须写 testbench。

## v1c 进入条件审查

### 1. 是否确认 IN1/IN2 都已通过

确认。

当前真实上板结果：

```text
v1ab-1：IN1 -> OUT1 已通过。
v1ab-2：IN2 -> OUT1 已通过。
```

这说明：

- `IN1 / adc_dat[0]` 通路可用；
- `IN2 / adc_dat[1]` 通路可用；
- `laser_lock_core` 已能接收两路 ADC 数据；
- DAC A / OUT1 输出路径可用；
- `bit.bin` 加载到 FPGA 后真实生效。

### 2. 是否允许进入 v1c_mixer_only

允许进入 `v1c_mixer_only` 的计划和开发阶段。

但这不表示可以接 `D2-125`，也不表示可以直接做真实锁频。`v1c` 只验证数字 mixer。

### 3. v1c 需要新增哪些文件

预计新增：

```text
E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv
```

还应新增对应 testbench，例如：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_mixer_core_v1c.sv
```

或按项目后续约定放在当前 Vivado/sim 使用的位置。

### 4. v1c 可能影响哪些路径

v1c 会影响：

- `laser_lock_core.sv` 内部 `pd_i/ref_i -> error_o` 的处理逻辑；
- `error_o -> laser_error -> dac_a_sum_laser -> dac_a_sum -> DAC A -> OUT1` 这条输出路径；
- `output_protect` 前后的位宽、缩放、饱和策略。

v1c 不应该影响：

- ADC IO；
- PLL；
- BUFG；
- ODDR；
- DAC IO；
- PS/AXI/DDR；
- XDC/SDC；
- D2-125；
- EOM 驱动。

### 5. v1c 必须避免修改哪些官方部分

必须避免修改：

```text
red_pitaya_top.sv 中的 ODDR
dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
PLL / BUFG
ADC IO
PS/AXI/DDR
XADC/AMS
XDC/SDC
官方 DAC saturation / conversion 后级结构
```

如果必须接入 top，也应保持最小接入，不做大改。

### 6. v1c 第一版推荐怎么写

推荐第一版非常保守：

```text
pd_i signed 14-bit
ref_i signed 14-bit
乘法得到 signed 28-bit mixed_wide
选择中间高位或算术右移缩放回 signed 14-bit
送入 output_protect
error_o -> OUT1
control_o 继续保持 0
```

第一版不要加入：

- LPF；
- BPF；
- gain；
- DC remove；
- 相位调节；
- AXI 参数寄存器；
- D2-125 输出控制。

### 7. v1c testbench 应该覆盖哪些情况

testbench 至少覆盖：

1. `pd_i = 0` 时输出应接近 0；
2. `ref_i = 0` 时输出应接近 0；
3. 正数乘正数；
4. 正数乘负数；
5. 负数乘正数；
6. 负数乘负数；
7. 大幅度输入是否溢出或被限幅；
8. reset 后输出为 0；
9. enable 后输出正常；
10. `control_o` 仍为 0。

如果 mixer 使用右移缩放，还要明确 testbench 中的期望值如何计算。

### 8. v1c 上板测试应该怎么看示波器

推荐先看测试 A：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
OUT1 -> 示波器 CH1
IN1 或 IN2 -> 示波器参考通道
```

理论上两个同频正弦相乘会出现：

```text
DC 分量 + 2f 分量
```

所以 `100 kHz / 100 kHz` 时，OUT1 可能出现低频偏置和 `200 kHz` 相关成分。由于没有 LPF，这个波形不一定像最终 error signal。

成功判断：

- OUT1 不再只是简单等于 IN1 或 IN2；
- 改变 IN1 或 IN2 幅度时，OUT1 幅度有对应变化；
- 改变相位时，输出平均值/形状有变化；
- 不长期顶死；
- 不严重削顶。

失败时先回退：

```text
v1ab-1 IN1 -> OUT1
v1ab-2 IN2 -> OUT1
```

确认两路基础通路仍然正常，再排查 mixer。

---

# 实验链路参数记录

## 1. 真实模拟链路

当前实验台真实模拟链路必须按下面顺序理解：

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

简写为：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
  -> ZFM-3+ mixer
  -> IF / error signal
  -> D2-125 error input
```

这不是抽象链路，而是当前实验台真实接线。后续 FPGA 设计不能只说“做一个滤波器”或“做一个 mixer”，而要明确每个数字模块对应哪一个真实器件。

当前 FPGA 项目目标是逐步替代：

- `10 MHz LPF`；
- `1.8 MHz HPF`；
- `ZFL-500LN+ amplifier`；
- `ZFM-3+ mixer`；
- mixer 后低通 / error signal 输出。

当前已完成：

```text
v1ab-1: IN1 -> OUT1，上板通过
v1ab-2: IN2 -> OUT1，上板通过
```

## 2. 各器件参数表

### 2.1 10 MHz Low Pass Filter

| 项目 | 当前记录 |
|---|---|
| 位置 | PD 后第一级滤波 |
| 作用 | 保留 DC 到 10 MHz 的信号 |
| 目的 | 抑制高于 10 MHz 的噪声和无用高频分量 |
| 当前照片可见参数 | `10 MHz low pass` |
| 具体型号 | 待补拍确认 |
| FPGA 等效 | `digital LPF`, cutoff ≈ `10 MHz` |

### 2.2 1.8 MHz High Pass Filter

| 项目 | 当前记录 |
|---|---|
| 标注 | `HIGH PASS FILTER 1.8 MHz` |
| 输入 | `50 Ω` |
| 输出 | `>=100 kΩ` |
| 作用 | 去除 DC、低频扫描背景、低频漂移和低频强噪声 |
| FPGA 等效 | `digital HPF`, cutoff ≈ `1.8 MHz` |

### 2.3 等效带通链路

由：

```text
10 MHz LPF + 1.8 MHz HPF
```

得到：

```text
约 1.8 MHz 到 10 MHz 的 band-pass path
```

作用：

- 保留 `4.6 MHz` 调制相关成分；
- 抑制低频背景和高频噪声；
- 提高进入 mixer 的有效信号占比。

FPGA 等效：

```text
digital BPF, passband roughly 1.8 MHz to 10 MHz
```

### 2.4 ZFL-500LN+ RF Amplifier

| 项目 | 当前记录 |
|---|---|
| 型号 | Mini-Circuits `ZFL-500LN+` |
| 频率范围 | 约 `0.1 MHz` 到 `500 MHz` |
| 典型增益 | 约 `24 dB` |
| 噪声系数 | 约 `2.9 dB` |
| 供电 | `15 V` |
| 作用 | 放大经过带通后的目标频带信号 |
| 24 dB 电压增益换算 | `voltage_gain = 10^(24/20) ≈ 15.85` |
| FPGA 初始等效 | `digital gain ≈ ×16` |
| 可调 gain 初值 | `×1, ×2, ×4, ×8, ×16` |
| 必须保护 | `saturation / clipping protection` |

重要解释：

数字增益不能恢复 ADC 前已经丢失的信噪比。如果目标信号在进入 Red Pitaya ADC 前已经被噪声淹没，FPGA 里的乘法或数字 gain 只能把“信号和噪声一起放大”。因此真实实验中 ADC 输入幅度、前端噪声、模拟链路状态仍然非常重要。

### 2.5 ZFM-3+ Mixer

| 项目 | 当前记录 |
|---|---|
| 型号 | Mini-Circuits `ZFM-3+` |
| 类型 | Level 7 double-balanced mixer |
| LO 标称 | `+7 dBm` |
| RF/LO 频率范围 | 约 `0.04 MHz` 到 `400 MHz` |
| 当前 REF | `4.6 MHz sine` |
| 作用 | 将 PD 中与 `4.6 MHz` 同步的调制成分下变频到低频 |
| FPGA 等效 | signed digital multiplier |
| FPGA 输入 | `pd_path signed 14-bit`, `ref_path signed 14-bit` |
| 原始乘法结果 | signed `28-bit` |
| 输出要求 | 必须做 `scaling / saturation` 后再输出 signed `14-bit` |

## 3. 信噪比和误差信号质量逻辑

为什么真实模拟链路是“先滤波，再放大，再混频”？

1. `10 MHz LPF` 去掉高频噪声，避免高频噪声被后级放大；
2. `1.8 MHz HPF` 去掉 DC、扫描背景、低频漂移；
3. 两者合成 `1.8–10 MHz` 带通，使 `4.6 MHz` 调制分量更突出；
4. `ZFL-500LN+` 放大器放大目标频带的有效信号，提高 mixer 前的有效幅度；
5. `ZFM-3+` mixer 与 `4.6 MHz REF` 同步相乘，把相干调制分量搬移到低频；
6. mixer 后 LPF 去掉 `2f` 和高频项，保留慢变 error signal；
7. 好用的误差信号需要：
   - 过零点清晰；
   - 斜率足够大；
   - 噪声小；
   - offset 可控；
   - 不削顶；
   - 不饱和；
   - 相位合适。

对 FPGA 设计来说，这意味着不能只做“能输出一个波形”。真正有用的 error signal 必须在信噪比、offset、幅度、斜率和安全范围上都可控。

## 4. FPGA 设计参数初值

| 项目 | 初始设计参数 |
|---|---|
| ADC sample rate | `125 MS/s` |
| REF | `4.6 MHz sine` |
| REF 输入安全 | 进入 `IN2` 前必须衰减到 Red Pitaya 安全范围 |
| REF 第一次测试 | 建议 `100–500 mVpp` |
| REF 禁止事项 | 不要直接输入原 mixer 的 `6.32 Vpp` |
| Digital HPF | cutoff ≈ `1.8 MHz` |
| Digital LPF for BPF | cutoff ≈ `10 MHz` |
| Digital BPF | passband ≈ `1.8–10 MHz` |
| Digital gain | initial selectable gain = `×1, ×2, ×4, ×8, ×16` |
| Analog equivalent gain | nominal `×15.85` |
| Mixer | signed `14-bit × 14-bit -> 28-bit` |
| Mixer scaling | scale back to signed `14-bit` |
| Mixer output LPF | `v1d` 以后加入 |
| Mixer output LPF cutoff | 需要根据 error signal 带宽和扫描/锁定需求确定，先不要拍脑袋固定 |
| Output | `OUT1` 先接示波器 |
| D2-125 | `v1g` 才允许接 |

## 5. 需要实验标定的参数

后续必须测量并记录：

1. PD 原始输出 `Vpp`；
2. `10 MHz LPF` 后 `Vpp`；
3. `1.8 MHz HPF` 后 `Vpp`；
4. `ZFL-500LN+` 放大后 `Vpp`；
5. mixer RF 输入 `Vpp`；
6. mixer LO / REF 输入 `Vpp`；
7. mixer IF 输出 `Vpp`；
8. mixer IF 输出 offset；
9. `D2-125 error input` 安全范围；
10. Red Pitaya `IN1/IN2` 实际输入幅度；
11. Red Pitaya `OUT1` 输出幅度；
12. FPGA 数字 gain 后是否削顶；
13. error signal 零点斜率；
14. error signal 噪声 RMS；
15. error signal 是否饱和或偏置过大。

## 6. 修正 v1 路线

`v1c_mixer_only`：

只做数字乘法，不加 LPF/BPF/gain。

目的：验证 `ZFM-3+` 的 FPGA 等效 mixer。

`v1d_mixer_lpf`：

加 mixer 后 LPF。

目的：验证同步解调后的低频输出。

`v1e_real_pd_ref`：

使用真实 PD 和 `4.6 MHz REF`，但暂时不加完整 BPF/gain。

目的：看真实实验输入下是否能得到 `error-like signal`。

`v1f_bpf_gain_enable`：

加入 `1.8 MHz HPF + 10 MHz LPF + selectable digital gain`。

目的：严格对应实际模拟滤波器和 `ZFL-500LN+` 放大器。

`v1g_error_to_D2_125`：

`OUT1 -> D2-125 error input`。

前提：示波器确认幅度、offset、噪声、安全性。

## 7. 后续代码开发要求

后续每个 RTL 模块必须对应真实器件：

```text
bpf_core.sv
  对应 10 MHz LPF + 1.8 MHz HPF

digital_gain.sv
  对应 ZFL-500LN+ amplifier

mixer_core.sv
  对应 ZFM-3+ mixer

lpf_core.sv
  对应 mixer 后 error extraction

output_protect.sv
  对应 OUT1 到 D2-125 前的安全保护
```

每个模块生成时必须说明：

- 对应哪个真实器件；
- 输入输出位宽；
- 系数/增益参数来源；
- 如何仿真；
- 如何上板；
- 如何判断信噪比是否改善；
- 如何避免溢出和削顶。

当前提醒：

```text
可以开始 v1c_mixer_only 的方案和代码开发准备。
但本报告更新本身不实现 v1c，不生成 mixer_core.sv，不运行 Vivado。
```

## 8. v1c_mixer_only 代码准备记录

本次已经进入 `v1c_mixer_only` 的最小 RTL 开发，但仍然没有进入 `v1d`。

`v1c` 的物理意义是用 FPGA 里的 signed digital multiplier 去等效真实模拟链路中的 `Mini-Circuits ZFM-3+ Mixer`。在真实实验中，mixer 把 PD 路径中与 `4.6 MHz REF` 同步的分量搬移到低频；在 FPGA 中，第一步等价写法就是：

```text
pd_i * ref_i -> scaled mixed output -> error_o -> OUT1
```

本次只完成 mixer-only 代码准备：

- 新增 `E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv`；
- 修改 `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv`，增加 `OUTPUT_MODE = 2`；
- 新增 `E:\new\fpga_lock\v94\v0.94\sim\tb_mixer_core.sv`；
- 新增 `E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v1c.sv`。

当前 `OUTPUT_MODE` 的教学含义：

```text
OUTPUT_MODE = 0: IN1 / pd_i passthrough -> OUT1
OUTPUT_MODE = 1: IN2 / ref_i passthrough -> OUT1
OUTPUT_MODE = 2: pd_i * ref_i mixer output -> OUT1
```

注意：`v1c` 仍然不是最终 MTS error signal。因为 mixer 输出中仍然可能包含 DC、低频项和 `2f` 高频项；真正用于提取慢变误差信号的 post-mixer LPF 要到 `v1d_mixer_lpf` 才加入。

本次没有运行 Vivado，没有生成 bitstream，也没有上板。下一步必须先做仿真/综合/实现/bitstream，再用信号发生器双路输入上板验证。
