# GPT Reading Guide for FPGA-MTS

This repository is my Red Pitaya FPGA laser frequency locking project.

## Active baseline

Only these paths are active for the current development route:

```text
version/
v0.94/
```

Important rule:

```text
Ignore all weifang-related directories. The active development baseline is v0.94 plus version/v2 documentation.
Do not read, reference, sync, copy, or modify any weifang / version-weifang related directory unless the user explicitly asks for historical comparison.
```

## Priority reading order

1. `version/`

   - v1/v2/v2a/v2B/v2PZT development records
   - roadmap, SOP, review checklist
   - current D2-125 wiring model and stage boundaries

2. `v0.94/`

   - real FPGA development directory
   - RTL, testbench, Vivado source files

3. `docs/`

   - earlier project documents, read only when needed for context

## Important status

The v2a PI/PID code has already been written. Do not ignore it.

v2a is useful because it is the first digital replacement of the D2-125 servo core, but it does not yet replace the full D2-125 workflow. The full workflow still requires scan, offset, scan-lock switching, lock acquisition, relock, and lock quality judgment.

Current OUT2 is still a control candidate / shadow control / sequential PI candidate unless a later SOP explicitly allows a real actuator connection. It must not be connected to the laser, D2-125 Servo Output tee, or Scan/PZT in the current stage.
