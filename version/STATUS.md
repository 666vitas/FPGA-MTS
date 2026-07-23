# STATUS

## 2026-07-23 v3LOCK-D1 Deterministic FPGA Lock Acquisition Design

### Stage

`v3LOCK-D1 / Deterministic FPGA Lock Acquisition Design`

### Current Gate

`Gate D1-A / Freeze the deterministic lock-acquisition interface`

### Current Blocker

- [IMPLEMENTED] 当前 GUI 能从历史 capture 选取并确认 `target_out2_counts`，但 `LOCK HERE` 仍由 Red Pitaya Linux 轮询 `OUT2_MONITOR`，再写 `CAPTURE_LOCK_POINT`。
- [NOT VERIFIED] GUI 保存的 `ramp_direction` 尚未成为 FPGA 实时触发条件。
- [NOT VERIFIED] 尚无独立的 ERROR crossing direction 配置与 FPGA 判定。
- [NOT VERIFIED] 尚无 FPGA `ARM/ARMED/TRIGGERED/LOCK_ACTIVE/FAULT` 状态契约。
- [NOT VERIFIED] 尚无包含实际触发 OUT2、ERROR、方向、配置代次和 FPGA 时间戳的触发事件 readback。
- [NOT VERIFIED] 通信延迟尚未退出实时触发链路；Linux 轮询和寄存器写入时刻仍决定当前切换发生在哪一个扫描点。

### Verified

#### SOFTWARE / RTL IMPLEMENTED

- [IMPLEMENTED] 当前 host 已实现 SCAN、四通道 capture、GUI ERROR 零交叉选取、confirmed target 和 Kp=0 `LOCK HERE` 命令路径。
- [IMPLEMENTED] 当前 `CAPTURE_LOCK_POINT` 命令到达 FPGA 后，会在同一 `clk_i` 域捕获当时的 `ERROR_MONITOR` 与 `OUT2_MONITOR`，将 Kp/Ki 清零并进入 `MODE=3 P_LOCK`。
- [IMPLEMENTED] 当前 RTL 已有 P-only 数据路径、correction limit、absolute limit、SAFE/SCAN/HOLD/P_LOCK 基础模式和 saturation readback；这些实现不等于确定性 acquisition 已完成。

#### AUTOMATED VERIFIED RECORDS

- [AUTOMATED VERIFIED] 最近完整 software test 记录为 `137 passed`；本轮只修改文档，没有重跑 Python 测试。
- [AUTOMATED VERIFIED] 最近独立 XSim 记录为 custom register bank `83/83`、OUT2 controller `29/29`；本轮没有修改 RTL，也没有重跑 RTL 仿真。

#### USER HARDWARE OBSERVATIONS

- [USER HARDWARE VERIFIED] PZT 断开时，用户确认当前软件预补偿后的 GUI OUT2 设定与板上真实 OUT2 输出一致；当前没有新增精确测量元数据。
- [USER HARDWARE VERIFIED] 用户已观察到真实 PZT 扫描、PD、MTS error 与 OUT2，并能在 GUI 中选择目标误差零点。
- [USER HARDWARE VERIFIED] 用户已观察到当前 `LOCK HERE` 后谱峰与 cursor 存在偏差；该观察只证明现象存在，不证明确定性切换或锁定通过。

### Not Verified

- [NOT VERIFIED] FPGA deterministic acquisition interface、寄存器契约、FSM RTL 和仿真验收尚未实现。
- [NOT VERIFIED] Kp=0 scan-to-lock 是否无扰。
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

### Unique Next Action

完成 FPGA deterministic lock acquisition 的接口设计、寄存器契约、状态机行为和软件/RTL 仿真验收标准；当前设计基线见 `software/redpitaya_lock_host/docs/FPGA_DETERMINISTIC_LOCK_ACQUISITION.md`。
