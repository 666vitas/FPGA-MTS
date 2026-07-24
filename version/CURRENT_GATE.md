Status: ACTIVE
Effective-Gate: LOCK-MVP-T0
Authority: CURRENT_GATE
Last-Updated: 2026-07-24
Supersedes: CURRENT_GATE_PROPOSED.md
Superseded-By: NONE

# CURRENT GATE — LOCK-MVP-T0 Timing-Clean Minimal Build

## 1. 当前事实

用户最新 Vivado implementation：

```text
WNS  = -0.387 ns
TNS  = -5.015 ns
Setup failing endpoints = 19
WHS  = +0.052 ns
Hold failing endpoints = 0
```

当前结论：setup timing 未通过，当前 bitstream 不得作为 Lock MVP 的 timing-clean 版本。

## 2. 本 Gate 唯一目标

创建并验证 `LOCK_MVP_BUILD`：

- 关闭 deterministic ARM acquisition 的综合实例/复杂运行路径；
- 保留 mixer/LPF、SCAN、HOLD、P_LOCK、capture、readback、limits、SAFE；
- 不删除 ARM 源码、寄存器定义和测试；
- 实现 timing closure；
- 不修改真实锁定算法和 GUI 外观。

## 3. 允许修改

- `v0.94/rtl/` 中构建选择、generate、与 ARM 隔离直接相关的 RTL；
- 与 `LOCK_MVP_BUILD` 直接相关的 testbench；
- 构建脚本、Tcl 和约束；
- `version/STATUS.md`、本 Gate、manifest 和直接相关开发日志。

## 4. 禁止修改

- 不新增 PI、自动重锁、AI、IQ；
- 不重写 GUI；
- 不删除 deterministic ARM；
- 不改变 IN1/IN2/OUT1/OUT2 语义；
- 不修改官方 Red Pitaya PLL、PS、DDR、AXI、DAC IO，除非最差路径证据明确指向且用户另行授权；
- 不声称运行了用户本机 Vivado；
- 不声称生成或烧录成功。

## 5. 验收条件

### 自动验证

- Lock MVP RTL testbench 通过；
- ARM build 原有仿真不回归；
- host 单元测试不回归。

### 用户 Vivado 验收

```text
WNS >= 0 ns
TNS = 0 ns
WHS >= 0 ns
THS = 0 ns
unconstrained paths = 0
```

用户需提供：

- Design Timing Summary；
- 最差 setup path；
- failing endpoints 分类；
- high fanout 报告；
- utilization；
- unconstrained paths。

## 6. Gate 完成后的唯一下一步

进入 `LOCK-MVP-S1 Host/FPGA Contract Cleanup`：建立统一 RegisterMapper 和最小 LockService，先迁移 CONNECT/SAFE/SCAN，不进行大规模 GUI 改版。
