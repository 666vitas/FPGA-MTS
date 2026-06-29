# FPGA-MTS

Red Pitaya FPGA laser frequency locking project.

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
