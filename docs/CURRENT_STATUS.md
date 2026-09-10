# Current Status

- Status: ACTIVE
- Authority: 唯一项目当前状态入口
- Snapshot-Date: 2026-09-09
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
- `tb_simple_lock_acquisition` 37/37、`tb_out2_lock_controller` 60/60、`tb_l1_error_crossing_plant` 10/10 PASS；覆盖 VALIDATE→SCAN→人工 ACTIVE、实际 OUT2 捕获、Q8 正负截断/限幅及输出模式优先级。plant 为简化数字模型，其 Kp=128 等数值不是硬件建议值。
- Host 定向套件（lock services、custom backend/workflow、低幅过零、操作员诊断）194 passed。
- Host `apply-p` 现在依据 FPGA 状态 4/5 设置 ACQUIRING/P_LOCKED；异常读回进入 SAFE/FAILED。
- VALIDATE 快速完成时，Host 仅接受 ARM 前 event sequence 基线之后、同一 config generation/方向的 VALIDATED 事件。
- 已确认目标绑定到 GUI 生命周期内持久的 AcquisitionService；worker 不再用请求 capture_id 初始化自己的有效状态。新 capture、重扫、参数变化、主机/基址变化及断连使旧目标失效，旧上下文的异步回复被丢弃；目标偏置微调需要重新确认。
- 离线证据位于 `v0.94/exp/l1-contract-20260909/`：最终 `host_pytest_delivery.log`、三个 `*_xsim.log`、`delivery_identity.json` 和 `delivery_worktree.patch`。`source_identity.json`/`source_worktree.patch` 是构建前快照；最后普通 STATUS 验证完成显示仅改 Host，未改变 RTL/构建输入。`host_pytest.log` 保留了诊断历史被误清除的中间失败，最终已修复并回归；当前证据不是 bit release。
- 当前构建证据：`current_build_identity.txt`、`build_input_hashes.json`、`current_*` 报告/route checkpoint、`build_verification.json`；DRC 4 个 Daisy IOSTDTYPE-1 Critical Warning + 41 Warning，与原 v3-arm 规则数量一致；CDC 已分析路径 Unsafe=0、Unknown=0，另有 32 个 No ASYNC_REG；Methodology TIMING-17 指向未定义时钟的 DNA 单元。

### 未完成

- Daisy I/O 标准、DNA 时钟、缺失 I/O delay 等既有约束/方法学问题的处置与完整签核。
- 所需检查闭合后的候选 bit；本次未执行 write_bitstream，没有可加载的本轮 bit。
- 与干净 Git commit 一一绑定的正式 bit release。
- FPGA commit、Host version、Interface version、bit hash 的发布映射。

### 未验证

- DRC Critical Warning 和未约束路径的影响是否可接受；正 WNS 不替代这些检查。
- 当前 bit 是否可启动并由 Host 正确识别。
- 真实 ERROR-Crossing、PZT 无扰捕获、P-only 收敛和持续锁定。
- custom_debug_capture 在当前硬件和 Host 流程中的完整板级行为。

### 工作树边界

资产审查快照中，v94/main 的 HEAD 为 3563136ab4f88ebf924321a7e9cd4b85d70c53d2，且存在未提交的 RTL、仿真和状态文档修改。因此该 HEAD 不能单独代表当前工作树，也不能作为当前 bit 的完整来源标识。

2026-09-09 实查 HEAD 为 `7c7b6570d4197939cd8e0101b096928d2ff67486`。进入本轮时仅 XPR 和 `project/redpitaya.cache/wt` 的 Vivado 元数据有改动，已保留。本次修改 custom RTL、Host、测试及固定文档，并在 XPR 新增两个独立构建 run。构建前 XPR 快照和语义比较确认：除新增 run 和同值组件条目排序外，其余内容一致；原 synth_1/impl_1 未重置。未修改 PS/BD、ADC/DAC 外壳、时钟或 XDC。

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

1. 当前 RTL 工作树不是可唯一复现的干净发布基线，且 XPR/Vivado 元数据有用户修改。
2. 当前源码综合/实现和 timing 已有证据，但 DRC/完整约束签核未关闭：no_clock=1、内部未约束端点=2、无输入延迟=16、无输出延迟=40。Daisy/ADC/DNA 问题涉及本轮保留的板级外壳与约束，未通过改 I/O/时钟或降低 DRC 级别处理，因此停止候选 bit 生成。
3. 尚无与当前源码一一绑定的 bit release。
4. 尚未完成板卡身份/版本读回和 Host/FPGA 兼容性确认。
5. 尚无绑定 release 的真实 P-only 锁定实验记录；D2 Main 双反馈和 OUT2→专用 SCAN/PZT 接线仍需人工验收。

上述阻塞项未关闭前不得把历史 bit、历史报告或仿真结果写成当前硬件已验证。GUI 占用曾阻止构建；本轮复查其退出后，已在原 XPR 下完成一次独立 run，当前阻塞不再是 GUI 占用。

## 更新要求

每次开发必须更新本文件中的 Snapshot-Date、当前 Gate、已完成、未完成、未验证和阻塞项，同时在 docs/CHANGELOG.md 记录修改文件、原因、影响模块和验证方式。接口变化还必须同步更新 docs/HOST_FPGA_INTERFACE.md；形成 bit 时必须按 docs/RELEASE_PROCESS.md 建立映射。
