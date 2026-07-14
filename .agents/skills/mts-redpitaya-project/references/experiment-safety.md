# 实验安全

## 硬件边界

- 目标平台：Red Pitaya STEMlab 125-14 / Zynq-7010。
- `IN1` 接 PD，`IN2` 接 4.6 MHz REF；两者绝对输入保持在 `+/-1 V`。
- `OUT1` 是 `laser_error` 观察输出。
- `OUT2` 是 `selected_out2`，只能接激光器专用 PZT / Scan 输入。
- 禁止 OUT2 接激光电流调制、`D2-125 Servo Output`、`D2-125 Aux Output`，禁止两个设备输出端并联。
- `EOM` 继续由外部信号源驱动。连接真实执行器前必须先用示波器确认幅度、偏置、频率和限幅。

## 最小人工流程

1. 先确认通信正常、`MAGIC`/`VERSION` 匹配、输入未越界，OUT2 处于 SAFE。
2. OUT2 先只接示波器；确认安全范围后，才允许接专用 PZT/Scan 输入。
3. 执行 `SAFE -> SCAN -> Capture`，观察 CH1/CH3/CH4 和 OUT2 限幅。
4. 在当前 capture 中人工选择 CH1 目标特征，确认附近 CH3 error zero crossing。
5. `Confirm Lock Point -> LOCK HERE`，首次保持 `Kp=0`，由 FPGA 同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS`。
6. 只能人工按 `Kp=0/4/8/16/32` 小步 `APPLY P`，人工判断 `polarity`。
7. 任何异常立刻停止并 SAFE；没有用户反馈时结论只能是等待验证。

## PASS / FAIL / SAFE

PASS 必须由当前实验数据支持：身份正确、输入安全、OUT2 在配置范围内、无持续 saturation/异常跳变、波形真实可用、P-only 方向和小增益行为符合预期。

FAIL 条件包括通信失败、`MAGIC/VERSION` 错误、输入越界、OUT2 越界或接近 limit、saturation、振荡、异常跳变、错误 polarity、无真实 capture points、锁点未经人工确认或准备接入禁止端口。

FAIL 时停止操作并执行接口规定的 SAFE 顺序，最小顺序通常为 `KP=0 -> ENABLE=0 -> MODE=0`；不得自动提高 Kp、切 polarity、重锁或继续接线。
