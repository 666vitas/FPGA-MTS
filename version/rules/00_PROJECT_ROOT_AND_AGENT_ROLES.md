# Project Root and Agent Roles

## 1. Current Project Root

The only active local project development root is:

```text
E:\new\fpga_lock\v94
```

This directory corresponds to the GitHub project:

```text
666vitas/FPGA-MTS
```

`E:\new\fpga_lock` is the total project archive and must not be used as the current code development root.

## 2. Current Active Development Directories

The current active development directories are:

- `E:\new\fpga_lock\v94\v0.94`
- `E:\new\fpga_lock\v94\version`
- `E:\new\fpga_lock\v94\software`

Directory roles:

- `v0.94/`: FPGA RTL / Vivado / Red Pitaya code mainline.
- `version/`: version records, rules, SOPs, roadmap, and experiment records.
- `software/`: upper-computer software mainline.

## 3. Prohibited Directories

The following directories are not the current development root or current code mainline:

- `E:\new\fpga_lock`
- `E:\new\fpga_lock\exp_data`
- `E:\new\fpga_lock\文献阅读`
- `E:\new\fpga_lock\vivado_exp`
- `E:\new\fpga_lock\python_sim`
- `E:\new\fpga_lock\open source`

The current mainline must not use any weifang-related directory. By default, Codex must not read, synchronize, copy, modify, or cite the following as the current mainline:

- `weifang`
- `v-weifang`
- `version-weifang`

If search results contain these names, ignore them unless the user explicitly says this task is a historical comparison.

## 4. GPT / Codex / Claude Code / User Roles

### GPT

GPT is responsible for:

1. Reading the GitHub project and newly generated project files.
2. Understanding the current experiment progress.
3. Generating Codex instructions from the user's experiment goals.
4. Helping judge next experiment wiring, normal observations, and stop conditions.
5. Not directly replacing Codex for local code changes.

### Codex

Codex is responsible for:

1. Reading files under `E:\new\fpga_lock\v94`.
2. Modifying Markdown / RTL / Python according to GPT instructions and user scope.
3. Generating experiment SOPs, code, simulations, and reports.
4. Strictly reporting which files were modified.
5. Not running Vivado by default.
6. Not generating bitstreams by default.
7. Not programming Red Pitaya by default.

### Claude Code

Claude Code is responsible for:

1. Reviewing Codex-generated code.
2. Reviewing RTL timing risks.
3. Reviewing SOP experiment safety risks.
4. Checking whether OUT2 is mistakenly connected to a real actuator.
5. Not acting as the only experiment authority; final validation still requires the user's manual Vivado and oscilloscope checks.

### User

The user is responsible for:

1. Manually opening Vivado.
2. Manually running synthesis and implementation.
3. Manually generating bitstreams.
4. Manually programming Red Pitaya.
5. Manually wiring hardware.
6. Saving oscilloscope screenshots, CSV data, and Vivado timing reports.
7. Reporting experiment observations back to GPT / Codex.

## 5. Default Permission Boundary

By default, Codex must not:

- Run Vivado
- Run synthesis
- Run implementation
- Generate bitstream
- Generate bin
- Program Red Pitaya
- Modify `redpitaya.xpr`
- Modify XDC / SDC
- Touch `weifang`, `v-weifang`, or `version-weifang`

The scope may be expanded only after the user explicitly requests and confirms it.

## 6. Codex Execution Reporting Rule

Before executing a task, Codex must list the files and directories it plans to read and the files it plans to modify when the scope is known.

After executing a task, Codex must list the files it actually read and the files it actually created or modified.

If the task involves Vivado, Codex may only generate a manual operation SOP for the user. Codex must not automatically run Vivado, synthesis, implementation, bitstream generation, bin generation, or Red Pitaya programming unless the user explicitly requests and confirms that expanded scope.
