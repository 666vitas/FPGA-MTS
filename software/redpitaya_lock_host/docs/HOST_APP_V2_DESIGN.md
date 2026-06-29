# Host App V2 Design

## Scope

V2 is a stable Red Pitaya host app for experiment-room use. It does not modify FPGA RTL, does not generate bitstreams, and does not read internal FPGA `error_internal`.

V2 explicitly separates Official SCPI Mode from Custom FPGA Mode so the GUI does not imply that SCPI ASG control is valid while the custom FPGA bitstream owns OUT1/OUT2.

## Modules

- `connection_probe.py`: resolves hostnames, probes ping, and checks ports 22/80/5000.
- `ssh_client.py`: uses Paramiko to run Red Pitaya service-management commands.
- `scpi_client.py`: low-level TCP SCPI transport with CRLF command endings.
- `rp_scpi_client.py`: Red Pitaya SCPI business layer for outputs and acquisition.
- `acquisition_worker.py`: background `QThread` acquisition loop.
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

In Custom FPGA Mode, CH3/CH4 labels switch to remind the user that actual OUT1/OUT2 are `laser_error` and `laser_control`. The plotted traces remain previews or placeholders, not measured custom FPGA outputs.

## FPGA Internal Signals

`error_internal`, mixer output, and LPF output require FPGA RTL support such as a debug buffer or AXI registers. V2 does not implement that path.
