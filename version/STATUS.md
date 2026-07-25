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

- [FAILED] 用户上一份 D1 构建报告为 WNS `-0.387 ns`、TNS `-5.015 ns`、`19` 个 setup failing endpoints；该旧 build 未 timing closure。
- [IMPLEMENTED] `LOCK_ACQ_IMPL=0/1/2` 从 `red_pitaya_top` 传播到唯一的 `custom_register_bank`；正式顶层默认 SIMPLE。
- [IMPLEMENTED] SIMPLE 只保留 request、运行前置条件、scan direction、target window、abort、注册单拍 trigger、trigger sample 和 ARMED/P_LOCK/FAULT readback。
- [IMPLEMENTED] SIMPLE trigger 同一 fast-control transaction 写入 bias、setpoint、limits、MODE、ENABLE 和 integral reset；不强制 Kp 清零。
- [IMPLEMENTED] D1 完整源码、atomic snapshot、event/timestamp 和 Kp=0 语义保留。
- [IMPLEMENTED] SIMPLE/D1 VERSION 分别为 `0x00030200`/`0x00030100`，Host 识别并显示 capability。
- [IMPLEMENTED] GUI ARM 路径经 `LocalClient → LockService → CustomFpgaBackend`；target 与 capture id 绑定，stale target 拒绝，readback mismatch 请求 SAFE。
- [RTL SIMULATED] `tb_simple_lock_acquisition` 24/24、`tb_custom_register_bank_basic` 166/166、`tb_deterministic_lock_acquisition` 50/50、`tb_out2_lock_controller` 35/35。
- [UNIT TESTED] `software/redpitaya_lock_host/tests/**` 共 146 个测试通过。
- [NOT VERIFIED] 本轮未运行 Vivado；SIMPLE build 的 WNS/TNS、high fanout、utilization 和 unconstrained paths 未验证。
- [NOT VERIFIED] 未生成或烧录 bitstream，未连接板卡；真实 Kp=0/Kp=4、模拟无扰和持续锁定均未验证。

## Current Blocker

唯一 blocker 是缺少用户对默认 SIMPLE build 的新 Vivado implementation 报告。
旧 D1 timing 报告不能用来判断 SIMPLE 是否收敛；旧报告的最差路径已位于 LPF，
因此 SIMPLE 降低 acquisition 负担后仍可能存在独立 LPF setup violation。

## Forbidden Scope

- 没有新 timing 报告前不继续 LPF 或其他大规模 RTL 重构。
- 不新增 PI/Ki、自动重锁、AI、IQ，不删除 D1。
- 不声称 timing、bitstream、烧录或真实硬件锁定通过。

## Unique Next Action

用户保持 `red_pitaya_top.LOCK_ACQ_IMPL=1`，运行 Vivado implementation，并返回
完整 timing summary、最差 setup path、failing endpoints、high fanout、utilization
和 unconstrained paths。
