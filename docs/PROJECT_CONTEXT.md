# FPGA-MTS Project Context

- Status: ACTIVE
- Authority: project context
- Last-Updated: 2026-09-09
- Project root: E:\new\fpga_lock\v94

## 项目目标

本项目是基于 FPGA 的激光器稳频系统研发项目。工程目标是让 Red Pitaya STEMlab 125-14 承担确定性的高速信号处理与锁定控制，由 Host 提供配置、观测和实验操作入口，并通过可追溯的 bit release 和实验记录形成可复现实验闭环。

当前工程不是一个已经完成的产品，也没有已经验证的深度学习闭环。所有状态必须以当前 Gate、当前源码、当前 release 和对应实验记录为依据。

## 当前阶段

当前 Gate 为 LOCK-MVP-L1，目标是验证 FPGA 实时 ERROR-Crossing、无扰捕获和 P-only 基础锁定链路。

已有审查确认：

- 当前活动工程候选位于 v0.94/project/redpitaya.xpr。
- 当前 top 为 red_pitaya_top，目标器件为 xc7z010clg400-1。
- 当前 RTL 已包含锁定主链路、采集、保护、斜坡及 L1 控制模块。
- 本轮已运行 Host/RTL 回归及一次 Vivado 综合/实现，结果在 CURRENT_STATUS 和其引用证据目录。
- 当前已声明约束下的 timing 通过，但 DRC/完整约束签核、候选 bitstream 和板级闭环尚未形成可追溯 release。
- 历史 bitstream 和历史实验资料不能替代当前 Gate 的验证证据。

详细状态和当前 Gate 只在 docs/CURRENT_STATUS.md 维护；原 version 控制文件随历史版本归档，仅作追溯。

## FPGA 作用

FPGA 负责确定性实时处理：

- 接收 IN1/PD 和 IN2/REF。
- 完成 mixer、LPF、误差信号生成与输出保护。
- 生成 OUT1/laser_error。
- 管理 OUT2/selected_out2 的 SAFE、SCAN、HOLD、P_LOCK 状态与斜坡、捕获过程。
- 提供 Host 可读写的寄存器、状态和调试采集通道。

当前主数据路径为：

IN1/PD + IN2/REF → laser_lock_core → mixer_core → lpf_core → output_protect → laser_error → OUT1

OUT2 由 custom_register_bank、ramp_generator 和 out2_lock_controller 相关逻辑形成 selected_out2。pi_controller_seq 虽可参与 elaboration，但当前 OUT2 默认控制路径不是已验证的 PI 闭环。

## Host 作用

当前 Host 工程位于 software/redpitaya_lock_host，入口为 run.bat，主要职责是：

- 通过 SSH 和 /dev/mem 访问 FPGA 自定义寄存器区。
- 读取身份、版本、能力和运行状态。
- 执行 SAFE、SCAN、捕获、目标选择、P_LOCK 等受控操作。
- 显示采集数据并保存实验所需信息。

Host 不是 FPGA 接口的独立定义者。任何寄存器、数据通道或控制语义变化，必须按 docs/HOST_FPGA_INTERFACE.md 与 FPGA 同步管理。

## 实验作用

实验阶段负责把源码、bit、硬件连接、参数和测量结果绑定为可追溯证据。现有 exp_data 包含示波器 CSV、图片和分析材料，但多数记录尚未统一绑定 FPGA commit、bit hash、Host version、仪器配置和测试结论，因此不能自动视为当前 Gate 的通过证据。

当前仍未验证的关键事项包括当前 bit 上板、板卡身份读取、真实 ERROR-Crossing、PZT 无扰切换、P-only 收敛和持续锁定。

## AI 未来方向

深度学习参数优化是长期研究方向，不是当前实现状态。只有在确定性 FPGA/Host 基线已发布、实验元数据完整、数据质量可审计并且人工定义安全边界后，实验数据才可用于离线参数分析或候选参数建议。

当前没有已部署到 FPGA、Host 或真实闭环中的 AI 优化模块。AI 输出不得直接绕过 Gate、Host/FPGA 接口约束或人工确认写入硬件。

## Linien 对应关系（本轮采用范围）

| Linien 源码符号 | 本项目对应模块 | 已具备/缺陷/不适用 | 测试或证据 |
| --- | --- | --- | --- |
| `LinienLogic.connect_pid`、`pid.running`/`sweep.hold` | `out2_lock_controller`、`simple_lock_acquisition` | 已具备 FPGA 接管与扫描保持分工；本项目只实现 OUT2 P-only，Linien 的双通道慢积分不直接适用 | `tb_simple_lock_acquisition` 37/37；OUT2 真实闭环未验证 |
| `SimpleAutolock.turn_on_lock` | `realtime_error_crossing_detector` → `simple_lock_acquisition` | 已具备按扫描方向、目标窗和误差过零判定；Linien 的扫点窗口不能替代本项目的实际 OUT2 捕获样本 | `tb_simple_lock_acquisition`；Host CSR 序列测试 |
| `linien_server.autolock.simple.SimpleAutolock` | Host acquisition/selection service | 可参考软件选点后交给 FPGA；不引入 correlation/autolock server 框架 | Host targeted pytest 通过 |
| `SweepCSR`/`Sweep` | `ramp_generator` + OUT2 SCAN 路径 | 扫描输出已存在且用户已验证；仅保留回归，不迁移 Migen 实现 | 用户 OUT2 扫描事实；当前 bit 未重新生成 |

Linien 的软件准备目标、FPGA 事件接管和控制启动属于不同时间尺度；本项目沿用这个分工，同时保留 D2 Main 双反馈和 FPGA OUT2→专用 SCAN/PZT 接线事实。验证成功、Kp=0 捕获、P-only 和持续稳频仍是四个不同判据。

## 当前权威入口

- 项目含义：docs/PROJECT_CONTEXT.md
- 当前状态：docs/CURRENT_STATUS.md
- 当前 Gate：docs/CURRENT_STATUS.md
- Host/FPGA 契约：docs/HOST_FPGA_INTERFACE.md
- 工程变更：docs/CHANGELOG.md
- FPGA 开发流程：docs/FPGA_DEVELOPMENT_RULES.md
- bit 发布：docs/RELEASE_PROCESS.md
