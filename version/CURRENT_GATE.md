Status: ACTIVE
Effective-Gate: LOCK-MVP-L0
Authority: CURRENT_GATE
Last-Updated: 2026-07-25
Supersedes: CURRENT_GATE_PROPOSED.md
Superseded-By: NONE

# CURRENT GATE — LOCK-MVP-L0 Linien-like Simple Scan-to-P-Lock

## 1. 当前事实

用户最近一次旧构建的 Vivado implementation：

```text
WNS  = -0.387 ns
TNS  = -5.015 ns
Setup failing endpoints = 19
WHS  = +0.052 ns
Hold failing endpoints = 0
```

该报告不代表本 Gate 的 SIMPLE build。当前代码已实现 `LOCK_ACQ_IMPL=0/1/2`
的编译期选择，正式 `red_pitaya_top` 默认 `1=SIMPLE`，D1 源码与测试保留。

## 2. 本 Gate 唯一目标

验证 timing-friendly 的基础 P-only 主路径：

```text
SCAN
→ aligned capture
→ select ERROR zero crossing
→ preload target / Kp / polarity / limits
→ request_lock
→ FPGA direction + target-window hit
→ atomic P_LOCK
→ lock health
```

HOLD/approach 是诊断回退路径，不是正式主路径的前置条件。

## 3. 构建模式

- `LOCK_ACQ_IMPL=0`：NONE。
- `LOCK_ACQ_IMPL=1`：SIMPLE，`LOCK_MVP_BUILD` 默认。
- `LOCK_ACQ_IMPL=2`：D1，保留完整 deterministic acquisition。
- SIMPLE VERSION：`0x00030200`。
- D1 VERSION：`0x00030100`。

## 4. 允许范围

- SIMPLE/D1 编译期 generate、SIMPLE acquisition 与对应 testbench；
- 最小 `LockService`、`AcquisitionService`、`LocalClient` 和 GUI adapter；
- 双 VERSION/capability readback；
- 本 Gate、STATUS 和本架构说明。

## 5. 禁止范围

- 不新增 PI/Ki、自动重锁、AI、IQ 或新的锁定算法；
- 不复制 Linien GPL 源码；
- 不删除 D1 源码、CSR 或测试；
- 不改变 IN1/IN2/OUT1/OUT2、CSR 地址、MAGIC；
- 不使用 false path、multicycle、降频或放宽约束掩盖功能路径；
- Codex 不运行 Vivado synthesis/implementation/bitstream，不连接板卡。

## 6. 验收条件

自动验证：

- SIMPLE、D1、register bank、OUT2 controller RTL testbench 全部通过；
- Host `tests/**` 全部通过；
- SIMPLE generate elaboration 不包含 D1 实例；
- stale capture 和 readback mismatch 回 SAFE 有测试。

用户 Vivado 验收：

```text
WNS >= 0 ns
TNS = 0 ns
WHS >= 0 ns
THS = 0 ns
setup failing endpoints = 0
unconstrained paths = 0
```

## 7. 唯一下一步

用户以默认 `LOCK_ACQ_IMPL=1` 运行一次 Vivado implementation，并返回
WNS、TNS、WHS、THS、failing endpoints、unconstrained paths、最差 setup
path 和 high-fanout 报告。没有新 timing 报告前不继续大规模 RTL 重构。
