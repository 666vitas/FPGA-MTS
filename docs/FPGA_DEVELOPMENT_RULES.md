# FPGA Development Rules

- Status: ACTIVE
- Authority: FPGA 开发与验证流程
- Last-Updated: 2026-09-04

## 适用范围

本规则适用于 v0.94 下的 RTL、仿真、约束、IP/Block Design 配置和 Vivado 工程变更。它规定证据链和发布条件，不授权任何特定功能开发，也不改变当前 Gate 的权限边界。

## 开发前

1. 按 AGENTS.md 的顺序读取项目上下文、当前状态、接口契约和当前 Gate。
2. 确认本次任务是否属于当前 Gate，记录明确的预期行为和禁止范围。
3. 检查 Git 工作树，保护用户已有修改；不得覆盖、回退或混入无关改动。
4. 确认目标 XPR、top、器件、Vivado 版本和需要运行的仿真集合。
5. 若改动涉及寄存器、采集通道或控制语义，先按 HOST_FPGA_INTERFACE.md 建立同步变更项。

## 修改 RTL 后的强制流程

### 1. 更新 CURRENT_STATUS

立即在 docs/CURRENT_STATUS.md 记录修改范围、当前完成度、待验证项和新阻塞。完成后再根据实际结果更新一次，不能让状态文件停留在预期状态。

### 2. 运行仿真

- 运行被修改模块的定向 testbench。
- 运行与其数据路径、状态机、定点位宽、饱和/舍入、复位和边界条件相关的回归。
- 记录命令、工具版本、测试数量、PASS/FAIL 和关键波形/日志位置。
- 未运行的测试写 NOT RUN；仅编译成功不能写成功能验证通过。

### 3. Vivado 综合与实现

- 使用当前权威 XPR 和明确记录的 Vivado 版本。
- 综合、实现、DRC/CDC/Methodology 检查必须对应同一源码基线。
- 不得用旧 run 目录或旧 bit 代替当前构建。
- 若当前 Gate 或用户未授权运行 Vivado，应停止并在 CURRENT_STATUS 中写 NOT RUN / NOT VERIFIED，不得继续生成正式 release。

### 4. 记录 timing

至少记录：

- WNS、TNS、WHS、THS
- 未约束路径或端点数量
- 关键时钟及目标频率
- timing summary、DRC、CDC/Methodology 报告路径
- Vivado 版本、器件、top、Git commit 和构建时间

Timing 未通过、存在未解释的未约束路径或报告不对应当前源码时，不得标记 release ready。

### 5. 生成 release

只有仿真、综合、实现、timing 和所需检查满足当前 Gate，且源码能由唯一 Git commit 重现时，才按 docs/RELEASE_PROCESS.md 生成正式 release。工作树有未提交源码改动时不得生成正式 release。

### 6. 记录 bit 对应关系

每个 bit 必须唯一绑定：

- release_name
- bit 文件名和 SHA256
- FPGA Git commit
- Host version/commit
- Interface version
- XPR、top、器件和 Vivado version
- build time
- 仿真、timing 和板级 test result

映射不完整的 bit 只能标记为 historical、candidate 或 unknown，不得标记为 current。

## 代码与生成物边界

- RTL、约束、工程配置和可重复生成脚本属于源码。
- bit、run logs、综合/实现中间目录、波形缓存和工具临时文件属于生成物或证据，不作为源码维护。
- 不得直接把生成目录中的临时副本当作权威 RTL 修改。
- 不得因工具运行覆盖用户未提交的工程文件；运行前应识别预期输出范围。

## 变更完成条件

一次 FPGA 变更只有在以下记录闭合后才能称为完成：

1. CURRENT_STATUS 已反映真实状态。
2. CHANGELOG 已记录修改原因和影响模块。
3. 仿真与 Vivado 结果有可定位证据，或明确写出未运行原因。
4. 接口影响已同步 Host 和 HOST_FPGA_INTERFACE。
5. 若生成 bit，release manifest 和 bit 映射完整。

## 统一 Vivado 构建配置（本轮起）

- 用户日常活动 run 固定为同一 XPR 下的 `synth_1` → `impl_1`，目录为 `v0.94/exp/test`；综合与实现策略分别为 `Vivado Synthesis Defaults`、`Vivado Implementation Defaults`。
- `STEPS.PHYS_OPT_DESIGN.IS_ENABLED=0`；`STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE=Explore`。Explore 只作用于 `route_design`，不得替换成 Performance_Explore 或其他策略；post-place/post-route 物理优化等其余属性保持工程默认并记录。
- 自动候选必须复用这两个标准 run；不得以独立 `build_candidate_*.tcl` run 作为用户复核配置，也不得为诊断新增 final2/explore2 等 run。
- 构建前后使用 `v0.94/exp/test/check_build.ps1 -Phase pre|post` 做只读核对。脚本只导出 INPUT/PROFILE/TIMING/DRC/约束/BIT 绑定状态，不修改 RTL、XDC、IP、工程设置，不重新综合/实现，不访问板卡。
- 约束加载日志中的未匹配对象、缺失 I/O delay、CDC/Methodology 保留项必须原样记录；不能因正 WNS、相同 WNS 或无新增 Warning 而宣称输入或功能等价。
