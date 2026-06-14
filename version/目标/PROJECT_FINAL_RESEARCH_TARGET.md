# PROJECT_FINAL_RESEARCH_TARGET

本文档把 `基于 Red Pitaya 的全自动数字稳频参数优化研究路线报告.docx` 纳入 version 主线。它描述最终论文目标，不改变当前 v2a 的最小开发路线。

## 1. 最终论文目标

最终论文目标建议表述为：

```text
基于 Red Pitaya 的分层式全自动数字稳频参数优化系统
```

核心不是只证明 Red Pitaya 可以锁住激光，而是建立一个可解释、可复现、可安全回退的自动稳频参数优化系统：

- FPGA 负责确定性快速内环；
- 经典 PI/PID / FSM 负责可审查的实时控制与重锁流程；
- AI 负责慢速监督外环，包括锁态识别、参数建议、自动调参、重锁策略和 benchmark 分析；
- benchmark 用统一扰动脚本、统一指标和多次重复实验比较人工调参、固定 PI/PID、增益调度、FSM 和 AI 外环。

## 2. 为什么单纯复现 Red Pitaya 数字锁定器不够

单纯做一个 Red Pitaya 数字锁定器，更像工程复现，不足以支撑“全自动数字稳频参数优化”的论文主线。原因是：

- Red Pitaya 生态中已有 PyRPL、Linien、Lock-in + PID 等成熟数字锁定工具；
- 只要能锁住，创新点容易被认为是已有工具链的重复实现；
- 论文需要回答“如何更安全、更稳、更自动、更可复现地优化参数”，而不只是“能不能锁住”；
- 真正有价值的是统一 benchmark、跨工况泛化、安全约束和自动调参效果。

因此，本项目的论文创新点应放在：

```text
安全约束的自动参数优化
  + FPGA 确定性内环
  + 跨工况 benchmark
```

## 3. 为什么采用 FPGA 快速内环 + AI 慢速监督外环

FPGA 适合做快速、确定、低延迟的内环：

- ADC 采样；
- digital demodulation；
- mixer + LPF；
- error generation；
- PI/PID；
- output limiter；
- 硬件级 enable / reset / saturation 保护。

AI 不适合直接进入 125 MS/s 的最快控制链路。AI 更适合做慢速监督外环：

- 判断是否锁住；
- 判断是否失锁或误锁；
- 推荐 Kp / Ki / Kd、滤波带宽、REF phase、重锁门限；
- 比较不同参数在 benchmark 下的表现；
- 在不确定或危险时回退到安全默认策略。

这种分层结构可以同时保留 FPGA 的确定性和 AI 的自适应能力。

## 4. v2 / v3 / v4 / v5 与最终论文目标的关系

| 阶段 | 与最终论文目标的关系 | 当前定位 |
|---|---|---|
| v2 | 建立 FPGA PI/PID servo 基础，用 FPGA 逐步替代 D2-125 的基本控制功能 | 先做独立 PI controller + testbench |
| v3 | 建立自动扫频、自动捕获、自动重锁、锁态管理 FSM | 不使用 AI 也要先能确定性重锁 |
| v4 | 建立 dataset + benchmark，记录锁定、失锁、重锁、噪声、饱和和参数表现 | 论文评价体系的基础 |
| v5 | 建立 AI 慢速监督外环，做自动调参、锁态识别、重锁策略和 benchmark 优化 | 论文创新层 |

v2 是论文工程基础；v3/v4 是自动化和评价体系；v5 才是 AI 创新层。

## 5. 当前 v2 为什么只做 PI controller

当前 v2a 只做独立 `pi_controller.sv` 和 `tb_pi_controller.sv`，原因是：

- v1 已经证明 FPGA mixer + LPF 能产生可用于锁定的 error-like signal；
- D2-125 仍是当前实验基准和安全回退路径；
- PI 是替代 D2-125 基本 servo 功能的最小可行控制器；
- P 项先确认控制方向，I 项再处理静态误差；
- D 项容易放大 MTS error-like signal 噪声，当前不应优先加入；
- 独立模块 + testbench 最容易审查 signed、位宽、saturation、anti-windup、reset 和 enable；
- 不接顶层、不跑 Vivado、不上板，可以避免一开始就影响激光安全。

当前 v2a 的目标不是完成最终论文系统，而是为后续 v2b/v2c、v3/v4/v5 打下可审查、可回退的控制器基础。

## 6. 哪些内容属于未来 v5，当前不能提前做

以下内容属于未来 v5 或 v3/v4 之后的工作，当前不能提前塞进 v2：

- AI 自动调参；
- reinforcement learning 在线控制；
- neural network 直接输出控制电压；
- AI 锁态识别；
- AI 自动选锁点；
- AI 自动重锁策略；
- 跨工况 benchmark 训练；
- 数据集驱动的参数优化；
- 端到端黑箱控制；
- 把 AI 放进 FPGA 快速内环。

当前 v2a 必须保持简单、确定和可审查：先做独立 PI controller，再做 testbench，再审查，再决定是否进入后续接顶层和 OUT2 示波器阶段。
