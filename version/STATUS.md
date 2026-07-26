Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: STATUS
Last-Updated: 2026-07-26
Supersedes: previous LOCK-MVP-L0 status
Superseded-By: NONE

# FPGA-MTS 当前状态

## 当前事实

- Repository：`666vitas/FPGA-MTS`
- Local branch/HEAD at task start：`main@adf52ac`
- 本轮工作区：有未提交的 L1 本地修改；未 commit、未 push、未创建 PR。
- `MAGIC=0x4D545330`、`VERSION=0x00030200` 与旧 `0x00..0xE0` CSR 地址保持不变。
- 新 L1 capability CSR 为 `0xE4 = 0x4C310001`；Host 同时检查 VERSION 与 capability。

## 本轮实现

- `[IMPLEMENTED]` `lock_error = error_i - active_error_setpoint` 的 H/N 连续样本 crossing detector。
- `[IMPLEMENTED]` `ARM_VALIDATE=8` 与 `ARM_ACTIVE=1` 共用 detector；VALIDATE 保持 SCAN，ACTIVE 捕获实际 `selected_out2`。
- `[IMPLEMENTED]` 状态：SAFE、SCAN、VALIDATING、ARMED、ACQUIRING、P_LOCKED、FAILED、FAULT。
- `[IMPLEMENTED]` FPGA `kp_effective` soft-start、servo update divider、OUT2 slew limit、均值/绝对均值 supervisor、timeout/divergence/saturation SAFE。
- `[IMPLEMENTED]` 正常 GUI 增加 `ARM VALIDATE`，隐藏正常视图中的 `Capture Bias`/`APPLY P`；legacy 源码保留作 engineer diagnostic。

## 自动验证

- `[RTL SIMULATED]` `tb_realtime_error_crossing_detector`: 13/13。
- `[RTL SIMULATED]` `tb_simple_lock_acquisition`: 28/28。
- `[RTL SIMULATED]` `tb_l1_error_crossing_plant`: 8/8。
- `[RTL SIMULATED]` `tb_out2_lock_controller`: 38/38。
- `[RTL SIMULATED]` `tb_custom_register_bank_basic` D1/legacy: 166/166。
- `[RTL SIMULATED]` `tb_ramp_generator`: 25/25。
- `[CODE INSPECTED]` `red_pitaya_top` 与全部本地 RTL 重新 `xvlog` 通过；未执行顶层 implementation。
- `[UNIT TESTED]` Host 分文件共 148 passed：backend 99、lock service 6、workflow 3、operator diagnostics 37、waveform 3。

## Timing 与硬件

- 用户报告的旧基线受约束 timing 已通过；该结果只属于修改前基线。
- `[NOT VERIFIED]` 本轮 RTL 的 synthesis/implementation、WNS/TNS/WHS、high-fanout、unconstrained path。
- `[NOT VERIFIED]` bitstream generated / burned / board connected。
- `[NOT VERIFIED]` 真实 ERROR crossing、PZT bumpless、P-only convergence 和 sustained lock。

## 唯一下一动作

用户 Reset `synth_1/impl_1`，重新运行 Synthesis 和 Implementation，并提供 timing summary、最差 setup/hold 路径、high-fanout 与 unconstrained path 报告。timing 通过前不要生成或烧录正式 bitstream。
