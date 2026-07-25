Status: ACTIVE
Effective-Gate: LOCK-MVP-L0
Authority: STATUS
Last-Updated: 2026-07-25
Supersedes: version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md
Superseded-By: NONE

# STATUS

## Current Stage

`LOCK-MVP / Linien-like Simple Scan-to-P-Lock`

## Current Gate

`LOCK-MVP-L0 / Linien-like Simple Scan-to-P-Lock`

## Current Facts

- [FAILED] 用户最新 SIMPLE 构建报告为 WNS `-0.119 ns`、TNS `-0.428 ns`、`4` 个 setup failing endpoints、WHS `+0.057 ns`；失败路径均为 `i_ramp_generator/limit_q → scan_o_reg`。
- [IMPLEMENTED] `LOCK_ACQ_IMPL=0/1/2` 从 `red_pitaya_top` 传播到唯一的 `custom_register_bank`；正式顶层默认 SIMPLE。
- [IMPLEMENTED] SIMPLE 只保留 request、运行前置条件、scan direction、target window、abort、注册单拍 trigger、trigger sample 和 ARMED/P_LOCK/FAULT readback。
- [IMPLEMENTED] SIMPLE trigger 同一 fast-control transaction 写入 bias、setpoint、limits、MODE、ENABLE 和 integral reset；不强制 Kp 清零。
- [IMPLEMENTED] D1 完整源码、atomic snapshot、event/timestamp 和 Kp=0 语义保留。
- [IMPLEMENTED] SIMPLE/D1 VERSION 分别为 `0x00030200`/`0x00030100`，Host 识别并显示 capability。
- [IMPLEMENTED] GUI ARM 路径经 `LocalClient → LockService → CustomFpgaBackend`；target 与 capture id 绑定，stale target 拒绝，readback mismatch 请求 SAFE。
- [IMPLEMENTED] `ramp_generator` 将规范化后的正负 limit 分别预寄存，实时输出只做单级 `raw_scan` 限幅；已删除后续 `±8191` 冗余比较/MUX，未增加 `scan_o` 时钟延迟。
- [RTL SIMULATED] `tb_simple_lock_acquisition` 24/24、`tb_custom_register_bank_basic` 166/166、`tb_deterministic_lock_acquisition` 50/50、`tb_out2_lock_controller` 35/35、`tb_ramp_generator` 25/25。
- [UNIT TESTED] `software/redpitaya_lock_host/tests/**` 共 146 个测试通过。
- [NOT VERIFIED] 本轮未运行 Vivado；ramp limit 重构后的 SIMPLE build WNS/TNS、high fanout、utilization 和 unconstrained paths 未验证。
- [NOT VERIFIED] 未生成或烧录 bitstream，未连接板卡；真实 Kp=0/Kp=4、模拟无扰和持续锁定均未验证。

## Current Blocker

唯一 blocker 是缺少 ramp limit 重构后的 SIMPLE synthesis/implementation timing 报告。

## Forbidden Scope

- 没有新 timing 报告前不继续 LPF 或其他大规模 RTL 重构。
- 不新增 PI/Ki、自动重锁、AI、IQ，不删除 D1。
- 不声称 timing、bitstream、烧录或真实硬件锁定通过。

## Unique Next Action

用户保持 `red_pitaya_top.LOCK_ACQ_IMPL=1`，Reset `synth_1`/`impl_1` 后重新运行
Synthesis 和 Implementation，并返回
完整 timing summary、最差 setup path、failing endpoints、high fanout、utilization
和 unconstrained paths。
