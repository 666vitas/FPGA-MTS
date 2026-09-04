# Engineering Changelog

- Status: ACTIVE
- Authority: 工程变更记录
- Last-Updated: 2026-09-04

本文件记录影响工程理解、接口、验证或发布的变更。它不是调试流水账，也不替代 Git 历史、CURRENT_STATUS 或 release manifest。

## 记录规则

每次有效开发完成后，在文件顶部新增一条记录，至少包含：

- 日期
- 当前 Gate
- 修改文件
- 修改原因
- 影响模块
- 接口影响
- 验证方式与结果
- 尚未验证事项
- Git commit 或 NOT COMMITTED
- Release 或 NOT RELEASED

验证结果必须区分 PASS、FAIL、NOT RUN 和 NOT VERIFIED。不得使用“应该可以”“预计通过”替代证据。

## 文档归位

禁止为普通开发过程随意建立大量 xxx_report.md。信息应写入以下固定入口：

| 信息 | 固定入口 |
| --- | --- |
| 当前状态、阻塞项 | docs/CURRENT_STATUS.md |
| 工程变更原因和验证摘要 | docs/CHANGELOG.md |
| Host/FPGA 接口 | docs/HOST_FPGA_INTERFACE.md |
| FPGA 开发规则 | docs/FPGA_DEVELOPMENT_RULES.md |
| bit 发布及测试结果 | releases/<release_name>/RELEASE_MANIFEST.md |
| 当前 Gate | docs/CURRENT_STATUS.md |

只有不可变的工具输出、正式评审交付或用户明确要求的独立证据，才允许建立新的报告；新报告必须由 CURRENT_STATUS、CHANGELOG 或 release manifest 链接，不得成为平行状态入口。

## 2026-09-04 — 最终开发前冻结

- Gate: LOCK-MVP-L1
- 修改文件: `AGENTS.md`、`docs/CURRENT_STATUS.md`、`docs/DEVELOPMENT_BASELINE.md`、本文件、`FINAL_PROJECT_FREEZE_REPORT.md`；移动旧 FPGA/Host 文档并删除指定 Markdown 缓存
- 修改原因: 完成最后一次文档和缓存清理，冻结当前开发入口，准备进入 FPGA/Host 优化阶段
- 影响模块: 文档路径、归档路径和开发入口；不影响 RTL、Host 源码、Vivado 工程、XDC/Tcl、实验数据、论文资料或 skills
- 接口影响: NONE
- 验证方式与结果: 删除 5 个空 Markdown 和 14 个缓存/第三方 license Markdown；旧 FPGA 文档 73 个文件归档至 `archive/obsolete/v0.94_docs/`；Host 历史文档 17 个文件归档至 `archive/obsolete/host_docs/`；Host 保留 `README.md`、`USAGE.md`、`HARDWARE_TEST_SOP.md`、`CONNECTION_DIAGNOSIS.md`；六个固定入口和冻结基线均存在
- 尚未验证: 未运行仿真、Vivado、timing 或板级实验
- Git commit: NOT COMMITTED
- Release: NOT RELEASED

## 2026-09-04 — 科研工作空间物理归位

- Gate: LOCK-MVP-L1
- 修改文件: `v94/AGENTS.md`、`v94/version/CURRENT_REVIEW_MANIFEST.md`、本文件及项目管理入口；同时移动工作空间目录和历史资产
- 修改原因: 将科研总空间、当前工程、知识、实验、会议、论文、AI 记录和归档分层，降低历史文件与当前工程混淆
- 影响模块: 文件路径与文档入口；不修改 RTL、Host 源码、Vivado 工程或实验原始内容
- 接口影响: NONE
- 验证方式与结果: 必需路径存在；`v94/docs` 仅六个规范入口；delete_candidates 不含源码、数据、论文扩展名；`git diff --check` 通过
- 尚未验证: 未重新运行仿真、Vivado、timing 或板级实验
- Git commit: NOT COMMITTED
- Release: NOT RELEASED

归档中的内容均为移动而非永久删除；`archive/delete_candidates/` 仅表示待人工确认的缓存/日志候选。

## 记录模板

### YYYY-MM-DD — 简短标题

- Gate:
- 修改文件:
- 修改原因:
- 影响模块:
- 接口影响: NONE / COMPATIBLE / BREAKING
- 验证方式与结果:
- 尚未验证:
- Git commit: NOT COMMITTED 或完整 commit
- Release: NOT RELEASED 或 release_name

## 2026-09-04 — 建立长期项目开发规范

- Gate: LOCK-MVP-L1
- 修改文件: docs/PROJECT_CONTEXT.md、docs/CURRENT_STATUS.md、docs/CHANGELOG.md、docs/FPGA_DEVELOPMENT_RULES.md、docs/HOST_FPGA_INTERFACE.md、docs/RELEASE_PROCESS.md、../WORKSPACE_CONTEXT.md、AGENTS.md
- 修改原因: 基于已完成资产审查建立固定的项目上下文、当前状态、接口、开发和发布入口
- 影响模块: 文档治理；不影响 RTL、Host、Vivado 工程或实验数据
- 接口影响: NONE
- 验证方式与结果: 文档路径、必需章节、交叉引用和 AGENTS.md 追加内容检查
- 尚未验证: 未重新运行仿真、Vivado 或板级实验
- Git commit: NOT COMMITTED
- Release: NOT RELEASED

本文件不回填无法从现有审查证据唯一确定的历史变更。
