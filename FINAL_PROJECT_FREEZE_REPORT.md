# FINAL PROJECT FREEZE REPORT

- Project: FPGA-MTS
- Project root: `E:\new\fpga_lock\v94`
- Freeze date: 2026-09-04
- Current Gate: `LOCK-MVP-L1`
- Result: FINAL DEVELOPMENT FREEZE COMPLETE

本报告是用户明确要求的最终整理与冻结记录，不是当前状态入口。后续开发
只依据 `v94/docs/` 中的固定入口；本报告和 `PROJECT_CLEANUP_REPORT.md`
仅用于追溯本次整理结果。

## 1. 删除内容

### 空 Markdown（5 个）

- `v0.94/redpitaya_laser_lock_project/docs/old/04_scope_asg_pid_reuse_analysis.md`
- `v0.94/redpitaya_laser_lock_project/docs/old/05_mts_demod_architecture.md`
- `v0.94/redpitaya_laser_lock_project/docs/old/07_board_test_sop.md`
- `v0.94/redpitaya_laser_lock_project/experiment_logs/log_001_top_learning.md`
- `v0.94/redpitaya_laser_lock_project/scripts/notes_build_steps.md`

### 缓存/第三方 license Markdown（14 个）

- `software/.venv/`：1 个 pip license Markdown。
- `software/redpitaya_lock_host/.venv/`：12 个 numpy/pip license Markdown。
- `software/redpitaya_lock_host/.pytest_cache/README.md`：1 个 pytest 缓存说明。

只删除了上述 Markdown 文件；`.venv/`、`.pytest_cache/` 和其他非 Markdown
文件均未删除。

## 2. 归档内容

### 旧 FPGA 工程文档

来源：`v0.94/redpitaya_laser_lock_project/docs/`

处理：删除其中 3 个空 Markdown 后，将其余 73 个文件（保留原有子目录结构）
移动至：

`E:\new\fpga_lock\archive\obsolete\v0.94_docs\`

源目录不再包含文档文件。
归档目录位于 `v94` Git 根之外；文件已物理保留，本次未执行 add、commit 或
push，因此源路径在 Git 状态中显示为删除是预期结果。

### Host 历史设计文档

来源：`software/redpitaya_lock_host/docs/`

移动 17 个历史文档至：

`E:\new\fpga_lock\archive\obsolete\host_docs\`

源目录保留：

- `CONNECTION_DIAGNOSIS.md`
- `HARDWARE_TEST_SOP.md`
- `USAGE.md`

同时保留 Host 根目录：`software/redpitaya_lock_host/README.md`。

### Reference

`v94/reference/` 保持原位，作为只读参考，不参与当前开发入口、Gate 判断或
当前实现依据。

## 3. 保留内容与冻结入口

以下六个文件继续是当前规范入口，并且均存在：

- `docs/PROJECT_CONTEXT.md`
- `docs/CURRENT_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/HOST_FPGA_INTERFACE.md`
- `docs/FPGA_DEVELOPMENT_RULES.md`
- `docs/RELEASE_PROCESS.md`

另按用户要求建立冻结记录：

- `docs/DEVELOPMENT_BASELINE.md`

未修改本次禁止范围：RTL 源码、Vivado 工程、XDC、TCL、Host 源码、实验数据、
论文资料和 `.agents/skills`。

## 4. 当前 Codex 读取顺序

后续任务固定按以下顺序读取：

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/HOST_FPGA_INTERFACE.md`
5. `docs/FPGA_DEVELOPMENT_RULES.md`
6. `docs/RELEASE_PROCESS.md`

`docs/DEVELOPMENT_BASELINE.md` 是冻结基线记录，不创建第二套状态入口；
归档和 reference 文件只在有明确追溯需要时读取。

## 5. 最终核对

- 空/空白 Markdown（当前 `v94`）：0 个。
- 指定缓存目录中的 Markdown：0 个残留。
- 旧 FPGA 文档源目录文件：0 个；归档文件：73 个。
- Host docs 源目录：仅 3 个指定保留文件。
- Host 根目录 `README.md`：存在。
- 六个固定入口：全部存在。
- `docs/DEVELOPMENT_BASELINE.md`：存在。
- 新建重复 `STATUS`、`CURRENT` 或普通 `REPORT` 文档：无；本报告和冻结基线均为用户明确要求的例外。
- 未运行仿真、Vivado、timing 或板级实验；本次仅执行文件整理和文档核对。

## 6. 冻结结论

最终整理到此结束。禁止再次大规模调整目录、建立新的项目管理体系或根据
归档历史重新规划当前结构。下一阶段只进行 FPGA/Host 代码优化、必要测试
以及固定入口文档更新。
