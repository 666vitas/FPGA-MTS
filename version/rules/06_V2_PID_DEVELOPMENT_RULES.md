# 06_V2_PID_DEVELOPMENT_RULES — HISTORICAL / NOT ACTIVE

> **HISTORICAL / NOT ACTIVE**：仅用于回顾旧 PI/PID 设计，不是当前实验入口。基础 P-only 硬件通过前禁止 PI；当前 Gate、输出路由和允许动作以当前代码、`version/STATUS.md` 与 `20_FPGA_MTS_ENGINEERING_WORKFLOW.md` 为准。

## 0.0B v2B1 timing-safe 默认路径规则（2026-06-16）

完整 `pi_controller.sv` 是 v2A 的完整 PI + anti-windup 核心，继续保留，不删除、不弱化。但 v2B1 主工程默认不能再直接使用完整 PI 路径驱动 OUT2，因为手动 implementation 已显示约 `WNS=-10.995 ns` 的 timing failure。

当前规则：

```text
USE_FULL_PI_CONTROLLER = 0：v2B1 默认，使用 timing-safe P-only Shadow Control。
USE_FULL_PI_CONTROLLER = 1：仅保留给后续 v2B2/v2B3 流水线 PI 开发和对照验证。
```

在完整 PI 完成流水线化并重新通过 Vivado timing 前，不能把它作为可上板默认路径；也不能用 multicycle/false path 掩盖未验证的长控制路径。

## 0.0A v2B1 RTL/SIM 注释规则（2026-06-15）

v2B1 以后，只要 Codex 修改或新增 RTL / SIM，注释必须服务于真实实验链路，不能只服务于代码阅读。至少要说明：

```text
当前替代的是 D2-125 的基础 Servo Core，不是完整 D2-125；
IN1/IN2 如何生成 FPGA 内部 error；
OUT1 为什么继续作为 error observation；
OUT2 为什么只是 Shadow PI control；
OUT2 第一阶段为什么只接示波器；
reset、enable、output_limit、saturation 如何防止上板风险；
Codex 为什么不操作 Vivado、bitstream 和上板。
```

当前有效 v2B1 路线固定为：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> error_o -> OUT1
error_o -> pi_controller -> control_o -> OUT2
```

`D2-125 DC Error -> Red Pitaya IN1` 是已废弃路线，不得作为当前 v2B1 输入来源。

## 0. 2026-06-15 v2B1 当前有效补充规则

当前 v2A 已完成独立 `pi_controller.sv` 的 P/I/anti-windup 基础开发。v2B1 的当前有效阶段是：

```text
v2B1 FPGA MTS Error Shadow PI
```

v2B1 在明确授权下允许修改：

```text
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/red_pitaya_top.sv
v0.94/sim/ 中对应 laser_lock_core 的 testbench
```

v2B1 当前有效链路是：

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> REF，必须在 +/-1 V 内

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

v2B1 必须保持：

```text
OUT1 保持 error observation
OUT2 只接示波器
OUT2 不接激光
OUT2 不接 D2-125 Servo Output
OUT2 不接 Scan
D2-125 DC Error 不作为 Red Pitaya IN1 输入
Codex 不操作 Vivado，Vivado 由用户手动完成
```

### enable 默认值规则

一般安全规则：

```text
OUT2 接真实执行器前，enable 默认必须为 0。
```

v2B1 示波器 Shadow PI 例外：

```text
为了让 OUT2 在示波器上可见，允许 PID_ENABLE_DEFAULT=1。
```

但必须同时满足：

```text
Ki=0
output_limit 很小
OUT2 只接示波器
文档明确禁止接激光
用户手动确认接线
```

该例外不能自动延伸到 v2D/v2E/v2F 的真实执行器测试。

## 1. v2 目标

v2 目标是用 FPGA PI/PID 逐步替代 D2-125 的基本 servo 功能。

## 2. v2 第一版边界

第一版只做独立 pi_controller.sv 和 tb_pi_controller.sv。
不接顶层，不生成 bitstream，不上板，不闭环。

v2a 默认不运行任何工具。

用户明确批准后，可以运行仅包含
pi_controller.sv + tb_pi_controller.sv
的独立 XSim 仿真。

独立仿真不等于允许：
- 接入 Vivado 主工程；
- 综合；
- 实现；
- bitstream；
- 上板；
- OUT2；
- 激光闭环。

## 3. D2-125 替代边界

D2-125 是 PI^2D，不是普通 PID。
v2 第一版 PI 只是最小可行闭环验证，不是完整复刻 D2-125。
D2-125 main/aux output 可到 ±10 V，Red Pitaya OUT2 约 ±1 V，不能直接等价。
D2-125 error input max 为 ±500 mV，必须做幅度映射。

## 4. PI controller 必须具备

- pid_ce_i
- enable_i
- hold_i
- reset_integrator_i
- polarity_i
- kp_i
- ki_i
- offset_i
- output_limit_i
- control_o
- p_term_o / i_term_o / sat_o debug 输出

## 5. 安全默认值

- enable 默认 0
- reset 后 control_o = 0
- ki 初始 0
- kp 初始极小
- output_limit 初始很小
- OUT2 第一阶段只接示波器

## 6. 开发顺序

1. GPT 审查文档
2. 写独立 pi_controller.sv
3. 写 tb_pi_controller.sv
4. 仿真 P-only
5. 仿真 I-only
6. 仿真 PI
7. 仿真 saturation / anti-windup
8. GPT / Claude Code 审查
9. 再考虑接 laser_lock_core.sv
10. 再考虑 OUT2 示波器
11. 最后才考虑低增益接入实验链路

## 7. 禁止事项

- 不直接完整 PID
- 不直接 D 通道
- 不直接 AI
- 不直接闭环
- 不直接接激光
- 不破坏 v1 OUT1 error 输出
- 不把 D2-125 的 4 MHz Peak Lock dither 和当前 MTS 4.6 MHz REF 混淆
- 不把 digital gain 当作模拟低噪声放大器
