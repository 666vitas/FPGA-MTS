# Reproducibility

This document defines the safest reproducible path for reviewing FPGA-MTS from a fresh clone **without connecting a laser or programming a Red Pitaya**.

The purpose is to let a contributor or reviewer reproduce the repository/Host checks that are currently suitable for automation while keeping Vivado implementation and physical laser-lock evidence separate.

## Supported baseline

Current maintained development baseline:

- Windows 10/11
- Python 3.11
- PowerShell
- Git
- Vivado 2020.1 for FPGA synthesis/implementation work
- Red Pitaya STEMlab 125-14 for later hardware validation

The offline verification below does **not** require Vivado or Red Pitaya hardware.

## 1. Clone

```powershell
git clone https://github.com/666vitas/FPGA-MTS.git
Set-Location .\FPGA-MTS
```

## 2. Create the Host Python environment

```powershell
py -3.11 -m venv .venv-ci
.\.venv-ci\Scripts\python.exe -m pip install --upgrade pip
.\.venv-ci\Scripts\python.exe -m pip install -r .\software\redpitaya_lock_host\requirements.txt
.\.venv-ci\Scripts\python.exe -m pip install pytest
```

If `py -3.11` is not available, use an installed Python 3.11 interpreter and pass its executable path to the verification script.

## 3. Verify repository rules and structure

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -Scope Rules
```

This checks the maintained project entry points, required paths, active-rule consistency, conflict markers, PowerShell syntax, and repository diff hygiene.

## 4. Run safe targeted Host verification

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1 `
  -Scope Host `
  -PythonPath .\.venv-ci\Scripts\python.exe `
  -TimeoutSeconds 600
```

The maintained Host verification includes:

- Python `tabnanny`;
- Python byte-compilation;
- pytest collection;
- targeted tests around custom FPGA identity/status, calibration, scan/hold/lock control, operator diagnostics, and decimation behavior.

It runs with Qt in offscreen mode and does not require a physical Red Pitaya.

## Continuous integration

The same safe offline path is represented by `.github/workflows/offline-verification.yml` on GitHub Actions using a Windows runner and Python 3.11.

A green workflow means only that the automated repository and targeted Host checks passed. It is **not** evidence that:

- Vivado synthesis or implementation passed for the tested commit;
- timing/DRC/CDC is closed;
- a bitstream was programmed successfully;
- OUT2 is electrically correct on the bench;
- a PZT loop converged;
- a laser is frequency locked.

Those claims require their own evidence under `docs/CURRENT_STATUS.md` and `docs/RELEASE_PROCESS.md`.

## FPGA verification boundary

FPGA development uses the active Vivado project under `v0.94/project/` and Vivado 2020.1. RTL simulation, synthesis, implementation, timing, DRC/CDC/methodology, bitstream provenance, and board-level testing are distinct gates.

Do not infer current FPGA release readiness from historical files in `v0.94/exp/` or from a successful Host CI run.

## Known reproducibility limits

The repository is still a research-stage laboratory system. Remaining work is tracked publicly in the issue tracker, including:

- provenance/license completion;
- further removal of maintainer-local absolute-path assumptions;
- current hardware-gate closure;
- the first hardware-validated traceable release.

If a step in this document fails from a clean clone, open a bug report and include the commit SHA, Windows/Python versions, command used, and full error output.