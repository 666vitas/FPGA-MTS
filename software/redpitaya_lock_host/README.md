# Red Pitaya Laser Lock Host V2

This is the Red Pitaya Laser Lock Host V2 upper-computer software for the FPGA laser frequency locking project.

It belongs to the main project:

```text
E:\new\fpga_lock\v94
```

The FPGA / RTL / Vivado project is located at:

```text
..\..\v0.94
```

## Modes

### Official SCPI Mode

The host application defaults to `Official SCPI Mode`.

In `Official SCPI Mode`, the host can use `redpitaya_scpi` to control OUT1/OUT2 waveform output and acquire IN1/IN2 data.

Starting `redpitaya_scpi` may load the official v0.94 overlay and may overwrite the currently loaded custom FPGA bitstream. Use this mode for official SCPI bring-up and hardware signal-chain checks.

### Custom FPGA Mode

In `Custom FPGA Mode`, OUT1/OUT2 come from the custom RTL signals `laser_error / laser_control`, and are not controlled by the SCPI ASG waveform generator.

If the GUI needs to display the FPGA internal `error_internal` signal, a later RTL debug buffer or register interface is required.

## Setup And Run

Use PowerShell from the host-app directory:

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```

Mock mode:

```powershell
.\run_mock.bat
```

In PowerShell, do not type `run.bat` directly. Use `.\run.bat`.
