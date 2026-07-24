Status: ACTIVE
Effective-Gate: ALL
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: NONE
Superseded-By: NONE

# FPGA-MTS Document Index

本索引说明文档用途、权威层级、移动/删除结果和全仓 Markdown 分类规则。禁止根据 Windows 修改日期、Git 时间或文件名中的日期判断哪个文件最新。

## 1. 当前唯一入口

| Category | Path | 用途 |
|---|---|---|
| `ACTIVE_ENTRY` | `AGENTS.md` | 唯一根入口、永久安全和冲突优先级 |
| `ACTIVE_GATE` | `version/CURRENT_GATE.md` | 当前唯一 Gate |
| `ACTIVE_GATE` | `version/STATUS.md` | 当前事实、blocker 和唯一下一动作 |
| `ACTIVE_ENTRY` | `version/CURRENT_REVIEW_MANIFEST.md` | 强制读取集合和排除范围 |
| `ACTIVE_ENTRY` | `version/DOCUMENT_INDEX.md` | 文档分类、移动和删除索引 |

## 2. 当前唯一 Gate

`LOCK-MVP-T0 / Timing-Clean Minimal Build`

唯一 Gate 的目标、范围和验收条件只看 `version/CURRENT_GATE.md`。其他文件中的“当前 Gate”“下一步”或 timing 数值不能覆盖它。

## 3. Active rules

| Category | Path | 用途 |
|---|---|---|
| `ACTIVE_RULE` | `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md` | 单 Gate、build、timing、证据和硬件安全工作流 |

`version/rules/` 中其他 Markdown 全部为 `HISTORY`，默认不读取。

## 4. Active architecture spec

| Category | Path | 用途 |
|---|---|---|
| `ACTIVE_SPEC` | `docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md` | Linien-inspired 最小 P-only 长期说明书 |

spec 的权威低于 `CURRENT_GATE`、`STATUS`、manifest 和 active rule。

## 5. Supporting docs

| Category | Path / pattern | 用途 |
|---|---|---|
| `SUPPORTING` | `README.md` | 面向用户的简洁项目入口 |
| `SUPPORTING` | `docs/process/CODEX_RULES_REORGANIZATION_PLAN.md` | 规则整理和后续 Host/FPGA 迁移方案 |
| `SUPPORTING` | `docs/architecture/HOST_APP_INTEGRATION.md` | Host 集成背景 |
| `SUPPORTING` | `docs/hardware/**` | 硬件 SOP、校准和验证记录 |
| `SUPPORTING` | `docs/experiment_logs/**` | 真实实验日志 |
| `SUPPORTING` | `software/redpitaya_lock_host/README.md` | Host 使用入口 |
| `SUPPORTING` | `software/redpitaya_lock_host/docs/*.md` | Host 设计、操作、测试和开发记录；旧 review/report 例外归为 HISTORY |
| `SUPPORTING` | `.agents/skills/**` | 本地 skill 指令；不能覆盖项目规则 |

`docs/process/PROJECT_AI_FPGA_WORKFLOW.md`、`docs/process/PROJECT_DIRECTORY_AND_WORKFLOW_RULES.md` 和 `docs/architecture/PROJECT_PAPER_ORIENTED_ROADMAP.md` 的文件头为 `Status: HISTORY`，因此不属于 active/supporting 决策入口。

## 6. History / Excluded

以下有序规则对仓库中每个 Markdown 分类；先匹配 exact active/supporting 表，再应用本表。任何未被前述 active/supporting exact path 命中的 Markdown，若匹配以下 pattern，均为 `HISTORY` 或明确的 `DELETE_CANDIDATE`。

| Category | Path / pattern | 说明 |
|---|---|---|
| `HISTORY` | `version/history/**` | 旧 Gate、状态、review、root legacy、imports、skills |
| `HISTORY` | `version/v1/**` 至 `version/v5/**` | 版本历史；默认任务禁止读取 |
| `HISTORY` | `version/productization/**` | 长期产品化草案 |
| `HISTORY` | `version/目标/**` | 旧研究目标 |
| `HISTORY` | `version/rules/*.md`，但排除 active `20_...` | 旧规则 |
| `HISTORY` | `v0.94/redpitaya_laser_lock_project/docs/**` | 旧嵌套工程说明、报告和教程 |
| `HISTORY` | `v0.94/redpitaya_laser_lock_project/experiment_logs/**` | 旧嵌套实验日志 |
| `HISTORY` | `v0.94/redpitaya_laser_lock_project/scripts/*.md` | 旧构建笔记 |
| `HISTORY` | `software/redpitaya_lock_host/docs/*REVIEW*.md` | 旧 review |
| `HISTORY` | `software/redpitaya_lock_host/docs/*REPORT*.md` | 旧 takeover/report |
| `HISTORY` | `docs/process/*.md` 且文件头为 `Status: HISTORY` | superseded 流程 |
| `HISTORY` | `docs/architecture/*.md` 且文件头为 `Status: HISTORY` | 论文/长期旧路线 |
| `HISTORY` | `software/.venv/**`、`software/redpitaya_lock_host/.venv/**` | vendor license/readme，不是项目规则 |
| `DELETE_CANDIDATE` | `.pytest_cache/**`、`software/redpitaya_lock_host/.pytest_cache/**` | 生成缓存；本轮未删除 |
| `HISTORY` | 其余未被 active/supporting 表列出的 `**/*.md` | 保守默认，防止新副本因日期或命名自动变为 active |

`version/v1-v5`、历史 review、备份副本、`*_PROPOSED.md`、`*_PACKAGE.md`、`*_RESTORED.md` 全部默认 excluded。只有用户明确要求历史追溯时才读取。

## 7. 移动与归档

| 原路径 | 新路径 | 分类与原因 |
|---|---|---|
| `CURRENT_GATE_PROPOSED.md` | `version/CURRENT_GATE.md` | `ACTIVE_GATE`；正式化当前唯一 Gate |
| `FPGA_MTS_Linien_Basic_Lock_Project_Spec.md` | `docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md` | `ACTIVE_SPEC`；移出根目录 |
| `CODEX_RULES_REORGANIZATION_PLAN.md` | `docs/process/CODEX_RULES_REORGANIZATION_PLAN.md` | `SUPPORTING` |
| `docs/HOST_APP_INTEGRATION.md` | `docs/architecture/HOST_APP_INTEGRATION.md` | `SUPPORTING` 架构背景 |
| `version/HARDWARE_VALIDATION.md` | `docs/hardware/HARDWARE_VALIDATION.md` | `SUPPORTING`；保留真实硬件证据 |
| `version/PROJECT_AI_FPGA_WORKFLOW.md` | `docs/process/PROJECT_AI_FPGA_WORKFLOW.md` | `HISTORY`；保留旧分层依据 |
| `version/PROJECT_DIRECTORY_AND_WORKFLOW_RULES.md` | `docs/process/PROJECT_DIRECTORY_AND_WORKFLOW_RULES.md` | `HISTORY`；有效规则已合并到 AGENTS |
| `version/PROJECT_PAPER_ORIENTED_ROADMAP.md` | `docs/architecture/PROJECT_PAPER_ORIENTED_ROADMAP.md` | `HISTORY`；保留论文路线 |
| `GPT_README.md` | `version/history/root_legacy/GPT_README.md` | `HISTORY`；旧读取入口含独立历史判断 |
| `version/AI_STRICT_REVIEW_ENTRY.md` | `version/history/reviews/AI_STRICT_REVIEW_ENTRY.md` | `HISTORY` |
| `docs/review_d2_125_pid_replacement.md` | `version/history/reviews/review_d2_125_pid_replacement.md` | `HISTORY`；保留 RTL 设计判断 |
| `version/history/CURRENT_MAINLINE_REVIEW_LEGACY.md` | `version/history/root_legacy/CURRENT_MAINLINE_REVIEW_LEGACY.md` | `HISTORY` |
| `version/history/SKILL_USAGE_GUIDE_LEGACY.md` | `version/history/root_legacy/SKILL_USAGE_GUIDE_LEGACY.md` | `HISTORY` |
| `software/redpitaya_lock_host/docs/experiment_logs/experiment_log_20260630_203915.md` | `docs/experiment_logs/experiment_log_20260630_203915.md` | `SUPPORTING`；集中真实实验日志 |

原 D1 `STATUS` 已完整保存到 `version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md`，避免当前 Gate 重写丢失实现、仿真和 timing 依据。

## 8. 已删除重复文档

| Path | 原分类 | 删除理由 |
|---|---|---|
| `AGENTS_PROPOSED.md` | `DUPLICATE` | 有效内容已合并到正式 `AGENTS.md` |
| `FPGA_MTS_CODEX_RULES_PACKAGE.md` | `DUPLICATE` | 是 AGENTS/CURRENT_GATE/reorganization plan 的逐字合并包，不含独立信息 |
| `docs/CODEX_RULES_REORGANIZATION_PLAN.md` | `DUPLICATE` | 与移动到 `docs/process/` 的文件 SHA-256 完全一致 |
| `AI_REVIEW_README.md` | `DELETE_CANDIDATE` | 仅为旧入口跳转，规则已由 AGENTS/manifest 完整覆盖 |
| `CURRENT_MAINLINE_REVIEW.md` | `DELETE_CANDIDATE` | 仅指向已归档 legacy 正文 |
| `SKILL_USAGE_GUIDE.md` | `DELETE_CANDIDATE` | 仅指向已归档 legacy 正文 |

这些删除均不包含独立实验记录、Vivado 报告、硬件数据、寄存器演变或未吸收的设计依据，并可从 Git 历史或本轮 diff 恢复。

## 9. Pre-existing working-tree changes

本轮开始前 `v0.94/red_pitaya_laser_lock_code_map.md` 已处于删除状态；多份 `.rpt` 也已由用户删除。文档整理没有恢复、覆盖或扩大这些既有修改。原 `v0.94/FPGA_MTS_Linien_Basic_Lock_Project_Spec.md` 的内容与用户放在根目录的 spec blob 完全一致，现统一归入 active spec 路径。
