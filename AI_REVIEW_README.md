# FPGA-MTS AI 入口

本仓库默认采用 `Development Mode`。完整行为边界见 `AGENTS.md`。

## Development Mode（默认）

```text
Data source: Current local workspace
Remote access: disabled
Goal: local development and experiment support
```

新任务直接读取：

1. `AGENTS.md`
2. `version/STATUS.md` 顶部当前状态
3. 本任务直接相关的本地代码、测试和文档

Development Mode 不要求 Git Gate，不主动 fetch/pull，不比较 `origin/main`，也不因 GitHub 或网络不可用而阻塞本地任务。完成后给出修改、原因、测试和后续动作，等待用户决定 commit。

## Review Mode

仅当用户明确输入 `@GitHub 审计` 或 `审查最新main` 时启用。

Review Mode 可以访问 GitHub、fetch 并比较版本，但只能审查，禁止修改项目文件。进入后读取：

1. `AGENTS.md` 的 Review Mode 规则
2. `version/CURRENT_REVIEW_MANIFEST.md`
3. `version/STATUS.md` 顶部
4. `version/AI_STRICT_REVIEW_ENTRY.md`
5. Manifest 指定的当前代码与记录

远端访问失败只影响本次 Review，不改变 Development Mode 的本地开发能力。

## 本地事实与历史资料

Development Mode 以当前 workspace 为准。Review Mode 判断 GitHub `main` 时，禁止把以下历史路径当作当前主线：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

动态项目状态看 `version/STATUS.md` 顶部；历史过程看现有 `DEVELOPMENT_LOG.md`。`version/AI_STRICT_REVIEW_ENTRY.md` 只用于 Review Mode，其中旧文字或冲突不得覆盖当前代码和 STATUS。

## 安全边界

默认不修改 RTL、Vivado、寄存器语义或 bitstream，不运行 Vivado。OUT2、SCAN、P_LOCK、LOCK HERE、PZT 相关异常必须停止并 SAFE。软件、GUI、硬件和闭环证据必须分开表述。
