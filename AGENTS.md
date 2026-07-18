# FPGA-MTS AI Workflow

本文件是 `666vitas/FPGA-MTS` 的 Codex、Claude Code 和其他开发 Agent 共用入口。默认使用中文记录；路径、命令、寄存器、模块、模式名和信号名保留英文原文。

详细的复杂任务多角色规则见：

```text
version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md
```

## 1. Default Mode：Development Mode

```text
Data source: Current local workspace
Default workspace: E:\new\fpga_lock\v94
Remote access: disabled unless Review Mode is explicitly requested
Goal: local development, testing, documentation, and experiment support
```

### Development Mode 行为

1. 只以当前本地 workspace 为开发依据。
2. 开始前读取 `version/STATUS.md` 顶部最新状态、本任务直接相关的代码、测试、SOP 和实验记录。
3. 禁止主动执行 `git fetch`、`git pull`、`git ls-remote`，禁止读取 GitHub online、比较 `origin/main` 或等待网络。
4. 可以按用户明确范围修改代码、测试和文档，并运行本地命令、测试和只读 Git 检查。
5. 本地存在未提交修改时先识别来源并保护；已知且不冲突的修改不阻塞开发。来源不明或与任务重叠时停止并报告。
6. 不自动 commit、push、reset、clean、rebase 或 amend。完成后等待用户决定是否提交。

## 2. Review Mode：GitHub main 只读审计

只有用户明确输入以下任一指令时，才进入 `Review Mode`：

```text
@GitHub 审计
审查最新main
```

普通 `@GitHub` 开发请求、修复请求或文件修改请求，不自动等于只读 Review Mode。

```text
Data source: GitHub main
Goal: inspect repository version, commit, project evidence, and current status
Mutation: audit only
```

### Review Mode 行为

1. 允许读取 GitHub online、检查远端 commit 和版本状态。
2. 按 `AI_REVIEW_README.md`、`version/AI_STRICT_REVIEW_ENTRY.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 执行。
3. 禁止修改代码、测试、RTL、Vivado 工程、寄存器、bitstream 和项目逻辑。
4. Review Mode 不会因发现问题自动切换为开发；修复必须由用户另行授权。
5. 远端不可用时报告审查不完整，不把网络问题扩散到 Development Mode。

## 3. Development Critic != Review Mode

复杂开发任务中的 `Critic` 是 Development Mode 内部的独立质量审查角色：

- 它审查当前任务 diff、测试和验收矩阵。
- 它不得直接修改代码。
- 它不因此获得 GitHub remote、硬件或实验权限。
- 它与只读 GitHub `Review Mode` 不是同一个概念。

高风险任务必须遵循：

```text
Builder -> independent Critic -> Builder repair -> Critic re-check -> Evaluator
```

具体触发条件、角色边界、最多三轮复验和输出模板见 `version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md`。

## 4. 当前事实与文档优先级

### 代码实现事实

```text
当前任务分支实际代码
> 当前任务分支测试
> version/STATUS.md 顶部
> 其他说明文档
```

### 当前 Stage、Gate 和下一步动作

```text
version/STATUS.md 顶部最新条目
> 当前 Gate 对应的最新 SOP/实验记录
> version/HARDWARE_VALIDATION.md 中同一 Gate 的有效记录
> README、代码注释和历史日志
```

如果 `STATUS.md`、SOP、`HARDWARE_VALIDATION.md`、README 或代码注释之间存在会影响接线、输出或推进顺序的冲突：

1. 停止有源输出和闭环动作。
2. 将冲突列为 `Blocker`。
3. 先修正文档或要求用户确认当前 Gate。
4. 不得自行选择更激进的路径继续。

判断 OUT1/OUT2 当前实现时必须追踪最终 DAC 路由，不能仅凭模块名或旧注释。

## 5. 修改与记录

1. 每次只完成用户指定任务，只修改明确允许的文件；保留既有改动，不混入无关重构。
2. 实现、验证或实验改变项目状态时更新 `version/STATUS.md` 顶部。
3. 过程记录追加到当前版本已有的 `DEVELOPMENT_LOG.md`；用户限制文件范围时服从用户范围。
4. 不得用历史 CSV、旧默认值或旧锁点冒充当前实验参数。
5. 不得为了通过验收删除、skip、xfail、弱化测试或修改最初需求。

## 6. 证据等级

继续使用：

- `[IMPLEMENTED]`
- `[AUTOMATED VERIFIED]`
- `[USER GUI VERIFIED]`
- `[USER HARDWARE VERIFIED]`
- `[FAILED]`
- `[NOT VERIFIED]`

证据必须分层：

```text
代码存在 != 自动化通过
自动化通过 != GUI 通过
GUI 通过 != 硬件通过
硬件波形通过 != 闭环锁定
短时闭环 != 激光稳频或长期稳定性
```

没有用户真实结果时不得声称硬件、P-only、PI、自动锁定、自动重锁、稳频或长期稳定性通过。

## 7. 本地验证

1. 验证范围必须与修改风险相称。
2. Python 修改至少依次运行相关 `tabnanny`、`py_compile`、`pytest --collect-only`、targeted pytest、当前测试文件和完整 software tests。
3. RTL 修改必须检查相关 testbench、signed/unsigned、位宽、截位、饱和、reset、mode/enable 切换和寄存器一致性；只有用户明确授权时才运行对应工具链。
4. 规则或纯文档修改至少运行 `git diff --check`，并检查实际 diff。
5. 任何验证失败都必须如实报告，不得写成 PASS。
6. 无法真正启动独立 Critic 时必须标记 `INDEPENDENT CRITIC NOT AVAILABLE`，不得假装完成多 Agent 审查。

## 8. RTL、Vivado 与硬件安全边界

1. 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。
2. Agent 不自行运行 Vivado synthesis / implementation，不生成或烧录 bitstream，除非用户明确授权且环境真实可用。
3. 默认信号映射：

```text
IN1 = PD
IN2 = REF
OUT1 = laser_error
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate
```

4. 当前基础主线是专用 PZT/Scan 执行器上的最小 P-only；PI、自动锁定、自动重锁和 AI 参数优化必须另行 Gate。
5. OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
6. 禁止 OUT2 接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output`，禁止任何两个有源输出并联。
7. 通信失败、身份不匹配、saturation、输出越界、异常跳变、极性无法解释或反馈方向疑似错误时立即 SAFE。
8. 不得自动提高 Kp、切换 polarity、恢复 Ki、扩大 safe range 或重新锁定。

## 9. 数字量与物理量边界

必须明确区分：

- raw counts
- host 计算值
- GUI ideal/calibrated estimate
- pre-DAC `selected_out2`
- 真实 OUT1/OUT2 示波器电压
- loaded PZT 节点电压
- 光谱位置和激光频率状态

CH4=`selected_out2` 不自动等于 loaded PZT 电压；CH3=`laser_error` 的 ideal equivalent 不自动等于真实 OUT1 电压。软件校准通过不等于负载条件下硬件校准通过。

## 10. 完成交接

Builder 完成后输出：

- 原始目标与验收矩阵
- 修改文件和修改原因
- 测试命令与真实结果
- 未修改边界
- 未验证事项
- 硬件/实验停止条件
- 交给 Critic 的检查重点

高风险任务最终由 Evaluator 给出：

```text
PASS
CONDITIONAL PASS
FAIL
LAB VERIFICATION REQUIRED
```

默认不 commit、不 push，等待用户审核。
