# FPGA-MTS

Red Pitaya FPGA laser frequency locking project.

## Current Mainline

当前主线 = v3REG-0 register-controlled OUT2 SAFE/SCAN。

- OUT1 = `laser_error` = mixer + LPF error observation.
- OUT2 = `selected_out2` = `custom_register_bank` + `ramp_generator` SAFE/SCAN.
- `laser_control` / `pi_controller_seq` 仅保留为后续候选，不是当前 OUT2 输出。
- 当前阶段只做 OUT2 示波器验证，不接 Scan/PZT，不接激光器。

## Project Layout

- `v0.94/`  
  FPGA / RTL / Vivado project.

- `software/redpitaya_lock_host/`  
  Python / PySide6 Red Pitaya upper-computer host software.

- `docs/`  
  Project documentation.

- `version/`  
  Project status and experiment records.

## Host App Startup

```powershell
cd software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```
