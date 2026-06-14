# REPORT_mts_error_chain_v1_plan

## 0. 本报告作用

本报告记录本次任务：根据最新实验策略，重新整理第一阶段 `mts_error_chain_v1` 实现计划。

本次只修改文档，不写 Verilog，不修改官方工程。

## 1. 最新策略摘要

最新策略如下：

- 第一版 `REF` 不由 FPGA 生成；
- 第一版 `REF` 从外部信号发生器输入 Red Pitaya `IN2`；
- 外部信号发生器继续驱动 EOM，约 `4.6 MHz`、`8.93 Vpp`；
- Red Pitaya 第一阶段不驱动 EOM；
- 输入 `IN2` 的 `REF` 必须衰减到 Red Pitaya 安全范围内，例如 ±1 V 内；
- 不允许把原模拟 mixer 的 `6.32 Vpp` 参考信号直接接入 `IN2`；
- `PD` 输入 Red Pitaya `IN1`；
- FPGA 内部使用 `pd_i = adc_dat[0]`，`ref_i = adc_dat[1]`；
- `OUT1` 先接示波器，确认安全后再接 `D2-125 error input`。

## 2. 本次修改的文件

| 文件 | 修改内容 |
|---|---|
| `docs\integration\IMPLEMENTATION_PLAN_mts_error_chain_v1.md` | 重写为最新外部 REF 输入策略和 v1a 到 v1g 测试驱动计划 |
| `docs\reports\REPORT_mts_error_chain_v1_plan.md` | 更新本报告，记录本次策略调整 |

## 3. 新版本规划

第一阶段现在按以下测试驱动版本推进：

| 版本 | 功能 | 目的 |
|---|---|---|
| `v1a_pd_passthrough` | `error_o = pd_i`，`control_o = 0` | 验证 `IN1 -> OUT1` 通路 |
| `v1b_ref_passthrough` | `error_o = ref_i`，`control_o = 0` | 验证 `IN2` 可以接收 4.6 MHz `REF` |
| `v1c_mixer_only` | `pd_i * ref_i -> 缩放 -> error_o` | 验证数字 mixer |
| `v1d_mixer_lpf` | `pd_i * ref_i -> lowpass_filter -> error_o` | 得到基础数字解调输出 |
| `v1e_real_pd_ref` | 真实 `PD` + 外部 `REF -> mixer + LPF -> error_o` | 第一次看到真实实验 error-like signal |
| `v1f_bpf_enable` | `PD -> BPF around 4.6 MHz -> mixer -> LPF -> error_o` | 替代模拟 `1.8 MHz high-pass + 10 MHz low-pass` 链路 |
| `v1g_error_to_D2_125` | `OUT1 -> D2-125 error input` | 用 FPGA error signal 替代模拟 mixer 输出 |

## 4. 每个版本必须包含的内容

每个版本必须包含：

- testbench；
- REPORT；
- 仿真成功标准；
- 上板测试方法；
- 失败排查表；
- 安全说明。

任何版本不能直接接 `D2-125`，除非前一版已经用示波器确认 `OUT1` 安全。

任何版本不能接激光器反馈。

## 5. 第一阶段明确不做

第一阶段明确不做：

- FPGA PID；
- sweep；
- AI；
- FPGA 生成 `REF`；
- FPGA 驱动 EOM；
- lock/relock FSM；
- PS/AXI 参数控制；
- 激光器反馈闭环。

## 6. 本次没有做的事

| 项目 | 状态 |
|---|---|
| 写 Verilog/SystemVerilog | 没有写 |
| 修改官方 `rtl` | 没有修改 |
| 修改官方 `project` | 没有修改 |
| 修改官方 `sim` | 没有修改 |
| 修改官方 `ip` | 没有修改 |
| 修改官方 `sdc` | 没有修改 |
| 修改 `rtl\red_pitaya_top.sv` | 没有修改 |
| 修改 Vivado 工程 | 没有修改 |
| 复制官方 top 到 `vendor_shell` | 没有复制 |
| 生成 integration patch | 没有生成 |

## 7. 风险提醒

| 风险 | 处理方式 |
|---|---|
| `IN2` 输入过大 | `REF` 必须先衰减到安全范围，例如 ±1 V 内 |
| 把 `6.32 Vpp` mixer reference 直接接入 `IN2` | 明确禁止 |
| EOM 驱动误接 Red Pitaya | EOM 驱动仍走原实验链路，不进 Red Pitaya |
| `OUT1` 输出未知 | 先接示波器，不接 `D2-125` |
| 激光器反馈风险 | 第一阶段不接激光器反馈 |
| 官方工程被污染 | 不修改官方 `red_pitaya_top.sv` 和 Vivado 工程 |

## 8. 下一步建议

下一步建议先审查：

```text
docs\integration\IMPLEMENTATION_PLAN_mts_error_chain_v1.md
```

如果用户确认计划，下一步进入：

```text
v1a_pd_passthrough
```

实现时仍然必须遵守：

- 只在 `redpitaya_laser_lock_project` 下工作；
- 每个版本有 testbench；
- 每个版本有 REPORT；
- 不修改官方工程；
- 不接激光器反馈。
