# 当前主线审查说明

## 当前主线

当前主线以 `version/STATUS.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 为准：

```text
项目最终目标：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
当前主线：PZT 基础稳频最小闭环。
当前操作：SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE。
```

当前控制链路：

```text
GUI / CLI
-> Red Pitaya Linux /dev/mem
-> custom_register_bank
-> out2_lock_controller / ramp_generator
-> selected_out2
-> OUT2
```

当前 OUT2 的目标执行器是激光器专用 PZT / Scan 输入。SCAN 和 P_LOCK 使用同一个 PZT 接口；必须限制幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`，异常立即 SAFE。禁止 OUT2 接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止与任何其他设备输出端并联。

## 当前信号含义

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK
laser_control / pi_controller_seq = 内部候选或历史路径，不是当前 OUT2 最终输出
```

不要把历史 v2B3 sequential PI / Shadow PI 注释误判为当前 OUT2 主线。当前 OUT2 由 `selected_out2` 驱动。

## 当前主线文件

判断当前状态时优先读取：

- `README.md`
- `AI_REVIEW_README.md`
- `version/STATUS.md`
- `version/CURRENT_REVIEW_MANIFEST.md`
- `version/v3/V3REG0_SCOPE_TEST_CHECKLIST.md`
- `v0.94/rtl/red_pitaya_top.sv`
- `v0.94/rtl/custom_register_bank.sv`
- `v0.94/rtl/ramp_generator.sv`
- `v0.94/sim/tb_custom_register_bank_basic.sv`
- `v0.94/sim/tb_out2_lock_controller.sv`
- `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`

## 历史或非主线目录

不要把以下目录或历史材料作为当前 mainline 依据：

- `version/v1/`
- `version/v2/`
- `version/v3/claude审查/`
- `guanfang-v0.94/`
- any `weifang` or `version-weifang` related directory

这些目录可能包含历史实验、外部审查、官方基线或禁止读取材料。除非用户明确授权当前任务需要，否则不要读取、引用或修改它们。

## 审查规则

审查当前 main 分支时，先确认：

1. `red_pitaya_top.sv` 中 `custom_register_bank` 挂在 `sys[6]`。
2. `selected_out2` 进入 DAC B / OUT2。
3. OUT1 保持 `laser_error`。
4. SAFE / disabled / reset 时 OUT2 为 0。
5. SCAN 默认参数、HOLD、P_LOCK、PI_LOCK 是否只停留在当前允许阶段。
6. `laser_control` 和 `pi_controller_seq` 只作为内部候选或历史路径，不是当前 OUT2 最终输出。

审查结论必须用中文写明“已确认、未确认、禁止动作、下一步最小安全动作”。
