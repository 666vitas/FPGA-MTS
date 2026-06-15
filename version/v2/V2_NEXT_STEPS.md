# V2_NEXT_STEPS

## 2026-06-14 v2B1 Shadow PI 当前下一步（当前有效）

v2B1 已把 v2A 的 `pi_controller.sv` 接入主链路的 Shadow PI 位置。当前目标不是闭环替代 D2-125，而是先让 FPGA 在 OUT2 上输出一个安全、很小、可观察的 P-only control。

### 当前 RTL 链路

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

同时：

error_o
-> pi_controller
-> control_o
-> OUT2
```

### 已完成

```text
laser_lock_core.sv：control_o 不再固定为 0，已实例化 pi_controller
red_pitaya_top.sv：OUT1 / DAC A 仍接 laser_error，OUT2 / DAC B 改接 laser_control
tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：新增 v2B1 Shadow PI 行为仿真
XSim：tests=13 pass=13 fail=0
```

### Codex 本次不做

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

### 用户手动下一步

```text
1. 打开 v0.94/project/redpitaya.xpr
2. 在 Sources 中确认 v0.94/rtl/pi_controller.sv 已存在
3. 如果不存在，手动 Add Sources：v0.94/rtl/pi_controller.sv
4. 确认 laser_lock_core.sv 和 red_pitaya_top.sv 来自 v0.94/rtl
5. 手动 Run Synthesis
6. 手动 Run Implementation
7. 手动 Generate Bitstream
8. 烧录后先只接示波器，不接激光，不接 D2-125 Servo Output
```

### 烧录后应该看到

```text
OUT1 / CH2：仍是 FPGA mixer+LPF error，当前约 0.12~0.15 V
OUT2 / CH4：跟随 OUT1 error 的小 P-only control
Kp=2048：OUT2 约为 OUT1 的 1/2
Ki=0：OUT2 不应慢慢爬升
output_limit=1500：OUT2 不应超过约 +/-0.18 V
polarity=0：OUT2 与 OUT1 同向
```

### 必须停止的现象

```text
OUT2 接近 +/-1 V
OUT2 随机跳变
OUT2 慢慢爬升
OUT1 原有 error 现象消失
任意 IN1/IN2 输入超过 +/-1 V
有人准备把 OUT2 接激光器或 D2-125 Servo Output
```

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前下一步。禁止执行“D2-125 DC Error -> Red Pitaya IN1”。当前有效下一步见本文档最前面的“v2B1 Shadow PI 当前下一步”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，而是：

```text
v2B1 Shadow PI DC Error

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代。它对应：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
error_i -> pi_controller.sv -> control_o
```

v2A2 独立 XSim 结果：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只说明 `pi_controller.sv` 独立 testbench 通过，不说明它已经接入 `red_pitaya_top`、OUT2、bitstream 或真实激光。

当前真实接线必须作为 v2B1 前提：

```text
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
Red Pitaya OUT2 -> 后续示波器 CH4
```

下一条代码任务标题草案：

```text
v2B1 Shadow PI DC Error to OUT2 RTL Integration
```

本次不执行该代码任务。

## 1. 当前状态

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

v2a-1 已经关闭：P-only RTL、首次仿真、Claude Code 集中审查、最终修正和 XSim 回归仿真全部完成。v2a-1 不再重复 GPT 或 Claude Code 审查。

v2a-2 已经完成 I 通道、integrator 和 anti-windup 的初次实现，并完成独立 XSim 回归。当前下一步不是继续扩大测试范围，也不是直接接主工程，而是等待 Claude Code 对 v2a-2 进行一次集中静态审查。

## 2. 最近一步

最近一步只做：

```text
Claude Code 对 v2a-2 做一次集中审查
```

审查结论只允许是：

- PASS
- PASS WITH NOTES
- FAIL

如果 PASS 或 PASS WITH NOTES，则 v2A 关闭，进入 v2B 系统集成准备。如果 FAIL，则 Codex 只做一次集中修正和回归仿真；通过后关闭 v2A，不再循环审查同一版本。

## 3. v2B 开始前必须回答的五个问题

进入 v2B 前，GPT 和用户必须明确：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

这些是物理接口问题，不是 RTL 算法问题。没有这些答案，就不能安全决定 OUT2 的限幅、offset、polarity 和 PI 更新速率。

## 4. v2B 的最小任务

v2B 的最小任务是系统接口和主工程集成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2
```

同时必须保持：

```text
OUT1 -> error observation
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器，不接激光，不接 D2-125，不接任何真实反馈端。

## 5. 当前禁止事项

当前仍然禁止：

- 不修改 `laser_lock_core.sv`，除非另开 v2B 授权任务。
- 不修改 `red_pitaya_top.sv`。
- 不修改 `redpitaya.xpr`。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 6. 下一主阶段

```text
下一主阶段：v2B 系统接口和主工程集成。
```

但 v2B 只能在 v2a-2 一次 Claude Code 集中审查完成，并且五个物理问题有答案之后开始。
