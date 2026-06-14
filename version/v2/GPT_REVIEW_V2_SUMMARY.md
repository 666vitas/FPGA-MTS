# GPT_REVIEW_V2_SUMMARY

## 2026-06-14 给 GPT 的 v2B1 判断摘要

当前下一步应判断为：

```text
v2B1 Shadow PI DC Error

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代。v2A 对应 D2-125 的这一段：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
```

FPGA 中对应：

```text
error_i -> pi_controller.sv -> control_o
```

当前真实接线仍由 D2-125 完成扫描和锁定：

```text
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
Red Pitaya OUT2 -> 后续示波器 CH4
```

GPT 需要避免把 v2A 仿真通过解释成“FPGA 已锁定激光”。v2A2 的 `tests=165 pass=165 fail=0` 只证明 `pi_controller.sv` 独立 testbench 通过。

本文档给 GPT 一个清晰的 v2 总览，避免把 v2a-1、v2a-2 误解成完整系统版本。

## 1. 一句话结论

v2 的目标是：

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

当前状态是：

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 2. v1 已完成的基础

v1 已经完成并实验证明：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

FPGA 已经能产生可用于 D2-125 锁定的 error-like signal。当前真正闭环控制激光的仍然是 D2-125。

## 3. v2 的目标链路

v2 目标是逐步形成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

这里的关键不是再做一个孤立模块，而是把 PI 控制器安全地放进真实 FPGA 主工程和真实实验链路。

## 4. v2A 的真实定位

v2A 是独立数字 PI 核心开发。

- v2a-1：P-only，已关闭。
- v2a-2：I + anti-windup，已完成初次实现和独立 XSim，等待一次 Claude Code 集中审查。

v2A 只证明算法零件在 testbench 中工作。它不能证明主工程能综合，不能证明 OUT2 硬件安全，也不能证明激光已由 FPGA 锁住。

## 5. v2 主阶段

| 阶段 | 定位 |
|---|---|
| v2A | 独立数字 PI 核心 |
| v2B | 系统接口和主工程集成 |
| v2C | Vivado 综合、实现、时序、DRC 和 bitstream |
| v2D | OUT2 示波器空载上板测试 |
| v2E | 真实 MTS error 输入、OUT2 开环观察 |
| v2F | 低增益闭环替代 D2-125 |
| v2G | FPGA PI 与 D2-125 性能对比 |

## 6. 论文架构参考

陈本勇等 2024 的 CNN 识峰论文中，系统分工是：

- 上位机 CNN：识别吸收峰，给出目标峰/锁点信息。
- FPGA：error signal demodulation、scan/lock control、slow PID、fast PID。
- DAC：输出到 PZT 和 current 两个执行器。

当前项目只参考这个分层。论文是 SAS + 200 kHz 电流调制 + 正交解调；当前项目是 MTS + 4.6 MHz EOM + 外部 REF 混频。不能照搬调制参数、PID 参数或 CNN 数据集。

## 7. v2B 前 GPT 需要回答的问题

GPT 在允许 v2B 前需要明确：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

这些问题决定 OUT2 的安全边界。没有答案时，不应进入真实系统接线或上板闭环。

## 8. 给 GPT 的审查边界

GPT 不需要再对 v2a-1 做逐行审查。v2a-2 也只等待一次 Claude Code 集中审查。审查通过后，应把注意力转到 v2B 的物理接口和主工程集成风险，而不是在 v2A 内部反复循环。

## 9. 当前禁止声称

当前不能声称：

- FPGA PI 已替代 D2-125。
- OUT2 已经可以接激光。
- Vivado 主工程已经通过。
- bitstream 已经生成。
- 已经完成 scan/lock FSM、相位自动匹配、CNN 识峰或双执行器控制。
