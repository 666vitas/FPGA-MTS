# Host App Design

Legacy note: this file documents the V1.1 design. For current V2 mode boundaries, connection flow, and Official SCPI Mode vs Custom FPGA Mode behavior, use `HOST_APP_V2_DESIGN.md` and `FPGA_MODE_BOUNDARY.md`.

## Version

V1.1 upgrades V1 from a mock-only GUI into a hardware-testable Red Pitaya host app with real IN1 / IN2 SCPI acquisition.

## Architecture

- `scpi_client.py`: low-level TCP socket SCPI transport.
- `rp_client.py`: Red Pitaya business wrapper for `*IDN?`, OUT2 scan control, acquisition configuration, IN1 / IN2 reads, and safe shutdown.
- `acquisition_worker.py`: `QThread` worker that performs blocking SCPI acquisition away from the GUI thread and emits numpy arrays through Qt signals.
- `safety.py`: scan validation plus an `atexit` fallback registry for best-effort shutdown.
- `mock_client.py`: hardware-free client that generates IN1 / IN2 mock waveforms and keeps `error_internal` at zero.
- `main_window.py`: PySide6 GUI, four-channel plotting, acquisition controls, export, and status display.
- `waveform_plot.py`: reusable pyqtgraph waveform widget.
- `data_logger.py`: CSV metadata export and PNG screenshot export.
- `main.py`: config loading and command-line parsing, including `--mock`.

## Command-Line Flow

`main.py` parses `--mock` with `argparse`, removes it from the Qt argument list, and passes `start_mock=True` to `MainWindow`. This prevents Qt from rejecting the custom argument.

## Connection Flow

1. User selects mock mode or real hardware mode.
2. Real mode opens the SCPI socket and sends `*IDN?`.
3. OUT2 and acquisition controls are enabled only after successful connection.
4. SCPI exceptions are caught and shown in the status bar.

## OUT2 Scan Flow

Applying scan settings sends:

```text
GEN:RST
SOUR2:FUNC TRIANGLE
SOUR2:FREQ:FIX <Hz>
SOUR2:VOLT <V>
SOUR2:VOLT:OFFS <V>
OUTPUT2:STATE ON|OFF
SOUR2:TRig:INT
```

Note: early V1 notes used `SOUR2:TRIG:IMM`. V2 uses `SOUR2:TRig:INT` after the output state command.

Stopping scan sends:

```text
OUTPUT2:STATE OFF
GEN:STOP
```

Safe shutdown sends:

```text
ACQ:STOP
SOUR2:VOLT 0
wait 100 ms
OUTPUT2:STATE OFF
GEN:STOP
close socket
```

## Acquisition Flow

The real hardware acquisition path runs in `AcquisitionWorker`, not in the GUI thread.

Configuration:

```text
ACQ:RST
ACQ:DATA:FORMAT ASCII
ACQ:DATA:UNITS VOLTS
ACQ:DEC <N>
ACQ:TRIG:DLY 0
```

Per-frame read:

```text
ACQ:START
ACQ:TRIG NOW
poll ACQ:TRIG:FILL?
ACQ:SOUR1:DATA?
ACQ:SOUR2:DATA?
ACQ:STOP
```

The worker emits IN1, IN2, and sample rate through Qt signals. `main_window.py` receives the signal in the main thread and updates pyqtgraph there.

## Four-Channel Display

- CH1: `IN1 / PD`, measured ADC voltage with Vpp / min / max / mean and clipping warning near +/-1 V.
- CH2: `IN2 / REF`, measured ADC voltage with stats and an aliasing warning when decimation > 8.
- CH3: `OUT1 / ERROR`, disabled placeholder. V1.1 does not read FPGA `error_internal`.
- CH4: `OUT2 / SCAN`, software-generated triangle preview based on current scan settings. This is not a measured OUT2 voltage.

Display modes:

- Time Mode: CH1 and CH2 are plotted versus time.
- Spectrum Mode: CH1 plots `x = OUT2 scan preview`, `y = IN1 / PD`.
- MTS Mode is reserved for the future `x = OUT2 scan preview`, `y = error_internal` workflow after FPGA debug buffer support exists.
