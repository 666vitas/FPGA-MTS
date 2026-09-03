Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: STATUS
Last-Updated: 2026-09-03
Supersedes: previous LOCK-MVP-L0 status
Superseded-By: NONE

# FPGA-MTS 当前状态

## 当前事实

- Repository：`666vitas/FPGA-MTS`
- Local branch/HEAD at task start：
  `main@04937478807fc6a2d65a43129180649cbdf99967`，与本地
  `origin/main` 一致；任务开始时 working tree clean。
- 2026-09-03 当前任务针对唯一 blocker 做最小 RTL 修改：
  `red_pitaya_top` 默认静态隔离 FIRST_LOCK 不使用的 legacy Daisy；未修改
  Host、XDC、CSR、`MAGIC`、`VERSION`、capability 或锁定数据通路，未创建
  分支、未 commit、未 push、未创建 PR。
- `MAGIC=0x4D545330`、`VERSION=0x00030200` 与旧 `0x00..0xE0` CSR 地址保持不变。
- 新 L1 capability CSR 为 `0xE4 = 0x4C310001`；Host 同时检查 VERSION 与 capability。

## 本轮实现

- `[IMPLEMENTED]` 2026-09-03 在 `red_pitaya_top` 增加顶层参数
  `ENABLE_DAISY=0`。默认单板 build 不 elaboration `red_pitaya_daisy` 的
  recovered-clock 数据通路；未使用 blanket false path，也未删除 legacy
  module。显式设为 1 时仍可构建原 Daisy 诊断路径。
- `[IMPLEMENTED]` Daisy disabled 分支把 SATA 差分输出驱动为静态互补值，
  `adc_clk_daisy` 连接本地 `adc_clk`，`par_dat` 与 legacy bus slot 返回确定
  空值。该分支不改变 FIRST_LOCK CSR、controller、capture 或 DAC 数据语义。
- `[NOT VERIFIED]` 修改后 RTL compile/elaboration、behavioral simulation、
  synthesis、implementation、CDC、DRC、methodology 与完整 timing。旧的
  2026-09-02 fresh routed 报告只作为修改前基线，不代表当前 candidate。

- `[TIMING FAILED]` 修改前 routed 基线：`WNS=-3.949 ns`、
  `TNS=-282.362 ns`、786 个 setup failing endpoints；`WHS=0.050 ns`、
  `THS=0`、0 个 hold failing endpoints。
- 修改前最差路径族：
  `i_out2_lock_controller/s5_lock_limit_reg[12]_replica`
  到 `i_out2_lock_controller/control_o_reg[*]`，8.000 ns requirement，
  约 11.844 ns total/23 logic levels。
- `[IMPLEMENTED]` `out2_lock_controller` 在 S4→S5 并行归一化
  absolute limit，`-8192` 饱和为 8191；新增 S6 注册
  absolute-clamped target、saturation、mode、enable、valid 和 normalized
  slew limit。最终输出周期只保留 `s6_target-control_o` 与单周期 slew
  commit，未把递归 feedback 拆成自由运行的多级 transaction。
- `[IMPLEMENTED]` P_LOCK pipeline latency 从 7 增为 8 clocks；离开
  P_LOCK/PI_LOCK、disable、abort 或 fault 会 flush pipeline valid。
  SAFE/SCAN/HOLD/acq_hold 继续直接绕过 P pipeline。
- `[IMPLEMENTED]` 未修改 `simple_lock_acquisition`、crossing、Kp ramp、
  supervisor、event recorder、`red_pitaya_top`、CSR、`MAGIC`、
  `VERSION`、`L1_CAPABILITY`、XDC 或 PLL。
- `[IMPLEMENTED]` Host 在单次写 `ACQ_COMMAND` 后使用 monotonic
  200 ms 有界轮询；VALIDATE 接受 `VALIDATING`，ACTIVE 接受
  `ARMED/ACQUIRING/P_LOCKED`，`FAILED/FAULT` 立即返回完整诊断。
- `[IMPLEMENTED]` Host/GUI 统一 L1 acquisition state `0..7`，区分
  Transport 与 FPGA Command/State/Validation 错误；逻辑失败保留
  Connected/Identity，并显示 last ARM intent/result、state、validation、
  fault、event 和 validate count。
- `[IMPLEMENTED]` SAFE 先禁止输出，再清零 P/PI 状态，单次发出
  acquisition ABORT，并只在 `MODE=SAFE`、`ENABLE=0`、
  `acquisition_state=SAFE` 回读一致时报告 `SAFE CONFIRMED`。
- `[IMPLEMENTED]` GUI 禁止并发 SSH register worker；Live Capture 的 ARM
  请求先停止 Live，等待当前 capture worker 完成，再串行启动。ARM 按钮
  绑定 L1 capability、SCAN/ENABLE/state、saturation、当前 confirmed
  target/generation、Kp 和 worker/live 状态。
- `[IMPLEMENTED]` Host Direct ERROR 选点使用默认 ±64 samples 搜索、
  局部最小二乘 CH4 趋势和分段一致性判断，允许量化低幅扫描、稳定异号
  夹住的 exact-zero/短 zero plateau；候选以点击距离优先，并拒绝转折、
  低 SNR/低 slope、越界、边缘、饱和与歧义。
- `[IMPLEMENTED]` 选点拒绝使用结构化 reason code，并在 Engineer Details
  保留 clicked/search window、candidate/rejection counts、ERROR noise/Vpp、
  ramp fit 和 safe-range 原始诊断；选择成功仍只产生 pending，必须用户
  Confirm 后才可手动 ARM。

## 自动验证

- `[RTL SIMULATED]` 全部 20 个 `v0.94/sim/tb_*.sv` 重新
  compile/elaborate/simulate 通过；有计数器的 15 个 testbench 合计
  642/642，另 5 个 legacy testbench 退出码 0。
- `[RTL SIMULATED]` 关键项：OUT2 controller 54/54、SIMPLE 32/32、
  plant 8/8、Kp ramp 6/6、supervisor 5/5、crossing 13/13、
  D1 register bank 166/166、deterministic 50/50、ramp 25/25。
- `[UNIT TESTED]` `python -m pytest -q tests`：181 passed；其中新增 17 个
  低幅量化 zero-crossing/ramp/安全拒绝/GUI 手动确认回归。

## Timing 与硬件

- `[AUTOMATED VERIFIED]` 2026-09-02 使用 Vivado 2020.1 build 2902540 对
  `synth_1/impl_1` 完成 clean Synthesis 与 routed Implementation；part 为
  `xc7z010clg400-1`。编译前 compile-order 检查及 synthesis elaboration 均
  证明 custom top/register/ramp/mixer/LPF 来自当前 `v0.94/rtl`。
- `[AUTOMATED VERIFIED]` fresh routed setup/hold：`WNS=0.142 ns`、
  `TNS=0`、0 个 setup failing endpoints；`WHS=0.053 ns`、`THS=0`、
  0 个 hold failing endpoints。正式报告写明
  `All user specified timing constraints are met`。
- `[CODE INSPECTED]` 全局最差 setup path 为
  `simple_lock_acquisition/servo_counter_q_reg[0]/C` 到
  `l1_lock_supervisor/abs_sum_snapshot_q_reg[0]/S`，data path
  7.295 ns/8 levels；最差 hold path 为 custom register-bank readback 到
  PS AXI `RDATA`，data path 0.440 ns/1 level。
- `[FAILED]` `check_timing` 仍有 52 个 no-clock findings、19 个
  unconstrained internal endpoints、17 个 no-input-delay ports 与 42 个
  no-output-delay ports。I/O 项已定位到 expansion/daisy GPIO 与 ADC/DAC
  source-synchronous/board interfaces；daisy latch 与 DNA 项不是新的 L1
  datapath，但未据此添加任何 exception。
- `[FAILED]` 唯一不可接受的 blocker 是 legacy
  `red_pitaya_daisy` 的 `pll_adc_clk <-> par_clk` 双向 CDC。Vivado
  `report_cdc -details` 报告共 73 条 critical findings：ADC→par 方向
  19 个 CDC-1 与 1 个 CDC-13；par→ADC 方向 49 个 CDC-1、3 个 CDC-4
  与 1 个 CDC-10。`report_methodology` 同时给出 TIMING-6/7 critical
  warnings，不能用正 WNS 或 blanket false path 视为已解释。
- Fresh reports：`v0.94/timing_for_codex/fresh_2026-09-02/`。
- `[IMPLEMENTED]` 2026-09-03 已按当前 Gate 对上述唯一 blocker 做编译期
  静态隔离；从代码结构推断 Daisy CDC 对象应从默认 build 消失，但尚无
  修改后 Vivado 报告，不能据此宣称 Timing Gate PASS。DNA 与板级 I/O 的
  `check_timing` finding 仍需在新报告中逐项审查。
- `[NOT VERIFIED]` Timing Gate PASS。因 Gate blocked，本轮未调用
  `write_bitstream`；clean reset 后当前 `impl_1/red_pitaya_top.bit` 不存在。
- `[NOT VERIFIED]` bitstream burned / board connected。
- `[NOT VERIFIED]` ARM VALIDATE、ARM ACTIVE、真实 ERROR crossing、
  PZT bumpless、P-only convergence 和 sustained lock。

## 唯一下一动作

用户在本地以默认 `ENABLE_DAISY=0` 对当前 candidate 重新执行 SystemVerilog
compile/elaboration、全部 RTL simulation、clean synthesis、implementation、
`report_cdc -details`、`check_timing`、DRC、methodology 和 routed setup/hold。
Daisy critical CDC 必须消失，其余 finding 逐项解释或修复；禁止用 blanket
false path 掩盖问题。完整 Timing Gate 通过前不生成或烧录 bitstream。
