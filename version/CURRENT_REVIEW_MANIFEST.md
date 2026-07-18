# CURRENT_REVIEW_MANIFEST

本文件只用于用户明确触发的 GitHub `Review Mode`，不是 Development Mode 启动入口，也不保存当前 Stage、Gate、`VERSION` 或实验参数。

## 固定入口

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Primary RTL root: v0.94/rtl
Primary Vivado project: v0.94/project/redpitaya.xpr
Primary status: version/STATUS.md
Hardware validation: version/HARDWARE_VALIDATION.md
Host root: software/redpitaya_lock_host
Strict review rules: version/AI_STRICT_REVIEW_ENTRY.md
Engineering, safety and evidence rules: version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md
```

Review Mode 可以 fetch、读取 GitHub online、检查 commit/push 状态和比较版本，但禁止修改代码、测试、RTL、Vivado 工程、寄存器、bitstream、文档或项目逻辑。远端失败时报告审查不完整。

## 读取顺序

1. GitHub `main` 的 `version/STATUS.md` 顶部。
2. 与当前问题对应的代码、工程文件和测试。
3. 同一 Gate 的 `version/HARDWARE_VALIDATION.md`、SOP、实验记录和开发日志。
4. `version/AI_STRICT_REVIEW_ENTRY.md` 的审查检查项。

只按问题选择文件，不默认读取全仓库。RTL/Vivado 问题通常从以下文件中选择：

```text
v0.94/project/redpitaya.xpr
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller_seq.sv
v0.94/rtl/pi_controller.sv
v0.94/rtl/error_setpoint_corrector.sv
v0.94/rtl/custom_debug_capture.sv
```

上位机问题只读取 `software/redpitaya_lock_host/` 下直接相关的当前代码、测试和记录。

## 历史排除

以下路径默认不能作为当前 `main` 结论依据：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

它们仅在用户明确询问历史时读取并标记为历史证据。

## 审查完成条件

- 当前代码事实与状态声明分别列明。
- 自动化、GUI、硬件和闭环证据没有混用。
- OUT2/PZT、SAFE、限幅、模式切换及异常停止条件已检查。
- 无法确认的内容明确标记，不把本地缓存当成已刷新远端。
- 只输出报告，不实施修复。
