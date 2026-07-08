# Development Log

## 2026-07-05 - v3REG-0 GUI 控制 OUT2 扫描并观察到实验波形

- 记录当前阶段推进：v3REG-0 已经从“板子是否能被上位机控制”推进到“上位机可以控制扫描参数，并且能观察到实验波形”的阶段。
- 已验证完整链路：GUI -> SSH -> `/dev/mem` -> `custom_register_bank` -> `ramp_generator` -> `selected_out2` -> DAC B / OUT2。Red Pitaya 自定义 bitstream 已在板上运行，base address 为 `0x40600000`；GUI Probe Registers 能找到 `MAGIC=0x4D545330`、`VERSION=0x00030000`、`found_base_addr=0x40600000`。
- 已确认手动 monitor 和 GUI 两条路径均通过：monitor 写寄存器可以产生 10 Hz OUT2 三角波，monitor SAFE 后三角波消失；修复 `/dev/mem mmap.flush()` EINVAL 的 host helper 问题后，GUI SCAN 可以产生 OUT2 三角波，GUI SAFE 可以关闭 OUT2 输出。
- 当前 GUI Custom FPGA Control 参数：base address `0x40600000`，`offset-v=0.7500 V`，`amp-v=0.2000 V`，`freq-hz=50.170 Hz`，`step-counts=1`，`limit-counts=8191`。
- GUI SCAN 读回：`MAGIC=0x4D545330`，`VERSION=0x00030000`，`MODE=1`，`ENABLE=1`，`STATUS=0x00000001`，`OUT2=4522 counts / 0.552069 V`。设定扫描范围约为 `0.55 V` 到 `0.95 V`（约 `0.40 Vpp`），因此当前读回值接近理论下限。
- 观察到波形时的激光器控制器状态：TEC 设置/工作 `22.66 C / 22.46 C`；电流设置/工作 `40.07 mA / 57.42 mA`；PZT 设置/工作 `34.99 V / 42.52 V`。后续波形变化需要与这些 TEC / current / PZT 条件对照。
- 本次波形指标：板端扫描/输出信号 `Vpp=0.4583 V`，`min=0.6236 V`，`max=1.082 V`，`RMS=0.8492 V`；CH2 信号 `Vpp=0.2701 V`，`min=0.3303 V`，`max=0.6004 V`，`RMS=0.4828 V`；CH3 信号 `Vpp=1.784 V`，`min=-1.16 V`，`max=0.6239 V`，`RMS=0.2433 V`；板端输出信号 `Vpp=0.08848 V`，`min=0.6243 V`，`max=0.7128 V`，`RMS=0.6696 V`。
- 结论：GUI 已经可以设置 OUT2 的 offset、amplitude、frequency、enable/safe 和 scan mode；在 `offset=0.75 V`、`amp=0.20 V`、`freq=50.17 Hz` 条件下，系统可以扫描并显示周期性通道响应，已经可以进入下一步谱线扫描观察。
- 边界：当前完成的是 GUI 可控扫描输出 + 实验波形观察，不是闭环锁定，也不是 D2-125 替代。继续以示波器优先观察；任何连接到激光器 PZT、scan、current modulation 或 D2-125 输入的操作，都必须记录接线、幅度、偏置和安全限制。
- 下一步计划：执行参数矩阵 A `offset=0.50 V, amp=0.20 V, freq=50 Hz`；B `offset=0.75 V, amp=0.20 V, freq=50 Hz`；C `offset=0.75 V, amp=0.10 V, freq=20 Hz`；D `offset=0.75 V, amp=0.05 V, freq=10 Hz`。每组记录 GUI 参数、OUT2 读回、示波器 OUT2 Vpp/min/max、CH2/CH3 稳定性，以及是否出现削顶、跳变、饱和或断裂。
- 修改 Python 文件：无。
- 验证方式：仅文档记录更新，本次未运行命令。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - 修复 GUI SAFE/SCAN 的 /dev/mem flush EINVAL 问题

- 修复 GUI Custom FPGA SAFE/SCAN 写寄存器失败问题：Probe Registers 和 Status 已经成功（`MAGIC=0x4D545330`，`VERSION=0x00030000`），但远端 helper 写寄存器时报 `OSError: [Errno 22] Invalid argument`。
- 根因：板端 Python helper 的 `RegisterWindow.write()` 在 `/dev/mem` MMIO 写入后调用了 `mmap.flush()`；当前 Red Pitaya Linux 路径下该调用可能返回 EINVAL，即使 monitor 写寄存器本身是有效的。
- 修复方式：从 REMOTE_HELPER 写寄存器路径中删除 `self.mem.flush()`；SAFE/SCAN 仍保留 MAGIC precheck，并在写入后继续读回 status。
- 修改 Python 文件：`scripts/custom_fpga_scan_control.py`，`tests/test_custom_fpga_backend.py`。
- 验证：`.\.venv\Scripts\python.exe -m py_compile scripts\custom_fpga_scan_control.py redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\main_window.py` 通过；`python -m pytest tests` 通过。`.\.venv\Scripts\python.exe -m pytest tests` 未能运行，因为 `.venv` 中未安装 pytest。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。

## 2026-07-05 - v3REG-0 板端 monitor 验证 OUT2 SAFE/SCAN 通过

- 记录板端 bring-up 证据：Red Pitaya 已加载 `/root/red_pitaya_top.bit.bin`；`/opt/redpitaya/bin/monitor 0x40600000` 返回 `0x4D545330`；`/opt/redpitaya/bin/monitor 0x40600004` 返回 `0x00030000`。
- 验证硬件行为：monitor 写入 `MODE=1`、`ENABLE=1`、`SCAN_OFFSET=0`、`SCAN_AMP=0x19A`、`SCAN_STEP=0x1`、`SCAN_UPDATE_DIV=0x1DC6`、`OUT2_LIMIT=0x1FFF` 后，OUT2 产生约 10 Hz 安全三角波。
- 验证 SAFE 关闭：向 `0x4060000C` 写 `0x0`，再向 `0x40600008` 写 `0x0` 后，OUT2 三角波消失，OUT2 回到无三角波状态。
- 结论：PS -> PL sys_bus 访问、base address `0x40600000`、`custom_register_bank`、`ramp_generator`、MODE/ENABLE 控制、`selected_out2` -> DAC B / OUT2、SAFE 关闭链路都已在硬件上验证通过。
- 修改 Python 文件：无。
- 如何运行/验证：使用上述 board monitor 命令；下一步 GUI 验证路径是 Custom FPGA Mode -> Probe Registers -> Status -> SAFE -> SCAN。
- 是否修改 RTL：否。
- 是否生成 bitstream：否。
- 安全边界不变：OUT2 仅接示波器观察；不要将 OUT2 接到 laser PZT、laser current、D2-125 Servo Output 或 Scan input。

## 2026-07-05 - GUI OUT2 path boundary wording fix

- Implemented a minimal GUI wording/defaults fix so users distinguish Official SCPI OUT2 from Custom FPGA `selected_out2` SAFE/SCAN.
- Python files changed: `redpitaya_lock_host/main_window.py`, `tests/test_custom_fpga_backend.py`, `tests/test_custom_fpga_workflow.py`.
- Verification: `python -m py_compile redpitaya_lock_host\main_window.py redpitaya_lock_host\custom_fpga_backend.py`; `python -m pytest tests`.
- Modified RTL: no.
- Generated bitstream: no.

## 2026-07-05 - Custom FPGA missing-register GUI status guard

- Implemented a GUI/status guard so `MAGIC != 0x4D545330` renders `custom_register_bank not found` instead of fake zero register state.
- Python files changed: `redpitaya_lock_host/custom_fpga_backend.py`, `redpitaya_lock_host/main_window.py`, `tests/test_custom_fpga_backend.py`.
- Verification: `python -m pytest tests\test_custom_fpga_backend.py`; `python -m py_compile redpitaya_lock_host\custom_fpga_backend.py redpitaya_lock_host\main_window.py`.
- Modified RTL: no.
- Generated bitstream: no.

## 2026-07-05 - GUI Custom FPGA Control v1

- Implemented first GUI Custom FPGA Control panel in Custom FPGA Mode.
- Added SSH + `/dev/mem` register operations for Probe Registers, Status, SAFE, and SCAN without starting `redpitaya_scpi`.
- Python files changed: `redpitaya_lock_host/custom_fpga_backend.py`, `redpitaya_lock_host/connection_workers.py`, `redpitaya_lock_host/main_window.py`.
- Verification: `python -m py_compile` passed for `custom_fpga_backend.py`, `connection_workers.py`, `main_window.py`, and `scripts/custom_fpga_scan_control.py`.
- GUI run path: `.\run.bat`, then Custom FPGA Mode -> Probe Registers -> Status -> SAFE -> SCAN.
- Modified RTL: no.
- Generated bitstream: no.

## 2026-06-30 - Four-mode GUI workflow structure

- Reorganized the host GUI around four mode pages:
  Hardware Bring-up, Custom FPGA Observe, Lock Workflow, and Data Log.
- Kept Official SCPI Mode for Probe, Start SCPI Server, Connect SCPI, safe OUT2 scan, IN1/IN2 acquisition, and output disable.
- Added Custom FPGA Observe manual oscilloscope inputs for OUT1 laser_error, OUT2 laser_control, PD/absorption, REF, and notes.
- Added automatic OUT2/OUT1 Vpp ratio and safety judgment for manual scope readings.
- Added Lock Workflow Mode as a D2-125 replacement checklist without pretending automatic lock control is implemented.
- Added Markdown experiment log export to `docs/experiment_logs/`.
- Added `custom_fpga_backend.py` as a future interface stub; all hardware methods raise `NotImplementedError`.
- No FPGA internal data is faked.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-30 - Canonical host-app development directory

- Confirmed all future Red Pitaya host-app development uses:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Confirmed the old standalone host-app directory is no longer used; the canonical directory is:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Documented the current directory rules:
  Python source in `redpitaya_lock_host/`, tests in `tests/`, Markdown docs/SOPs/stage notes in `docs/`, and stage records in `docs/DEVELOPMENT_LOG.md`.
- Confirmed usage instructions belong in `README.md` and `docs/USAGE.md`.
- Confirmed SCPI notes belong in `docs/SCPI_MODE_NOTES.md`.
- Confirmed `.venv/` is local only and must not be added to Git.
- Replaced remaining old standalone-directory references in active Markdown docs with the canonical host-app directory.
- Renamed the preview helper module to `waveform_preview.py` and the offline test to `tests/test_waveform_preview.py`.
- Confirmed root-level Word report cleanup was attempted, but the `.docx` file was locked by another process and was not moved.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-29 - OUT1/OUT2 preview time-axis fix

- Fixed CH3/CH4 generated previews so they no longer reuse the IN1/IN2 acquisition time axis.
- Added `preview.cycles`, `preview.min_points`, and `preview.max_points` configuration.
- Documented that a 50 Hz triangle wave has a 20 ms period.
- Root cause: default `sample_count=2048` and `decimation=1024` gives about 16.78 ms of acquisition data, shorter than one 50 Hz period.
- CH3/CH4 now use an independent generated preview time axis and default to two cycles.
- CH4 remains a generated preview, not a measured OUT2 waveform.
- Real OUT2 must still be checked on an oscilloscope, or by safe OUT2 -> IN1 loopback with IN1 kept within ±1 V.
- Confirmed V2 SCPI apply uses `SOURn:TRig:INT`.
- Updated the legacy `rp_client.py` compatibility path to avoid the old `SOUR2:TRIG:IMM` command.
- Added offline preview waveform tests that do not require Red Pitaya.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

## 2026-06-29 - Windows environment and host-app documentation update

- Confirmed host app location:
  `E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Confirmed project-local `.venv` exists.
- Documented recommended environment:
  Official Python 3.11 + project-local `.venv`.
- Documented that Anaconda base is not recommended for this PySide6 GUI because of possible Qt/DLL conflicts.
- Added Windows setup instructions.
- Added usage instructions for `run.bat` and `run_mock.bat`.
- Added SCPI mode notes and hardware safety checklist.
- No FPGA RTL was modified.
- No Vivado project was modified.
- No bitstream was generated.

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

Created Red Pitaya laser lock host V1; current development now lives in `E:\new\fpga_lock\v94\software\redpitaya_lock_host`.

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
