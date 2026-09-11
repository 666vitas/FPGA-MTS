# Current Status

- Status: ACTIVE
- Authority: 唯一项目当前状态入口
- Snapshot-Date: 2026-09-11
- Evidence-Basis: 本地 Git/源码审查、Host 定向 pytest、Vivado 2020.1 xsim/综合/实现/报告；未连接板卡
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
- 用户截图对应的既有 routed run：`v0.94/exp/v3-arm/impl_1`，Vivado 2020.1，2026-09-09 14:05；WNS 0.080 ns、TNS 0、WHS 0.053 ns、THS 0、TPWS 0、Failed Routes 0。该报告早于本次 RTL 修改，不能替代当前源码时序证据
- 本次当前源码 run：`v0.94/exp/l1-contract-20260909/build/l1_contract_impl_20260909`；WNS 0.121 ns、TNS 0、WHS 0.051 ns、THS 0、TPWS 0、Failed Routes 0。源码/输入哈希前后匹配，已完成综合和 route_design；检查范围内 timing PASS，完整签核未闭合。
- 本轮当前源码 run：`v0.94/exp/l1-candidate-20260911` 的 `l1_candidate_impl_final_20260911`；WNS 0.024 ns、TNS 0、WHS 0.049 ns、THS 0、TPWS 0，Fully Routed。phys_opt_design 在 Vivado 2020.1 发生可复现访问冲突，已在独立 run 中禁用并以 Explore route 完成；旧 `impl_1` 和 `l1_contract_impl_20260909` 未被冒充或覆盖。
- 当前可发布 bitstream：CANDIDATE；`E:\new\fpga_lock\releases\20260911_LOCK-MVP-L1_CANDIDATE_8fc084e\red_pitaya_top_CANDIDATE.bit`，2,083,850 bytes，SHA-256 `6E5077DE121E261C198FB828E4178687932A79BC9D468D3931FE796A2369CB0B`。这是首次板级测试候选，不是硬件验证通过的 release。

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
- `tb_simple_lock_acquisition` 37/37、`tb_out2_lock_controller` 60/60、`tb_l1_error_crossing_plant` 10/10 PASS；覆盖 VALIDATE→SCAN→人工 ACTIVE、实际 OUT2 捕获、Q8 正负截断/限幅及输出模式优先级。plant 为简化数字模型，其 Kp=128 等数值不是硬件建议值。
- Host 定向套件（lock services、custom backend/workflow、低幅过零、操作员诊断）194 passed。
- Host `apply-p` 现在依据 FPGA 状态 4/5 设置 ACQUIRING/P_LOCKED；异常读回进入 SAFE/FAILED。
- VALIDATE 快速完成时，Host 仅接受 ARM 前 event sequence 基线之后、同一 config generation/方向的 VALIDATED 事件。
- 已确认目标绑定到 GUI 生命周期内持久的 AcquisitionService；worker 不再用请求 capture_id 初始化自己的有效状态。新 capture、重扫、参数变化、主机/基址变化及断连使旧目标失效，旧上下文的异步回复被丢弃；目标偏置微调需要重新确认。
- 离线证据位于 `v0.94/exp/l1-contract-20260909/`：最终 `host_pytest_delivery.log`、三个 `*_xsim.log`、`delivery_identity.json` 和 `delivery_worktree.patch`。`source_identity.json`/`source_worktree.patch` 是构建前快照；最后普通 STATUS 验证完成显示仅改 Host，未改变 RTL/构建输入。`host_pytest.log` 保留了诊断历史被误清除的中间失败，最终已修复并回归；当前证据不是 bit release。
- 当前构建证据：`v0.94/exp/l1-candidate-20260911/final_build_identity.txt`、`final_*` 报告和 `final_routed.dcp`；Daisy 禁用分支已改为静态 `OBUFDS`，最终 DRC 无 IOSTDTYPE-1 Critical Warning/Error；DNA 使用实际 `adc_clk/16` generated clock，`no_clock=0`、内部未约束端点=0。扩展 GPIO、DAC 数据/控制、可选输出时钟仍有 no_input_delay=16、no_output_delay=40，因缺少板级时序资料没有填 0 或设 false path。
- CDC 分析路径 Unsafe=0、Unknown=0，但 `clk_fpga_0 -> pll_adc_clk` false-path 行仍有 32 个 No ASYNC_REG，未宣称所有跨时钟问题已证明安全。Methodology 保留 TIMING-10=1、TIMING-18=38、XDCH-2=32；这些是候选的人工批准项。

### 未完成

- 板级 I/O delay 仍需原理图、连接器走线和 ADC/DAC 数据手册给出具体时序；本轮只完成可追溯候选，不把缺失资料自行批准。
- 与干净 Git commit 一一绑定的正式 bit release；当前 manifest 明确为 CANDIDATE。
- FPGA commit、Host version、Interface version、bit hash 的发布映射。

### 未验证

- DRC 普通 Warning/Advisory、保留的 CDC No ASYNC_REG 和缺失板级 I/O delay 的实际影响是否可接受；正 WNS 不替代这些检查。
- 当前 bit 是否可启动并由 Host 正确识别。
- 真实 ERROR-Crossing、PZT 无扰捕获、P-only 收敛和持续锁定。
- custom_debug_capture 在当前硬件和 Host 流程中的完整板级行为。

### 工作树边界

资产审查快照中，v94/main 的 HEAD 为 3563136ab4f88ebf924321a7e9cd4b85d70c53d2，且存在未提交的 RTL、仿真和状态文档修改。因此该 HEAD 不能单独代表当前工作树，也不能作为当前 bit 的完整来源标识。

2026-09-11 实查 HEAD 为 `8fc084e55cc353813edc980559a8f78fdec4658c`。本轮保留 XPR/Vivado 元数据改动；只修改 disabled Daisy RTL、相关 XDC、候选构建脚本和固定文档，并在 XPR 下使用独立 final run。原 synth_1/impl_1 与旧 l1-contract run 未重置；未修改 PS/BD、ADC/DAC 主数据通路或锁定算法。

## Host状态

- 当前 Host：software/redpitaya_lock_host
- 启动入口：software/redpitaya_lock_host/run.bat
- Python 入口：redpitaya_lock_host.main
- FPGA 访问：SSH + /dev/mem，自定义 CSR 基址 0x40600000
- 当前操作链：Probe Registers → Status → SAFE → SCAN → Capture → 选择过零点 → LOCK HERE → Apply Kp → SAFE
- 当前独立 Host release/tag：未识别
- 与正式 FPGA bit 的兼容性绑定：NOT DONE
- 现有 Host 测试结果：本次定向回归 PASS；完整 `pytest -q` 未完成（长时间未结束后中断，具体阻塞项未定位）

根目录 raunjian 为历史 Host 资产，不是当前 Host 入口。

## 实验状态

- exp_data 中已有示波器 CSV、PNG、分析脚本和少量说明文件。
- data 主要为仿真或处理数据，不应与真实板级原始数据混用。
- 组会目录主要为 PPT/PPTX 汇报资产。
- 现有实验记录尚未普遍绑定当前 FPGA commit、bit SHA256、Host version、Interface version、板卡、接线、仪器和参数。
- 当前 LOCK-MVP-L1 的真实硬件闭环结论：NOT VERIFIED。

## 当前阻塞问题

1. 当前 RTL 工作树不是可唯一复现的干净发布基线，且 XPR/Vivado 元数据有用户修改；本候选不宣称正式 clean release。
2. 板级 I/O delay 资料缺失：no_input_delay=16、no_output_delay=40；扩展 GPIO、DAC 数据/控制和可选输出时钟需人工审查，不能以 0/false-path 替代。
3. 尚未完成板卡身份/版本读回和 Host/FPGA 兼容性确认。
4. 尚无绑定 candidate 的真实 P-only 锁定实验记录；D2 Main 双反馈和 OUT2→专用 SCAN/PZT 接线仍需人工验收。

上述未验证项不得把 candidate bit 写成硬件已验证。GUI 占用已不再阻塞；本轮已在原 XPR 下完成独立 final run 和 write_bitstream，保留旧报告与旧 run。

## 更新要求

每次开发必须更新本文件中的 Snapshot-Date、当前 Gate、已完成、未完成、未验证和阻塞项，同时在 docs/CHANGELOG.md 记录修改文件、原因、影响模块和验证方式。接口变化还必须同步更新 docs/HOST_FPGA_INTERFACE.md；形成 bit 时必须按 docs/RELEASE_PROCESS.md 建立映射。
