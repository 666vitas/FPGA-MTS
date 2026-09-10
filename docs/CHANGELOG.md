# Engineering Changelog

- Status: ACTIVE
- Authority: 工程变更记录
- Last-Updated: 2026-09-09

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

## 2026-09-09 — VALIDATE/ACTIVE 与 P-only 状态契约修复

- Gate: LOCK-MVP-L1
- 修改文件: `v0.94/rtl/simple_lock_acquisition.sv`；`v0.94/sim/` 下 acquisition、out2 controller、l1 plant 三个 testbench；Host 的 `core/acquisition_service.py`、`core/lock_service.py`、`connection_workers.py`、`main_window.py`、`scripts/custom_fpga_scan_control.py` 及 lock services/backend/low-amplitude 三个测试文件；XPR 新增两个独立 run；同步更新 `PROJECT_CONTEXT`、`CURRENT_STATUS`、`HOST_FPGA_INTERFACE`、`USAGE`、`HARDWARE_TEST_SOP` 和本文件。
- 修改原因: VALIDATE 记录事件后原状态停在 VALIDATING，阻断后续人工 ACTIVE；Host 把非零 Kp 误显示为 P_LOCKED；快速事件需要 ARM 前 sequence 基线及 generation/方向匹配；worker 原先用请求 capture_id 验证同一请求，缺少持久确认目标。
- 影响模块: simple acquisition FSM、Host lock service、远程 CSR helper、选点到 P-only 操作文档。
- 接口影响: COMPATIBLE；寄存器地址和数值不变，明确了 VALIDATED 事件后回 SCAN 的状态语义，并要求 Host 以 FPGA 状态读回判定 Apply P。
- 验证方式与结果: Vivado 2020.1 xsim acquisition 37/37、OUT2 controller 60/60、组合 plant 10/10 PASS；Host 相关套件 194 passed。plant 为数字模型，Kp=128 等仅为模型假设。原始日志、源码 SHA256 和差异在 `v0.94/exp/l1-contract-20260909/`。当前源码一次综合/实现完成：WNS=0.121 ns、TNS=0、WHS=0.051 ns、THS=0、TPWS=0、Failed Routes=0。源码和构建输入哈希复核一致。旧 `exp/v3-arm/impl_1` 的 WNS=0.080 ns 对应用户截图，未被重置或当作本次修改结果。
- DRC/签核: 4 个 Daisy IOSTDTYPE-1 Critical Warning + 41 Warning（与旧 run 数量一致）；Methodology 的 DNA TIMING-17、no_clock=1、内部未约束端点=2、I/O delay 缺失尚未关闭。CDC 已分析路径 Unsafe/Unknown 均为 0，32 个 No ASYNC_REG 警告；未定义时钟路径不在其分析范围。未降低检查级别或更改时钟/XDC，停止 write_bitstream。
- 尚未验证: 候选 bit、板卡读回、OUT2 示波器接管连续性、真实 P-only 收敛和持续稳频；未连接板卡/SSH/加载 overlay/烧录。完整 Host 全量 pytest 未完成，只声明上述相关套件结果。
- 工程保护: GUI 占用期间未并发构建；确认退出后使用原 XPR 新增独立 run。只读打开无法创建 run，因此保存构建前 XPR 快照后正常打开；构建后 XML 比较确认仅新增 run 和组件排序，原配置/原 run 保持，未另建 XPR。
- 最终 Host 补充: 普通 STATUS 也按 ARM 前 sequence、generation/方向确认 VALIDATE 完成并显示 `VALIDATED / SCAN`；新增操作员诊断测试。此补充未改变 FPGA 输入，只重跑 Host 至 194 passed，最终差异/身份记录为 `delivery_worktree.patch`/`delivery_identity.json`。
- Git commit: NOT COMMITTED（基线 HEAD `7c7b6570d4197939cd8e0101b096928d2ff67486`；工作树含用户/Vivado 元数据修改）
- Release: NOT RELEASED

实际读取的技能与执行步骤（均在 `.agents/skills/`，未安装任何工具）：

| SKILL.md | 本轮实际使用 |
| --- | --- |
| `diagnose/SKILL.md` | 沿 GUI→worker→service→CSR→RTL 列出并核对状态/代际/捕获/读回假设，复现 VALIDATING 不退出和 Apply P 错标 |
| `tdd/SKILL.md` | 先以定向测试暴露状态缺陷，再进行最小修复和回归；保留中间失败与最终通过日志 |
| `vivado-sim/SKILL.md` | 用已安装的 xvlog/xelab/xsim 2020.1 跑三个行为仿真，检查最终 SUMMARY |
| `vivado-synth/SKILL.md` | 核查 include 链、LOCK_ACQ_IMPL=1、Q8 算术；用原综合策略完成一次 synth_design |
| `vivado-tcl/SKILL.md` | 核对 Project flow 和本机命令帮助，新增独立 run、复制已有 step 参数、完成构建和报告；保护原 XPR 用户内容 |
| `vivado-analysis/SKILL.md` | 解读真实 routed timing、route status、未约束端点和 clock 检查 |
| `vivado-impl/SKILL.md` | 核对旧 route_design，并以同一原策略执行本次 placement/route；没有策略搜索 |
| `vivado-constraints/SKILL.md` | 根据实际 no_clock/I/O delay/XDC unmatched 警告检查约束风险；没有添加 false path 或改时钟 |

未读取/使用 vivado-debug：本轮没有 ILA/板级调试证据需求。

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
