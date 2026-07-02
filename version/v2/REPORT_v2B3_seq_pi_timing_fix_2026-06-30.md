# REPORT_v2B3_seq_pi_timing_fix_2026-06-30

## 0. 本文件作用

本报告记录 `v2B3 mode=1 sequential PI` 的一次 RTL 拆拍修复。

修复目标不是改变 PI 功能，而是解决用户手动 Vivado post-route timing 发现的关键时序问题：

```text
WNS = -1.931 ns
TNS ≈ -100 ns
Worst path:
integrator_next_q_reg -> integrator_next_q_reg

路径经过：
current_control_pre_w
freeze_integrator_w
integrator_candidate_w
integrator_accepted_w
```

大白话解释：旧版虽然已经把 PI 拆成 7 个状态，但“积分器下一拍该不该更新、更新多少、是否冻结、是否限幅”仍然在一个时钟周期里算完再反馈给积分器寄存器。125 MHz 下这条路太长，所以 Vivado timing 没过。

## 1. 本次修改范围

只修改了以下文件：

| 文件 | 修改内容 |
|---|---|
| `v0.94/rtl/pi_controller_seq.sv` | 将 sequential PI 从 7 状态继续拆成 15 状态，把长组合反馈路径拆拍寄存 |
| `v0.94/sim/tb_pi_controller_seq.sv` | 将固定输出延迟从 7 拍改为 15 拍，更新 PASS/FAIL 标识 |
| `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` | 将 sequential PI 集成检查的等待时间加长，适配 15 拍 latency |
| `version/v2/REPORT_v2B3_seq_pi_timing_fix_2026-06-30.md` | 记录本次修复、仿真结果和限制 |

## 2. 明确没有修改的内容

本次没有修改：

```text
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv 接口
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller.sv
XDC
xpr
```

本次没有读取或修改：

```text
v-weifang
version-weifang
guanfang-v0.94
```

## 3. RTL 修复内容

`pi_controller_seq.sv` 现在使用 15 个状态：

```text
S_IDLE
S_CAPTURE
S_LIMIT_PREP
S_P_MUL
S_P_SCALE_I_MUL
S_I_SCALE
S_FREEZE_PREP
S_FREEZE_DECIDE
S_I_CANDIDATE
S_I_CLAMP
S_I_COMMIT
S_SUM_PRE
S_SUM_FINAL
S_LIMIT_COMPARE
S_OUTPUT
```

这些中间结果已经拆拍或寄存：

| 中间量 | 新处理方式 |
|---|---|
| `limit_pos` / `limit_neg` | 在 `S_LIMIT_PREP` 写入 `limit_pos_q` / `limit_neg_q` |
| `p_scaled` | 在 `S_P_SCALE_I_MUL` 写入 `p_scaled_q` |
| `i_delta` | 在 `S_I_SCALE` 写入 `i_delta_q` |
| `control_pre_for_freeze` | 在 `S_FREEZE_PREP` 写入 `control_pre_for_freeze_q` |
| `freeze_integrator` | 在 `S_FREEZE_DECIDE` 写入 `freeze_integrator_q` |
| `integrator_candidate` | 在 `S_I_CANDIDATE` 写入 `integrator_candidate_q` |
| `integrator_accepted` | 在 `S_I_CLAMP` 写入 `integrator_accepted_q` |
| final sum | 拆成 `S_SUM_PRE` 和 `S_SUM_FINAL` |
| output limit | 拆成 `S_LIMIT_COMPARE` 和 `S_OUTPUT` |

## 4. 功能保持原则

本次保持以下行为不变：

- `pid_ce_i` 仍然只是 clock enable，不是新时钟；
- 所有逻辑仍然在 `clk_i` 域；
- `CONTROL_PATH_MODE=1` 仍然选择 sequential PI；
- `enable_i=0` 仍然立即清零输出和积分器；
- `hold_i=1` 仍然保持可见输出和积分器；
- `reset_integrator_i=1` 仍然清零 I 项，但保留 P + offset 输出语义；
- `polarity_i` 仍然反转控制方向；
- `output_limit_i` 仍然限制 OUT2 控制输出；
- OUT1 error 路径没有修改；
- OUT2 仍然只允许接示波器观察。

## 5. 仿真结果

### 5.1 `tb_pi_controller_seq`

命令：

```text
xvlog -sv .\rtl\pi_controller_seq.sv .\sim\tb_pi_controller_seq.sv
xelab tb_pi_controller_seq -s tb_pi_controller_seq_sim
xsim tb_pi_controller_seq_sim -runall
```

结果：

```text
SUMMARY tests=35 pass=35 fail=0
V2B3_PI_CONTROLLER_SEQ_SIM PASS
```

### 5.2 `tb_laser_lock_core_v2b1_shadow_pi_dc_error`

命令：

```text
xvlog -sv .\rtl\output_protect.sv .\rtl\mixer_core.sv .\rtl\lpf_core.sv .\rtl\pi_controller.sv .\rtl\pi_controller_seq.sv .\rtl\laser_lock_core.sv .\sim\tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv
xelab tb_laser_lock_core_v2b1_shadow_pi_dc_error -s tb_laser_lock_core_v2b1_shadow_pi_dc_error_sim
xsim tb_laser_lock_core_v2b1_shadow_pi_dc_error_sim -runall
```

结果：

```text
SUMMARY tests=27 pass=27 fail=0
V2B1_V2B3_CONTROL_PATH_SIM PASS
```

## 6. 本次没有执行的操作

本次没有运行：

```text
Vivado Synthesis
Vivado Implementation
Generate Bitstream
write_cfgmem
```

本次没有生成：

```text
.bit
.bin
```

因此，本次结果只能说明 RTL 仿真通过，不能说明 post-route timing 已通过。

## 7. 下一步建议

下一步由用户在 Vivado 中手动重新运行：

```text
Run Synthesis
Run Implementation
Open Implemented Design
Report Timing Summary
```

只有用户手动 Vivado timing 通过后，才允许继续讨论 bitstream/bin 和上板。

即使 timing 通过，OUT2 也仍然只能先接示波器，不能接激光器、不能接 `D2-125 Servo Output`、不能接 `Scan`、不能接任何真实反馈执行器。

## 8. 给 GPT 审查的问题

1. 15 状态拆拍是否足以切断 `integrator_next_q_reg -> integrator_next_q_reg` 的长反馈路径？
2. 是否还需要把 `S_FREEZE_PREP` 的 `p_scaled_q + integrator_q + offset_ext_q` 再拆成两拍？
3. 是否需要在 Vivado timing 仍未通过时继续拆 `S_LIMIT_COMPARE` 的比较逻辑？
4. 是否应把 `UPDATE_LATENCY_CYCLES=15` 写入 v2 SOP，提醒后续 testbench 不要按旧 7 拍检查？
