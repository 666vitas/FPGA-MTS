# FPGA Mode Boundary

## 2026-07-05 OUT2 Path Boundary

The current v3REG-0 custom RTL routes physical OUT2 to `selected_out2`, not to `laser_control`.

Two GUI paths must stay separate:

```text
A. Official SCPI Mode -> redpitaya_scpi -> official ASG -> OUT1/OUT2
   Use only with the official overlay/ASG test path.

B. Custom FPGA Mode -> SSH + /dev/mem -> custom_register_bank
   -> ramp_generator -> selected_out2 -> physical OUT2
   Use Custom FPGA Observe -> Probe Registers -> Status -> SAFE/SCAN.
```

When `USE_LASER_LOCK_CORE=1` custom RTL is loaded, official SCPI ASG OUT2 commands may succeed but do not drive physical OUT2.

## 2026-07-01 Aux/PZT 边界补充

最新 D2-125 Aux Output / Scan-PZT 数据说明，Aux Output 在 Ramp 状态约为：

```text
0.81 V DC 偏置 + 0.063 到 0.117 Vpp 小三角波
频率约 52.7 Hz
```

在 Lock 状态约为：

```text
0.813 V DC 保持 + 约 16.9 mVpp 小幅扰动
```

这说明后续 Custom FPGA Mode 如果要替代 D2-125 Aux Output，OUT2 不能只是从 0 V 开始的普通三角波，而应支持：

```text
SCAN: OUT2 = scan_offset + triangle
HOLD: OUT2 = captured_vlock
P_LOCK: OUT2 = captured_vlock + Kp * error
PI_LOCK: OUT2 = captured_vlock + Kp * error + Ki * integral(error)
```

当前边界仍然不变：

```text
当前 FPGA 还没有 OUT2 scan/lock mode selector。
当前 FPGA 还没有 register_bank。
当前上位机不能在 Custom FPGA Mode 下写 FPGA 内部参数。
当前不能用 Official SCPI 的 SOUR2:FUNC TRIANGLE 控制 custom FPGA OUT2。
当前不能声称已经实现 PZT 锁定。
```

安全规则：

```text
Red Pitaya OUT2 不能和 D2-125 Aux Output 同时并联到 Scan/PZT。
Red Pitaya OUT2 不能和 D2-125 Servo Output 并联。
OUT2 初始必须先接示波器。
OUT2 输出必须限制在 +/-1 V 内。
```

## Files Reviewed

- `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv`
- `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv`
- `E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv`
- `E:\new\fpga_lock\version\STATUS.md` was checked and was not present.

## Current Custom FPGA Routing

`red_pitaya_top.sv` sets:

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;
localparam int   LASER_LOCK_CONTROL_PATH_MODE = 1;
```

With `USE_LASER_LOCK_CORE = 1` in the current v3REG-0 routing:

- OUT1 / DAC A = `laser_error`
- OUT2 / DAC B = `selected_out2` from `custom_register_bank` SAFE/SCAN and `ramp_generator`
- official `asg_dat[0]` and `asg_dat[1]` no longer directly drive OUT1/OUT2

The custom FPGA signal chain is:

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> OUT1 laser_error
SSH /dev/mem -> custom_register_bank -> ramp_generator -> selected_out2 -> OUT2
```

## Hardware Safety Boundary

In the current custom FPGA mode, OUT2 is still oscilloscope-only.

Do not connect OUT2 to:

- laser scan/PZT
- D2-125
- any real actuator path

OUT2 should be observed on an oscilloscope only until physical voltage range, polarity, bandwidth, timing, and lock/scan switching are reviewed.

## Official SCPI Mode

Official SCPI Mode is different. It starts or connects to `redpitaya_scpi`, then controls the official ASG outputs through SCPI. This is useful for oscilloscope and signal-generator bring-up, but it may not preserve the custom FPGA bitstream.

Starting `redpitaya_scpi` may execute the official v0.94 overlay path and may overwrite the currently loaded custom FPGA bitstream.

If a custom FPGA bitstream with `USE_LASER_LOCK_CORE=1` is loaded, SCPI OUT2 commands can still succeed at the protocol level but will not drive physical OUT2, because physical OUT2 is routed to `selected_out2`.

## Custom FPGA Mode

Custom FPGA Mode means the current custom bitstream is treated as loaded and should not be disturbed by starting official SCPI overlay services.

In this mode:

- OUT1 is the FPGA `laser_error`, not SCPI ASG OUT1.
- OUT2 is `selected_out2` from register-controlled SAFE/SCAN, not SCPI ASG OUT2.
- The V2 host app Custom FPGA Control writes the SAFE/SCAN register bank through SSH `/dev/mem`.
- Probe Registers and Status are read-only. SAFE and SCAN require `MAGIC = 0x4D545330` before writing.
- Custom FPGA Observe Mode only records manual oscilloscope readings and safety judgments. It does not read internal FPGA mixer/LPF/error snapshots.
- Lock Workflow Mode is a process checklist for the D2-125 replacement path, not an implemented lock controller.

## Future Integration

If the project needs official SCPI output control and the custom FPGA error path at the same time, the RTL/top-level integration must be redesigned. One likely direction is to preserve required official scope/acquisition plumbing while exposing custom FPGA control/status through an explicit register/debug interface.
