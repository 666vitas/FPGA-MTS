# Red Pitaya Laser Lock Host V2

Red Pitaya Laser Lock Host V2 is the upper-computer software for the Red Pitaya laser frequency locking project.

Its core goal is to support the step-by-step replacement of the D2-125 workflow with Red Pitaya FPGA logic and host-side experiment management: scan, error-signal observation, control-output observation, lock readiness checks, and later lock/relock workflows.

## Canonical Development Directory

All Red Pitaya host-app development is now done in:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

Do not use the old standalone development directory. The canonical host-app path is the `software/redpitaya_lock_host` directory shown above.

Markdown documentation, SOPs, and stage notes belong in `docs/`. Stage records are kept in `docs/DEVELOPMENT_LOG.md`. Usage instructions are kept in this README and `docs/USAGE.md`. SCPI notes are kept in `docs/SCPI_MODE_NOTES.md`. If a temporary stage report is needed, place it under `docs/reports/`, not in the software root.

## Directory Structure

```text
redpitaya_lock_host/
├── .venv/                  # Local Python virtual environment, not tracked by Git
├── docs/                   # Software documentation
├── redpitaya_lock_host/    # Python source code
├── tests/                  # Host-app tests
├── config.yaml             # Default configuration
├── requirements.txt        # Python dependencies
├── run.bat                 # Normal-mode startup script
├── run_mock.bat            # Mock-mode startup script
└── README.md
```

## Relationship To The FPGA Project

This host application is located at:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

The FPGA / RTL / Vivado project is located at:

```text
E:\new\fpga_lock\v94\v0.94
```

This documentation update does not modify the FPGA project, RTL files, Vivado project files, or bitstreams.

## Python Environment

Recommended:

```text
Official Python 3.11 + project-local .venv
```

Not recommended:

```text
Anaconda base environment
```

Anaconda base may contain Qt / PySide6 / DLL conflicts, which can cause:

```text
ImportError: DLL load failed while importing QtWidgets
```

## First-Time Installation

Use PowerShell:

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host

py -3.11 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

If the `py` command does not exist, the official Python Launcher is not installed. Install official Python 3.11, then reopen PowerShell.

## Environment Tests

```powershell
.\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
.\.venv\Scripts\python.exe -c "import yaml; print('PyYAML OK')"
```

## Startup

Mock mode:

```powershell
.\run_mock.bat
```

Real connection mode:

```powershell
.\run.bat
```

Backup startup commands:

```powershell
.\.venv\Scripts\python.exe -m redpitaya_lock_host.main --mock
.\.venv\Scripts\python.exe -m redpitaya_lock_host.main
```

In PowerShell, do not type:

```powershell
run.bat
```

Use:

```powershell
.\run.bat
```

## Red Pitaya Connection Flow

1. Probe.
2. If SCPI is False, click Start SCPI Server.
3. Probe again.
4. When SCPI is True, click Connect SCPI.
5. Connect OUT2 to the oscilloscope.
6. Set OUT2 to `triangle / 50 Hz / 0.05 V / offset 0`.
7. Apply.
8. After confirming the waveform on the oscilloscope, consider connecting the laser scan/PZT input.

## GUI Custom FPGA Control

Use this only after the timing-pass custom bitstream has been programmed into the Red Pitaya FPGA. This path uses SSH plus `/dev/mem`; it does not start `redpitaya_scpi` and does not use the Official SCPI ASG to control Custom FPGA OUT2.

1. Start the GUI with `.\run.bat`.
2. Select `Custom FPGA Mode` or open the `Custom FPGA Observe` page.
3. Keep `base address` at `0x40600000` unless the register probe shows a different matching base.
4. Click `Probe Registers`.
5. Click `Status` and confirm `MAGIC = 0x4D545330`.
6. Click `SAFE`.
7. With OUT2 connected only to the oscilloscope, use the defaults `offset-v=0.0000`, `amp-v=0.0500`, `freq-hz=10.000`, `step-counts=1`, `limit-counts=8191`, then click `SCAN`.

If `MAGIC = 0x00000000`, the GUI treats SAFE/SCAN as blocked. It means no `custom_register_bank` was read; possible causes are no Program Device, an old bit file, a wrong base address, or needing to reload the timing-pass bitstream. Run `Probe Registers` again after fixing the bitstream/base address.

### v3REG-1 / v3REG-2 手动锁定最短路径

当前 Custom FPGA Control 已经支持 `SAFE`、`SCAN`、`HOLD`、`P_LOCK` 和 `PI_LOCK`。这些按钮走同一条自定义寄存器路径：

```text
GUI -> SSH -> /dev/mem -> custom_register_bank -> out2_lock_controller -> selected_out2 -> DAC B / OUT2
```

推荐上板顺序：

```text
Custom FPGA Mode
-> Probe Registers
-> Status
-> SAFE
-> SCAN
-> HOLD
-> P_LOCK, with Kp=0 first
-> PI_LOCK, with Kp=0 and Ki=0 first
```

`HOLD` 输出固定电压，使用 `hold-v` 设置。`P_LOCK` 使用 `Kp raw`、`polarity`、`lock-bias-v` 和 `lock-limit-counts`。`PI_LOCK` 在 P_LOCK 基础上增加 `Ki raw`。`Kp raw` 和 `Ki raw` 约定 `256 = 1.0x`，GUI 默认值为 0，必须人工逐步增加。

安全边界：HOLD/P_LOCK/PI_LOCK 第一阶段仍然只允许 OUT2 接示波器。不要把 OUT2 默认接到 PZT、激光电流、D2-125 Servo Output 或 Scan input。只有在 scope-only 验证了幅度、偏置、极性、限幅和 SAFE 关闭行为后，才允许单独制定执行器连接 SOP。

## GUI Modes

- Hardware Bring-up / SCPI Mode: Probe, Start SCPI Server, Connect SCPI, official ASG OUT2 Safe Scan, IN1/IN2 acquisition, and Stop/Disable outputs. This path is only for official overlay/ASG testing.
- Custom FPGA Observe Mode: Custom FPGA Control for Probe Registers, Status, SAFE, SCAN, HOLD, P_LOCK, and PI_LOCK through SSH `/dev/mem`, plus manual oscilloscope readings for real wiring: IN1 PD/MTS, IN2 REF, OUT1 laser_error, and OUT2 selected_out2. OUT2 is scope-only for HOLD/P_LOCK/PI_LOCK until a separate actuator connection SOP is written.
- Lock Workflow Mode: step-by-step D2-125 replacement workflow management. It does not pretend to lock automatically.
- Data & Experiment Log: exports Markdown experiment logs to `docs/experiment_logs/`.

Debug-buffer reads, higher-level lock FSM control, relock, and actuator connection SOPs remain future work. The first FPGA-side register path for SCAN/HOLD/P_LOCK/PI_LOCK now exists, but P/PI gains default to zero and must be enabled manually.

## OUT1/OUT2 Preview Notes

CH3 and CH4 are generated previews, not measured ADC data.

A 50 Hz triangle wave has a 20 ms period. The IN1/IN2 acquisition window can be shorter than that when `sample_count=2048` and `decimation=1024`, so OUT1/OUT2 previews use a separate generated preview time axis instead of the acquisition time axis.

Preview display is configured in `config.yaml`:

```yaml
preview:
  cycles: 2
  min_points: 1024
  max_points: 5000
```

Real OUT2 must still be verified on an oscilloscope, or by a safe physical loopback such as OUT2 -> IN1 with IN1 kept within ±1 V.

## Official SCPI Mode And Custom FPGA Mode

Official SCPI Mode:

- Controls official ASG OUT1/OUT2 waveforms through `redpitaya_scpi`.
- Can acquire IN1/IN2.
- Starting `redpitaya_scpi` may load the official v0.94 overlay.
- Starting `redpitaya_scpi` may overwrite the currently loaded custom FPGA bitstream.
- If a custom FPGA bitstream with `USE_LASER_LOCK_CORE=1` is loaded, SCPI OUT2 commands may succeed but will not drive physical OUT2 because OUT2 is routed to `selected_out2`.

Custom FPGA Mode:

- OUT1/OUT2 are driven by custom FPGA RTL outputs.
- OUT1 usually corresponds to `laser_error`.
- OUT2 is `selected_out2`: `/dev/mem` -> `custom_register_bank` -> `ramp_generator` -> SAFE/SCAN triangle -> physical OUT2.
- OUT1/OUT2 are not controlled by the official SCPI ASG in this mode.
- Reading the FPGA internal `error_internal` signal requires a later RTL debug buffer, register interface, or AXI readout path.
- The host app currently cannot set FPGA PI parameters or read internal mixer/LPF/error snapshots.
