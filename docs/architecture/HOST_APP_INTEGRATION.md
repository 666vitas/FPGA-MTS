Status: SUPPORTING
Effective-Gate: ALL
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: docs/HOST_APP_INTEGRATION.md
Superseded-By: NONE

# Host App Integration

## 为什么集成上位机软件

Red Pitaya Laser Lock Host V2 当前只在下面目录开发：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

旧的独立开发目录不再作为上位机软件主开发目录。当前项目内唯一的上位机主目录是：

```text
v94\software\redpitaya_lock_host
```

这样可以把 FPGA 工程、上位机软件和项目文档放在同一个仓库中，同时继续保持上位机软件与 FPGA/Vivado 工作之间的清晰边界。

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
