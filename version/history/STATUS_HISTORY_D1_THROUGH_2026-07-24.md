Status: HISTORY
Effective-Gate: D1-D
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: version/STATUS.md

# STATUS History — D1 through 2026-07-24

本文件保存 `LOCK-MVP-T0` 生效前的 D1 状态快照。它包含独立 RTL/host 实现、仿真和用户 Vivado 结果，不能作为当前 Gate 入口。

## 2026-07-23 v3LOCK-D1 Deterministic FPGA Lock Acquisition Implementation

### Stage

`v3LOCK-D1 / Deterministic FPGA Lock Acquisition`

### Current Gate

`Gate D1-D / Integrated software/RTL verification and hardware SOP`

### Current Blocker

- [FAILED] 第一阶段控制集拆分后的用户 Vivado implementation 结果改善为 WNS `-0.630 ns`、TNS `-97.981 ns`、`310` setup failing endpoints、`0` hold failing endpoints，但尚未 timing closure；A 类自定义 `pll_adc_clk` 路径占 `295` endpoints。
- [NOT VERIFIED] 已完成第二阶段 acquisition decision/hold/event-commit 流水化，但尚未由用户重新运行 implementation，不能判断 WNS/TNS/high-fanout 是否已收敛。
- [NOT VERIFIED] 新 acquisition 尚未在真实板卡上验证寄存器 readback、ARM、实际触发点、Kp=0 无扰切换和 OUT2/PZT 行为。
- [NOT VERIFIED] 尚未执行新的硬件 SOP；最小非零 Kp 与基础 P-only 仍必须等待用户真实硬件结果。

### Verified

#### SOFTWARE / RTL IMPLEMENTED

- [IMPLEMENTED] `custom_register_bank` 已增加 D1 shadow/config、written mask、W1P `ARM/ABORT/CLEAR_EVENT`、状态、sticky coherent event、active readback 与 fault/reject readback，`VERSION=0x00030100`。
- [IMPLEMENTED] 独立 `deterministic_lock_acquisition` 在 `adc_clk` 域根据实际 `selected_out2` 相邻值生成 scan direction，并以 active target window 和原始 `laser_error` crossing 产生一次性 trigger。
- [IMPLEMENTED] 合法 ARM 同拍完成 shadow-to-active snapshot；ARM 后 shadow 修改不影响当前 transaction。trigger 同拍捕获实际 OUT2 为 `LOCK_BIAS`、应用 active `ERROR_SETPOINT`/limits，并原子进入 `MODE=3`、Kp=0、Ki=0。
- [IMPLEMENTED] `out2_lock_controller` 明确实现 `ABORT/FAULT > TRIGGER > normal` 输出优先级；trigger 拍保持当前 OUT2，P pipeline 填充期间输出捕获 bias。
- [IMPLEMENTED] 第一阶段 timing refactor 将 `custom_register_bank` 大型寄存器过程拆为 acquisition fast-control、shadow、scan/hold、capture 四个唯一驱动 `always_ff`；只有 fast-control 组保留 acquisition 决策优先级，其他三组仅由 reset 和相关 bus write 驱动。
- [IMPLEMENTED] 第二阶段在 ARM 时预计算 signed 16-bit target low/high；运行时 window 改为双边界比较，移除 subtract/abs。实时 comparator tree 只进入 `trigger_pending`，外部 `trigger`/`fault` 为注册单拍。
- [IMPLEMENTED] 新增注册 hold/trigger sample/event-commit 流水级；OUT2 controller 在 pending 与 commit 周期保持真实输出，register bank 使用捕获的 trigger OUT2 设置 `LOCK_BIAS`，event 仅由注册 commit 更新。
- [IMPLEMENTED] Python backend、Linux helper、CLI 和最小 GUI 已切换正常路径为完整 shadow preload + 单次 ARM；实时触发不再由 host target polling 或 `CAPTURE_LOCK_POINT` 决定。
- [IMPLEMENTED] GUI confirmed target 显示 scan direction、ERROR crossing direction、polarity suggestion（仅显示、不自动应用）和 `config_generation`；只有匹配 generation 的 sticky `TRIGGERED` event 才允许 Apply P。
- [IMPLEMENTED] legacy `lock-here` / `CAPTURE_LOCK_POINT` 保留为显式 diagnostic 路径，不是 GUI 正常 acquisition 路径。

#### AUTOMATED VERIFIED RECORDS

- [AUTOMATED VERIFIED] 正式 host 测试文件 `tests/test_custom_fpga_backend.py`、`tests/test_operator_voltage_diagnostics.py`、`tests/test_custom_fpga_workflow.py`、`tests/test_waveform_preview.py` 合计 `142 passed`。
- [AUTOMATED VERIFIED] XSim `tb_custom_register_bank_basic` 为 `143/143 PASS`，覆盖原有寄存器/acquisition 行为、控制集隔离，以及正负 target low/high snapshot。
- [AUTOMATED VERIFIED] XSim `tb_out2_lock_controller` 为 `35/35 PASS`，覆盖 SAFE/SCAN/HOLD/P_LOCK、trigger hold、ABORT/FAULT、P pipeline、correction/absolute saturation。
- [AUTOMATED VERIFIED] XSim `tb_deterministic_lock_acquisition` 为 `48/48 PASS`，覆盖 RISING/FALLING、两种 crossing、signed low/high、window 等号/窗口外、注册 trigger 单拍、真实 event sample/generation、ABORT/FAULT 优先级和逐拍 scan 变化。
- [AUTOMATED VERIFIED] 集成仿真记录 `out2_before=106`、`out2_trigger=106`、`captured_bias=106`、首拍及后续 Kp=0 OUT2 均为 `106`，数字命令跳变为 `0 counts`。

#### USER HARDWARE OBSERVATIONS

- [USER HARDWARE VERIFIED] PZT 断开时，用户确认当前软件预补偿后的 GUI OUT2 设定与板上真实 OUT2 输出一致；当前没有新增精确测量元数据。
- [USER HARDWARE VERIFIED] 用户已观察到真实 PZT 扫描、PD、MTS error 与 OUT2，并能在 GUI 中选择目标误差零点。
- [USER HARDWARE VERIFIED] 用户已观察到当前 `LOCK HERE` 后谱峰与 cursor 存在偏差；该观察只证明现象存在，不证明确定性切换或锁定通过。

### Not Verified

- [NOT VERIFIED] 第二阶段重构后的 Vivado synthesis/implementation 与 125 MHz timing closure；行为级仿真不等于 timing closed。
- [NOT VERIFIED] 真实板卡 Kp=0 scan-to-lock 是否无扰；`0 counts` 仅为 RTL 数字命令证据，不包含 DAC 模拟瞬态、PZT 或激光动态。
- [NOT VERIFIED] 最小非零 Kp 是否形成负反馈。
- [NOT VERIFIED] 基础 P-only 是否能够持续锁定。
- [NOT VERIFIED] 所有真实硬件锁定、自动重锁和长期稳频结果。

### Historical / Superseded Diagnostic Path

- 原 `Gate L0 / Diagnose scan-to-lock offset` 及其 HOLD/LOCK HERE A/B SOP 和已有记录全部保留，不删除，也不标记为 PASS。
- Gate L0 标记为 `historical / superseded diagnostic path`。

### 当时唯一下一动作

当时要求用户重新运行 Vivado implementation，并提供 WNS/TNS/failing endpoints、WHS/THS、unconstrained paths、最差路径和 high-fanout 报告。该动作现已被 `LOCK-MVP-T0` 取代。
