# Host App V2 Design

## 2026-07-08 v3REG-1 / v3REG-2 Custom FPGA Control 第一版

当前 Custom FPGA Control 已经从 v3REG-0 的 `SAFE/SCAN` 扩展到最短手动/半自动锁定路径：

```text
SAFE -> SCAN -> HOLD -> P_LOCK -> PI_LOCK
```

上位机链路仍然是：

```text
main_window.py
-> CustomFpgaRegisterWorker
-> CustomFpgaBackend
-> SSH
-> remote Python /dev/mem helper
-> custom_register_bank
-> out2_lock_controller / ramp_generator
-> selected_out2
```

新增 GUI 控件：

```text
HOLD button
P_LOCK button
PI_LOCK button
hold-v
Kp raw, Ki raw
polarity
lock-bias-v
lock-limit-counts
ERROR_MONITOR / CONTROL_MONITOR readback
```

新增寄存器：

```text
0x2C HOLD_VALUE
0x30 KP
0x34 POLARITY
0x38 LOCK_BIAS
0x3C LOCK_LIMIT
0x40 ERROR_MONITOR    read-only
0x44 CONTROL_MONITOR  read-only
0x48 KI
0x4C INTEGRAL_RESET
```

MODE 定义：

```text
0 SAFE
1 SCAN
2 HOLD
3 P_LOCK
4 PI_LOCK
```

`SAFE` 仍然是最高优先级：`ENABLE=0` 或 `MODE=0` 时 OUT2 必须为 0。`Probe Registers` 和 `Status` 只读；`SAFE/SCAN/HOLD/P_LOCK/PI_LOCK` 写寄存器前都必须通过 `MAGIC=0x4D545330` 检查。P_LOCK/PI_LOCK 的默认增益为 `Kp=0`、`Ki=0`，GUI 只提供人工逐步增加入口，不做自动闭环调参。

当前阶段边界：上位机已经能写 HOLD/P/PI 参数，但上板验证必须先 scope-only。不要把 OUT2 默认接到 PZT、激光电流、D2-125 Servo Output 或 Scan input。debug buffer、relock、自动找峰、执行器连接 SOP 仍是后续工作。

## 2026-07-05 GUI Custom FPGA Control v1

The PySide6 GUI now has a first Custom FPGA Control panel on the Custom FPGA Observe page. It supports:

```text
Probe Registers: read-only scan of candidate GP0 base addresses
Status: read-only MAGIC/VERSION/MODE/ENABLE/STATUS/OUT2 monitor
SAFE: require MAGIC=0x4D545330, then write ENABLE=0 and MODE=0
SCAN: require MAGIC=0x4D545330, then write scan parameters and enable MODE=1
```

The implementation path is:

```text
main_window.py
-> CustomFpgaRegisterWorker in connection_workers.py
-> CustomFpgaBackend in custom_fpga_backend.py
-> SSH
-> remote Python /dev/mem helper
-> custom_register_bank
```

This path does not start `redpitaya_scpi` and does not use Official SCPI ASG control for Custom FPGA OUT2. Probe and Status are read-only. SAFE and SCAN are blocked by the remote helper unless `MAGIC = 0x4D545330`. If `MAGIC = 0x00000000`, the GUI tells the user that no `custom_register_bank` was read and points to Program Device, old bit file, base address, or timing-pass bitstream reload as the likely fixes.

## 2026-07-04 v3REG-0 Custom FPGA register client

新增最小命令行脚本：

```text
software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py
```

用途是控制 Custom FPGA Mode 下的最小 SAFE/SCAN register bank。它不启动 `redpitaya_scpi`，不使用 official SCPI ASG，而是通过 SSH 在 Red Pitaya Linux 端运行临时 Python `/dev/mem` helper。

示例：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0.85 --amp-v 0.05 --freq-hz 50
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local status
```

只打印 SSH 命令、不执行：

```powershell
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local --print-command scan --offset-v 0.85 --amp-v 0.05 --freq-hz 50
```

默认寄存器物理基地址为 `0x40600000`，对应 GP0 base `0x40000000` + `sys[6]` 区域 `0x00600000`。烧录后必须先用 `status` 读取 `REG_MAGIC = 0x4D545330` 确认接口存在。

本脚本当前没有在真实 Red Pitaya 上执行验证；它是 v3REG-0 的最小 host-side 控制入口。第一阶段仍然只接 OUT2 到示波器，不接 Scan/PZT，不接激光器，不接 D2-125 Aux Output。

## 2026-07-01 Custom FPGA Lock Panel 规划边界

根据最新 Aux/PZT 数据，未来上位机 Custom FPGA Lock Panel 的职责应是“写模式和参数、记录状态”，而不是在 PC 上做高速实时 PID。

未来 FPGA 负责：

```text
实时 mixer
LPF
triangle scan
HOLD
P/PI control
OUT2 limit
polarity
reset_integrator
```

未来上位机负责：

```text
切换 SAFE / SCAN / HOLD / P_LOCK / PI_LOCK / RESCAN
写 scan_offset、scan_amp、Kp、Ki、polarity、output_limit
记录 error/control/Vlock
显示状态
后续 AI 识峰和调参
```

当前 V2 上位机仍然不能在 Custom FPGA Mode 下写 FPGA 内部参数，因为 RTL 侧还没有 `register_bank`。Official SCPI Mode 可以单独测试 OUT2 三角波和采集 IN1/IN2，但不能控制 custom FPGA OUT2；Custom FPGA Mode 后续必须通过 `register_bank` 切换 `SCAN / HOLD / P_LOCK / PI_LOCK`。

安全边界：

```text
Red Pitaya OUT2 不能和 D2-125 Aux Output 同时并联到 Scan/PZT。
Red Pitaya OUT2 不能和 D2-125 Servo Output 并联。
OUT2 初始必须先接示波器。
上位机不做高速实时 PID。
AI 不直接参与 125 MHz 实时控制。
```

## Scope

V2 is a stable Red Pitaya host app for experiment-room use. It does not modify FPGA RTL, does not generate bitstreams, and does not read internal FPGA `error_internal`.

V2 explicitly separates Official SCPI Mode from Custom FPGA Mode so the GUI does not imply that SCPI ASG control is valid while the custom FPGA bitstream owns OUT1/OUT2.

The app is not a generic signal-generator GUI. Its main purpose is to support the D2-125 replacement path:

```text
Red Pitaya IN1 + IN2
-> FPGA mixer_core
-> FPGA lpf_core
-> FPGA laser_error / OUT1
-> FPGA laser_control / OUT2
-> future low-gain laser lock
```

The canonical host-app development directory is:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

Markdown docs, SOPs, stage records, and small reports should stay under `docs/`. Do not keep generating large Word reports in the software root.

## Modules

- `connection_probe.py`: resolves hostnames, probes ping, and checks ports 22/80/5000.
- `ssh_client.py`: uses Paramiko to run Red Pitaya service-management commands.
- `scpi_client.py`: low-level TCP SCPI transport with CRLF command endings.
- `rp_scpi_client.py`: Red Pitaya SCPI business layer for outputs and acquisition.
- `acquisition_worker.py`: background `QThread` acquisition loop.
- `waveform_preview.py`: generated OUT1/OUT2 preview time axis and waveform helpers.
- `custom_fpga_workflow.py`: manual oscilloscope reading analysis for observe-mode safety decisions.
- `custom_fpga_backend.py`: Custom FPGA Control backend for SSH + `/dev/mem` Probe Registers, Status, SAFE, SCAN, HOLD, P_LOCK, and PI_LOCK. Debug buffers, automatic lock/relock, and actuator connection SOP remain future work.
- `main_window.py`: V2 GUI with connection management, output control, acquisition, and four-channel display.
- `data_logger.py`: CSV metadata and PNG export.
- `safety.py`: output safety validation and best-effort exit shutdown hooks.

## Two-Layer Connection

Layer 1: SSH / network management.

- Resolve host to IP.
- Probe ping.
- Probe SSH port 22.
- Probe Web port 80.
- Probe SCPI port 5000.
- Start SCPI server over SSH when needed.

Layer 2: SCPI control.

- Connect to selected host/IP on port 5000.
- Run `*IDN?`.
- Configure OUT1 / OUT2.
- Acquire IN1 / IN2 with `ACQ:*` commands.

This two-layer flow applies to Official SCPI Mode. In Custom FPGA Mode, probing is still useful, but starting `redpitaya_scpi` is intentionally avoided because it may load the official overlay.

## Mode Boundary

The GUI is organized into four mode pages:

- Hardware Bring-up: Official SCPI hardware checks and safe OUT2 scan.
- Custom FPGA Observe: manual scope readings for IN1/IN2/OUT1/OUT2 experiment wiring.
- Lock Workflow: D2-125 replacement checklist and future lock/relock planning.
- Data Log: Markdown experiment log export.

Official SCPI Mode:

- May start `redpitaya_scpi`.
- May connect to port 5000 and run `*IDN?`.
- Controls official ASG OUT1/OUT2.
- Acquires IN1/IN2 through official SCPI ACQ.
- May overwrite the currently loaded custom FPGA bitstream.

Custom FPGA Mode:

- Does not start the SCPI overlay.
- Treats the current custom bitstream as the active hardware route.
- Current RTL has `USE_LASER_LOCK_CORE = 1`.
- OUT1 / DAC A = `laser_error`.
- OUT2 / DAC B = `selected_out2`.
- Official `asg_dat[0]` / `asg_dat[1]` do not directly drive OUT1/OUT2.
- The host app can now read the custom register bank and write SAFE/SCAN/HOLD/P_LOCK/PI_LOCK controls through SSH `/dev/mem`.
- The host app still does not implement debug-buffer reads, automatic lock/relock, or a safe actuator connection workflow.

## Output Control

Each output supports:

- enable
- waveform type: sine, square, triangle, sawtooth
- frequency_hz
- amplitude_v
- offset_v
- phase_deg

Safety rules:

- `amplitude_v >= 0`
- `abs(offset_v) + amplitude_v <= output_range_v`
- default `output_range_v = 1.0 V`
- default `amplitude_v = 0.05 V`

Shutdown sequence:

```text
SOUR1:VOLT 0
SOUR2:VOLT 0
OUTPUT1:STATE OFF
OUTPUT2:STATE OFF
GEN:STOP
```

## Acquisition

The acquisition worker runs:

```text
ACQ:RST
ACQ:DATA:FORMAT ASCII
ACQ:DATA:UNITS VOLTS
ACQ:DEC <N>
ACQ:TRIG:DLY 0
ACQ:START
ACQ:TRIG NOW
poll ACQ:TRIG:FILL?
ACQ:SOUR1:DATA?
ACQ:SOUR2:DATA?
ACQ:STOP
```

Blocking SCPI reads occur in `AcquisitionWorker`, not the GUI thread. Numpy arrays are emitted to the main thread with Qt signals, and pyqtgraph is updated only in the main thread.

## Four-Channel Display

- CH1: IN1 / ADC measured from `ACQ:SOUR1:DATA?`.
- CH2: IN2 / ADC measured from `ACQ:SOUR2:DATA?`.
- CH3: OUT1 generated preview, not measured.
- CH4: OUT2 generated preview, not measured.

OUT1 and OUT2 are output ports. The host app cannot directly measure their actual voltage unless the user physically loops them back into IN1 or IN2.

CH3/CH4 use an independent generated preview time axis. They do not reuse the IN1/IN2 acquisition time axis. A 50 Hz triangle wave has a 20 ms period; the preview defaults to two cycles so it shows at least 40 ms. Real OUT2 must still be verified with an oscilloscope, or with a safe physical loopback into IN1/IN2 while keeping the input below ±1 V.

In Custom FPGA Mode, CH3/CH4 labels switch to remind the user that actual OUT1/OUT2 are `laser_error` and `laser_control`. The plotted traces remain previews or placeholders, not measured custom FPGA outputs.

## FPGA Internal Signals

`error_internal`, mixer output, LPF output, HOLD/P_LOCK/PI_LOCK, PID tuning, and high-rate snapshots still require later FPGA RTL support such as debug buffers or expanded AXI registers. V2 now implements only the first real Custom FPGA register control path for status/probe/safe/scan; it does not fake unavailable internal FPGA signals.
