Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: STATUS
Last-Updated: 2026-07-26
Supersedes: previous LOCK-MVP-L0 status
Superseded-By: NONE

# FPGA-MTS 当前状态

## 当前事实

- Repository：`666vitas/FPGA-MTS`
- Local branch/HEAD at task start：`main@56e49fb`；task start working tree clean。
- 本轮工作区：有 4 个预期未提交文件；未 commit、未 push、未创建 PR。
- `MAGIC=0x4D545330`、`VERSION=0x00030200` 与旧 `0x00..0xE0` CSR 地址保持不变。
- 新 L1 capability CSR 为 `0xE4 = 0x4C310001`；Host 同时检查 VERSION 与 capability。

## 本轮实现

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

## 自动验证

- `[RTL SIMULATED]` 全部 20 个 `v0.94/sim/tb_*.sv` 重新
  compile/elaborate/simulate 通过；有计数器的 15 个 testbench 合计
  642/642，另 5 个 legacy testbench 退出码 0。
- `[RTL SIMULATED]` 关键项：OUT2 controller 54/54、SIMPLE 32/32、
  plant 8/8、Kp ramp 6/6、supervisor 5/5、crossing 13/13、
  D1 register bank 166/166、deterministic 50/50、ramp 25/25。
- `[UNIT TESTED]` `python -m pytest -q tests`：148 passed。

## Timing 与硬件

- `[AUTOMATED VERIFIED]` 2026-07-26 clean Synthesis/route_design 完成；
  project source 指向当前 `v0.94/rtl/custom_register_bank.sv`。
- `[AUTOMATED VERIFIED]` routed setup/hold：`WNS=0.142 ns`、
  `TNS=0`、0 个 setup failing endpoints；`WHS=0.053 ns`、`THS=0`、
  0 个 hold failing endpoints。Vivado 报告
  `All user specified timing constraints are met`。
- `[CODE INSPECTED]` 旧 `s5_lock_limit -> control_o` 路径族不在新的
  top-10 setup paths。新全局最差 setup path 为
  `simple_lock_acquisition/servo_counter_q_reg[0]/C` 到
  `l1_lock_supervisor/abs_sum_snapshot_q_reg[0]/S`，slack 0.142 ns，
  data path 7.295 ns/8 levels。
- `[NOT VERIFIED]` 完整 Timing Gate 尚未满足：`check_timing` 仍报告
  19 个 unconstrained internal endpoints、17 个 no-input-delay ports、
  42 个 no-output-delay ports，以及 daisy/DNA no-clock 项。本轮禁止修改
  XDC，未添加 false path、multicycle、降频或 blanket CDC exception。
- `[NOT VERIFIED]` bitstream generated / burned / board connected。
- `[NOT VERIFIED]` ARM VALIDATE、ARM ACTIVE、真实 ERROR crossing、
  PZT bumpless、P-only convergence 和 sustained lock。

## 唯一下一动作

在不生成 bitstream、不连接板卡的前提下，单独授权并审查现有
XDC/官方 I/O 的 `check_timing` 项，明确每个 no-clock、unconstrained
internal endpoint 和未约束 I/O 的真实接口语义；在证据充分前不得用
blanket false path 清零报告。完整 Timing Gate 通过前不要生成或烧录
正式 bitstream。
