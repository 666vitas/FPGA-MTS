# GPT Reading Guide for FPGA-MTS

This repository is the active local checkout for the Red Pitaya FPGA laser frequency locking project.

## Active Project Boundary

Active local project root:

```text
E:\new\fpga_lock\v94
```

Active GitHub project:

```text
666vitas/FPGA-MTS
```

Active development directories:

- `v0.94/`
- `version/`
- `software/`

Do not use:

- `weifang`
- `v-weifang`
- `version-weifang`

## Agent Workflow

GPT should read the GitHub project and newly generated project files, understand the current experiment progress, and generate instructions for Codex.

Codex should perform local file operations under `E:\new\fpga_lock\v94`, report the files it reads and modifies, and follow the user's explicit scope for Markdown, RTL, Python, testbench, simulation, and experiment SOP work.

Claude Code should review Codex-generated code, RTL timing risks, SOP safety risks, and experiment safety issues, but it is not the only experiment authority.

The user is responsible for manually running Vivado, generating bitstreams, programming Red Pitaya, wiring hardware, saving oscilloscope/Vivado evidence, and reporting experiment results back to GPT/Codex.

## Default Safety Boundary

By default, Codex must not run Vivado, run synthesis, run implementation, generate bitstream/bin files, program Red Pitaya, modify `redpitaya.xpr`, modify XDC/SDC constraints, or read/modify any weifang-related directory.
