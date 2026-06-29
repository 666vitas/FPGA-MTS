# Project Context

## Fixed Project Boundary

- FPGA project code directory: `E:\new\fpga_lock\v94\v0.94`
- Host application development directory: `E:\new\fpga_lock\raunjian`
- No directory containing `weifang` is used, referenced, or modified.
- First-stage work is host software only. FPGA RTL, Vivado project files, and bitstream generation are out of scope.

## Hardware Platform

- Red Pitaya STEMlab 125-14
- Host software stack: Python 3.10+, PySide6, pyqtgraph, numpy, pandas, pyyaml, socket
- SCPI endpoint: default `rp-f0cb13.local:5000`, manually editable in the GUI

## Current Experimental Chain

1. PD signal goes through an analog band-pass filter and amplifier, then enters Red Pitaya IN1.
2. External 4.6 MHz REF enters Red Pitaya IN2.
3. FPGA project is located at `E:\new\fpga_lock\v94\v0.94`.
4. The current FPGA is used as a digital mixer plus LPF; OUT1 outputs an error-like signal.
5. OUT2 is used for unlocked scan and outputs a triangle wave to the laser scan / PZT input.
6. The host application controls OUT2 triangle frequency, amplitude, and offset so scan changes do not require rebuilding or reflashing the FPGA.

## V2 Mode Boundary

The host app now separates two modes:

- Official SCPI Mode: may start `redpitaya_scpi`, connect to port 5000, control official ASG OUT1/OUT2, and acquire IN1/IN2 through SCPI. Starting `redpitaya_scpi` may load the official v0.94 overlay and overwrite the currently loaded custom FPGA bitstream.
- Custom FPGA Mode: preserves the current custom bitstream. In the reviewed RTL, `USE_LASER_LOCK_CORE = 1`, OUT1 / DAC A is `laser_error`, OUT2 / DAC B is `laser_control`, and official ASG data no longer directly drives OUT1/OUT2.

In Custom FPGA Mode, OUT2 remains oscilloscope-only and must not be connected to laser scan/PZT or D2-125. V2 does not read FPGA internal `error_internal`; that requires a later debug buffer, register bank, or AXI-accessible capture path.
