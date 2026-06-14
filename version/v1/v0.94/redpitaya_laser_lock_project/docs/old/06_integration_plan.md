# 06 后续集成路线

本文件记录当前项目的阶段性路线。它是计划文档，不代表已经开始修改官方工程。

## 阶段一：传统数字解调

目标：完成 PL 端 MTS 数字解调，输出 `error_signal` 到 OUT1 观察。

输入：

- IN1：PD 信号，候选 `adc_dat[0]`。
- IN2：EOM 同源参考，候选 `adc_dat[1]`。

输出：

- `error_signal`
- OUT1 示波器观察信号

FPGA/PL 模块：

- `adc_frontend`
- `bandpass_filter`
- `mixer`
- `lowpass_filter`
- `mts_demod_core`
- `output_protect`

PS/PC 模块：

- 参数配置
- 波形观察
- 实验日志

当前下一步仍然是追踪 DAC 输出路径，明确 OUT1/OUT2 与官方 `dac_a/dac_b` 路径的关系。

## 阶段二：PID + scan/lock control

目标：在 `error_signal` 基础上实现 PID 锁定，并加入扫描、锁定、失锁检测和重扫状态机。

输入：

- `error_signal`
- lock enable
- scan 参数
- PID 参数

输出：

- OUT1：error/debug 观察
- OUT2：PID 控制输出
- lock 状态

FPGA/PL 模块：

- `pid_lock_core`
- `scan_lock_fsm`
- `output_protect`
- debug/scope mux

PS/PC 模块：

- PID 参数配置
- scan/lock/relock 参数配置
- 状态监控
- 实验日志和性能评估

## 阶段三：AI peak recognition + auto relock

目标：用 AI/1D-CNN 辅助识别饱和吸收峰或 MTS 锁点，并做自动重锁。

输入：

- 原始 PD 波形
- `error_signal`
- 扫描数据
- 锁定状态历史

输出：

- 峰识别结果
- 锁点建议
- 自动重扫/重锁策略

FPGA/PL 模块：

- 暂时不放 AI/CNN。
- PL 端只负责稳定产生数据、执行传统解调、PID 和状态机。

PS/PC 模块：

- AI/1D-CNN 推理与训练
- 锁点识别
- 自动重锁策略
- 数据集管理和可视化

## 当前边界

- 不写 Verilog。
- 不修改 Red Pitaya 官方工程。
- 不实现 AI。
- 不写 CNN。
- 当前任务链仍然围绕官方 top、ADC 路径、DAC 路径和传统 MTS 解调架构整理。
