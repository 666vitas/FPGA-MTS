# Development Log

## 2026-06-26

### Python environment fix

Fixed repeated `ModuleNotFoundError: No module named 'yaml'` risk caused by mixed Anaconda/system Python and project `.venv` usage.

Changed:

- `requirements.txt` explicitly includes `PyYAML>=6.0`, `paramiko>=3.4`, `PySide6`, `pyqtgraph`, `numpy`, and `pandas`.
- `run.bat` now uses only `.venv\Scripts\python.exe` and no longer falls back to system Python.
- `run.bat` prints virtual-environment setup commands if `.venv` is missing.
- `main.py` prints a friendly PyYAML install hint if `import yaml` fails.
- README documents the recommended PowerShell `.venv` command path.

Confirmed scope:

- Host environment/startup files only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 OUT1/OUT2 Apply SCPI fix

Fixed GUI Apply output command sequence after manual SCPI testing proved OUT2 hardware and wiring were healthy.

Manual verified sequence for OUT2:

```text
GEN:RST
SOUR2:FUNC TRIANGLE
SOUR2:FREQ:FIX 50
SOUR2:VOLT 0.05
SOUR2:VOLT:OFFS 0
OUTPUT2:STATE ON
SOUR2:TRig:INT
```

Changed:

- GUI Apply now uses `SOUR<n>:TRig:INT`, not `SOUR<n>:TRIG:IMM`.
- GUI Apply sends output state before the trigger.
- GUI Apply logs every sent SCPI command with `>>`.
- GUI Apply performs readback queries for function, frequency, amplitude, offset, and output state.
- Disable sends `SOUR<n>:VOLT 0`, `OUTPUT<n>:STATE OFF`, and `GEN:STOP`.
- Output amplitudes `>= 0.5 V` require a confirmation dialog.
- OUT2 defaults remain safe: triangle, `50 Hz`, `0.05 V`, `0 V`, enable unchecked.

Confirmed scope:

- Host SCPI output-control logic only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 GUI freeze fix

Moved blocking network/SSH/SCPI actions out of the GUI thread.

Changed:

- Added background workers for Probe, Start SCPI Server, Connect SCPI, and Disconnect/safe shutdown.
- Added connection state handling for `DISCONNECTED`, `PROBING`, `SSH_AVAILABLE`, `SCPI_STARTING`, `SCPI_READY`, `SCPI_CONNECTED`, `ACQUIRING`, and `ERROR`.
- Start SCPI Server is only enabled when Probe shows SSH available and SCPI unavailable.
- If Probe shows `SCPI True`, Start SCPI Server no longer runs and the GUI instructs the user to click Connect SCPI.
- SSH startup command now uses short commands and timeout handling instead of `systemctl status`.
- Connection log and status bar report SSH/SCPI failures instead of freezing.

Confirmed scope:

- Host GUI/connection flow only.
- No FPGA RTL changes.
- No bitstream generation.

### V2 GUI layout fix

Fixed left-panel layout compression in the PySide6 GUI.

Changed:

- Main window default size is now `1600 x 950`.
- Left control panel is inside a `QScrollArea` with minimum width `430 px`.
- OUT1 and OUT2 controls are separated into tabs.
- Output controls use `QFormLayout` with minimum field widths and consistent button/input heights.
- Connection status uses a bounded read-only text area instead of a long compressed label.
- Plot panels and waveform widgets now use expanding size policies and minimum sizes.
- README documents PowerShell `.\run.bat` and notes the scrollable V2 layout.

Confirmed scope:

- GUI/layout-only code changes.
- No FPGA RTL changes.
- No bitstream generation.

### V2 mode-boundary correction

Reviewed the specified custom FPGA files and updated the host app/docs so Official SCPI Mode and Custom FPGA Mode are not mixed.

Confirmed from RTL:

- `USE_LASER_LOCK_CORE = 1`.
- OUT1 / DAC A is `laser_error`.
- OUT2 / DAC B is `laser_control`.
- official `asg_dat[0]` / `asg_dat[1]` no longer directly drive OUT1/OUT2 in custom FPGA mode.
- custom chain is IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> OUT1 error, and the same protected error feeds the shadow/sequential PI candidate -> OUT2 control.

Changed:

- Added GUI mode selector: Official SCPI Mode / Custom FPGA Mode.
- Disabled Start SCPI Server, SCPI connect, SCPI output apply, and SCPI acquisition in Custom FPGA Mode.
- Updated CH3/CH4 labels and warnings for custom FPGA output meaning.
- Hardened `run.bat` for PowerShell/CMD use, optional venv activation, argument forwarding, and missing Python message.
- Added `docs\FPGA_MODE_BOUNDARY.md`.
- Updated README and SOP documents with PowerShell `.\run.bat` instructions and mode boundary.

### V2 connection-stability refactor

Created a V2 host workflow focused on real lab connection stability.

Added:

- `connection_probe.py` for hostname resolution, ping, and port checks for 22/80/5000.
- `ssh_client.py` using Paramiko for Red Pitaya service-management commands.
- `rp_scpi_client.py` as the V2 Red Pitaya SCPI business layer.
- V2 GUI with Probe, Start SCPI Server, Connect SCPI, Disconnect, SSH credentials, resolved IP selection, OUT1/OUT2 controls, acquisition, and four-channel scope display.
- Documentation: `CONNECTION_DIAGNOSIS.md`, `SCPI_SERVER_STARTUP.md`, `HOST_APP_V2_DESIGN.md`, and `HARDWARE_TEST_SOP.md`.

Changed:

- Output defaults now use conservative `amplitude_v = 0.05 V`.
- Safe shutdown covers both OUT1 and OUT2.
- CH3 and CH4 are explicitly generated previews, not measured outputs.

Confirmed scope:

- No FPGA RTL changes.
- No bitstream generation.
- No use of any directory containing `weifang`.

### V1.1 hardware-test upgrade

Updated the host app based on `docs\CLAUDE_REVIEW_HOST_APP_V1.md`.

Added:

- `--mock` command-line support in `main.py`, with custom arguments filtered before creating `QApplication`.
- `acquisition_worker.py`, a `QThread` worker for non-blocking real SCPI acquisition.
- Real Red Pitaya acquisition methods in `rp_client.py`: `configure_acquisition`, `acquire_in1_in2`, `read_in1`, `read_in2`, and `parse_scpi_data`.
- Four-channel oscilloscope-style GUI layout.
- CH1 / CH2 measured ADC statistics and warnings.
- CH3 disabled placeholder for unavailable `error_internal`.
- CH4 generated OUT2 scan preview, explicitly not measured.
- Acquisition controls, decimation selection, sample rate display, and actual refresh-rate display.
- CSV metadata header lines.
- `atexit` best-effort safe shutdown registration.

Fixed:

- Mock mode no longer generates nonzero `error_internal`.
- `run.bat` now activates `.venv` and forwards arguments.
- `requirements.txt` now uses standard `PyYAML` package naming.

Confirmed scope:

- No FPGA RTL changes.
- No Vivado project changes.
- No bitstream generation.
- No use of any directory containing `weifang`.

### V1 initial implementation

Created Red Pitaya laser lock host V1 in `E:\new\fpga_lock\raunjian`.

Added:

- PySide6 GUI entry point and main window.
- SCPI socket client with query and write support.
- Red Pitaya client wrapper with `*IDN?` connection gate.
- OUT2 triangle scan apply, stop, and safe shutdown sequences.
- Safety validation for frequency, amplitude, and offset.
- Mock mode client with synthetic IN1, IN2, and placeholder `error_internal` waveforms.
- CSV export through pandas.
- PNG export of the plotting panel.
- Project config file, requirements file, and Windows run script.
- Documentation for project context, host design, test plan, and next FPGA debug-buffer phase.

Confirmed project boundary:

- No FPGA RTL changes.
- No Vivado project changes.
- No bitstream generation.
- No use of any directory containing `weifang`.
