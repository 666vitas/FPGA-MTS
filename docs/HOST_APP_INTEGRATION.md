# Host App Integration

## Why Integrate The Host App

The Red Pitaya Laser Lock Host V2 is now developed only in:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

The old standalone directory is not the development source anymore. The
canonical host-app path inside this project is:

```text
v94\software\redpitaya_lock_host
```

This keeps the FPGA project, host software, and project documentation in one repository while preserving a clear boundary between the software and FPGA/Vivado work.

## Directory Structure

```text
v94/
  v0.94/
    FPGA / RTL / Vivado project
  software/
    redpitaya_lock_host/
      Python / PySide6 host software
  docs/
    Project documentation
  version/
    Project status and experiment records
```

## Host And FPGA Boundary

The host application is responsible for GUI control, Red Pitaya connection management, SCPI communication, waveform preview, data acquisition, and logging.

The FPGA project remains in `v0.94/`. This integration does not modify RTL, Vivado project files, or bitstreams.

## Official SCPI Mode And Custom FPGA Mode

`Official SCPI Mode` uses `redpitaya_scpi` to control OUT1/OUT2 waveform generation and acquire IN1/IN2 data through the official Red Pitaya SCPI path.

Starting `redpitaya_scpi` may load the official v0.94 overlay and may overwrite the currently loaded custom FPGA bitstream.

`Custom FPGA Mode` assumes the custom FPGA bitstream is already loaded. In this mode, OUT1/OUT2 are driven by the custom RTL signals `laser_error / laser_control`, not by SCPI ASG waveform control.

## Current RTL Policy

This integration does not modify RTL.

If later work needs to connect host-side parameter control with FPGA registers, or expose FPGA internal `error_internal` data to the GUI, the RTL must add a debug buffer, register map, or another explicit readout path.

## Current Hardware Test Order

1. Probe.
2. Start SCPI Server.
3. Connect SCPI.
4. Connect OUT2 to the oscilloscope.
5. Test `triangle / 50 Hz / 0.05 V / 0 offset`.
6. Test IN1/IN2 with a signal source.
7. Finally connect PD and laser scan/PZT.
