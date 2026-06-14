# Red Pitaya 激光稳频 FPGA 项目目标

## 当前定位

本项目是在 Red Pitaya 官方 Vivado FPGA 工程基础上，逐步开发一套用于饱和吸收/MTS 激光稳频的数字处理与控制系统。

最终目标不只是传统 PID，而是分阶段实现：

1. Red Pitaya PL 端数字 MTS 解调。
2. FPGA 数字 PID 锁定。
3. 扫描、锁定、失锁检测、重扫状态机。
4. 后续加入 AI/1D-CNN，用于饱和吸收峰或 MTS 锁点识别，并支持自动重锁。

当前阶段不实现 AI，不写 CNN，也不修改 Red Pitaya 官方工程。当前只完成传统数字解调信号链路的阅读、规划和后续集成准备。

## 当前阶段信号链路

当前阶段的实验定义：

- IN1 = PD 信号，采集到的是饱和吸收/MTS 光强信号。
- IN2 = EOM 同源参考信号，由外部信号发生器提供。
- OUT1 = FPGA 解调得到的 `error_signal`，先用示波器观察。

当前阶段只关注以下传统数字解调链路：

```text
IN1: PD signal
IN2: EOM reference
    |
    v
adc_dat[0] / adc_dat[1]
    |
    v
adc_frontend
    |
    v
bandpass_filter
    |
    v
mixer
    |
    v
lowpass_filter
    |
    v
error_signal
    |
    v
OUT1 观察
```

重要边界：

- PD 采集到的是光强信号，不是最终误差信号。
- 误差信号必须由 FPGA 内部的带通、混频、低通等 MTS 解调链路产生。
- 当前阶段只规划传统信号链路，不实现 PID 闭环、不实现状态机、不实现 AI。

## 三阶段路线

### 阶段一：传统数字解调

目标：在 PL 端实现从 PD 光强信号和 EOM 同源参考信号到 MTS `error_signal` 的数字解调链路。

输入：

- IN1：PD 饱和吸收/MTS 光强信号，候选为 `adc_dat[0]`。
- IN2：EOM 同源参考信号，候选为 `adc_dat[1]`。

输出：

- `error_signal`：MTS 解调误差信号。
- OUT1：把 `error_signal` 输出到 DAC，先用示波器观察。

FPGA/PL 模块：

- `adc_frontend`
- `bandpass_filter`
- `mixer`
- `lowpass_filter`
- `mts_demod_core`
- `output_protect`

PS/PC 模块：

- 参数配置界面或脚本。
- 示波器/采集程序，用于观察原始 PD、参考信号和 error signal。
- 实验日志记录。

当前下一步：

- 继续追踪 DAC 输出路径，明确 `error_signal` 未来如何安全输出到 OUT1。

### 阶段二：PID + scan/lock control

目标：在阶段一的 `error_signal` 基础上，实现 FPGA 数字 PID 锁定，并加入扫描、锁定、失锁检测、重扫控制。

输入：

- `error_signal`
- 扫描控制参数
- 锁定使能
- 失锁检测阈值

输出：

- OUT1：继续用于 error signal 或调试观察。
- OUT2：PID 控制输出，接激光器 scan/current slow feedback。
- 状态标志：scanning、locking、locked、lost_lock、relock。

FPGA/PL 模块：

- `pid_lock_core`
- `scan_lock_fsm`
- `output_protect`
- error/控制量监测模块
- 可选 debug/scope mux

PS/PC 模块：

- PID 参数配置。
- scan range、scan speed、lock point、relock 参数配置。
- 状态监控与实验日志。
- 锁定性能评估脚本。

### 阶段三：AI peak recognition + auto relock

目标：加入饱和吸收峰或 MTS 锁点识别能力，实现更智能的自动找峰、自动选锁点和自动重锁。

输入：

- 原始 PD 波形。
- 解调 error signal。
- 扫描过程中的时序数据。
- 当前锁定状态和历史日志。

输出：

- 峰位置识别结果。
- 推荐锁点。
- 自动重扫/重锁策略。
- 参数建议，例如扫描范围、阈值、锁点极性。

FPGA/PL 模块：

- 暂时不放 AI/CNN。
- PL 端只保留数据采集、解调、PID、状态机和必要的特征/窗口数据输出。

PS/PC 模块：

- AI/1D-CNN 模型。
- 峰识别与锁点识别程序。
- 自动重锁策略。
- 模型训练、验证、日志和可视化工具。

明确原则：

- AI 模块暂时先放在 PC/PS 端，不进入 PL。
- 当前不写 CNN，不设计神经网络硬件加速。
- 等传统链路稳定、数据集足够后，再评估是否需要把部分 AI 推理迁移到 PL。

## 开发原则

1. 官方工程保持干净  
   不直接修改 Red Pitaya 官方 RTL、IP、约束和 Vivado 工程结构。所有自定义资料先放在 `redpitaya_laser_lock_project/` 下。

2. 先读懂，再接入  
   先完成 `red_pitaya_top.sv`、ADC 路径、DAC 路径、scope、ASG、PID 和 system bus 的阅读记录，再决定 `laser_lock_core` 的实际插入点。

3. 传统链路先闭合  
   当前优先完成 `adc_dat[0]/adc_dat[1] -> adc_frontend -> bandpass_filter -> mixer -> lowpass_filter -> error_signal -> OUT1`。

4. AI 后置  
   AI/1D-CNN 是第三阶段目标，先放在 PC/PS 端。当前阶段不实现 AI，不写 CNN，不把 AI 放入 PL。

5. 优先使用 `adc_clk` 时钟域  
   早期设计尽量让 `adc_frontend`、`mts_demod_core`、`pid_lock_core` 工作在官方 ADC 处理时钟域，减少跨时钟域风险。

6. 所有输出必须可保护  
   任何送往 DAC 或激光器执行器的信号都必须经过限幅、使能控制和安全默认值，避免上电、复位、参数错误或环路发散时冲击激光器。

7. 保留可观测性  
   后续集成时应尽量保留 scope 对原始 PD、EOM reference、error signal、PID 输出和最终 DAC 控制量的观察能力。

8. 每一步都能板上验证  
   从只读代码地图、ADC/DAC 路径追踪、开环解调输出、PID 闭环，到 scan/lock/relock，每一步都应有实验记录和回退方案。

