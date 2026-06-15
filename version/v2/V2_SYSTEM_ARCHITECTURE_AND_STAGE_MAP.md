# V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP

## 2026-06-15 v2B1 FPGA MTS Error Shadow PI（当前有效）

当前 v2B1 有效路线是 FPGA MTS Error Shadow PI，不是 D2-125 DC Error 旁路进板子。

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

OUT1 继续作为 FPGA mixer+LPF error observation。OUT2 当前只接示波器 CH4，观察 P-only Shadow PI control，不接激光、不接 D2-125 Servo Output、不接 Scan。

本文档后续旧 “Shadow PI DC Error” 描述仅作为历史记录，已废弃，禁止执行。

从 2026-06-15 起，凡是本文档后面出现 `D2-125 DC Error Monitor -> Red Pitaya IN1 -> pi_controller -> OUT2`，都只能按历史废弃方案理解，不能作为当前接线、当前代码目标或当前上板预期。

## 2026-06-14 v2B1 Shadow PI 更新

当前 v2B 不直接跳到完整系统集成，而先进入：

```text
v2B1 Shadow PI DC Error 旁路测试
```

v2A 的定位需要重新强调：

```text
v2A 已完成 FPGA 版 D2-125 Servo Core；
v2A 不是完整 D2-125 替代；
v2A 还没有接入 red_pitaya_top；
v2A 还没有接 OUT2；
v2A 还没有生成 bitstream；
v2A 还没有上板；
v2A 还没有控制激光。
```

v2B1 当前链路：

```text
D2-125 DC Error Monitor
-> Red Pitaya IN1
-> v2A 已完成的 pi_controller.sv
-> Red Pitaya OUT2
-> 示波器 CH4
```

v2B1 不替代 D2-125 Ramp，不替代 D2-125 Servo Output，不替代 D2-125 Aux Servo Output。D2-125 继续完成真实扫描、找谱线、缩小扫描范围和锁定。

本文档用于把 v2 从“几个代码子步骤”重新放回完整实验链路里。请把 v2a-1 和 v2a-2 理解成 v2A 里面的 PI 控制器零件测试，不要理解成两个已经可以上板替代 D2-125 的完整系统版本。

## 1. v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

这里的“逐步”很重要。独立仿真通过，只说明 PI 算法零件在 testbench 里算得对；它还没有接入真实 FPGA 主工程，没有经过 Vivado 综合/实现，没有连接 OUT2，也没有接到激光执行器。

## 2. 当前实际链路

当前真实实验仍然是 D2-125 在做最终闭环控制：

```text
PD
-> ADC
-> mixer
-> LPF
-> error-like signal
-> OUT1
-> D2-125
-> Laser
```

可以把它理解成：FPGA 现在已经会“做出一个可用的误差信号”，但真正拉住激光的 servo 仍然是 D2-125。

## 3. v2 目标链路

v2 的目标是把 PI 控制器放进 FPGA，让 OUT2 输出控制量：

```text
PD
-> ADC
-> mixer
-> LPF
-> pi_controller
-> OUT2
-> Laser actuator
```

v2B 到 v2F 期间，OUT1 始终保留为 error observation，也就是继续当“误差信号观察口”。OUT2 的第一阶段只接示波器，不接激光，不接 D2-125，不接任何会改变激光频率的执行器。

## 4. v2A 到 v2G 阶段图

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

## 5. 每个阶段做什么

| 阶段 | 输入是什么 | 处理什么 | 输出是什么 | 修改哪些文件 | 使用什么工具 | 示波器上能看到什么 | 通过标准 | 不能声称什么 |
|---|---|---|---|---|---|---|---|---|
| v2A 独立数字 PI 核心 | testbench 人工 error、kp、ki、offset、limit | 在独立 `pi_controller.sv` 中验证 P、I、anti-windup、reset、enable、hold、polarity、limit | 仿真里的 `control_o`、`p_term_o`、`i_term_o`、`sat_o` | `rtl/pi_controller.sv`、`sim/tb_pi_controller.sv`、version 记录 | XSim 独立仿真；不运行 Vivado 主工程 | 没有真实示波器输出 | v2a-1 P-only 已关闭；v2a-2 初次实现和 XSim 通过，等待一次 Claude Code 集中审查 | 不能说 FPGA 已替代 D2-125，不能说 OUT2 可接激光 |
| v2B 系统接口和主工程集成 | v1 的 mixer+LPF error-like signal，以及 v2A 的 PI core | 把 `error-like signal -> pi_controller -> OUT2` 接入主工程，同时保留 OUT1 观察 | 主工程中出现 OUT2 控制输出路径 | 预计涉及 `laser_lock_core.sv`、可能涉及顶层连接和工程源文件；必须另行授权 | 代码审查、必要的独立/集成仿真；不自动综合 | 仍不一定上板；若只仿真则示波器无变化 | OUT1 路径不被破坏；OUT2 默认安全；enable 默认关闭；接口极性和限幅清楚 | 不能说 bitstream 已生成，不能说硬件可用 |
| v2C Vivado 综合、实现、时序、DRC 和 bitstream | v2B 集成后的主工程 | Vivado 编译整个 FPGA 工程，检查资源、时序、DRC、约束和 bitstream 生成 | `.bit` / `.bin` 候选文件和 Vivado 日志 | Vivado 工程文件、必要的工程源列表；只在授权后修改 | Vivado Synthesis、Implementation、DRC、Timing、Bitstream | 还没有示波器结论 | synthesis/implementation 0 error；关键 DRC/timing 可解释；bitstream 来源明确 | 不能说已上板，不能说 OUT2 实测安全 |
| v2D OUT2 示波器空载上板测试 | v2C 生成的 bitstream；OUT2 只接示波器 | 测 reset、enable、hold、offset、limit、低增益输出是否安全 | OUT2 电压波形；OUT1 error observation | 原则上不改 RTL，除非发现明确安全问题并重新走流程 | Red Pitaya 上板、示波器、必要日志 | OUT1 仍是 error-like signal；OUT2 应可控、限幅、无异常跳变 | OUT2 空载幅度、offset、极性、限幅、enable 行为通过 | 不能说已经接入激光，不能说闭环成功 |
| v2E 真实 MTS error 输入、OUT2 开环观察 | 真实 PD/ADC/mixer/LPF 后的 MTS error-like signal | PI 根据真实 error 计算控制量，但 OUT2 仍只观察，不闭环 | OUT1 error 波形；OUT2 open-loop 控制量波形 | 原则上不改 RTL，必要时只记录参数和现象 | 示波器、Red Pitaya、实验记录 | OUT1 显示真实 error；OUT2 随 error 合理变化但不驱动激光 | OUT2 对真实 error 的方向、幅度、噪声、限幅可解释 | 不能说替代 D2-125，不能说激光被 FPGA 锁住 |
| v2F 低增益闭环替代 D2-125 | v2E 验证过的 OUT2，低 Kp/Ki，小 output limit，已确认执行器接口 | 让 FPGA PI 以很低风险接管一个激光控制端 | OUT2 到 laser actuator；闭环后的 error 变化 | 可能只改运行参数；若改 RTL 必须另开任务 | 示波器、实验记录、必要时 Vivado/上板流程 | OUT1 error 应变小或稳定；OUT2 不应打满或乱跳 | 低增益短时闭环稳定；无饱和失控；可安全回退 D2-125 | 不能说性能已经优于 D2-125，不能说双执行器完成 |
| v2G FPGA PI 与 D2-125 性能对比 | 同一套真实 MTS 条件下的 D2-125 与 FPGA PI 数据 | 比较锁定误差、噪声、保持时间、饱和、恢复、参数敏感性 | 对比报告和后续优化依据 | version 实验报告；必要时参数表 | 示波器、数据采集、统计分析 | 两种控制器在同一指标下的波形差异 | 有重复实验和统一指标，不只看一次波形 | 不能说已完成 AI、自动重锁、双 PID 或完整 D2-125 复刻 |

## 6. v2B 开始前必须回答的五个物理问题

进入 v2B 之前必须先把下面五件事写清楚，否则 OUT2 的工程接口没有物理边界：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性，也就是 OUT2 增大时激光频率往哪边走。
4. 执行器响应带宽，是慢 PZT、scan 端，还是某种 current feedback。
5. 初始 `pid_ce` 频率，先用多慢的 PI 更新速率开始最安全。

## 7. 论文架构与当前项目映射

参考文献：`E:\new\fpga_lock\文献阅读\02_AI智能锁频_机器学习\Chen Benyong 等 - 2024 - 基于卷积神经网络智能识别吸收峰的激光稳频方法.pdf`，以及本地笔记 `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\AI\Paper_AI_002_CNN_Absorption_Peak_Recognition_Chen_Benyong_2024.md`。

该论文系统中，上位机 CNN 负责识别吸收峰和给出锁点，FPGA 负责 error signal demodulation、scan/lock control、slow PID、fast PID，并通过两路 DAC 控制 PZT 和 current 两个执行器。

| 论文模块 | 当前项目对应 | 当前版本 |
|---|---|---|
| Mixer + LPF | v1 数字解调 | 已完成 |
| Slow/Fast PID | 当前先单路 PI | v2 |
| Scan/Lock control | 未来 FSM | v3 |
| 相位自动匹配 | 未来 IQ 解调/相位优化 | v4 |
| CNN peak recognition | 上位机 AI 识峰 | v5 |
| 双 DAC/PZT+Current | 双执行器控制 | 后续版本 |

必须注意：当前项目不是完整复现论文。论文是 SAS + 200 kHz 电流调制 + 正交解调；当前项目是 MTS + 4.6 MHz EOM + 外部 REF 混频。我们只参考它的系统架构分层，不能照搬调制参数、PID 参数、CNN 训练集或峰编号。

## 8. 当前结论

v2A 的意义是先把 PI 控制器这个“算法零件”做成可仿真、可审查、可回归的模块。v2B 才开始把这个零件装进真实 FPGA 主工程。v2C 才开始问 Vivado 能不能把完整系统编出来。v2D 以后才开始问板子和示波器上的 OUT2 是否安全。v2F 才是第一次尝试低增益替代 D2-125。
