# Windows Environment Setup

## Recommended Environment

```text
Windows 10/11
Official Python 3.11
Project-local .venv
PowerShell
```

## Not Recommended

```text
Anaconda base
```

Anaconda base may conflict with PySide6 / Qt DLLs and cause QtWidgets DLL load failures.

## Check Python

```powershell
where.exe python
python -c "import sys; print(sys.executable)"
py -0p
```

If the output shows:

```text
D:\anaconda\python.exe
```

then the current default Python is Anaconda.

## Install Official Python 3.11

```powershell
winget install -e --id Python.Python.3.11
```

After installation, close PowerShell, reopen it, and check:

```powershell
py -0p
```

## Create The Virtual Environment

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host

if (Test-Path .\.venv) { Remove-Item -Recurse -Force .\.venv }

py -3.11 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

## Test PySide6

```powershell
.\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

If this reports:

```text
ImportError: DLL load failed while importing QtWidgets
```

check the following:

1. Confirm Anaconda base is not being used.
2. Delete `.venv` and rebuild it with official Python 3.11.
3. Install Microsoft Visual C++ Redistributable x64.
4. Close PowerShell and reopen it.
5. Test PySide6 again.

## Start The Software

```powershell
.\run_mock.bat
.\run.bat
```
