# FPGA-MTS AI 入口

本仓库采用两种互斥模式。共同的 Gate、任务分级、证据和安全规则见 `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`。

## Development Mode（默认）

数据源是当前本地 workspace，用于开发、测试、文档和实验支持。

开始时只需读取：

1. `AGENTS.md`。
2. `version/STATUS.md` 顶部当前状态。
3. 本任务直接相关的代码、测试、SOP 和实验记录。

Development Mode 不访问远端、不要求 Git Gate、不比较 `origin/main`。按用户范围修改并验证，完成后等待用户决定是否 commit 或上传。

## Review Mode

仅当用户明确输入 `@GitHub 审计` 或 `审查最新main` 时启用。普通开发请求中的 `@GitHub` 不自动触发。

Review Mode 的数据源是 GitHub `main`，只做版本、代码和证据审查，不修改任何项目文件。依次读取：

1. `AGENTS.md` 的 Review Mode 边界。
2. `version/CURRENT_REVIEW_MANIFEST.md`。
3. GitHub `main` 中 `version/STATUS.md` 的顶部。
4. `version/AI_STRICT_REVIEW_ENTRY.md`。
5. Manifest 指定且与问题相关的当前代码、测试和记录。

远端不可用时报告本次审查不完整，不影响之后的本地 Development Mode。

## 事实边界

- 动态状态以 `version/STATUS.md` 顶部和同一 Gate 的有效记录为准。
- 历史路径只能回答历史问题，不得覆盖当前代码和状态。
- 软件、仿真、GUI、bitstream、真实输出、loaded PZT、闭环和长期稳频证据必须分开。
- Review Mode 只交付审查报告；修复需要另行授权 Development Mode 任务。
