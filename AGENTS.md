# FPGA-MTS AI Workflow

本文件是 `666vitas/FPGA-MTS` 的本地工程总入口。Codex 是主要工程开发助手，目标是尽快、安全、可验证地实现真实 MTS 激光 PZT 稳频。默认使用中文；路径、命令、寄存器、模块、信号和模式名保留英文。详细规则见 `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`。

## Development Mode（默认）

1. 只以当前本地 workspace 为开发数据源。先读 `version/STATUS.md` 顶部和任务直接相关的代码、测试、SOP、实验记录；以当前代码和最终信号路由核实状态，不用 README、旧日志或旧注释覆盖当前事实。
2. 开始前检查 branch 和 working tree。保护已有修改；已知且不冲突的修改可保留，来源不明或与任务重叠时先停止并报告。
3. 禁止主动执行 `git fetch`、`git pull`、`git ls-remote`，禁止访问 GitHub online、比较 `origin/main` 或等待网络。
4. 只修改用户授权范围，运行与风险相称的本地验证并检查 diff。不自动执行 commit、push、reset、clean、rebase 或 amend。
5. 一次只推进一个当前 Gate。普通任务直接开发和验证；FPGA/MTS 关键任务完成后做一次未参与实现的独立工程复核，只让 `Blocker` 或 `High` 阻止继续。

## 状态、证据与记录

- 当前状态优先级：当前代码、寄存器和最终信号路由 > `version/STATUS.md` 顶部 > 当前 Gate 的最新 SOP/实验记录和 `version/HARDWARE_VALIDATION.md` > 本轮测试 > 历史资料。
- 证据等级只使用 `[IMPLEMENTED]`、`[AUTOMATED VERIFIED]`、`[USER GUI VERIFIED]`、`[USER HARDWARE VERIFIED]`、`[FAILED]`、`[NOT VERIFIED]`。
- 实现、验证或实验改变项目状态时，更新 `version/STATUS.md` 顶部，并在当前版本已有的 `DEVELOPMENT_LOG.md` 追加记录；用户限制文件范围时服从该范围。
- 没有用户真实结果，不得声称 GUI、硬件、锁定、自动重锁或长期稳频通过。

## 硬件边界

- 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream；不运行 Vivado synthesis / implementation，不生成或烧录 bitstream。
- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备；禁止接激光器电流调制、D2-125 Servo/Aux Output 或任何其他有源输出端，禁止有源输出并联。
- 通信、身份、SAFE、saturation、输出范围、跳变、readback、锁点来源、接线、示波器条件或反馈方向异常时，立即停止并请求 SAFE。
- Codex 不自动提高 Kp、恢复或提高 Ki、切换 polarity、扩大 PZT safe range、重新锁定或进入下一实验 Gate。

## Review Mode

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 才进入 Review Mode。该模式按 `AI_REVIEW_README.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 读取 GitHub `main` 并进行只读审查；禁止修改项目文件。普通开发请求中的 `@GitHub` 和 Development Mode 内的一次独立复核都不触发 Review Mode。

## 交接

只需报告：修改文件及原因、实际测试结果、未修改边界、仍需用户验证的内容和下一步。默认不 commit、不 push。
