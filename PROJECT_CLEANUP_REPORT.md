# PROJECT_CLEANUP_REPORT

- 审计日期：2026-09-04
- 审计范围：`E:\new\fpga_lock\v94`
- 扫描口径：递归扫描文件系统中的全部 `*.md`，包含隐藏目录、被 ignore 的虚拟环境/缓存和第三方参考目录。
- 扫描快照：生成本报告前共发现 **175** 个 Markdown 文件；本报告是扫描后的冻结审计产物，不计入这 175 个文件。
- 执行边界：本次不删除文件，不修改 RTL、Vivado 工程、XDC/Tcl、Host 源码或实验原始数据；不运行 Vivado、仿真或板卡操作。

## 分类定义

- `ACTIVE`：当前可作为工作依据的文档；在保留清单中以 `KEEP` 表示。
- `ARCHIVE`：历史、参考或已被新入口取代的文档；保留原文，不作为当前状态入口。
- `DELETE_CANDIDATE`：重复、缓存、空文件或生成附带物；只记录未来人工确认候选，本次不删除。

## 分类总览（报告生成前）

| 分类 | 数量 | 说明 |
| --- | ---: | --- |
| `ACTIVE` / `KEEP` | 40 | 六个规范入口、根规则、项目 skills、当前 Host 入口及当前 Host supporting 文档 |
| `ARCHIVE` | 116 | 旧嵌套工程文档、历史 Host 文档、第三方/开源参考 |
| `DELETE_CANDIDATE` | 19 | 虚拟环境/pytest 缓存 Markdown、5 个空 Markdown |
| **合计** | **175** | 以本次文件系统快照为准 |

## 唯一权威入口

当前项目状态、接口、开发和发布信息只从 `v94/docs/` 读取。以下六个文件均已确认存在，文件头标为 `Status: ACTIVE`，更新时间为 2026-09-04：

1. `docs/PROJECT_CONTEXT.md` — 项目含义、边界和目录职责。
2. `docs/CURRENT_STATUS.md` — 唯一当前状态和当前 Gate（`LOCK-MVP-L1`）。
3. `docs/CHANGELOG.md` — 工程变更及验证摘要。
4. `docs/HOST_FPGA_INTERFACE.md` — 唯一 Host/FPGA 接口契约。
5. `docs/FPGA_DEVELOPMENT_RULES.md` — FPGA 修改、仿真、Vivado、时序和证据规则。
6. `docs/RELEASE_PROCESS.md` — bit 发布、命名和追溯规则。

上述六个入口的 SHA-256 快照如下，用于冻结时的可追溯核对：

| 文件 | SHA-256 |
| --- | --- |
| `docs/PROJECT_CONTEXT.md` | `F10F6CDD46F77B5A7C4773C927B2B5FE982938DB9A14EC5C6894FD58BCA30F40` |
| `docs/CURRENT_STATUS.md` | `6E961895DF5A5ABB86FBF540DB353999AC228AF05054876EFE67A4D659D3DDBC` |
| `docs/CHANGELOG.md` | `1608E60360F6918DFC9A0CC738215C4999E1FEB1964CB1B024D8D77A44062D05` |
| `docs/HOST_FPGA_INTERFACE.md` | `C3D2834DB09583E2FFE0594013CFA1A25A5D388AD8302C4BEE8B9DB46634AA92` |
| `docs/FPGA_DEVELOPMENT_RULES.md` | `38A4344707ADFEEC10B132428BF862283E68095408FBDE1AB7F6E0FE671DBF43` |
| `docs/RELEASE_PROCESS.md` | `0CB57674BAA47345369C0912FB905A950CBC40EC220D45CD6363B9DD18130A11` |

本报告是用户明确要求的独立冻结审计记录，不是第七个状态入口；不得用它替代 `docs/CURRENT_STATUS.md`。

## KEEP:

### 规范和工具入口（22 + 1 + 6 = 29 个 Markdown）

- `AGENTS.md`：长期安全边界、文档优先级和工作树保护规则。
- `.agents/skills/**/*.md`（22 个）：项目本地 skills；只提供工作方法，不能覆盖 `docs/` 规范。
- `docs/PROJECT_CONTEXT.md`
- `docs/CURRENT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/HOST_FPGA_INTERFACE.md`
- `docs/FPGA_DEVELOPMENT_RULES.md`
- `docs/RELEASE_PROCESS.md`

### 当前 Host 入口及 supporting 文档（11 个）

- `software/redpitaya_lock_host/README.md`：当前 Host 使用入口；不是项目状态权威。
- `software/redpitaya_lock_host/docs/CONNECTION_DIAGNOSIS.md`
- `software/redpitaya_lock_host/docs/FPGA_DETERMINISTIC_LOCK_ACQUISITION.md`
- `software/redpitaya_lock_host/docs/FPGA_MODE_BOUNDARY.md`
- `software/redpitaya_lock_host/docs/HARDWARE_TEST_SOP.md`
- `software/redpitaya_lock_host/docs/HOST_APP_V2_DESIGN.md`
- `software/redpitaya_lock_host/docs/PROJECT_CONTEXT.md`
- `software/redpitaya_lock_host/docs/SCPI_MODE_NOTES.md`
- `software/redpitaya_lock_host/docs/SCPI_SERVER_STARTUP.md`
- `software/redpitaya_lock_host/docs/USAGE.md`
- `software/redpitaya_lock_host/docs/WINDOWS_ENV_SETUP.md`

这些 Host 文档只作为实现/操作 supporting material；其中 `PROJECT_CONTEXT.md` 和 `HOST_APP_V2_DESIGN.md` 的阶段描述可能落后于当前 L1，不能作为状态依据；如与 `v94/docs/` 冲突，始终以 `v94/docs/` 为准。

## ARCHIVE:

ARCHIVE 文件保留，不删除；它们可以用于历史追溯，但不得被当作当前 Gate、当前状态或当前接口入口。

### 当前树中的历史/参考 Markdown（共 116 个）

- `reference/**/*.md`（33 个）：开源项目、上游工程、代码阅读和方案对比；全部为外部参考，不是本项目 authority。
- `software/redpitaya_lock_host/docs/CLAUDE_REVIEW_HOST_APP_V1.md`
- `software/redpitaya_lock_host/docs/CUSTOM_FPGA_LOCK_WORKFLOW.md`
- `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`
- `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md`
- `software/redpitaya_lock_host/docs/HOST_APP_DESIGN.md`
- `software/redpitaya_lock_host/docs/LOADED_PZT_SCAN_SOP.md`
- `software/redpitaya_lock_host/docs/LOCK_WORKFLOW_MODE.md`
- `software/redpitaya_lock_host/docs/NEXT_FPGA_DEBUG_BUFFER_PLAN.md`
- `software/redpitaya_lock_host/docs/TAKEOVER_REPORT_2026-07-15.md`
- `software/redpitaya_lock_host/docs/TEST_PLAN.md`
- `v0.94/redpitaya_laser_lock_project/docs/**/*.md` 中除下方 3 个空文件以外的 73 个文件：`current/`、`old/`、`project_master/`、`reports/`、`beginner_roadmap/`、`learning/`、`integration/`、`board_tests/` 以及旧索引/评审文档。

特别注意：`v0.94/redpitaya_laser_lock_project/docs/project_master/01_CURRENT_STATUS_SUMMARY.md`、`docs/current/**`、`docs/README_DOCS_INDEX.md` 和 `docs/beginner_roadmap/00_README_beginner_roadmap.md` 的内容属于旧 v1ab/D1 时代的状态、规划或索引，即使文件名含 `CURRENT`/`README`，也不覆盖 `v94/docs/CURRENT_STATUS.md`。它们先按 ARCHIVE 保留，待单独归档任务处理。

### 已在工作区归档目录中的旧入口

旧状态文档已经位于工作区级 `E:\new\fpga_lock\archive\obsolete\` 下，不在 `v94` 当前入口中：

- `archive/obsolete/v94_version/current_controls/CURRENT_GATE.md`
- `archive/obsolete/v94_version/current_controls/STATUS.md`
- `archive/obsolete/v94_version/current_controls/CURRENT_REVIEW_MANIFEST.md`
- `archive/obsolete/v94_version/history/README.md`
- `archive/obsolete/v94_version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md`
- `archive/obsolete/v94_version/history/STATUS_HISTORY_THROUGH_2026-07-18.md`
- `archive/obsolete/v94_version/history/root_legacy/GPT_README.md`
- `archive/obsolete/v94_root_docs/README.md`

归档文件内部可能仍保留旧的 `Status: ACTIVE`、旧 Gate 或旧路径文字；“位于 `archive/obsolete/`”这一层级将它们降级为历史材料。不得按文件日期或文件头重新提升为当前入口。

## DELETE_CANDIDATE:

以下仅登记为未来可删除候选，不执行删除、不移动、不清空：

### 缓存/虚拟环境附带 Markdown（14 个）

- `software/.venv/**/*.md`（1 个第三方 license Markdown）。
- `software/redpitaya_lock_host/.venv/**/*.md`（12 个第三方 license Markdown；其中有重复副本）。
- `software/redpitaya_lock_host/.pytest_cache/README.md`（pytest 生成说明）。

### 空文件（5 个）

- `v0.94/redpitaya_laser_lock_project/docs/old/04_scope_asg_pid_reuse_analysis.md`
- `v0.94/redpitaya_laser_lock_project/docs/old/05_mts_demod_architecture.md`
- `v0.94/redpitaya_laser_lock_project/docs/old/07_board_test_sop.md`
- `v0.94/redpitaya_laser_lock_project/experiment_logs/log_001_top_learning.md`
- `v0.94/redpitaya_laser_lock_project/scripts/notes_build_steps.md`

### 重复核对结果

- 上述 5 个空文件共享 SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`，无内容可供当前开发使用。
- `software/redpitaya_lock_host/.venv/Lib/site-packages/pip/_vendor/idna/LICENSE.md` 与 `software/redpitaya_lock_host/.venv/Lib/site-packages/pip-26.1.2.dist-info/licenses/src/pip/_vendor/idna/LICENSE.md` 内容相同。
- `software/redpitaya_lock_host/.venv/Lib/site-packages/numpy/random/LICENSE.md` 与 `software/redpitaya_lock_host/.venv/Lib/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/LICENSE.md` 内容相同。
- 其余报告即使主题相近，也未作自动删除判断；需由人工确认历史证据价值后再处理。

### 非 Markdown 的生成物（仅记录，不计入 175 个 Markdown）

后续可单独审查的生成/缓存目录包括：

- `v0.94/.Xil/`、`v0.94/xsim.dir/`、`v0.94/project/redpitaya.cache/`、`v0.94/project/redpitaya.hw/`、`v0.94/project/redpitaya.ip_user_files/`、`v0.94/project/redpitaya.sim/`。
- `v0.94/exp/**/impl_1/`、`v0.94/exp/**/synth_1/` 及其日志/报告。
- `software/.venv/`、`software/redpitaya_lock_host/.venv/`、`software/redpitaya_lock_host/.pytest_cache/`。
- `reference/guanfang-v0.94/` 中的 Vivado 生成缓存和 run 输出。

这些目录可能被 Vivado 或 Host 工作流引用；本轮不移动、不删除，也不据此判断源码是否可删。

## 旧状态文件检查与移动结果

对 `v94` 当前文件系统按不区分大小写的路径/文件名检查结果：

| 检查项 | `v94` 当前是否存在 | 处理 |
| --- | --- | --- |
| `CURRENT_GATE`（独立文件/目录） | 否 | 无需移动；旧副本已在 `archive/obsolete/v94_version/current_controls/` |
| `STATUS`（独立文件/目录） | 否 | `docs/CURRENT_STATUS.md` 是明确豁免的当前入口；旧副本已归档 |
| `version`（独立旧目录/文件） | 否 | 历史 `version` 树已在 `archive/obsolete/v94_version/` |
| `history`（独立旧目录/文件） | 否 | 历史记录已在 `archive/obsolete/v94_version/history/` |
| 根旧 `README.md` | 否 | 已在 `archive/obsolete/v94_root_docs/README.md` |
| Host 当前 `README.md` | 是 | KEEP；不是状态入口 |
| `reference/` 上游 README | 是 | ARCHIVE；保留第三方参考 |

因此本轮实际移动数量为 **0**：没有发现仍位于 `v94` 内、且需要再次移动的精确旧状态路径。没有创建重复的 `v94/archive/obsolete/`，以免与工作区级既有归档树并行。

## v94 目录边界检查

### 功能类别已存在

| 期望类别 | 当前路径 | 结论 |
| --- | --- | --- |
| FPGA 源码 / Vivado 工程 | `v0.94/`（含 `rtl/`、`sim/`、`project/`） | 存在，KEEP；不改动 |
| Host | `software/redpitaya_lock_host/` | 存在，KEEP；不改动 |
| scripts | `scripts/` | 存在，KEEP；不改动 |
| docs | `docs/` | 存在；规范入口为上述六个文件 |
| reference | `reference/` | 存在；只作参考 |
| skills | `.agents/skills/` | 存在；没有顶层 `skills/`，隐藏路径即项目 skills 位置 |

### 额外目录/文件（不作搬迁）

当前 `v94` 顶层还包含 `.agents/`、`.claude/`、`.hbs/`、`.vscode/`、`.git/`、`software/` 容器、`.gitignore`、`AGENTS.md` 和 `skills-lock.json`，以及 `v0.94`/Host 内的构建缓存。故按“严格顶层只允许六类名称”判定为 **不严格满足**；按功能类别判定为 **满足**。这些是工具元数据、仓库元数据、Host 容器或工程必须目录，不在本轮移动范围内。

## 工作树保护和本轮变更

- 本轮新建文件：`PROJECT_CLEANUP_REPORT.md`（本文件）。
- 本轮未修改任何 RTL、Vivado 工程、XDC/Tcl、Host 源码、测试源码或实验原始数据。
- 本轮未执行删除，未执行 `git restore/reset/clean`，未恢复已有删除。
- 开始审计时工作树已有大量未提交的历史移动/删除和新增 `docs`/`reference` 变更；这些属于既有状态，不归因于本报告。
- 未运行仿真、Vivado、timing 或硬件验证；本报告只记录文件系统和文档分类证据。

## 已知残留引用（不改变本轮分类）

- `AGENTS.md` 的早期第 3–5 节仍出现 `version/CURRENT_GATE.md`、`version/STATUS.md` 和 `version/CURRENT_REVIEW_MANIFEST.md`；同文件第 11 节已经明确这些是历史路径，并规定新的 `docs/` 读取顺序。后续开发应遵循第 11 节和本报告的唯一入口结论，不按旧段落恢复 `version/`。
- 被列入 ARCHIVE 的 Host SOP、旧 project master 和旧 README 也可能保留旧 Gate/路径文字。这些文字是历史记录，不构成当前事实；如需引用，必须同时标记为历史并回到 `docs/CURRENT_STATUS.md` 核对。
- 本轮没有改写上述历史文本，以避免扩大用户已有 working-tree 变更；如需消除文字级歧义，应另开文档修订任务。

## 冻结结论

后续 FPGA-MTS 开发首先读取 `AGENTS.md`，再读取 `docs/PROJECT_CONTEXT.md`、`docs/CURRENT_STATUS.md`、`docs/HOST_FPGA_INTERFACE.md`、`docs/FPGA_DEVELOPMENT_RULES.md` 和 `docs/RELEASE_PROCESS.md`。历史文档优先从 `archive/obsolete/` 或 `reference/` 追溯；仍留在 `v94` 当前树中、但本报告标为 `ARCHIVE` 的路径同样不得作为入口。`DELETE_CANDIDATE` 只有在单独获得确认后才能处理。
