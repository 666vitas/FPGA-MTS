# Agent Working Rules

本文件是 `666vitas/FPGA-MTS` 的 Codex 与 Claude Code 共用接管、修改、记录和实验交接入口。项目说明、状态和日志默认使用中文；路径、命令、寄存器、模块和模式名保持英文原文。

## 执行者与接管

1. Codex 是默认执行 Agent。
2. Claude Code 只在 Codex 额度不足，或用户明确指定 Claude Code 时接管。
3. 接管不改变项目架构、版本主线、文档模式、任务范围或安全边界；Claude Code 与 Codex 使用完全相同的本文件流程。
4. 每次只完成用户指定的一个任务。不得借机重新规划项目、引入新主线、扩大修改范围，或修改未获授权的文件。

## Git Baseline Gate

每个新 Codex / Claude Code 窗口必须先执行 Git Gate，再读取项目入口；不得只依赖聊天历史。先记录：

```text
git status -sb
git status
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git log -1 --oneline
```

只有同时满足以下条件才允许继续：branch 为 `main`、working tree clean、无 rebase / merge / cherry-pick 状态、`HEAD == origin/main`。初始 Gate PASS 后执行 `git fetch origin`，再复核 `HEAD == origin/main`；远端变化、身份不明或原因不清楚时停止并报告。

出现 detached HEAD、interactive rebase in progress、merge conflict、来源不明的未提交修改，或 `HEAD` 与 `origin/main` 不一致且原因不清楚时，必须停止，不得自行执行 `git rebase --continue`、`git rebase --abort`、`git reset --hard`、`git clean` 或 `git commit --amend`。

如果终端已经显示 `Successfully rebased and updated refs/heads/main.`，随后 `git status` 显示正常 `main`，且 `git rebase --continue` 显示 `no rebase in progress`，表示 rebase 已结束，不是错误；不得继续尝试 rebase。保险分支只作为恢复点，不影响正常 `main` Gate。

## 每次开始前

1. Git Gate PASS 后，依次读取 `AI_REVIEW_README.md`、`AGENTS.md`、`version/AI_STRICT_REVIEW_ENTRY.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md` 顶部和相关 `DEVELOPMENT_LOG.md` 末尾，再读取最新 commit、任务关联代码与测试。
2. 执行并记录 `git fetch origin` 后的 branch、HEAD、`origin/main`、工作区和 rebase / merge / cherry-pick 状态，以及 `git diff --name-only`、`git diff --cached --name-only` 和 `git log -3 --oneline`。
3. `version/STATUS.md` 是当前状态唯一权威快照；`DEVELOPMENT_LOG.md` 是只追加的历史记录。历史日志和严格审查模板不能覆盖当前代码事实与 STATUS 顶部。
4. 开始修改前明确当前阶段、已有功能、缺失项、允许/禁止文件、完成标准和本轮不进入的下一阶段。
5. 发现未提交修改、rebase/merge、冲突标记、旧结论或未经证实的说法时，先保护并报告；未经用户授权不得改变或清理这些状态。

## 证据等级

项目状态只使用以下等级：

- `[IMPLEMENTED]`：代码、文档或操作入口存在，尚未完成对应验证。
- `[AUTOMATED VERIFIED]`：本轮实际执行 `pytest`、`py_compile`、`tabnanny` 等并通过。
- `[USER GUI VERIFIED]`：用户已在真实 Windows GUI 或真实 Red Pitaya 数据中操作并提供明确结果。
- `[USER HARDWARE VERIFIED]`：用户已完成真实接线与物理实验，并提供对应测量结果。
- `[FAILED]`：当前 Gate 已有明确失败证据，必须停止推进。
- `[NOT VERIFIED]`：尚未执行或证据不足。

没有真实硬件结果时，硬件结论只能是 `[IMPLEMENTED]`、`[AUTOMATED VERIFIED]` 或 `[NOT VERIFIED]`；`[USER GUI VERIFIED]` 只证明 GUI 操作，不证明物理电压或硬件 Gate。尚未准备或执行的未来硬件 Gate 统一标记 `[NOT VERIFIED]`，不得用计划标签伪装进度。禁止把代码存在写成测试通过，把 mock/自动化测试写成真实 GUI 或硬件验证，把波形显示或 Kp=0 切换写成闭环锁定成功，把短时现象写成长时间稳频成功。

## 固定开发阶段与 Gate

项目开发固定按以下顺序推进：

```text
Stage 0: Audit
Stage 1: Code
Stage 2: Software Verification
Stage 3: Hardware Verification
Stage 4: Review
```

软件测试通过只完成 Stage 2，不等于项目阶段通过。任一 Gate 为 `[FAILED]` 时不得进入下一大阶段；硬件实验失败后必须先审计接线、寄存器 readback、测量条件和证据，不得直接猜测并修改 RTL。

每次任务只能记录一个 `Current Stage`、一个 `Current Gate` 和一个“下一步唯一动作”。`version/STATUS.md`、相关 `DEVELOPMENT_LOG.md` 与 `version/HARDWARE_VALIDATION.md` 的 Stage、Gate 和证据等级必须一致。

## 修改与记录

1. 只修改用户明确允许的文件。保留工作区既有改动，不回退、不覆盖、不混入无关重构。
2. 每次修改完成后，更新 `version/STATUS.md` 顶部的当前状态快照。
3. 每次修改完成后，向当前版本已有的 `DEVELOPMENT_LOG.md` 文件末尾追加历史记录；涉及上位机时，也向已有 `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md` 文件末尾追加。
4. 未得到用户实验反馈时，只能写“代码完成但等待验证”或“等待验证”，不得写成硬件、锁定或长期稳定性已经通过。
5. 纯 GUI/上位机修改与 FPGA RTL、Vivado、bitstream、烧录是不同验证层级。没有改动 RTL、Vivado 工程、寄存器语义或 bitstream 时，不得要求或声称需要重新 Vivado、生成 bitstream 或烧录。
6. `AGENTS.md` 只记录长期稳定规则；`AI_REVIEW_README.md` 只作为项目入口；`CURRENT_REVIEW_MANIFEST.md` 只记录当前权威审查范围；动态状态只写 `STATUS.md` 顶部；具体过程只追加到 `DEVELOPMENT_LOG.md`。
7. `version/AI_STRICT_REVIEW_ENTRY.md` 只作为严格审查模板，其中的旧文字或冲突不得覆盖 STATUS 顶部与当前代码事实。

## 最小开发与分层验证

1. 只修改本轮目标所需文件；禁止顺便重构、全文件格式化、测试数据特判、删除/skip/xfail 安全测试或降低安全检查。
2. 验证必须依次执行：`tabnanny`、`py_compile`、`pytest --collect-only`、targeted pytest、当前测试文件、完整 software tests、`git diff --check`。
3. 任一级失败时停止扩大范围，只修复该级真实错误；只有全部实际验证完成后才能把准确命令和结果写入 STATUS 与日志。
4. 未经用户授权不运行 Vivado、不生成或烧录 bitstream、不修改 RTL、寄存器地址/语义、`MAGIC` 或 `VERSION`。

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

完成时输出标准交接包：任务名称；仓库/branch/initial HEAD/final HEAD/origin/main/工作区；实际读取文件；任务边界；修改文件及关键变化；根因；当前上位机能力；整个项目进度；证据等级表；完整测试命令与真实结果；用户已验证与未验证内容；未修改边界；阶段结论；下一步唯一动作；新窗口启动说明。没有用户实验反馈时，结论必须止于“等待验证”。

新窗口启动说明统一为：读取 `AI_REVIEW_README.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md` 顶部、`AGENTS.md` 和相关 `DEVELOPMENT_LOG.md` 末尾，然后根据上一交接包继续当前唯一动作。

## Project Skill（已移除）

项目不再使用自定义 Agent skill。Agent 应直接遵守本文件、AI_STRICT_REVIEW_ENTRY.md、STATUS.md 和现有规则文件。
