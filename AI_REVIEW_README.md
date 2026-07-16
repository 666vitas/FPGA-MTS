# FPGA-MTS Agent 入口

本仓库目标是基于 Red Pitaya STEMlab 125-14 逐步实现 MTS 激光稳频系统。当前主分支固定为 `main`；当前项目阶段、代码/测试/GUI/板卡/闭环证据和唯一下一步只以 `version/STATUS.md` 顶部最新记录为准，历史过程查阅现有 `DEVELOPMENT_LOG.md`。

## 必读顺序

新 Codex / Claude Code 窗口不得只依赖聊天历史。先按 `AGENTS.md` 的 `Git Baseline Gate` 执行只读 Git 检查；只有 branch=`main`、working tree clean、无 rebase / merge / cherry-pick 且 `HEAD == origin/main` 才继续。Gate PASS 后按以下顺序读取：

1. `AI_REVIEW_README.md`
2. `AGENTS.md`
3. `version/AI_STRICT_REVIEW_ENTRY.md`
4. `version/CURRENT_REVIEW_MANIFEST.md`
5. `version/STATUS.md` 顶部最新记录
6. 当前任务相关 `DEVELOPMENT_LOG.md` 末尾
7. 当前最新 commit 的 message 与完整 diff
8. 当前任务相关代码和测试

初始 Git Gate PASS 后执行 `git fetch origin` 并再次确认 `HEAD == origin/main`。开发任务按 `AGENTS.md` 的最小修改与分层验证流程执行；只读审查不得修改文件、Git 状态或外部系统。

## 固定阶段与 Gate

```text
Stage 0: Audit
Stage 1: Code
Stage 2: Software Verification
Stage 3: Hardware Verification
Stage 4: Review
```

软件 PASS 不等于项目 PASS。任一 Gate FAIL 都阻止进入下一阶段；没有用户真实硬件实验结果时不得标记 `[USER HARDWARE VERIFIED]`。每次任务只允许一个 `Current Stage`、一个 `Current Gate` 和一个下一步唯一动作；硬件失败先审计证据，不直接猜测修改 RTL。动态 Stage/Gate 和证据等级以 `version/STATUS.md` 顶部、相关 `DEVELOPMENT_LOG.md` 与 `version/HARDWARE_VALIDATION.md` 的一致记录为准。

## 禁止作为当前结论依据的路径

除非用户明确要求回顾历史，否则审查当前状态时禁止把以下路径当作当前 main 结论依据：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
v0.94/redpitaya_laser_lock_project/docs/old/**
**/*.before_*
**/*before*
**/old/**
```

这些路径只能作为历史资料，不能覆盖当前主线判断。

## 审查与安全

严格审查按 `version/AI_STRICT_REVIEW_ENTRY.md` 模板执行，但模板中的旧状态不能覆盖当前代码事实和 STATUS 顶部。结论必须区分代码、自动化、用户 GUI、板卡实验和闭环证据，并给出文件/行号、不能确认的事实、禁止动作及下一步最小安全动作。

默认使用中文记录；路径、命令、寄存器、模块、信号和模式名保留英文。OUT2 接线与实验边界以 `CURRENT_REVIEW_MANIFEST.md` 和 STATUS 顶部为准，异常必须 SAFE。
