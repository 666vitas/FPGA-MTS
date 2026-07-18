# FPGA-MTS AI Workflow

本文件是 `666vitas/FPGA-MTS` 的本地工程总入口。当前唯一目标是在现有 SystemVerilog MTS 信号链上实现 Linien 风格的最小手动锁定：目标谱线选择与扫描方向确认 -> FPGA 原子 scan-to-Kp=0 transition -> 最小非零 Kp -> 基础 P-only。默认使用中文；路径、命令、寄存器、模块、信号和模式名保留英文。详细规则见 `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`。

## 单开发者模式

- 用户是唯一真实硬件实验操作者，也是唯一有权确认硬件 Gate 通过的人；负责接线、示波器、PZT、谱线位置和真实锁定结果。
- Codex 是唯一主要开发者，负责实现、测试、文档和提交前自检；默认不启动 subagent，不创建 Builder/Critic/Evaluator/Supervisor，不以多 Agent 结论作为完成证据。
- 日常开发只需读取本文件、`version/STATUS.md` 顶部、`version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`、`version/CURRENT_REVIEW_MANIFEST.md` 和当前 Gate 的 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md`。

## Development Mode（默认）

1. 只以当前本地 workspace 为开发数据源。先读 `version/STATUS.md` 顶部和任务直接相关的代码、测试、SOP、实验记录；以当前代码和最终信号路由核实状态，不用 README、旧日志或旧注释覆盖当前事实。
2. 开始前检查 branch 和 working tree。保护已有修改；已知且不冲突的修改可保留，来源不明或与任务重叠时先停止并报告。
3. 禁止主动执行 `git fetch`、`git pull`、`git ls-remote`，禁止访问 GitHub online、比较 `origin/main` 或等待网络。
4. 只修改用户授权范围，运行与风险相称的本地验证并检查 diff。不自动执行 commit、push、reset、clean、rebase 或 amend。
5. 一次只推进一个当前 Gate。普通任务完成后只做一次同线程自检；只有 OUT2/PZT、模式切换、寄存器 signed/位宽、限幅/saturation 或 FPGA 原子切换等高风险改动才允许一次额外工程审查，不形成多轮或强制多 Agent 循环。

## 状态、证据与记录

- 当前状态优先级：当前代码、寄存器和最终信号路由 > `version/STATUS.md` 顶部 > 当前 Gate 的最新 SOP/实验记录和 `version/HARDWARE_VALIDATION.md` > 本轮测试 > 历史资料。
- 软件、仿真和硬件证据必须分开；证据等级只使用 `[IMPLEMENTED]`、`[AUTOMATED VERIFIED]`、`[USER GUI VERIFIED]`、`[USER HARDWARE VERIFIED]`、`[FAILED]`、`[NOT VERIFIED]`。
- 实现、验证或实验改变项目状态时，更新 `version/STATUS.md` 顶部，并在当前版本已有的 `DEVELOPMENT_LOG.md` 追加记录；用户限制文件范围时服从该范围。
- 没有用户真实结果，不得声称 GUI、硬件、锁定、自动重锁或长期稳频通过。

## 硬件边界

- 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream；不运行 Vivado synthesis / implementation，不生成或烧录 bitstream。
- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备；禁止接激光器电流调制、D2-125 Servo/Aux Output 或任何其他有源输出端，禁止有源输出并联。
- 通信、身份、SAFE、saturation、输出范围、跳变、readback、锁点来源、接线、示波器条件或反馈方向异常时，立即停止并请求 SAFE。
- Codex 不自动提高 Kp、恢复或提高 Ki、切换 polarity、扩大 PZT safe range、重新锁定或进入下一实验 Gate。基础 P-only 未通过前禁止 PI、自动重锁、完整自动锁定、AI 优化、大量 GUI 扩张或大规模上位机重构。

## Review Mode

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 才进入 Review Mode。该模式按 `version/CURRENT_REVIEW_MANIFEST.md` 读取 GitHub `main` 并进行只读审查；禁止修改项目文件。普通开发请求中的 `@GitHub` 和 Development Mode 内的同线程自检或一次高风险额外审查都不触发 Review Mode。

## 交接

只需报告：修改文件及原因、实际测试结果、未修改边界、仍需用户验证的内容和下一步。默认不 commit、不 push。
