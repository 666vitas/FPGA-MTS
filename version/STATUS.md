# STATUS

## 2026-07-23 v3LOCK-D1 Deterministic FPGA Lock Acquisition Implementation

### Stage

`v3LOCK-D1 / Deterministic FPGA Lock Acquisition`

### Current Gate

`Gate D1-D / Integrated software/RTL verification and hardware SOP`

### Current Blocker

- [NOT VERIFIED] 尚未由用户在 Vivado 中执行 synthesis/implementation、确认 125 MHz timing、生成或烧录新 bitstream。
- [NOT VERIFIED] 新 acquisition 尚未在真实板卡上验证寄存器 readback、ARM、实际触发点、Kp=0 无扰切换和 OUT2/PZT 行为。
- [NOT VERIFIED] 尚未执行新的硬件 SOP；最小非零 Kp 与基础 P-only 仍必须等待用户真实硬件结果。

### Verified

#### SOFTWARE / RTL IMPLEMENTED

- [IMPLEMENTED] `custom_register_bank` 已增加 D1 shadow/config、written mask、W1P `ARM/ABORT/CLEAR_EVENT`、状态、sticky coherent event、active readback 与 fault/reject readback，`VERSION=0x00030100`。
- [IMPLEMENTED] 独立 `deterministic_lock_acquisition` 在 `adc_clk` 域根据实际 `selected_out2` 相邻值生成 scan direction，并以 active target window 和原始 `laser_error` crossing 产生一次性 trigger。
- [IMPLEMENTED] 合法 ARM 同拍完成 shadow-to-active snapshot；ARM 后 shadow 修改不影响当前 transaction。trigger 同拍捕获实际 OUT2 为 `LOCK_BIAS`、应用 active `ERROR_SETPOINT`/limits，并原子进入 `MODE=3`、Kp=0、Ki=0。
- [IMPLEMENTED] `out2_lock_controller` 明确实现 `ABORT/FAULT > TRIGGER > normal` 输出优先级；trigger 拍保持当前 OUT2，P pipeline 填充期间输出捕获 bias。
- [IMPLEMENTED] Python backend、Linux helper、CLI 和最小 GUI 已切换正常路径为完整 shadow preload + 单次 ARM；实时触发不再由 host target polling 或 `CAPTURE_LOCK_POINT` 决定。
- [IMPLEMENTED] GUI confirmed target 显示 scan direction、ERROR crossing direction、polarity suggestion（仅显示、不自动应用）和 `config_generation`；只有匹配 generation 的 sticky `TRIGGERED` event 才允许 Apply P。
- [IMPLEMENTED] legacy `lock-here` / `CAPTURE_LOCK_POINT` 保留为显式 diagnostic 路径，不是 GUI 正常 acquisition 路径。

#### AUTOMATED VERIFIED RECORDS

- [AUTOMATED VERIFIED] 正式 host 测试文件 `tests/test_custom_fpga_backend.py`、`tests/test_operator_voltage_diagnostics.py`、`tests/test_custom_fpga_workflow.py`、`tests/test_waveform_preview.py` 合计 `142 passed`。
- [AUTOMATED VERIFIED] XSim `tb_custom_register_bank_basic` 为 `136/136 PASS`，覆盖地址、signed readback、partial/complete config、invalid ARM、multi-command、snapshot、sticky event、generation、CLEAR_EVENT、Apply P 和 ABORT。
- [AUTOMATED VERIFIED] XSim `tb_out2_lock_controller` 为 `35/35 PASS`，覆盖 SAFE/SCAN/HOLD/P_LOCK、trigger hold、ABORT/FAULT、P pipeline、correction/absolute saturation。
- [AUTOMATED VERIFIED] XSim `tb_deterministic_lock_acquisition` 为 `32/32 PASS`，覆盖 RISING/FALLING/相等 sample/端点反转、方向或窗口不匹配、两种 crossing、同拍 ABORT、runtime fault 和集成 trigger。
- [AUTOMATED VERIFIED] 集成仿真记录 `out2_before=100`、`out2_trigger=100`、`captured_bias=100`、首拍及后续 Kp=0 OUT2 均为 `100`，数字命令跳变为 `0 counts`。

#### USER HARDWARE OBSERVATIONS

- [USER HARDWARE VERIFIED] PZT 断开时，用户确认当前软件预补偿后的 GUI OUT2 设定与板上真实 OUT2 输出一致；当前没有新增精确测量元数据。
- [USER HARDWARE VERIFIED] 用户已观察到真实 PZT 扫描、PD、MTS error 与 OUT2，并能在 GUI 中选择目标误差零点。
- [USER HARDWARE VERIFIED] 用户已观察到当前 `LOCK HERE` 后谱峰与 cursor 存在偏差；该观察只证明现象存在，不证明确定性切换或锁定通过。

### Not Verified

- [NOT VERIFIED] Vivado synthesis/implementation 与 125 MHz timing closure；本轮行为级仿真不等于 timing closed。
- [NOT VERIFIED] 真实板卡 Kp=0 scan-to-lock 是否无扰；`0 counts` 仅为 RTL 数字命令证据，不包含 DAC 模拟瞬态、PZT 或激光动态。
- [NOT VERIFIED] 最小非零 Kp 是否形成负反馈。
- [NOT VERIFIED] 基础 P-only 是否能够持续锁定。
- [NOT VERIFIED] 所有真实硬件锁定、自动重锁和长期稳频结果。

### Forbidden Scope

- 本 Gate 不做 PI、Ki、自动重锁、机器学习、谱形相关、完整自动锁定或无关 GUI 扩张。
- 本 Gate 不进行硬件实验，不运行 Vivado synthesis/implementation，不生成或烧录 bitstream。
- 不把接口设计、软件测试或 RTL 仿真写成 GUI/硬件/锁定通过。

### Historical / Superseded Diagnostic Path

- 原 `Gate L0 / Diagnose scan-to-lock offset` 及其 HOLD/LOCK HERE A/B SOP 和已有记录全部保留，不删除，也不标记为 PASS。
- Gate L0 现标记为 `historical / superseded diagnostic path`。用户已明确授权先修复数字获取架构，暂缓 HOLD/LOCK HERE 硬件 A/B；待软件与 RTL 仿真通过后再制定新的硬件 Gate。
- 原 L0 结果仍可作为偏移现象与安全边界的历史证据，但不再是当前唯一 blocker。

### Unique Next Experiment

由用户在 Vivado 中确认现有 `custom_register_bank.sv` 已作为工程 source，运行 synthesis/implementation 并检查 125 MHz timing；通过后再生成 bitstream，并按新的单项硬件 SOP 先验证身份、SAFE、SCAN、ARM/event 与 Kp=0 OUT2，无真实结果不得进入 Gate D2。
