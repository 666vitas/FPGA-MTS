Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: STATUS
Last-Updated: 2026-07-26
Supersedes: previous LOCK-MVP-L0 status
Superseded-By: NONE

# FPGA-MTS 当前状态

## 当前事实

- Repository：`666vitas/FPGA-MTS`
- Local branch/HEAD at task start：`main@0f273cd`
- 本轮工作区：有未提交的 L1 本地修改；未 commit、未 push、未创建 PR。
- `MAGIC=0x4D545330`、`VERSION=0x00030200` 与旧 `0x00..0xE0` CSR 地址保持不变。
- 新 L1 capability CSR 为 `0xE4 = 0x4C310001`；Host 同时检查 VERSION 与 capability。

## 本轮实现

- 失败基线：`WNS=-5.323 ns`、`TNS=-2624.753 ns`、3224 个 setup failing endpoints，最差路径 13.244 ns/24 levels；路径从 active setpoint 经 subtract/abs、48-bit accumulate、dynamic shift、supervisor compare/divergence 到 `kp_effective`。
- `[IMPLEMENTED]` `simple_lock_acquisition` 改为小型 orchestrator：注册 sample alignment、既有 realtime crossing detector、小型 FSM、独立 Kp ramp、固定窗口 supervisor 和独立 event recorder。
- `[IMPLEMENTED]` L1 supervisor 固定 `OBSERVE_SHIFT=8`/256 servo ticks；ARM 拒绝其他 shift；24-bit 饱和累加，ARM 时预计算 sum thresholds，window snapshot/compare/counter/FSM 分拍。
- `[IMPLEMENTED]` crossing event 及其 OUT2/ERROR/lock-error payload 同拍对齐；VALIDATE 保持 SCAN，ACTIVE 仍捕获实际 OUT2，Kp=0 scan-to-lock 数字无跳变行为保留。
- `[IMPLEMENTED]` 大数据 sum/snapshot/event payload 不使用全局 reset，由 valid、start、window clear 控制；状态、pending、fault 和小控制寄存器保留 reset。
- `[CODE INSPECTED]` `par_clk -> pll_adc_clk` 7 个 endpoint 来自官方 daisy `rxp_datr_reg[15] -> par_dat[15] -> daisy_trig/trig_ext -> i_asg/ch[0]/rep_cnt_reg[*]/CE`。两个时钟真正异步，现路径无 2FF/toggle/handshake；未添加 blanket false path 或未经证明的 `ASYNC_REG`。

## 自动验证

- `[RTL SIMULATED]` 全部 20 个 `v0.94/sim/tb_*.sv` 均重新 compile/elaborate/simulate 通过；有计数器的 15 个 testbench 合计 626/626，另 5 个 legacy testbench 退出码 0。
- `[RTL SIMULATED]` 关键新增/更新项：SIMPLE 32/32、plant 8/8、Kp ramp 6/6、supervisor 5/5、crossing 13/13、OUT2 controller 38/38、D1 register bank 166/166、deterministic 50/50、ramp 25/25。
- `[CODE INSPECTED]` `custom_register_bank`、L1 RTL 与 `red_pitaya_top` 重新 `xvlog` 通过；未执行 synthesis/implementation。
- `[UNIT TESTED]` `python -m pytest -q tests`：148 passed。

## Timing 与硬件

- `[FAILED]` 用户提供的本轮修改前 implementation：`WNS=-5.323 ns`、`TNS=-2624.753 ns`、3224 setup failing endpoints、hold failing endpoints=0。
- `[NOT VERIFIED]` 本轮 RTL 的 synthesis/implementation、WNS/TNS/WHS、high-fanout、unconstrained path。
- `[NOT VERIFIED]` bitstream generated / burned / board connected。
- `[NOT VERIFIED]` 真实 ERROR crossing、PZT bumpless、P-only convergence 和 sustained lock。

## 唯一下一动作

用户 Reset `synth_1/impl_1`，重新运行 Synthesis 和 Implementation，并提供 timing summary、最差 setup/hold 路径、high-fanout 与 unconstrained path 报告。timing 通过前不要生成或烧录正式 bitstream。
