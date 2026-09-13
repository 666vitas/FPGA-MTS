# Current Status

## 规则维护（2026-09-13）

- 已完成一次有限的 Astra 指令/Skill 规则维护：合并当前文档入口、按任务读取、授权连续执行边界，并更新 Rules 校验路径。
- 本轮未修改 Host/RTL、接口、Vivado 工程、约束、构建产物或硬件状态；未运行 Host、RTL、Vivado 或硬件验证。
- 客户端实际 Skill 自动加载链无法由仓库文件确认，需新会话核实。

## Host PZT-only 流程修复（2026-09-12）

- 本轮仅修改 Host、测试和固定文档；RTL、XDC、Vivado run、bitstream 均未修改/未运行。
- `ARM VALIDATE` 现在等待新的 VALIDATED sticky event、generation/双方向匹配，并自动确认 `SCAN/ENABLE=1、saturation=false`；不再要求手动 `REFRESH IDENTITY`。
- `ARM BASIC LOCK` 仅在当前 confirmed target 已完成本 generation VALIDATE 后启用，并固定从 Kp=0 开始。匹配 TRIGGERED 后显示 `PZT HOLD / Kp=0 / NOT LOCKED`，并显示 captured bias、delta 和 APPLY P。
- `APPLY P` 只开放 Kp=4，复用同一 captured bias、ERROR_SETPOINT 和 generation；Kp=0 hold 不宣称锁定。
- Host 定向回归：201 passed（含新增 VALIDATE→HOLD→APPLY P 门禁测试）；完整 `pytest -q` 曾因既有 GUI 测试不退出而中断，未作全量通过声明。
- 2026-09-12 板级事实仍按人工记录：OUT2 约 50 Hz scan、ERROR crossing 可选、VALIDATE 可产生 VALIDATED 并回 SCAN、Kp=0 后 OUT2 三角波停止并进入近似 DC hold；Kp=4 收敛/极性/持续锁定仍未验证。

## 本轮构建/手动复核对照卡（2026-09-12）

| 项目 | 自动构建（本轮候选） | 用户手动 `exp/test` |
| --- | --- | --- |
| 功能范围 | 仅现有 LOCK-MVP-L1 统一构建；不含 PZT 新功能 | PENDING |
| 候选文件 | `E:\new\fpga_lock\releases\20260912_LOCK-MVP-L1_CANDIDATE_4d754160\red_pitaya_top_CANDIDATE.bit`；同目录 `.bit.bin` | PENDING |
| 输入指纹 | `final_input_hashes.txt`；RTL/XDC/XPR 与本轮报告绑定，HEAD `4d754160c06346e6e0837bc38ca9d364a0301390`，工作树 dirty | 手动前运行 `check_build.ps1 -Phase pre` |
| 配置指纹 | Vivado 2020.1；top `red_pitaya_top`；`xc7z010clg400-1`；标准 `synth_1`→`impl_1`；Synthesis/Implementation Defaults；`PHYS_OPT_DESIGN=0`；route directive `Explore`；增量关闭 | 关闭并重开同一 XPR 后核对相同配置 |
| WNS / TNS | 0.024 ns / 0 | PENDING |
| WHS / THS | 0.049 ns / 0 | PENDING |
| WPWS / TPWS | 1.000 ns / 0 | PENDING |
| 失败端点 / Failed Routes | 0 / 0（15140/15140 fully routed） | PENDING |
| DRC | 43 violations：NSTD-1 14、PLIO-8 28、REQP-24 Advisory 1；最终 DRC Critical Warning/Error 0 | PENDING；与候选证据比较 |
| 全流程 Critical Warning | 47 行（含重复约束加载诊断；另有 198 行 Warning） | PENDING |
| 约束完整性 / CDC | `no_input_delay=16`、`no_output_delay=40`；未匹配 `dac_clk_o/dac_clk_*/ser_clk/pdm_clk/clk_fpga_0` false-path；`i_ams/XADC_inst` 不存在；CDC Unsafe=0、Unknown=0，但 32 `No ASYNC_REG` 保留 | PENDING；不得以 WNS 相同忽略差异 |
| BIT 与报告绑定 | 已核实：bit SHA256 `E2FCCF86CADD9A9D67439761483C6D77DDF8FF1BCB374BFAEAD4051C378080D0`；bit.bin SHA256 `C66257193D94AF8B40488F9EEEF609032FFF2970B7B44DAF3F35CB3D8422C1CA`；DCP SHA256 `FE45A276349AB003D4BB038FFD47F5F1DE9310497C23E6E073BEA407C4A0B2F2` | PENDING；不复制自动 bit 冒充手动结果 |
| 手动复核结论 | 不替代用户验证 | PENDING |

核对入口：构建前 `powershell -ExecutionPolicy Bypass -File v0.94/exp/test/check_build.ps1 -Phase pre`；构建后先将用户报告放在 `v0.94/exp/test/impl_1`（或 `evidence`），再运行 `...check_build.ps1 -Phase post`。允许下一步仅为：用户打开同一 XPR，选择标准 `synth_1`/`impl_1`，独立重建并回填手动结果；期间不要修改 RTL、XDC、IP 或运行设置。

此前用户提供的 `0.024/0/0.049/0` 仅保留为历史证据；在手动输入、配置和报告来源完成核对前，不并入本轮手动列。

- Status: ACTIVE
- Authority: 唯一项目当前状态入口
- Snapshot-Date: 2026-09-12
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
- 用户截图对应的既有 routed run：`v0.94/exp/v3-arm/impl_1`，Vivado 2020.1，2026-09-09 14:05；WNS 0.080 ns、TNS 0、WHS 0.053 ns、THS 0、TPWS 0、Failed Routes 0。该报告仅作历史证据。
- `v0.94/exp/l1-contract-20260909/build/l1_contract_impl_20260909` 与 `v0.94/exp/l1-candidate-20260911` 均保留为历史构建，不替代本轮标准 run。
- 本轮统一源码 run：标准 `v0.94/exp/test/synth_1` → `v0.94/exp/test/impl_1`；WNS 0.024 ns、TNS 0、WHS 0.049 ns、THS 0、WPWS 1.000 ns、TPWS 0，15140/15140 nets fully routed。`phys_opt_design` 禁用、route directive Explore 已保存到 XPR 标准 run。
- 当前候选 bitstream：`E:\new\fpga_lock\releases\20260912_LOCK-MVP-L1_CANDIDATE_4d754160\red_pitaya_top_CANDIDATE.bit`（2,083,850 bytes，SHA-256 `E2FCCF86CADD9A9D67439761483C6D77DDF8FF1BCB374BFAEAD4051C378080D0`）；同一 bit 的 `.bit.bin` SHA-256 `C66257193D94AF8B40488F9EEEF609032FFF2970B7B44DAF3F35CB3D8422C1CA`。这是候选，不是硬件验证通过的 release。

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
- Host 定向套件（lock services、custom backend/workflow、低幅过零、操作员诊断、波形预览）201 passed。
- Host `apply-p` 复用 Kp=0 captured context，仅开放 Kp=4；依据 FPGA 状态 4/5 设置 P-ONLY ACQUIRING 或 FPGA P_LOCKED/PHYSICAL VERIFICATION REQUIRED，异常读回进入 SAFE/FAILED。
- VALIDATE 快速完成时，Host 仅接受 ARM 前 event sequence 基线之后、同一 config generation/方向的 VALIDATED 事件。
- 已确认目标绑定到 GUI 生命周期内持久的 AcquisitionService；worker 不再用请求 capture_id 初始化自己的有效状态。新 capture、重扫、参数变化、主机/基址变化及断连使旧目标失效，旧上下文的异步回复被丢弃；目标偏置微调需要重新确认。
- 离线证据位于 `v0.94/exp/l1-contract-20260909/`：最终 `host_pytest_delivery.log`、三个 `*_xsim.log`、`delivery_identity.json` 和 `delivery_worktree.patch`。`source_identity.json`/`source_worktree.patch` 是构建前快照；最后普通 STATUS 验证完成显示仅改 Host，未改变 RTL/构建输入。`host_pytest.log` 保留了诊断历史被误清除的中间失败，最终已修复并回归；当前证据不是 bit release。
- 当前构建证据：`releases/20260912_LOCK-MVP-L1_CANDIDATE_4d754160/` 的 `final_*` 报告、`final_routed.dcp` 与 `final_input_hashes.txt`，均来自标准 `impl_1` routed 设计；DNA 使用实际 `adc_clk/16` generated clock，`no_clock=0`、内部未约束端点=0。扩展 GPIO、DAC 数据/控制、可选输出时钟仍有 no_input_delay=16、no_output_delay=40，因缺少板级时序资料没有填 0 或设 false path。
- CDC 分析路径 Unsafe=0、Unknown=0，但 `clk_fpga_0 -> pll_adc_clk` false-path 行仍有 32 个 No ASYNC_REG；Methodology 保留 TIMING-10=1、TIMING-18=38、XDCH-2=32。统一构建日志还明确记录 dac/ser/pdm/clk_fpga false-path 对象未匹配及 `i_ams/XADC_inst` 缺失，未宣称这些问题已解决。

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

2026-09-12 实查 HEAD 为 `4d754160c06346e6e0837bc38ca9d364a0301390`，工作树 dirty。保留用户 XPR/Vivado 元数据改动；本轮使用标准 `synth_1/impl_1`，未修改 PS/BD、ADC/DAC 主数据通路或锁定算法。旧 candidate 与历史 run 未覆盖。

## Host状态

- 当前 Host：software/redpitaya_lock_host
- 启动入口：software/redpitaya_lock_host/run.bat
- Python 入口：redpitaya_lock_host.main
- FPGA 访问：SSH + /dev/mem，自定义 CSR 基址 0x40600000
- 当前操作链：Probe Registers → SAFE → SCAN → Capture → PICK/CONFIRM → ARM VALIDATE（自动等待 VALIDATED/READY）→ Kp=0 ARM BASIC LOCK（PZT HOLD）→ Kp=4 APPLY P
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
