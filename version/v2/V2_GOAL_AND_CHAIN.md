# V2_GOAL_AND_CHAIN

本文档说明 v2 的总目标和真实信号链。更完整的阶段地图见 `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`。

## 1. v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

v2 不是“写完 `pi_controller.sv` 就结束”。v2 包含从独立 PI 核心、主工程集成、Vivado、OUT2 示波器验证、真实 MTS error 开环观察，到低增益闭环替代 D2-125 的完整路线。

## 2. v1 已经完成什么

v1 已经完成 FPGA 数字解调主链路：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

也就是说，FPGA 已经能把输入信号处理成可用于锁定的 error-like signal，并通过 OUT1 给 D2-125 使用。当前真正闭环拉住激光的仍然是 D2-125，不是 FPGA PI。

## 3. v2 目标链路

v2 想逐步变成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

OUT1 在 v2B-v2F 始终保留为 error observation，不删除、不弱化。OUT2 第一阶段只接示波器，先证明它安全、可控、限幅正确，再讨论接激光执行器。

## 4. v2A 只是独立 PI 核心

v2A 是独立数字 PI 核心开发，不是完整系统集成。

- v2a-1：P-only，验证比例项方向、极性、限幅、reset、enable、hold 等基础行为。
- v2a-2：I + anti-windup，验证积分项、积分复位、积分限幅、饱和冻结和恢复。

这两步只证明 `pi_controller.sv` 在独立 testbench 中算得对。它们不代表 OUT2 已经接入主工程，也不代表 Vivado 已经通过，更不代表可以上板或替代 D2-125。

## 5. 当前状态

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

v2a-1 已关闭，不再重复 GPT 或 Claude Code 审查。v2a-2 仍需要一次 Claude Code 集中审查；若审查结论为 PASS 或 PASS WITH NOTES，才进入 v2B 的系统集成讨论。

## 6. v2B 开始前的五个物理问题

v2B 不是继续写 PI 算法，而是把 PI 装进真实系统。因此必须先回答：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

这些问题没有答案前，只能做文档、审查和接口规划，不能把 OUT2 接到激光反馈端。

## 7. 论文架构的参考边界

陈本勇等 2024 的 CNN 识峰论文给出了一个很有用的系统分层：上位机 CNN 识别吸收峰，FPGA 做误差信号解调、scan/lock control、slow PID、fast PID，并通过两路 DAC 控制 PZT 和 current。

当前项目只参考这个架构分层。论文是 SAS + 200 kHz 电流调制 + 正交解调；当前项目是 MTS + 4.6 MHz EOM + 外部 REF 混频。不能直接照搬调制参数、PID 参数或 CNN 数据集。

## 8. v2 当前不能声称什么

当前不能声称：

- FPGA PI 已经替代 D2-125。
- OUT2 可以接激光。
- Vivado 主工程已经集成通过。
- bitstream 已经可用。
- 已经完成双 PID、scan/lock FSM、CNN 识峰或相位自动匹配。
