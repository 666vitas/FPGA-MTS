# V2 Custom Register Interface 与 OUT2 Scan/Lock 规划

## 当前边界

本文档只做规划，不代表已经实现。

```text
Codex 本次没有修改 RTL。
Codex 本次没有操作 Vivado。
Codex 本次没有综合、实现、生成 bit/bin，也没有烧录 Red Pitaya。
```

当前 `red_pitaya_top.sv` 顶层审查结果：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 3
LASER_LOCK_CONTROL_PATH_MODE = 1
OUT1 / DAC A = laser_error
OUT2 / DAC B = laser_control
```

`sys_bus_interconnect` 一共有 8 个区域。当前顶层使用情况如下：

```text
sys[0] red_pitaya_hk / housekeeper
sys[1] red_pitaya_scope
sys[2] red_pitaya_asg
sys[3] red_pitaya_pid
sys[4] red_pitaya_ams
sys[5] red_pitaya_daisy
sys[6] sys_bus_stub
sys[7] sys_bus_stub
```

规划判断：未来 `laser_lock_register_bank` 优先挂到 `sys[6]`。原因是
`sys[6]` 当前是 stub，不会挤占 scope、ASG、PID、AMS、housekeeper 或 daisy
这些已有官方功能。`sys[7]` 建议暂时保留为备用区域。

## 上位机模式边界

Official SCPI Mode：

```text
通过 redpitaya_scpi / 5000 端口工作。
可以控制官方 ASG OUT1/OUT2。
可以通过官方 ACQ 采集 IN1/IN2。
启动 redpitaya_scpi 可能加载官方 overlay，从而覆盖当前 custom bitstream。
```

Custom FPGA Mode：

```text
默认 custom bitstream 已经由用户手动加载。
OUT1 是 FPGA laser_error。
OUT2 是 FPGA laser_control。
官方 SCPI ASG 命令不是 Custom FPGA OUT1/OUT2 的控制路径。
未来要调 FPGA 内部参数，需要 register/debug/AXI 接口。
```

## 规划中的寄存器接口

未来 RTL 文件：

```text
v0.94/rtl/laser_lock_register_bank.sv
```

未来顶层接入位置：

```text
red_pitaya_top.sv 的 sys[6]
```

寄存器表规划：

```text
0x00 REG_MAGIC_VERSION
0x04 REG_CONTROL
0x08 REG_OUT2_MODE
0x0C REG_SCAN_AMP
0x10 REG_SCAN_OFFSET
0x14 REG_SCAN_STEP
0x18 REG_VLOCK_VALUE
0x1C REG_KP
0x20 REG_KI
0x24 REG_PID_OFFSET
0x28 REG_OUTPUT_LIMIT
0x2C REG_POLARITY
0x30 REG_STATUS
0x34 REG_ERROR_SAMPLE
0x38 REG_CONTROL_SAMPLE
0x3C REG_INTEGRATOR_LOW
0x40 REG_INTEGRATOR_HIGH
0x44 REG_ERROR_ABS_PEAK
0x48 REG_CONTROL_ABS_PEAK
```

DAC 14-bit signed counts 与电压的规划换算：

```text
+8191 约等于 +1 V
0     约等于  0 V
-8192 约等于 -1 V
0.05 V 约等于 410 counts
0.10 V 约等于 819 counts
0.20 V 约等于 1638 counts
```

## 规划中的 RTL 模块

未来文件：

```text
triangle_scan_gen.sv
scan_lock_control.sv
out2_output_mux.sv
debug_status_sampler.sv
```

模块职责：

```text
triangle_scan_gen:
  产生有幅度限制的三角波 scan，输出为 signed 14-bit DAC counts。

scan_lock_control:
  管理 OUT2 模式切换、Vlock 捕获、积分器复位和状态标志。

out2_output_mux:
  在 SAFE / SCAN / HOLD / P_LOCK / PI_LOCK 之间选择 OUT2 输出。

debug_status_sampler:
  采样 error、control、integrator、峰值、饱和、ADC clip 和 lock flag。
```

OUT2 模式规划：

```text
0 SAFE:   OUT2 = 0
1 SCAN:   OUT2 = triangle(scan_amp, scan_offset, scan_step)
2 HOLD:   OUT2 = captured_vlock
3 P_LOCK: OUT2 = captured_vlock + Kp * error
4 PI_LOCK: OUT2 = captured_vlock + Kp * error + Ki * integral(error)
5 RESCAN: reset integrator, clear lock flag, return to SCAN
```

关键含义：

```text
scan 阶段的 OUT2 是三角波。
lock 阶段的 OUT2 不是三角波。
lock 阶段的 OUT2 = Vlock + P/PI(error)。
```

## 未来上位机 Custom FPGA Control Panel

未来按钮规划，当前不实现：

```text
SAFE
Start Scan
Capture Vlock / Hold
Enable P Lock
Enable PI Lock
Reset Integrator
Reverse Polarity
Rescan
```

未来参数规划：

```text
scan_amp_v
scan_freq_hz
scan_offset_v
Kp
Ki
output_limit_v
pid_offset_v
polarity
```

未来状态显示规划：

```text
current_mode
error_sample
control_sample
vlock_value
sat_flag
adc_clip_flag
lock_flag
integrator_sample
```

上位机安全规则规划：

```text
output_limit_v > 0.2 V：必须明确确认。
output_limit_v > 0.5 V：禁止，或必须有非常强的二次确认/互锁。
没有 captured Vlock：禁止进入 P_LOCK 和 PI_LOCK。
没有先完成 P_LOCK：禁止直接进入 PI_LOCK。
如果 D2-125 Aux Servo Output 仍然接在激光器 Scan 上，不建议连接 RP OUT2 到 Scan/PZT。
```

## 阶段拆分

```text
v2B3-close:
  记录 timing clean，关闭 sequential PI 时序候选问题。

v2PZT-DOC:
  先完成寄存器表、安全规则和首次实验 SOP，再考虑 RTL 修改。

v2PZT-RTL-SAFE-SCAN-HOLD:
  增加 register bank、SAFE/SCAN/HOLD、三角波 scan、Vlock 捕获和状态采样。

v2PZT-RTL-PLOCK:
  在 captured Vlock 附近增加有限幅 P lock。

v2PZT-RTL-PILOCK:
  增加有限幅 PI lock，带可复位积分器和 anti-windup。

v2HOST-REG:
  上位机通过 register interface 增加 Custom FPGA Control Panel。
```

## 首次实验 SOP

第一轮必须先低风险、只看示波器：

```text
1. IN1 <- PD BPF/amp 信号，确认在 +/-1 V 内。
2. IN2 <- REF 信号，确认在 +/-1 V 内。
3. OUT1 -> 示波器 CH2：观察 FPGA error。
4. OUT2 -> 示波器 CH4：此时不要接激光器。
5. SAFE：确认 OUT2 = 0。
6. SCAN：确认 OUT2 上有小幅三角波。
7. 断开 D2-125 Aux Servo Output 到激光器 Scan 的连接。
8. 只有完成第 7 步后，才允许考虑 RP OUT2 -> laser power Scan/PZT。
9. 确认能看到光谱扫描。
10. 在接近过零点的位置 Capture Vlock。
11. HOLD。
12. 后续经过复核后，再进入 P_LOCK，然后才是 PI_LOCK。
```

停止条件：

```text
IN1 或 IN2 超过 +/-1 V。
OUT1 error 异常消失或异常饱和。
OUT2 超过规划的 output_limit。
OUT2 接近 +/-1 V。
OUT2 随机跳变或无解释地爬升。
光谱扫描方向不明确。
D2-125 Aux/Scan 仍然连接在激光器上。
操作者不确定当前到底是哪台设备在控制 laser Scan/PZT。
```
