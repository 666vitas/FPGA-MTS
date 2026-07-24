Status: ACTIVE
Effective-Gate: LOCK-MVP-T0
Authority: MANIFEST
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: NONE

# CURRENT REVIEW MANIFEST

Current Gate: `LOCK-MVP-T0 / Timing-Clean Minimal Build`

本文件只定义当前强制读取集合、当前代码范围和默认排除范围，不保存动态 timing 结论。禁止按 Windows 修改日期、Git 时间或文件名日期推断权威性。

## Mandatory

按顺序读取：

1. `AGENTS.md` — 唯一根入口与长期安全规则。
2. `version/CURRENT_GATE.md` — 当前唯一 Gate、范围和验收条件。
3. `version/STATUS.md` — 当前事实、blocker 和唯一下一动作。
4. `version/CURRENT_REVIEW_MANIFEST.md` — 当前文件边界。
5. `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md` — 唯一 active 工程规则。
6. `docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md` — active architecture spec；权威低于 `CURRENT_GATE`。

## Current code scope

当前 Gate 只将以下代码/测试视为直接范围；本轮文档整理不修改它们：

```text
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/sim/tb_custom_register_bank_basic.sv
v0.94/sim/tb_deterministic_lock_acquisition.sv
v0.94/sim/tb_out2_lock_controller.sv
software/redpitaya_lock_host/tests/**
```

`out2_lock_controller` 和 `deterministic_lock_acquisition` 当前定义位置必须从实际 RTL source/file-set 核对，不能因旧文档中的独立文件名而假设存在单独 `.sv` 文件。

## Supporting

```text
README.md
docs/process/**
docs/hardware/**
```

Supporting 文档可以提供操作背景、迁移方案和历史硬件证据，但不能覆盖 `CURRENT_GATE`、`STATUS` 或 active rule/spec。

## Excluded by default

只有用户明确要求历史追溯时才读取：

```text
version/history/**
version/v1/**
version/v2/**
version/v3/**
version/v4/**
version/v5/**
version/rules/00_*.md
version/rules/01_*.md
version/rules/02_*.md
version/rules/03_*.md
version/rules/04_*.md
version/rules/05_*.md
version/rules/06_*.md
version/rules/RULE_*.md
v0.94/redpitaya_laser_lock_project/docs/old/**
*_PROPOSED.md
*_PACKAGE.md
*_RESTORED.md
**/*.before_*
**/*backup*
legacy review files
```

`version/v1` 至 `version/v5` 全部属于 `HISTORY`，默认任务禁止读取；文件时间、复制时间或名称中的日期不能使其重新成为 active。

## Review Mode boundary

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 才允许访问 GitHub，并且只读。普通 Development Mode 不主动 fetch/pull/ls-remote，不用远端覆盖本地 current Gate。
