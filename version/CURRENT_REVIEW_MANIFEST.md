# CURRENT_REVIEW_MANIFEST

本文件列出当前有效代码、测试和文档边界。Development Mode 可用它避免误读历史；只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 时才允许访问 GitHub `main`，且只读不修改。

## 当前有效根目录

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
RTL: v0.94/rtl/**
Simulation: v0.94/sim/**
Vivado project: v0.94/project/redpitaya.xpr
Host code: software/redpitaya_lock_host/redpitaya_lock_host/**
Host scripts: software/redpitaya_lock_host/scripts/**
Host tests: software/redpitaya_lock_host/tests/**
```

只读取与当前 Gate 或问题直接相关的文件，不默认全仓审查。

## 当前有效文档

```text
AGENTS.md
version/STATUS.md
version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md
version/CURRENT_REVIEW_MANIFEST.md
version/HARDWARE_VALIDATION.md
software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md
software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md
```

其他 SOP 或实现说明只有在 `version/STATUS.md` 顶部明确指向或与当前问题直接相关时才读取。`AI_REVIEW_README.md` 和 `version/AI_STRICT_REVIEW_ENTRY.md` 是历史兼容入口，不是当前规则源。

## 历史排除

以下路径默认只能作为历史证据，不能决定当前 Stage、Gate、接线、参数或完成状态：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
version/v3/**
**/old/**
**/*.before_*
**/*before*
```

`version/rules/` 中除 `20_FPGA_MTS_ENGINEERING_WORKFLOW.md` 外的文件均为 `HISTORICAL / NOT ACTIVE`。

## Review Mode 完成边界

- 只报告 GitHub `main` 中实际取得的当前代码、测试和证据。
- 自动化、GUI、硬件和闭环证据分别列出。
- 无法确认的内容明确标记，不使用本地缓存冒充远端。
- 只输出报告，不实施修复，不启动多轮或多角色审查。
