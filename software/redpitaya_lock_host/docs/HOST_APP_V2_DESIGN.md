# Host App V2 Design

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
- `custom_fpga_backend.py`: future Custom FPGA interface stub; every hardware access raises `NotImplementedError`.
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
- OUT2 / DAC B = `laser_control`.
- Official `asg_dat[0]` / `asg_dat[1]` do not directly drive OUT1/OUT2.
- The host app does not currently change custom FPGA parameters.

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

`error_internal`, mixer output, LPF output, and writable FPGA parameters require FPGA RTL support such as `register_bank`, `debug_buffer`, or AXI registers. V2 does not implement that path and this task does not add a fake Custom FPGA control panel.
