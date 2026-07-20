# STATUS

## 2026-07-18 v3LOCK-P0 Linien-style Manual Lock Foundation — Gate L0

### Stage

`v3LOCK-P0 / Linien-style Manual Lock Foundation`

### Current Gate

`Gate L0 / Diagnose scan-to-lock offset`

### Current Blocker

- [USER HARDWARE VERIFIED] 用户已在真实硬件中观察到：板卡能够产生 PZT 扫描，能够观察 PD、MTS error 和 OUT2，上位机能够选择目标误差零点。
- [USER HARDWARE VERIFIED] 用户确认当前故障现象：执行 `LOCK HERE` 后，目标饱和吸收峰与示波器 cursor 存在明显偏差。
- [NOT VERIFIED] 尚未区分偏差来自 loaded PZT 实际电压/动态迟滞、rising/falling 扫描方向、Linux 轮询与寄存器写入时刻、`LOCK HERE` 重新捕获机制，还是 MTS error 零交叉与目标谱峰中心本身不重合。
- 当前 blocker 是缺少同一谱线、同一零交叉、同一扫描方向下 `HOLD SELECTED COUNT` 与 `LOCK HERE, Kp=0` 的可比较硬件记录；不是已确认的 Python、RTL、寄存器或 bitstream 缺陷。

### Verified

#### SOFTWARE VERIFIED

- [AUTOMATED VERIFIED] 最新本地记录：当前 host 已提供 identity、SAFE、SCAN safe range、当前 capture 选点、`HOLD SELECTED COUNT`、`LOCK HERE`、MODE/ENABLE、OUT2 readback、saturation 和 CH1/CH3/CH4 capture；最近完整 software tests 为 `137 passed`。

#### SIMULATION VERIFIED

- [AUTOMATED VERIFIED] 当前记录中的独立 XSim：custom register bank `83/83`、OUT2 controller `29/29`，均无失败。未运行 synthesis、implementation 或 timing。

#### HARDWARE VERIFIED

- [USER HARDWARE VERIFIED] PZT 断开时，用户确认当前软件预补偿后的 GUI OUT2 设定与板上真实 OUT2 输出一致；本轮没有新增精确测量元数据。
- [USER HARDWARE VERIFIED] loaded PZT 实验中已经观察到可扫描的 PD、MTS error、OUT2 和 `LOCK HERE` 后谱峰/cursor 偏差这一故障现象；这只证明现象存在，不证明锁定或 Gate 通过。

### Not Verified

- [NOT VERIFIED] 当前 loaded PZT 节点在对比实验中的真实 min/max/center/Vpp。
- [NOT VERIFIED] 同一目标点在 rising/falling 方向下的频率或谱峰位置差异。
- [NOT VERIFIED] `HOLD SELECTED COUNT` 后谱峰是否相对 cursor 偏移。
- [NOT VERIFIED] `LOCK HERE` 后真实 OUT2 跳变量及捕获时刻。
- [NOT VERIFIED] Kp=0 scan-to-lock 是否无扰。
- [NOT VERIFIED] 最小非零 Kp 是否形成负反馈。
- [NOT VERIFIED] 基础 P-only 是否能够持续锁定。

### Forbidden Scope

- 本 Gate 只诊断偏移，不实现 Linien 状态机，不提高 Kp，不改变 Ki/polarity，不开展 PI、自动锁定、自动重锁、AI 优化或 GUI 扩张。
- 只有用户返回可比较的 HOLD/LOCK HERE 硬件记录并确认判据，才能结束 Gate L0；不得自动进入 Gate L1。

### Unique Next Experiment

只按 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 执行一次 Gate L0 A/B 对比：在已确认安全的同一接线和 `0.770 V / 0.080 V / 2 Hz / Kp=0 / Ki=0` 扫描条件下，对同一谱线、零交叉和扫描方向依次记录 `HOLD SELECTED COUNT` 与 `LOCK HERE` 的 selected counts、readback counts、loaded-node 实际电压、谱峰相对 cursor 偏移和 rising/falling；两次动作之间及结束后均返回 SAFE。任一身份、接线、范围、readback、saturation、跳变或最终 SAFE 条件不明确时立即停止。
