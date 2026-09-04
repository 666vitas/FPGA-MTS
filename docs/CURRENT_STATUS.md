# Current Status

- Status: ACTIVE
- Authority: 唯一项目当前状态入口
- Snapshot-Date: 2026-09-04
- Evidence-Basis: 已完成的项目资产审查；本次未重新扫描、未重新仿真、未重新运行 Vivado
- Workspace-Reorganization: DONE；源码、Host、Vivado 工程未改动，历史/参考/生成资产已分层归位
- Development-Freeze: FINAL；目录整理、旧文档归档和 Markdown 缓存清理已完成；后续进入 FPGA/Host 优化开发

本文件必须在每次开发后更新。本文件同时是项目当前状态和当前 Gate 的唯一入口；归档中的旧 version 文件仅作追溯，不得与本文件并行维护另一套“当前状态”。

本次最终冻结后，不再进行大规模目录规划或重复状态文档创建。后续开发只在
现有目录内修改 FPGA/Host、必要测试和固定入口文档；冻结基线记录在
`docs/DEVELOPMENT_BASELINE.md`。

状态词约定：

- DONE：已有对应实现或资产。
- DOCUMENTED：已有记录，但本次没有重跑验证。
- NOT DONE：所需产物尚未形成。
- NOT VERIFIED：没有足够的当前证据证明。
- BLOCKED：继续推进依赖明确的外部操作或人工确认。

## 当前Gate

LOCK-MVP-L1

目标：FPGA Real-Time ERROR-Crossing P-Only Lock。当前 Gate 只验证真实、可重复的 P-only 基础锁定；PI/Ki、自动重锁、相位优化和深度学习优化不属于当前 Gate。

## FPGA状态

### 当前Vivado工程

- 工程入口：E:\new\fpga_lock\v94\v0.94\project\redpitaya.xpr
- Top：red_pitaya_top
- Top 源文件：v0.94/rtl/red_pitaya_top.sv
- Device：xc7z010clg400-1
- 最近可识别的历史 routed run：Vivado 2020.1，生成于当前 RTL 修改之前，仅可作历史证据
- 当前可发布 bitstream：NOT DONE

### 主要模块

| 模块 | 当前作用 | 状态 |
| --- | --- | --- |
| red_pitaya_top | 顶层互联、ADC/DAC 与系统集成 | DONE |
| laser_lock_core | 锁定信号主链路 | DONE |
| mixer_core | PD/REF 混频 | DONE |
| lpf_core | 低通滤波 | DONE |
| output_protect | 输出限幅与保护 | DONE |
| custom_register_bank | Host CSR、状态和参数入口 | DONE |
| simple_lock_acquisition | 当前选择的采集实现 | DONE |
| realtime_error_crossing_detector | 实时误差过零检测 | DONE |
| l1_kp_ramp | L1 Kp 斜坡 | DONE |
| l1_lock_supervisor | L1 状态监督 | DONE |
| l1_event_recorder | L1 事件记录 | DONE |
| out2_lock_controller | OUT2 SAFE/SCAN/HOLD/P_LOCK 控制 | DONE |
| ramp_generator | 扫描斜坡 | DONE |
| error_setpoint_corrector | 误差设定点校正 | DONE |
| custom_debug_capture | 调试采集 | DONE；板级用途 NOT VERIFIED |
| pi_controller_seq | PI 候选逻辑 | 已 elaboration；当前 OUT2 路径未验证使用 |
| pi_controller | 旧/备选 PI 分支 | 当前 build 路径未选择 |
| deterministic_lock_acquisition | 备选 D1 分支 | LOCK_ACQ_IMPL=1 时未选择 |

### 已完成

- 当前 XPR、top 和主要模块关系已由资产审查识别。
- 锁定、采集、保护和 Host CSR 所需的 RTL 路径已存在。
- 归档前 version/STATUS.md 记录行为回归 20/20 和 Host pytest 181 passed；这些结果在本阶段仅标记为 DOCUMENTED，本次未重跑。

### 未完成

- 基于当前 RTL 工作树的 Vivado 综合和实现。
- 基于当前 RTL 的时序签核记录。
- 与干净 Git commit 一一绑定的正式 bit release。
- FPGA commit、Host version、Interface version、bit hash 的发布映射。

### 未验证

- 当前修改后的 RTL 是否通过综合、实现、DRC/CDC 和 timing。
- 当前 bit 是否可启动并由 Host 正确识别。
- 真实 ERROR-Crossing、PZT 无扰捕获、P-only 收敛和持续锁定。
- custom_debug_capture 在当前硬件和 Host 流程中的完整板级行为。

### 工作树边界

资产审查快照中，v94/main 的 HEAD 为 3563136ab4f88ebf924321a7e9cd4b85d70c53d2，且存在未提交的 RTL、仿真和状态文档修改。因此该 HEAD 不能单独代表当前工作树，也不能作为当前 bit 的完整来源标识。

## Host状态

- 当前 Host：software/redpitaya_lock_host
- 启动入口：software/redpitaya_lock_host/run.bat
- Python 入口：redpitaya_lock_host.main
- FPGA 访问：SSH + /dev/mem，自定义 CSR 基址 0x40600000
- 当前操作链：Probe Registers → Status → SAFE → SCAN → Capture → 选择过零点 → LOCK HERE → Apply Kp → SAFE
- 当前独立 Host release/tag：未识别
- 与正式 FPGA bit 的兼容性绑定：NOT DONE
- 现有 Host 测试结果：DOCUMENTED，未在本阶段重跑

根目录 raunjian 为历史 Host 资产，不是当前 Host 入口。

## 实验状态

- exp_data 中已有示波器 CSV、PNG、分析脚本和少量说明文件。
- data 主要为仿真或处理数据，不应与真实板级原始数据混用。
- 组会目录主要为 PPT/PPTX 汇报资产。
- 现有实验记录尚未普遍绑定当前 FPGA commit、bit SHA256、Host version、Interface version、板卡、接线、仪器和参数。
- 当前 LOCK-MVP-L1 的真实硬件闭环结论：NOT VERIFIED。

## 当前阻塞问题

1. 当前 RTL 工作树不是可唯一复现的干净发布基线。
2. 当前 RTL 修改后尚无新的 Vivado 综合、实现和 timing 证据。
3. 尚无与当前源码一一绑定的 bit release。
4. 尚未完成板卡身份/版本读回和 Host/FPGA 兼容性确认。
5. 尚无绑定 release 的真实 P-only 锁定实验记录。

上述阻塞项需要在用户授权的下一 Gate 中逐项关闭；未关闭前不得把历史 bit、历史报告或仿真结果写成当前硬件已验证。

## 更新要求

每次开发必须更新本文件中的 Snapshot-Date、当前 Gate、已完成、未完成、未验证和阻塞项，同时在 docs/CHANGELOG.md 记录修改文件、原因、影响模块和验证方式。接口变化还必须同步更新 docs/HOST_FPGA_INTERFACE.md；形成 bit 时必须按 docs/RELEASE_PROCESS.md 建立映射。
