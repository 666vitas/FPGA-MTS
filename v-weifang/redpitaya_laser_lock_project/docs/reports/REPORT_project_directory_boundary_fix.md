# REPORT: Project Directory Boundary Fix

Date: 2026-05-14

## 1. Boundary Rule

The official Red Pitaya project root is:

```text
E:\new\fpga_lock\v94\v0.94
```

Official RTL is read-only for this project:

```text
E:\new\fpga_lock\v94\v0.94\rtl
```

The custom laser-lock project must live under:

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

Custom RTL, simulation files, reports, and experiment logs must use these directories:

```text
redpitaya_laser_lock_project\rtl
redpitaya_laser_lock_project\sim
redpitaya_laser_lock_project\docs
redpitaya_laser_lock_project\experiment_logs
```

## 2. Scan Result

The following custom files were found in official directories and should be treated as misplaced project files.

### Misplaced RTL

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

Recommended project location:

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\laser_lock_core.sv
```

### Misplaced Testbench

```text
E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core.sv
```

Recommended project location:

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv
```

## 3. Official Top File Status

The official top file contains laser-lock integration edits and should be restored or replaced by a clean official copy before continuing board integration:

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

Observed laser-lock related markers:

```text
line 198: // Laser lock core
line 199: localparam logic USE_LASER_LOCK_CORE = 1'b1;
line 419: // v1_pd_passthrough can route laser_lock_core outputs...
line 425: assign dac_a_sum = USE_LASER_LOCK_CORE ? laser_error_ext : dac_a_sum_official;
line 426: assign dac_b_sum = USE_LASER_LOCK_CORE ? laser_control_ext : dac_b_sum_official;
line 610: // Laser lock core - v1 PD passthrough
line 613: laser_lock_core i_laser_lock_core (
```

No further edits should be made directly to this file for the custom project. Future connection work should be delivered as a separate integration patch or Markdown wiring document.

## 4. Recommended Migration Plan

Do not continue development inside the official `rtl` or `sim` folders.

Recommended safe steps:

1. Copy the misplaced custom RTL into the project RTL directory:

```powershell
Copy-Item -LiteralPath "E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv" `
  -Destination "E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\laser_lock_core.sv"
```

2. Copy the misplaced custom testbench into the project simulation directory:

```powershell
Copy-Item -LiteralPath "E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core.sv" `
  -Destination "E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv"
```

3. After confirming the copied files are correct, remove the misplaced custom files from the official directories only with explicit user approval:

```powershell
Remove-Item -LiteralPath "E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv"
Remove-Item -LiteralPath "E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core.sv"
```

4. Restore `rtl\red_pitaya_top.sv` to the official version or manually remove only the laser-lock integration edits. This should also be done only with explicit user approval or from a known clean official source.

5. For future integration, create one of the following instead of editing official files directly:

```text
redpitaya_laser_lock_project\docs\INTEGRATION_v1_pd_passthrough.md
redpitaya_laser_lock_project\patches\integration_v1_pd_passthrough.patch
```

## 5. Current Action Taken

This report was generated in the custom project documentation directory:

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\REPORT_project_directory_boundary_fix.md
```

No official Red Pitaya source file, XDC file, PS module, AXI module, PLL module, or ODDR logic was modified while creating this report.

## 6. Future Rule

All future custom implementation work must be created under:

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

Official files may be read for analysis, but direct edits to official files should be replaced by generated documentation or integration patches unless the user explicitly approves an actual edit.
