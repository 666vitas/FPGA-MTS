# STATUS

## 2026-06-14 当前主线：v2B1 FPGA MTS Error Shadow PI（当前有效）

当前安全主线已经从旧的“D2-125 DC Error -> Red Pitaya IN1”旁路方案，修正为使用 Red Pitaya 自身 IN1/IN2 生成 FPGA 内部 error，并把该 error 同时送到 OUT1 观察和 OUT2 Shadow PI 控制输出。

### 当前硬件接线边界

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> 外部 REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器 CH2：FPGA mixer+LPF error，当前约 0.12~0.15 V
Red Pitaya OUT2 -> 示波器 CH4：FPGA P-only control
```

禁止：

```text
D2-125 DC Error -> Red Pitaya IN1
D2-125 Servo Output -> Red Pitaya IN1
Red Pitaya OUT2 -> 激光器
Red Pitaya OUT2 -> D2-125 Servo Output 三通
Red Pitaya OUT2 -> 激光器电源 Scan
任何超过 +/-1 V 的信号进入 IN1/IN2
```

### 当前代码状态

```text
v0.94/rtl/laser_lock_core.sv：
control_o 不再固定为 0，已接入 pi_controller。

v0.94/rtl/red_pitaya_top.sv：
OUT1 / DAC A 仍为 laser_error；
OUT2 / DAC B 已改为 laser_control。

v0.94/rtl/pi_controller.sv：
本次未修改，继续使用 v2A 已完成的 PI 控制器核心。

v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：
新增 v2B1 Shadow PI 行为仿真。
```

### 初始参数

```text
PID_ENABLE_DEFAULT = 1
PID_HOLD_DEFAULT = 0
PID_RESET_INTEGRATOR_DEFAULT = 0
PID_POLARITY_DEFAULT = 0
PID_KP_DEFAULT = 16'sd2048
PID_KI_DEFAULT = 16'sd0
PID_OFFSET_DEFAULT = 14'sd0
PID_OUTPUT_LIMIT_DEFAULT = 14'd1500
PID_UPDATE_HZ = 10_000
```

含义：

```text
Kp=2048：OUT2 约为 OUT1 error 的 1/2
Ki=0：避免 OUT2 积分慢慢爬升
output_limit=1500：约 +/-0.18 V，防止 OUT2 接近 +/-1 V
```

### 独立仿真状态

```text
xvlog：0 error
xelab：0 error
xsim：SUMMARY tests=13 pass=13 fail=0
```

### 本轮不执行

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

Vivado、bitstream、bin 和烧录由用户手动完成。

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前执行路线。禁止把 D2-125 DC Error 或 D2-125 Servo Output 接入 Red Pitaya IN1。当前有效主线见本文档最前面的“v2B1 FPGA MTS Error Shadow PI”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，也不是 FPGA 直接替代 D2-125。当前下一步定义为：

```text
v2B1 Shadow PI DC Error 旁路测试

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

当前真实接线：

```text
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 三通 -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3，后续接 Red Pitaya IN1
Red Pitaya OUT2 -> 后续示波器 CH4
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
对应
error_i -> pi_controller.sv -> control_o
```

v2A2 独立仿真报告结论：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只证明 `pi_controller.sv` 独立 testbench 通过，不证明它已进入主工程、已接 OUT2、已生成 bitstream、已上板或已控制激光。

下一步代码边界：

```text
允许修改：
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/red_pitaya_top.sv

允许新建：
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv

禁止修改：
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
```

本轮文档任务不修改任何 `.sv`，不运行 XSim，不运行 Vivado，不生成 bitstream，不上板。

## 2026-06-15 注释与路线清理状态

本轮允许对 RTL/SIM 增加解释性注释，但不允许改变功能逻辑。当前已经把 v2B1 的有效路线固定为：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> error_o -> OUT1
error_o -> pi_controller -> control_o -> OUT2
```

所有后续文档和代码注释都必须把 `D2-125 DC Error -> Red Pitaya IN1` 视为历史废弃路线，不得作为当前接线方案。OUT1 在 v2B1-v2F 继续作为 error observation；OUT2 第一阶段只接示波器。

## 当前阶段

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 当前协作原则

每个子阶段最多一次 Claude Code 集中审查和一次 Codex 修正。通过回归仿真后关闭子阶段，不再循环审查。

## v1 状态

v1 已完成 FPGA 数字解调基础链路：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

含义：FPGA 已经能产生可用于 D2-125 的 error-like signal。当前真正闭环控制激光的仍然是 D2-125。

## v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

v2 目标链路：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器。

## v2 阶段图

```text
v2A：独立数字 PI 核心
  v2a-1：P-only
  v2a-2：I + anti-windup

v2B：系统接口和主工程集成
v2C：Vivado 综合、实现、时序、DRC 和 bitstream
v2D：OUT2 示波器空载上板测试
v2E：真实 MTS error 输入、OUT2 开环观察
v2F：低增益闭环替代 D2-125
v2G：FPGA PI 与 D2-125 性能对比
```

## v2A 当前记录

- v2a-1：P-only 已关闭；不再重复 GPT 或 Claude Code 审查。
- v2a-2：I 通道、integrator 和 anti-windup 已完成初次实现和独立 XSim 回归；等待一次 Claude Code 集中审查。

## v2B 开始前必须回答

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 当前禁止事项

- 不修改 RTL，除非用户另行明确授权。
- 不运行 XSim，除非用户另行明确授权。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 关键文档

- `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_GOAL_AND_CHAIN.md`
- `E:\new\fpga_lock\v94\version\v2\V2_DEVELOPMENT_ROADMAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_NEXT_STEPS.md`
- `E:\new\fpga_lock\v94\version\v2\GPT_REVIEW_V2_SUMMARY.md`
