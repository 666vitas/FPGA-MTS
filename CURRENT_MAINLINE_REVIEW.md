# Current Mainline Review

## Current Mainline

当前主线 = v3REG-0 register-controlled OUT2 SAFE/SCAN。

```text
上位机
-> Red Pitaya Linux /dev/mem
-> custom_register_bank
-> ramp_generator
-> OUT2
```

当前阶段只验证 OUT2 示波器三角波，不验证锁定，不接 Scan/PZT，不接激光器。

## Current Signal Meaning

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2 = custom_register_bank + ramp_generator SAFE/SCAN
laser_control / pi_controller_seq = 后续候选，不是当前 OUT2 输出
```

不要把历史 v2B3 sequential PI / Shadow PI 注释误判为当前 OUT2 主线。当前 OUT2 由 `selected_out2` 驱动，`selected_out2` 的 v3REG-0 来源是 `custom_register_bank` 和 `ramp_generator`。

## Current Mainline Files

优先读取以下文件判断当前状态：

- `README.md`
- `GPT_README.md`
- `version/STATUS.md`
- `version/v3/V3REG0_HOST_CONTROLLED_SCAN_PLAN.md`
- `version/v3/V3REG0_SCOPE_TEST_CHECKLIST.md`
- `v0.94/rtl/red_pitaya_top.sv`
- `v0.94/rtl/custom_register_bank.sv`
- `v0.94/rtl/ramp_generator.sv`
- `v0.94/sim/tb_custom_register_bank_basic.sv`
- `v0.94/sim/tb_ramp_generator.sv`
- `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`

## Historical Or Non-Mainline Areas To Avoid

不要把以下目录或历史材料作为当前 mainline 依据：

- `version/v1/`
- `version/v2/`
- `version/v3/claude审查/`
- `guanfang-v0.94/`
- any `weifang` or `version-weifang` related directory

这些目录可能包含历史实验、外部审查、官方基线或禁止读取材料。除非用户明确授权当前任务需要，否则不要读取、引用或修改它们。

## Review Rule

审查当前 main 分支时，先确认：

1. `red_pitaya_top.sv` 中 `custom_register_bank` 挂在 `sys[6]`。
2. `selected_out2` 进入 DAC B / OUT2。
3. OUT1 保持 `laser_error`。
4. SAFE / disabled / reset 时 OUT2 为 0。
5. SCAN 默认约为 `0.85 V +/-0.05 V`、约 `50 Hz`。
6. `laser_control` 和 `pi_controller_seq` 只作为后续候选存在，不是当前 OUT2 输出。

