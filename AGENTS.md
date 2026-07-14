# Agent Working Rules

本文件是 `666vitas/FPGA-MTS` 的 Codex 与 Claude Code 共用接管、修改、记录和实验交接入口。项目说明、状态和日志默认使用中文；路径、命令、寄存器、模块和模式名保持英文原文。

## 执行者与接管

1. Codex 是默认执行 Agent。
2. Claude Code 只在 Codex 额度不足，或用户明确指定 Claude Code 时接管。
3. 接管不改变项目架构、版本主线、文档模式、任务范围或安全边界；Claude Code 与 Codex 使用完全相同的本文件流程。
4. 每次只完成用户指定的一个任务。不得借机重新规划项目、引入新主线、扩大修改范围，或修改未获授权的文件。

## 每次开始前

1. 读取 `AI_REVIEW_README.md`、`version/AI_STRICT_REVIEW_ENTRY.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md`、`version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md`。
2. 读取当前 `git branch --show-current`、`git rev-parse HEAD`、`git status --short --branch`，并读取任务关联文件和现有 `DEVELOPMENT_LOG.md`。
3. `version/STATUS.md` 是当前状态快照；已有 `DEVELOPMENT_LOG.md` 是按时间追加的历史记录。历史日志不能覆盖当前状态快照。
4. 发现冲突、合并标记、旧结论或未经证实的说法时，先在本轮允许修改的状态/记录文档中隔离并说明；未经用户授权不得顺手改动范围外文件。

## 修改与记录

1. 只修改用户明确允许的文件。保留工作区既有改动，不回退、不覆盖、不混入无关重构。
2. 每次修改完成后，更新 `version/STATUS.md` 顶部的当前状态快照。
3. 每次修改完成后，向当前版本已有的 `DEVELOPMENT_LOG.md` 文件末尾追加历史记录；涉及上位机时，也向已有 `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md` 文件末尾追加。
4. 未得到用户实验反馈时，只能写“代码完成但等待验证”或“等待验证”，不得写成硬件、锁定或长期稳定性已经通过。
5. 纯 GUI/上位机修改与 FPGA RTL、Vivado、bitstream、烧录是不同验证层级。没有改动 RTL、Vivado 工程、寄存器语义或 bitstream 时，不得要求或声称需要重新 Vivado、生成 bitstream 或烧录。

## 工具与实验边界

1. Agent 不运行 Vivado、不生成 bitstream、不烧录；这些操作仅由用户在明确授权和安全条件满足时手动执行。
2. 不得改变寄存器地址或语义、RTL 架构、版本主线或既有安全边界，除非用户对该单项明确授权。
3. 涉及 `OUT2`、`SCAN`、`P_LOCK` 或 `LOCK HERE` 时，完成交接必须给出用户实验操作、PASS/FAIL 判据和必须 SAFE 条件。
4. 发现通信失败、寄存器身份不匹配、saturation、输出越界、异常跳变、反馈方向疑似错误或用户准备连接禁止端口时，必须要求停止并执行 SAFE；不得自动提高 Kp、自动切换 polarity 或自动重新锁定。

## 提交纯净性

每次准备提交前必须依次检查：

```text
git status --short
git diff --name-only
git diff --cached --name-only
```

文档或 Python 任务不得混入 Vivado 自动生成 metadata、`.jou`、`.log`、cache、usage statistics、临时文件或与本任务无关的修改。发现无关文件时，不得删除用户文件、不得覆盖用户修改；只从本次 staged commit 中排除，并在交接结果中如实报告。

## 完成交接

完成时说明：实际修改文件、验证结果与未运行项、用户下一步实验操作、PASS/FAIL 判据、必须 SAFE 条件，以及下一步唯一任务。没有用户实验反馈时，结论必须止于“等待验证”。

## Project Skill（已移除）

项目不再使用自定义 Agent skill。Agent 应直接遵守本文件、AI_STRICT_REVIEW_ENTRY.md、STATUS.md 和现有规则文件。
