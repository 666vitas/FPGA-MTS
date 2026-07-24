Status: HISTORY
Effective-Gate: ALL
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md

# 面向论文的项目路线图

> 本文件保存论文长期路线与旧阶段判断；当前 Gate、短期步骤和硬件许可只看 `version/CURRENT_GATE.md` 与 `version/STATUS.md`。

## 0. 论文主线

目标报告《基于 Red Pitaya 的全自动数字稳频参数优化研究路线报告》给出的核心判断是：

```text
单纯做一个 Red Pitaya 数字锁定器，不足以构成高质量论文创新。
更有价值的路线是：
FPGA 保留确定性的快速内环，
AI 放在监督调参、锁态识别、重捕获和 benchmark 的慢速外环。
```

因此本项目的论文主线应表述为：

```text
基于 Red Pitaya 的分层式全自动数字稳频参数优化系统
```

论文创新点不是“能锁住”。单纯锁住更像工程验收；论文创新应聚焦：

```text
安全约束的自动参数优化
  + FPGA 确定性内环
  + 跨工况 benchmark
```

其中 v2 是论文工程基础：先把 FPGA PI/PID servo 做成可审查、可仿真、可回退的确定性内环。v5 才是 AI 创新层：在 v3/v4 的自动化流程和 benchmark 基础上做慢速监督、锁态识别、自动调参和跨工况优化。

其中：

- FPGA 做高速、确定、可解释的误差信号生成和后续 PID；
- AI 做慢速监督、参数优化、锁态识别、自动重锁和跨工况泛化；
- 先实现可锁定系统，再建立 benchmark，最后进入 AI 参数优化。

## 1. 当前短期目标

当前短期目标不是 AI，也不是完整 PID，而是 v2a：

```text
独立 pi_controller.sv
  + tb_pi_controller.sv
  + GPT / Claude Code 审查
```

这一步服务于论文的 FPGA 确定性内环基础，但不直接接顶层、不跑 Vivado、不上板、不闭环。

## 2. 中期目标

中期目标是：

```text
FPGA PID / servo
```

进入条件：

- D2-125 已经能用 FPGA error signal 尝试锁定；
- D2-125 参数、极性、带宽、增益已有记录；
- FPGA error signal 可重复、低噪声、过零点清晰；
- 已经知道闭环需要什么控制方向和增益范围。

FPGA PID 不是用来修坏的 error signal，而是在 error signal 已经可用后，逐步替代 D2-125 的控制功能。

## 3. 长期目标

长期目标是 AI 慢速外环：

- 锁定状态识别；
- 自动找峰；
- 自动重锁；
- PID / REF phase / LPF / gain 参数推荐；
- 多工况 benchmark；
- 安全约束下的自动调参。

AI 不替代 FPGA fast loop。AI 不直接进入 125 MS/s 的实时 DSP 链路。

## 4. v1-v5 论文导向路线表

| 阶段 | 目标 | 输入 | 输出 | 成功标准 | 禁止事项 |
|---|---|---|---|---|---|
| v1 | FPGA error signal generation + D2-125 access verification | PD 模拟前级输出、4.6 MHz REF | FPGA OUT1 error-like signal，D2-125 后级响应 | D2-125 对 FPGA error 有安全、可重复、不过载响应；之后低增益短时间锁定可尝试 | 不做 FPGA PID，不做 AI，不直接闭环 |
| v2 | FPGA PID / servo replacing D2-125 | 已验证 FPGA error signal | FPGA control output | FPGA PID 能稳定降低 error，参数可解释，可安全退出 | 不用 PID 掩盖坏 error，不跳过 D2-125 经验参数 |
| v3 | lock / relock FSM | error、control、scan、状态指标 | 自动寻峰、捕获、失锁检测、重扫 | 不用 AI 也能重复完成自动锁定流程 | 不做黑箱 AI 直接控制 |
| v4 | dataset + benchmark | CH1/CH2/CH3/CH4、锁态、扰动脚本 | 可复现实验数据集和指标 | 能比较人工调参、固定 PID、gain schedule、FSM、AI 方法 | 不只展示最好一次结果 |
| v5 | AI slow supervisory optimization | v4 数据集和实时特征 | 参数建议、锁态分类、重锁策略 | AI 在统一 benchmark 上优于强基线，且有安全回退 | 不做端到端 AI 直接控激光 |

## 5. v4 benchmark 必须记录的指标

论文需要的不只是“锁住了”，还需要可复现指标：

- lock time；
- relock time；
- relock success rate；
- loss count；
- error RMS；
- control saturation rate；
- output clipping rate；
- zero-crossing slope；
- Allan deviation，后续条件允许时加入；
- phase noise / PSD，后续条件允许时加入；
- FPGA 资源占用；
- CPU / 通信延迟，AI 外环阶段记录。

## 6. 当前项目位置

截至 new-6.9：

- v1c raw mixer 已通过；
- v1d mixer + post-mixer LPF 已通过；
- v1e 真实链路 error-like signal 已看到；
- FPGA OUT1 输入 D2-125 后，D2-125 后级输出约 `3.42 Vpp`；
- 当前处于 `v2a_pi_controller_standalone` 准备阶段；
- FPGA OUT1 error-like signal 接入 D2-125 后已经可以锁住；
- 还没有 FPGA 内部 PI/PID 替代 D2-125；
- 还没有 AI。

## 7. 论文风险提醒

如果只停留在：

```text
Red Pitaya 能输出一个 error-like signal
```

这更像工程实现，不够支撑“全自动数字稳频参数优化”主题。

论文价值要靠后续补齐：

1. FPGA error 能真实驱动锁定系统；
2. FPGA PID 能替代 D2-125；
3. 自动重锁 FSM 能减少人工操作；
4. benchmark 能量化对比；
5. AI 外环能在 benchmark 上改进参数、重锁或锁态判断。

## 8. 当前下一步

当前下一步不是写 AI，也不是直接完整 PID，而是：

```text
GPT 审查 v2 文档和 rules
-> 写独立 pi_controller.sv
-> 写 tb_pi_controller.sv
-> 仿真与审查
```

v2a 不接 `laser_lock_core.sv`，不跑 Vivado，不生成 bitstream，不上板，不接激光。AI 自动调参、自动重锁和 benchmark 优化属于 v5，不能提前塞进 v2。
