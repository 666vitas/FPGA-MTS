Status: ACTIVE
Effective-Gate: LOCK-MVP-T0
Authority: STATUS
Last-Updated: 2026-07-24
Supersedes: version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md
Superseded-By: NONE

# STATUS

## Current Stage

`LOCK-MVP / Timing-Clean Minimal P-only Build`

## Current Gate

`LOCK-MVP-T0 / Timing-Clean Minimal Build`

## Current Facts

- [FAILED] 用户最新 Vivado implementation：WNS `-0.387 ns`、TNS `-5.015 ns`、`19` setup failing endpoints；setup timing 未通过。
- [TIMING PASSED] 用户报告 WHS `+0.052 ns`、hold failing endpoints `0`；hold timing 通过不能抵消 setup failure。
- [FAILED] 当前 bitstream 不能标记为 timing-clean，也不能作为第一次 P-only 锁定的合格 build。
- [IMPLEMENTED] deterministic ARM acquisition 源码、寄存器路径、host 路径和测试已经存在，必须保留。
- [RTL SIMULATED] D1 历史记录包含 register bank、OUT2 controller、deterministic acquisition 和 host 自动验证；完整证据已归档到 `version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md`。
- [NOT VERIFIED] `LOCK_MVP_BUILD` 的编译期 ARM 隔离、对应 RTL/testbench 和 timing closure 尚未完成。
- [NOT VERIFIED] ARM 不作为第一次 P-only 锁定依赖；这不表示 ARM 被删除、失败或不再开发。
- [NOT VERIFIED] 真实板卡 Kp=0 无扰切换、最小非零 Kp、基础 P-only 和持续锁定仍未通过。

## Current Blocker

当前 blocker 是带完整 deterministic ARM 综合路径的 build 未通过 125 MHz setup timing。先建立 `LOCK_MVP_BUILD`，在编译期关闭 ARM acquisition 的复杂综合实例/运行路径，同时保留 mixer/LPF、SCAN、HOLD、P_LOCK、capture、readback、limits 和 SAFE。

## Forbidden Scope

- 当前 Gate 不删除 ARM 源码、寄存器定义或测试。
- 不新增 PI/Ki、自动重锁、AI、IQ 或新的锁定算法。
- 不重写 GUI，不改变 IN1/IN2/OUT1/OUT2 语义。
- 没有新的用户 Vivado 报告前，不声称 timing passed、bitstream 合格、烧录成功或真实锁定通过。

## Unique Next Action

按 `version/CURRENT_GATE.md` 实现并验证 `LOCK_MVP_BUILD` 的编译期 ARM 隔离；随后由用户重新运行 Vivado implementation，并按 Gate 验收 WNS/TNS/WHS/THS、failing endpoints 和 unconstrained paths。
