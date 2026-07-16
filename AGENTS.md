# FPGA-MTS AI Workflow

本文件是 `666vitas/FPGA-MTS` 的 Codex 与 Claude Code 共用工作规则。默认使用中文记录；路径、命令、寄存器、模块和模式名保留英文原文。

## Default Mode

`Development Mode` 是默认模式。

```text
Data source: Current local workspace
Default workspace: E:\new\fpga_lock\v94
Remote access: disabled unless Review Mode is explicitly requested
Goal: complete local development, testing, documentation, and experiment support
```

### Development Mode 行为

1. 只以当前本地 workspace 文件为开发依据；开始前读取 `version/STATUS.md` 顶部和本任务直接相关的本地代码、测试、文档。
2. 禁止主动执行 `git fetch`、`git pull`、`git ls-remote`，禁止读取 GitHub online、比较 `origin/main` 或等待网络。
3. 可以按用户明确范围修改代码、测试和文档，并运行本地命令、测试和只读 Git 检查。
4. 本地存在未提交修改时先识别来源并保护；已知且不冲突的本地修改不阻塞开发。遇到来源不明或与任务重叠的改动时停止并报告。
5. 不自动 commit、push、reset、clean、rebase 或 amend。完成后报告修改文件、修改原因、实际测试结果和后续动作，等待用户决定是否 commit。

## Review Mode

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 时，才进入 `Review Mode`。

```text
Data source: GitHub main
Goal: inspect repository version, commit, push state, and project status
Mutation: audit only
```

### Review Mode 行为

1. 允许执行 `git fetch`、检查 `origin/main`、commit、push 状态和版本差异，也允许读取 GitHub online。
2. 按 `AI_REVIEW_README.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 执行审查；远端不可用时报告审查不完整，不把网络问题扩散到 Development Mode。
3. 禁止修改代码、测试、RTL、Vivado 工程、寄存器、bitstream 和项目逻辑；只输出审查报告。
4. Review Mode 不会因发现问题自动切换为开发。需要修复时，等待用户另行授权 Development Mode 任务。

## Development != Review

- Development Mode 解决当前本地任务，默认不关心远端是否最新。
- Review Mode 判断 GitHub `main` 和版本状态，不实施修复。
- 用户没有明确触发 Review Mode 时，一律按 Development Mode 继续本地工作。

## 修改与记录

1. 每次只完成用户指定任务，只修改明确允许的文件；保留既有改动，不混入无关重构。
2. `version/STATUS.md` 顶部保存当前项目状态；实现、验证或实验改变项目状态时同步更新。过程记录追加到当前版本已有的 `DEVELOPMENT_LOG.md`；若用户限制可修改文件，以用户范围为准。
3. 软件存在不等于软件验证，软件验证不等于 GUI、硬件或闭环验证。没有用户真实结果时不得声称硬件、锁定或长期稳定性通过。
4. 证据等级使用 `[IMPLEMENTED]`、`[AUTOMATED VERIFIED]`、`[USER GUI VERIFIED]`、`[USER HARDWARE VERIFIED]`、`[FAILED]`、`[NOT VERIFIED]`，不得抬高证据等级。

## 本地验证

1. 验证范围与修改风险相称；不得删除、skip、xfail 或弱化既有安全测试。
2. Python 修改至少依次运行相关 `tabnanny`、`py_compile`、`pytest --collect-only`、targeted pytest、当前测试文件和完整 software tests。
3. 规则或纯文档修改至少运行 `git diff --check`，并按用户要求检查 `git diff --stat` 和 `git diff`。
4. 任何验证失败都必须如实报告，不得写成 PASS。

## RTL、Vivado 与硬件安全边界

1. 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。
2. Agent 不运行 Vivado synthesis / implementation，不生成或烧录 bitstream。
3. 涉及 OUT2、SCAN、P_LOCK、LOCK HERE 或 PZT 时，交接必须写明操作、PASS/FAIL 和 SAFE 条件。
4. 通信失败、身份不匹配、saturation、输出越界、异常跳变、反馈方向疑似错误或有源输出并联风险时，立即停止并要求 SAFE；不得自动提高 Kp、切换 polarity 或重新锁定。

## 完成交接

Development Mode 完成后只需清楚输出：

- 修改文件
- 修改原因
- 测试命令与真实结果
- 未修改边界
- 后续动作

默认不 commit、不 push，等待用户审核。
