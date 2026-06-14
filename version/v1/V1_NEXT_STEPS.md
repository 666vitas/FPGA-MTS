# V1_NEXT_STEPS

## 2026-06-10 当前下一步：v2 PI/PID 方案收敛

当前准备从 `v1` 进入 `v2`。`v2` 的目标不是继续扩大论文阅读范围，也不是立刻闭环，而是把 FPGA 端的 PI/PID 方案收敛到可审查、可仿真、可逐步上板的最小版本。

下一步分两天完成：

```text
Day 1：提取关键论文 / 项目笔记中的 PID 设计约束。
Day 2：形成 v2 PI/PID RTL 开发指令。
```

用户下一步不需要写代码，只负责后续实验测试和现象记录。Codex 下一轮可以开始写 RTL，但必须先经过 GPT 方案审查；当前仍不允许直接闭环，不允许 AI，不允许把 `digital gain` 当作 `ZFL-500LN+` 的替代。

## v2 PI/PID 文献依据简表

| 资料/论文 | 与 v2 相关的点 | 对本项目采用/不采用的决定 |
|---|---|---|
| Linien: Red Pitaya FPGA laser locking | Red Pitaya 上可做数字解调、IIR filtering、PID/DAC 输出；自动选锁点和参数优化属于更高层功能。 | v2 采用“error signal -> low-latency filtering/PI -> limited DAC output”的实时链路思想；automatic lock point / 参数优化暂不用在 v2，保留到 v3/v5。 |
| PyRPL / Lockbox / IQ / PID | Red Pitaya 的 IQ、IIR、PID 和 Lockbox 模块说明了实时 DSP 路由、输出动态范围、低通带宽和状态机分层。 | v2 采用 enable、polarity、gain、output limit、safe output 等接口边界；Lockbox 自动流程暂不用在 v2，保留到 v3。 |
| Digital laser frequency and intensity stabilization based on STEMlab | STEMlab/Red Pitaya 可作为 PI 控制平台，但输入/输出幅度、offset、DAC 噪声、延迟和带宽必须实测约束。 | v2 第一版优先 PI 而非完整 PID；必须加入输出限幅、safe reset/disable、offset 和低增益测试流程。 |

## v2 第一版设计原则：先 PI，暂不优先 D 项

v2 第一版采用 `PI` 控制器，不优先加入 `D` 项。

原因：

1. `P` 项用于误差响应；
2. `I` 项用于消除静态误差；
3. `D` 项容易放大噪声，第一版不利于安全上板；
4. 当前目标是先替代 `D2-125` 的基本 servo 功能，而不是一次性做复杂控制器；
5. 当前 MTS error-like signal 已经能让 `D2-125` 锁定，因此 v2 重点是安全、可控、可回退地替代 `D2-125`；
6. 第一版先做 PI，可以减少参数维度，便于用户测试。

第一版 v2 PI/PID 必须具备：

- `enable_i`：一键关闭控制输出；
- `polarity_i`：切换控制极性，避免正反馈；
- `kp_i`：比例增益；
- `ki_i`：积分增益；
- `integrator`：signed 宽位积分器；
- `anti-windup`：积分限幅，或输出饱和时冻结积分；
- `output_limit_i`：输出限幅，保护激光器反馈输入；
- `offset_i`：输出偏置，用于匹配激光器反馈中心点；
- safe output：`enable=0` 或 `reset` 时输出安全值，不允许随机输出；
- debug 信号：可选输出 `p_term`、`i_term`、`sat_o`，便于仿真和后续调试。

## v2 分阶段开发路线

### v2a：PI/PID RTL 方案与 testbench

- 不接板子；
- 只做仿真；
- 检查 signed；
- 检查饱和；
- 检查 reset；
- 检查 enable；
- 检查极性；
- 检查 anti-windup；
- 检查 output_limit；
- 检查 offset；
- 检查 safe output。

### v2b：信号源模拟 error 输入测试

- 用低频正弦 / 三角波模拟 error；
- PI 输出只接示波器；
- 不接激光器；
- 看输出方向；
- 看限幅；
- 看 enable；
- 看 offset；
- 看是否有随机跳变。

### v2c：真实 FPGA error 输入，PI 输出只接示波器

- 使用真实 MTS error；
- PI 输出仍不接激光器；
- 检查是否削顶；
- 检查漂移；
- 检查饱和；
- 检查噪声是否过大；
- 检查积分是否 windup；
- 检查关断后输出是否安全。

### v2d：低增益短时间闭环

- 只有 v2c 通过后才允许；
- 使用很小 `kp/ki`；
- 随时准备断开反馈；
- 先短时间闭环；
- 记录是否能锁；
- 记录锁多久；
- 记录是否饱和；
- 记录是否发散；
- 记录是否存在正反馈极性错误。

## 2026-06-09 论文路线重构后的当前执行顺序

当前总目标已经对齐为：

```text
基于 Red Pitaya 的全自动数字稳频参数优化系统
```

但当前不能跳到 PID 或 AI。按照目标报告的建议，本项目采用分层路线：

```text
FPGA = 快速确定性内环
AI   = 慢速监督调参和重锁外环
```

当前用户只需要做实验测试，不需要写代码。当前最小下一步是：

```text
执行 V1I_D2_125_SAFETY_TEST_SOP.md
```

### 当前优先级

1. 固定当前真实链路接线，确认 FPGA OUT1 输入 D2-125 的安全性；
2. 确认 D2-125 后级 CH3 不削顶、不饱和、过零点清晰；
3. 做 IN1 / IN2 / OUT1 依赖性测试；
4. 记录 CH3 与 CH1 scan、CH2 PD 的位置关系；
5. 记录极性、offset、噪声和多周期重复性；
6. 只有这些通过后，才准备低增益短时间闭环。

### v1g 当前定位

`v1g digital gain / output scaling` 不是当前唯一下一步。因为 new-6.9 已经看到：

```text
FPGA OUT1 输入 D2-125 后，D2-125 后级输出 CH3 约 3.42 Vpp
```

这说明 D2-125 已经对当前 FPGA error-like signal 有明显响应。是否需要 digital gain，应由 D2-125 输入是否足够、是否饱和、过零点噪声和安全测试决定。不要只因为 FPGA OUT1 的 Vpp 比模拟链路小，就立刻加 gain。

### 当前禁止

- 不直接闭环；
- 不把 D2-125 输出接激光器反馈；
- 不做 FPGA PID；
- 不做 AI；
- 不盲目增加 digital gain；
- 不替代前级 `10 MHz LPF / 1.8 MHz HPF / ZFL-500LN+`。

## 2026-06-09 当前下一步：v1i_D2-125 安全接入前置验证

当前 new-6.9 已经记录三组关键现象：

- 测试 A：FPGA 直接输出 error-like signal，约 `160 mVpp`；
- 测试 B：三通/并联 REF 条件下，FPGA OUT1 可能下降到约 `30-120 mVpp`；
- 测试 C：FPGA OUT1 输入 `D2-125` 后，D2-125 后级输出 CH3 约 `3.42 Vpp`。

因此当前下一步不再是盲目把 FPGA OUT1 做到最大，也不应立刻进入 PID/AI。下一步是确认 `D2-125` 对 FPGA error input 的安全响应，并为低增益短时间闭环做准备。

### Step 1：D2-125 输入安全确认

- 确认 Red Pitaya `OUT1` 进入 `D2-125 error input` 的电压范围；
- 确认 offset；
- 确认是否削顶；
- 确认 `D2-125` 输入端不饱和。

### Step 2：D2-125 后级输出检查

- 当前 CH3 约 `3.42 Vpp`；
- 检查是否削顶；
- 检查过零点；
- 检查噪声；
- 检查和 CH2 PD 峰位置的对应关系；
- 检查多次扫描重复性；
- 断开 FPGA OUT1 或 REF 后，CH3 应明显变化或消失。

### Step 3：REF 分配方式检查

- 不要只用三通条件下的 `30-120 mVpp` 判断 FPGA 输出能力；
- 对比无三通时 FPGA OUT1 是否回到约 `160 mVpp`；
- 测量 Red Pitaya `IN2` 端实际 REF `Vpp`；
- 后续优先使用双通道同步信号源或正规功分器。

### Step 4：极性确认

- FPGA error 和模拟链路可能同相，也可能反相；
- 反相不代表错误；
- 后续可通过 REF 相位 `+180°`、FPGA 取反、`D2-125 polarity` 调整解决；
- 极性确认前不要闭环。

### Step 5：闭环前保护检查

- D2-125 输出暂时不要直接接激光器；
- 先只观察 D2-125 对 FPGA error input 的响应；
- 确认无跳变、无饱和、无异常尖峰；
- 确认 ramp/scan 下重复性。

### Step 6：低增益短时间闭环准备

只有在上述安全检查通过后，才允许：

- 使用低 servo gain；
- 小心接入激光器反馈；
- 尝试短时间锁定；
- 随时准备断开反馈。

### 下一步实验中什么现象是好的

当前下一步最重要的好现象不是单纯 `Vpp` 最大，而是：

1. D2-125 后级输出 CH3 有清晰误差信号结构；
2. CH3 与 CH2 PD 峰位置对应；
3. CH3 过零点清晰；
4. CH3 噪声可接受；
5. CH3 没有明显削顶；
6. CH3 在多个扫描周期重复；
7. 改变 REF 相位或极性时，CH3 形状/方向可控变化；
8. D2-125 输出端没有异常跳变；
9. 断开 FPGA OUT1 或 REF 后，CH3 明显变化或消失；
10. 在不接激光反馈的情况下，D2-125 对 FPGA error 输入响应稳定。

进入短时间闭环测试前必须满足：

- FPGA OUT1 输入 D2-125 安全；
- D2-125 后级输出不饱和；
- 极性确认；
- offset 合适；
- 过零点明确；
- 激光反馈通道准备好；
- 使用低增益；
- 有紧急断开方案。

### v1g digital gain 当前定位

`v1g digital gain / output scaling` 保留为可选优化，不再作为唯一下一步。

- 如果 D2-125 输入端需要更大 FPGA OUT1，则开发 `gain x2 / x4`；
- 如果 D2-125 对当前 FPGA OUT1 已经有良好响应，则优先进行 `v1i` 安全接入，而不是盲目增加 FPGA 输出增益；
- 避免过大 gain 导致 D2-125 输入饱和；
- 是否需要 digital gain 不应仅由 CH2/CH4 幅度比决定，而应由 D2-125 输入需求、是否饱和、过零点噪声和闭环前安全测试决定。

历史说明：下面较早的“先 v1g 再 v1i”路线是 2026-06-01 阶段判断。new-6.9 之后，已看到 `FPGA OUT1 -> D2-125` 后级约 `3.42 Vpp` 响应，因此当前优先级调整为 `v1i` 前置安全验证，`v1g` 作为可选优化。

## 2026-06-01 当前下一步：从 FPGA error signal 走向 FPGA 完成锁定

当前总目标重新明确为：

```text
最终用 FPGA 板子完成 MTS 激光锁定功能。
```

这个目标分两步实现：

1. 先用 FPGA 替代误差信号生成链路；
2. 再用 FPGA 替代 D2-125 的 PID / servo 控制链路。

当前已经完成的关键事实：

- `v1d_mixer_lpf` 信号源差频上板测试通过；
- `v1e-A / v1e-B` 真实链路三基准对照已经记录；
- FPGA 已经在真实链路中产生 error-like signal；
- FPGA OUT1 约 `0.16 Vpp`，噪声小、形状好、过零点清晰；
- 模拟 mixer 直接输出约 `0.46-0.47 Vpp`，噪声大；
- D2-125 后级输出约 `1.57-1.8 Vpp`，噪声小、形状好、过零点清晰。

当前阶段之后的实验顺序如下。

### Step 1：v1g digital gain / output scaling

目标：

```text
FPGA OUT1: 0.16 Vpp -> 0.5-1.0 Vpp
```

建议增益：

```text
gain x2 -> 约 0.32 Vpp
gain x4 -> 约 0.64 Vpp
gain x8 -> 约 1.28 Vpp
```

优先开发和测试：

```text
gain x4
```

要求：

- 不削顶；
- 噪声不过度放大；
- 过零点仍然清晰；
- `output_protect` 仍然有效；
- OUT1 仍然只接示波器。

### Step 2：v1h REF 相位扫描 / I-Q 优化

目标：

找到误差信号斜率最大、过零点最清晰、噪声最低的 REF 相位。后续再考虑 I/Q 数字解调。

相位扫描点：

```text
0°
30°
60°
90°
100°
120°
150°
180°
```

记录：

- CH4 Vpp；
- 过零点；
- 斜率；
- 噪声；
- 和 CH2/CH3 的对应关系。

### Step 3：v1i D2-125 安全接入

目标：

```text
FPGA OUT1 -> D2-125 error input
```

但第一步不是闭环锁定，而是只观察 D2-125 对 FPGA error 的响应。

先确认：

- FPGA OUT1 幅度；
- offset；
- 极性；
- 是否削顶；
- D2-125 error input 允许范围；
- D2-125 output 暂不接激光器，只观察响应。

确认安全后，再尝试使用 D2-125 进行锁定。

### Step 4：v2 FPGA PID

目标：

在 FPGA 内部实现 PID / servo，逐步替代 D2-125。

进入条件：

- D2-125 能用 FPGA error signal 尝试锁定；
- 已记录锁定参数；
- 已知道需要的 servo 极性、增益、带宽；
- FPGA error signal 稳定、可重复。

### Step 5：v3 自动寻峰 / 重锁 FSM

目标：

实现自动找峰、判断锁定状态、失锁重锁。

这一步仍然不是 AI，而是确定性的 FPGA / 软件状态机。

### Step 6：v5 AI 优化

目标：

基于数据集做：

- 锁定状态识别；
- 自动参数优化；
- 智能重锁。

AI 不替代基本物理链路，也不跳过安全联锁。

### 前级滤波和放大器替代时机

前级 `10 MHz LPF`、`1.8 MHz HPF`、`ZFL-500LN+ 放大器` 暂时不替代。

只有在：

1. FPGA error signal 经 D2-125 能尝试锁定；或
2. FPGA PID 初步跑通；

之后，再逐步替代前级：

1. 先替代 `ZFL-500LN+ 放大器`，用 digital gain / scaling；
2. 再替代 `1.8 MHz HPF`；
3. 最后替代 `10 MHz LPF`。

### 当前继续禁止

- 不接 D2-125；
- 不直接闭环；
- 不声称已经完成 FPGA 锁定；
- 不进入 PID 代码开发；
- 不进入 AI；
- 不修改 RTL；
- 不运行 Vivado。

## 2026-05-31 当前下一步：v1e-A 扫描补充 + v1g 输出增益方案

当前已经完成：

```text
v1d 信号源差频上板测试通过；
v1e-A 真实链路 FPGA OUT1 已看到 error-like signal；
FPGA OUT1 约 0.16 Vpp；
原模拟链路 error 约 1.57 Vpp。
```

当前对比结论：

```text
1.57 / 0.16 ≈ 9.8
```

也就是说，FPGA 当前已经能替代 `ZFM-3+ mixer + mixer 后 LPF` 的核心功能，但输出幅度明显小于原模拟链路。下一步要先把相位、幅度和 CH3/CH4 对照证据补齐，再设计 `v1g digital gain / output scaling`。

### A. REF 相位扫描

建议相位点：

```text
0°, 30°, 60°, 90°, 100°, 120°, 150°, 180°
```

每个相位点记录：

- CH4 Vpp；
- CH4 形状；
- 过零点是否清晰；
- 过零附近斜率；
- 噪声；
- CH4 与 CH3 的极性和时间对应关系。

目的：找到 error-like 结构最清晰、斜率最大、噪声最小的 REF 相位。同步解调不是只看 Vpp；相位会决定低通后留下的是更像色散 error，还是混入更多吸收背景。

### B. REF 幅度扫描

建议幅度点：

```text
0.3 Vpp, 0.5 Vpp, 0.8 Vpp, 1.0 Vpp
```

每个幅度点记录：

- CH4 Vpp；
- CH4 是否近似随 REF 幅度线性变化；
- 是否出现削顶；
- 是否噪声也明显增加；
- Red Pitaya IN2 输入是否仍在安全范围。

### C. CH3 / CH4 对比

比较模拟 error 和 FPGA error：

- 峰位置；
- 过零点；
- 极性；
- 斜率；
- 噪声；
- 是否随 scan 重复；
- 是否随 REF 相位/幅度合理变化。

### D. v1g digital gain 方案

准备设计可切换输出增益版本：

```text
mixer_core
  -> lpf_core
  -> digital_gain
  -> output_protect
  -> OUT1
```

建议先考虑：

- gain x4；
- gain x8。

目标：

```text
FPGA OUT1: 0.16 Vpp -> 0.6-1.0 Vpp
```

同时必须保证：

- 不削顶；
- 不饱和；
- 不让噪声变得不可用；
- `output_protect` 仍然有效；
- D2-125 仍然不接入。

### 继续禁止

- 不接 D2-125；
- 不闭环锁定；
- 不做 PID；
- 不做 AI；
- 不声称已实现高精度锁定；
- 不在 REF 相位/幅度扫描和 CH3/CH4 对比记录完成前直接写 v1g RTL。

## 2026-05-30 当前下一步：v1e-A 补充依赖性测试与幅度/相位优化

当前最新状态：

```text
v1d_mixer_lpf 信号源差频上板测试已通过。
v1e-A_real_chain_mixer_replacement 已在真实链路下观察到 FPGA OUT1 error-like signal。
CH4 / FPGA OUT1 幅度约 160-170 mVpp，截图读数约 169 mV。
```

这说明 FPGA 的 `mixer_core + lpf_core` 已经开始在真实 MTS 链路中产生有物理相关性的输出，但当前还不能标记为完全通过，也不能接 D2-125。

### 1. 需要立即保存的证据

1. 保存示波器截图，当前截图 / 文件标记：`mix-lpf-dui2`；
2. 如果示波器支持，保存四通道 CSV；
3. 记录当前 FPGA 参数：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

4. 记录当前四通道：

| 通道 | 信号 | 当前观测 |
|---|---|---|
| CH1 | scan / ramp | 约 `48.913 Hz`，约 `14.1 mVpp` |
| CH2 | PD / 饱和吸收相关信号 | 约 `131 mVpp` |
| CH3 | analog error reference | 约 `80 mVpp` |
| CH4 | FPGA OUT1 error-like signal | 约 `160-170 mVpp` |

### 2. 下一轮必须做的依赖性测试

1. IN1 依赖性测试：拔掉 IN1，CH4 是否消失或变成无相关噪声；
2. IN2 / REF 依赖性测试：拔掉 IN2，CH4 是否明显变化；
3. REF 幅度扫描：逐步改变安全范围内的 REF 幅度，记录 CH4 Vpp 和形状；
4. REF 相位扫描：寻找 CH4 结构最清晰、斜率最大、噪声最小的相位；
5. 时间对应关系记录：比较 CH4 与 CH2 / CH3 的峰、谷、过零或结构位置；
6. 重复性检查：多次扫描时 CH4 结构是否稳定重复；
7. 评估是否需要 `v1e-debug`：例如调整 `LPF_SHIFT` 或加入受控 digital gain。

### 3. 为什么下一步不是 PID/AI

当前 CH4 虽然已经出现 error-like 结构，但还没有完成物理因果验证。必须先证明：

- CH4 依赖真实 PD 输入；
- CH4 依赖同源 REF；
- CH4 与 scan / PD / analog error reference 有稳定关系；
- CH4 幅度、offset、噪声和相位可控；
- OUT1 不削顶、不饱和、不会伤害后级设备。

在这些证据完整前，PID 和 AI 都只会把不确定性放大，而不是解决问题。

### 4. 继续禁止

- 不接 D2-125；
- 不闭环锁定；
- 不接激光器反馈；
- 不做 PID；
- 不做 AI；
- 不声称已经得到最终 MTS error。

## 2026-05-27 当前下一步：整理 v1d 证据并准备 v1e

当前 `v1d_mixer_lpf` 已经完成：

```text
tb_lpf_core PASS
tb_laser_lock_core_v1d PASS
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 3
100 kHz x 102 kHz -> OUT1 约 1.992 kHz，约 68.3 mVpp
100 kHz x 101 kHz -> OUT1 约 1 kHz
```

这说明 FPGA 在真实 Red Pitaya 上已经能完成：

```text
IN1/测试信号 x IN2/REF
  -> mixer_core
  -> post-mixer LPF
  -> OUT1 差频输出
```

当前最小下一步不是 D2-125、PID 或 AI，而是把 v1d 证据保存完整：

1. 保存 `100 kHz x 102 kHz -> 2 kHz` 的示波器截图和 CSV；
2. 保存 `100 kHz x 101 kHz -> 1 kHz` 的示波器截图和 CSV；
3. 如果尚未完成，补充拔掉 IN1 / IN2 任一路时 OUT1 是否明显变化的依赖性测试；
4. 记录 bit/bin 文件名、`fpgautil` 加载命令、示波器 time/div 和 volt/div；
5. 准备 `v1e_real_pd_ref` 方案。

`v1e_real_pd_ref` 的第一轮接线目标：

```text
IN1 = 真实 PD 饱和吸收 / MTS 信号
IN2 = 4.6 MHz REF，进入 Red Pitaya 前必须衰减到安全范围
OUT1 = 示波器观察 error-like low-frequency signal
```

仍然禁止：

- 不直接接 D2-125；
- 不直接闭环锁定；
- 不直接做 PID；
- 不直接做 AI；
- 不把 v1d 信号源差频结果称为最终 MTS error。

## 2026-05-27 当前下一步：v1d Generate Bitstream

当前已经完成：

```text
tb_lpf_core PASS
tb_laser_lock_core_v1d PASS
```

本次上板前代码检查已经确认：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
```

含义：

```text
OUTPUT_MODE=3:
IN1 / test signal
IN2 / REF
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

下一步 Vivado 操作：

1. 确认 `red_pitaya_top` 是 `Design Top`；
2. 确认 `rtl/lpf_core.sv` 在 `Design Sources`；
3. 确认 testbench 只在 `Simulation Sources`；
4. `Run Synthesis`；
5. `Run Implementation`；
6. `Generate Bitstream`；
7. bitstream timing 通过后，再转换 `.bit.bin` 并用 `fpgautil` 加载。

Generate Bitstream 后的第一轮 v1d 上板测试仍然只用信号源：

```text
IN1 = 100 kHz sine, 200-500 mVpp, 0 V offset
IN2 = 101 kHz sine, 200-500 mVpp, 0 V offset
OUT1 -> oscilloscope
```

预期：

- `OUTPUT_MODE=3` 下主要看到约 `1 kHz`，周期约 `1 ms`；
- `201 kHz` 和频分量应被 post-mixer LPF 明显压低；
- 改 `IN2 = 102 kHz` 后，`OUT1` 应变成约 `2 kHz`。

仍然禁止：

- 不接真实 PD；
- 不接 D2-125；
- 不接激光器反馈；
- 不声称已经得到最终 MTS error。

> 当前状态以 [[STATUS]] 为准。本文件保留 v1c→v1d 过渡期间的历史规划。

## 2026-05-27 当前下一步：v1d 仿真前检查

`v1d_mixer_lpf` 已开始受控 RTL 开发。当前下一步不是上板，也不是 bitstream，而是先把新增模块加入仿真并确认两个 testbench 通过。

必须先做：

1. 将 `rtl/lpf_core.sv` 加入 Vivado `Design Sources`；
2. 确认 `rtl/laser_lock_core.sv` 已更新并能看到 `OUTPUT_MODE=3`；
3. 将 `sim/tb_lpf_core.sv` 加入 Vivado `Simulation Sources`；
4. 将 `sim/tb_laser_lock_core_v1d.sv` 加入 Vivado `Simulation Sources`；
5. 先运行 `tb_lpf_core`；
6. 再运行 `tb_laser_lock_core_v1d`。

必须看到：

```text
PASS: tb_lpf_core
PASS: tb_laser_lock_core_v1d
```

两个 testbench 都 PASS 后，才允许准备 `Generate Bitstream`。当前仍然不允许上板。

后续 v1d 第一轮上板测试目标：

```text
IN1 = 100 kHz sine, 200-500 mVpp, 0 V offset
IN2 = 101 kHz sine, 200-500 mVpp, 0 V offset
```

理论：

```text
100 kHz x 101 kHz = 1 kHz 差频 + 201 kHz 和频
```

预期：

- `OUTPUT_MODE=2`：看到 raw mixer，高频纹波明显；
- `OUTPUT_MODE=3`：主要看到约 `1 kHz`，周期约 `1 ms`，`201 kHz` 明显被压制；
- 改 `IN2 = 102 kHz` 后，`OUT1` 应变成约 `2 kHz`；
- 改 `LPF_SHIFT` 后，平滑程度应按预期变化。

仍然禁止：

- 不接真实 PD；
- 不接 D2-125；
- 不做 BPF/gain/I-Q/PID/AI；
- 不声称已经得到最终 MTS error。

## 2026-05-21 当前最新状态：v1c 已通过，允许准备 v1d

当前最新结论：

```text
v1c_mixer_only 已经真实上板通过。
```

通过证据：

1. `tb_mixer_core` 已通过；
2. `tb_laser_lock_core_v1c` 已通过；
3. Vivado `Generate Bitstream` 成功；
4. Timing 通过，`WNS` 为正，`Failing Endpoints = 0`；
5. 已生成 `.bit.bin` 并通过 `fpgautil` 加载；
6. `IN1 = 100 kHz sine`，约 `200 mVpp`；
7. `IN2 = 100 kHz sine`，约 `200 mVpp`；
8. `OUT1 / CH4` 看到明显波形；
9. `OUT1 Vpp` 约 `20-22 mV`；
10. cursor 测得相邻峰间距约 `5 us`，对应 `200 kHz`；
11. 拔掉 `IN1` 后，`OUT1` 波形消失；
12. 说明 `OUT1` 依赖 `IN1` 和 `IN2`，两路信号已经在 FPGA 内部完成数字混频。

历史记录说明：

本文后面关于“准备 v1c”“v1c 上板测试准备”“当前不进入 v1d”的段落，是当时阶段的历史记录。当前状态已经更新为：`v1c_mixer_only` 可以正式记为通过。

## 下一阶段：v1d_mixer_lpf

`v1d` 目标：

```text
mixer_core 输出
  -> post-mixer LPF
  -> 保留低频/差频/基带分量
  -> 抑制 2f 高频分量
  -> OUT1
```

`v1d` 仍然不是最终 MTS error signal。  
`v1d` 仍然不允许接 `D2-125`。  
`v1d` 不做 BPF/gain。  
`v1d` 不做 PID。  
`v1d` 不做 AI。

推荐测试：

测试 A：

```text
IN1 = 100 kHz sine
IN2 = 100 kHz sine
预期：LPF 后 200 kHz 分量被压低，主要剩 DC/慢变分量。
```

测试 B：

```text
IN1 = 100 kHz sine
IN2 = 101 kHz sine
预期：LPF 后看到 1 kHz 差频，201 kHz 被压低。
```

测试 C：

```text
IN1 = 4.6 MHz sine
IN2 = 4.6 MHz sine
预期：9.2 MHz 被压低，留下低频/DC 分量。
```

下一步允许准备 `v1d_mixer_lpf` 的方案、testbench 和教学文档，但本次不写 RTL。

## 2026-05-20 当前下一步：v1c 上板测试准备

当前已经满足进入 v1c 上板测试准备的前提：

1. `v1ab-1: IN1 -> OUT1` 已经上板通过；
2. `v1ab-2: IN2 -> OUT1` 已经上板通过；
3. `tb_mixer_core` 已通过；
4. `tb_laser_lock_core_v1c` 已通过；
5. Vivado 已经成功 `Generate Bitstream`；
6. 当前 `red_pitaya_top.sv` 应保持：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 2;
```

下一步最小动作：

1. 确认当前 `.bit` 对应 `LASER_LOCK_OUTPUT_MODE = 2`；
2. 转换为 `.bit.bin`；
3. 上传到 Red Pitaya；
4. 用 `fpgautil` 加载；
5. 用两路干净正弦做第一轮 v1c mixer-only 上板测试。

第一轮推荐测试：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
OUT1 -> oscilloscope
```

通过标准：

- `OUT1` 有随两路输入相乘产生的 mixer-only 输出；
- 允许存在 DC/低频分量；
- 允许存在二倍频分量；
- 不要求看到干净 error signal。

当前仍然禁止：

- 不接 `D2-125`；
- 不接激光器反馈；
- 不直接接真实 PD 做第一轮测试；
- 不进入 `v1d_mixer_lpf`；
- 不声称已经得到最终 MTS error signal。

## 0. 本文件作用

本文件记录 v1 的下一步开发顺序。当前下一步是 `v1c_mixer_only`。

## 1. 是否允许进入 v1c

结论：

```text
允许准备进入 v1c_mixer_only。
```

理由：

```text
v1ab-1: IN1 -> OUT1 已真实上板通过。
v1ab-2: IN2 -> OUT1 已真实上板通过。
```

这说明两路 ADC 输入和 DAC A / OUT1 输出链路已经可用。

## 2. v1c 只做什么

`v1c_mixer_only` 只做：

```text
pd_i * ref_i -> scaled mixed output -> error_o -> OUT1
```

对应真实器件：

```text
ZFM-3+ Mixer
```

## 3. v1c 不做什么

`v1c` 不做：

- LPF；
- BPF；
- gain；
- PID；
- sweep / scan；
- AI；
- D2-125 输出；
- 激光器反馈；
- 真实锁频。

## 4. v1c 推荐教学开发顺序

下一步必须按下面顺序做：

1. 解释 `ZFM-3+` 模拟 mixer 的作用；
2. 解释数字 mixer = signed multiplication；
3. 解释 `14-bit × 14-bit = 28-bit`；
4. 解释为什么要缩放；
5. 解释为什么还不是 final error；
6. 生成 `mixer_core.sv`；
7. 生成 `tb_mixer_core.sv`；
8. 仿真；
9. Vivado；
10. 上板低频双路测试；
11. 再上 `4.6 MHz` 测试。

## 5. v1c 开发前必须理解的 FPGA 概念

进入 v1c 前必须理解：

- signed / unsigned；
- 二进制定点数；
- 位宽增长；
- 乘法器可能推断 DSP；
- 算术右移和截位的区别；
- saturation；
- reset 后安全输出；
- `adc_clk` 时钟域；
- testbench 如何计算 expected value；
- 示波器上 mixer 输出为什么可能包含 DC 和 `2f`。

## 6. v1c 必须生成的文件

预计新增：

```text
E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_mixer_core_v1c.sv
```

预计修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

注意：这是下一步开发计划，本次文档整理没有生成这些 RTL 文件。

## 7. v1c testbench 必须覆盖

testbench 至少覆盖：

1. `pd_i = 0`；
2. `ref_i = 0`；
3. 正数 × 正数；
4. 正数 × 负数；
5. 负数 × 正数；
6. 负数 × 负数；
7. 大幅输入是否限幅；
8. reset 后输出 0；
9. enable 后输出正常；
10. `control_o` 仍为 0。

## 8. v1c 上板测试顺序

测试 A：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
OUT1 -> 示波器
```

测试 B：

```text
IN1 = 4.6 MHz sine, 100 mVpp, 0 V offset
IN2 = 4.6 MHz sine, 100 mVpp, 0 V offset
OUT1 -> 示波器
```

测试 C 以后才考虑：

```text
真实 PD + 安全衰减后的 4.6 MHz REF
```

## 9. 下一条给 Codex 的开发指令建议

建议下一条指令是：

```text
请进入 v1c_mixer_only 教学型 TDD 开发模式。
不要修改 red_pitaya_top.sv 的 ODDR/PLL/ADC IO/DAC IO/PS/AXI/XDC。
先解释 ZFM-3+ mixer 对应的数字乘法原理。
然后生成最小 mixer_core.sv 和 tb_mixer_core_v1c.sv。
必须审查 signed、位宽、缩放和 saturation。
不要加入 LPF/BPF/gain/PID/AI。
不要接 D2-125。
```

## 10. v1c_mixer_only 当前代码已生成后的下一步

当前已经生成 v1c 的最小 mixer-only RTL 和自检 testbench。下一步不是进入 `v1d`，而是按下面顺序把 v1c 自己验证完整：

1. 用仿真工具运行 `tb_mixer_core.sv`，确认 signed 乘法、缩放、saturation、reset、enable 全部通过；
2. 用仿真工具运行 `tb_laser_lock_core_v1c.sv`，确认 `OUTPUT_MODE=0/1/2` 都符合预期；
3. 在 Vivado 中 `Add Sources` 添加 `mixer_core.sv`；
4. 在 Vivado 中 `Add Sources` 或仿真 sources 添加两个 testbench；
5. 确认 `red_pitaya_top.sv` 中 `LASER_LOCK_OUTPUT_MODE` 需要改为 `2` 时，再单独执行最小 top 参数修改；
6. Run Synthesis；
7. Run Implementation；
8. Generate Bitstream；
9. 转换为 `.bit.bin` 并用 `fpgautil` 加载；
10. 用双路信号发生器先做低频测试，再做 `4.6 MHz` 测试。

v1c 上板第一轮建议：

```text
IN1 = 100 kHz sine, 100 mVpp, 0 V offset
IN2 = 100 kHz sine, 100 mVpp, 0 V offset
OUT1 -> oscilloscope
```

示波器上应该看到 mixer-only 的乘法输出特征。两个同频正弦相乘后，理论上会出现一个慢变/DC 相关分量和一个二倍频分量；因为 v1c 还没有 LPF，所以不要期待干净的 MTS error signal。

当前仍然禁止：

- 不接 D2-125；
- 不接激光器反馈；
- 不声称已经完成 MTS error；
- 不进入 v1d，除非 v1c 仿真、Vivado、上板测试都通过。
