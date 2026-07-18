# FPGA-MTS 复杂任务多角色开发与验收规则

本规则用于 `666vitas/FPGA-MTS` 的高复杂度开发任务，目标是避免同一个 Agent 在实现后沿用自己的假设完成“自我证明”。

本规则属于 `Development Mode` 内部的质量控制协议，不会把开发任务自动切换为只读的 `Review Mode`，也不会授权访问远端、修改硬件或执行实验。

## 1. 适用范围

任务开始时先分级：

### L0：简单任务

示例：

- 纯文字修正
- 不改变语义的排版调整
- README 链接修复
- 无行为变化的注释清理

流程：`Builder 自检`。

### L1：普通功能任务

示例：

- 上位机非安全关键显示
- 数据导出
- 普通解析逻辑
- 不改变寄存器或输出路径的测试补充

流程：`Builder -> Critic -> Builder 修复`。

### L2：高风险任务

出现以下任一项，必须执行完整流程：

- 修改 RTL、Vivado 工程、时钟、复位、位宽、signed/unsigned、乘法、截位、饱和或 DAC 路径
- 修改寄存器地址、寄存器语义、`MAGIC`、`VERSION`、模式编码或 host/FPGA 协议
- 修改 `SAFE / SCAN / HOLD / P_LOCK / PI_LOCK / LOCK HERE / CAPTURE_LOCK_POINT`
- 修改 OUT2、PZT、Scan、反馈极性、Kp、Ki、积分、限幅或 saturation 行为
- 修改锁点选择、过零检测、误差信号解释、校准、counts/volts 映射或实验导出证据
- 修改通信失败、窗口关闭、身份不匹配、超时、capture 重入或自动 SAFE 行为
- 宣称某个 Stage、Gate、bitstream、上板、闭环、稳频或长期稳定性完成
- 大规模重构、跨前端/后端/RTL 的联动修改

流程：

```text
Builder
  -> independent Critic
  -> Builder repair
  -> Critic re-check
  -> Evaluator
  -> user lab evidence when required
  -> final Evaluator
```

## 2. 角色隔离

### 2.1 Builder

Builder 负责实现，但无权给出最终 `PASS`。

开始前必须：

1. 读取 `AGENTS.md`。
2. 读取 `version/STATUS.md` 顶部最新状态。
3. 读取本任务直接相关代码、测试、SOP 和实验记录。
4. 把原始目标冻结成验收矩阵，不得在实现过程中悄悄降低要求。
5. 明确本轮允许修改和禁止修改的文件范围。

完成后必须交付：

- 原始需求与实现位置的对应关系
- 修改文件及原因
- 实际执行的命令
- 真实测试结果
- 未执行的验证
- 需要用户 GUI、硬件或实验完成的步骤
- 已知风险和立即 SAFE 条件

### 2.2 Critic

Critic 必须是未参与本轮实现的独立线程或独立 Agent。

Critic 不得直接修改代码，不得根据 Builder 的总结替代代码和测试检查。Critic 必须重新读取原始任务、验收矩阵、实际 diff、相关代码和测试结果。

如果当前工具无法真正启动独立线程，必须明确写：

```text
INDEPENDENT CRITIC NOT AVAILABLE
```

随后可以执行一次隔离的第二遍审查，但不得把它描述成独立 Agent 审查。

Critic 检查范围：

1. 需求完整性
2. 逻辑正确性
3. 边界情况
4. 数值、位宽和饱和
5. 安全状态与失败路径
6. host/FPGA/GUI/文档语义一致性
7. 测试是否真实执行且覆盖核心风险
8. 证据等级是否被抬高
9. 旧版本、旧注释和历史目录是否污染当前结论
10. 是否存在需要实验但被软件结果替代的结论

Critic 的每个问题必须包含：

- 严重级别：`Blocker / High / Medium / Low`
- 对应原始需求
- 文件和位置
- 复现或检查方法
- 实际结果
- 预期结果
- 建议修复方向

Critic 不得为了“显得严格”制造没有证据的问题。

### 2.3 Evaluator

Evaluator 不开发、不修复，只判断原始目标是否被证据证明。

Evaluator 必须独立核对：

- 原始验收矩阵
- Builder 交接
- Critic 问题清单
- 修复后的 diff
- 实际测试输出
- 当前 Stage/Gate
- 用户 GUI、硬件和实验记录

最终状态只能为：

- `PASS`
- `CONDITIONAL PASS`
- `FAIL`
- `LAB VERIFICATION REQUIRED`

规则：

- 软件和自动化全部通过，但缺少真实硬件或闭环证据时，必须是 `LAB VERIFICATION REQUIRED`。
- 存在未解决 `Blocker`、核心 `High`、关键测试失败或验收项缺失时，必须是 `FAIL`。
- 不得用“代码看起来正确”“理论上可行”“应当工作”替代证据。

### 2.4 User / Experiment Operator

真实接线、示波器测量、Vivado 手工流程、bitstream 烧录、激光扫描和闭环实验只能由用户或现场操作者完成。

Agent 可以：

- 给出单步 SOP
- 分析用户提供的截图、CSV、日志和读回值
- 根据停止条件要求 SAFE

Agent 不得虚构：

- 已烧录
- 已上板
- 已测得真实电压
- 已找到正确 MTS 锁点
- 已完成 P-only、PI、自动重锁或稳频

## 3. 当前事实的权威顺序

不同问题使用不同权威来源，禁止用一份文档覆盖所有事实。

### 3.1 代码实现事实

优先级：

```text
当前任务分支的实际代码
> 当前任务分支的测试
> version/STATUS.md 顶部状态记录
> 其他说明文档
```

判断 OUT1/OUT2 最终路由时，必须追踪到 `red_pitaya_top.sv` 的最终 DAC 选择路径，不能只看模块名、旧注释或候选控制器。

### 3.2 当前阶段和下一步动作

优先级：

```text
version/STATUS.md 顶部最新条目
> 当前 Gate 对应的最新实验/SOP 文档
> version/HARDWARE_VALIDATION.md 中同一 Gate 的最新有效记录
> README 和历史日志
```

如果 `STATUS.md`、SOP、`HARDWARE_VALIDATION.md`、README 或代码注释之间存在影响接线或推进顺序的冲突：

1. 停止执行有源输出或闭环动作。
2. 将冲突列为 `Blocker`。
3. 先修正文档或由用户确认当前 Gate。
4. 不得自行选择更激进的版本继续实验。

### 3.3 Review Mode 远端事实

只有用户明确触发 `@GitHub 审计` 或 `审查最新main` 时，才以 GitHub `main`、`CURRENT_REVIEW_MANIFEST.md` 和实际远端文件为准。

### 3.4 历史资料

以下路径默认只能回答历史问题，不得作为当前主线结论：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

## 4. FPGA-MTS 固定架构与安全约束

除非用户明确授权新的架构变更任务，默认映射为：

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

当前基础稳频主线以 PZT/Scan 执行器和最小 P-only 闭环为目标。PI、自动锁定、自动重锁和 AI 参数优化不能因为代码入口存在就被视为当前授权主线。

固定安全边界：

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止 OUT2 接激光器电流调制输入。
- 禁止 OUT2 接 D2-125 `Servo Output` 或 `Aux Output`。
- 禁止任何两个有源输出并联。
- 输入、输出、偏置、扫描幅度和 correction limit 必须处于当前已确认安全范围。
- 通信失败、`MAGIC/VERSION` 不匹配、saturation、越界、异常跳变、极性无法解释或反馈方向疑似错误时，立即 SAFE。
- 不得自动提高 Kp、改变 polarity、恢复 Ki、继续重锁或扩大安全范围。

## 5. 数字量、显示量和物理量必须分开

必须明确区分：

- FPGA raw counts
- host 计算值
- GUI ideal/calibrated estimate
- pre-DAC `selected_out2`
- 真实 OUT1/OUT2 示波器电压
- PZT 接入后的 loaded node voltage
- 光谱位置和激光频率状态

特别规则：

- CH4=`selected_out2` 是 FPGA 内部 command/capture，不自动等于 loaded PZT 节点电压。
- CH3=`laser_error` 的 ideal equivalent 不自动等于真实 OUT1 电压。
- 软件校准通过不等于负载条件下硬件校准通过。
- `HOLD`、`Kp=0 LOCK HERE`、非零 Kp P-only 是不同 Gate，不得合并描述。
- bitstream 生成、烧录、寄存器读回、示波器验证和真实闭环必须分别记录。

## 6. 证据等级

继续使用项目既有等级：

- `[IMPLEMENTED]`
- `[AUTOMATED VERIFIED]`
- `[USER GUI VERIFIED]`
- `[USER HARDWARE VERIFIED]`
- `[FAILED]`
- `[NOT VERIFIED]`

证据不得跨层升级：

```text
存在代码 != 自动化通过
自动化通过 != GUI 通过
GUI 通过 != 硬件通过
硬件波形通过 != 闭环锁定
短时闭环 != 激光稳频或长期稳定性
```

## 7. 必查清单

### 7.1 Python / GUI

至少检查：

- 输入校验和异常路径
- worker/capture 防重入
- Live 停止条件
- 断线和身份错误是否请求 SAFE
- host 写入值与 FPGA readback 是否分开
- unavailable 是否被 0 或期望值冒充
- CSV、实验日志和 GUI 是否保持同一语义
- 相关 `tabnanny`、`py_compile`、collect、targeted pytest 和完整 software tests

### 7.2 RTL / 寄存器

至少检查：

- signed/unsigned
- 加法、乘法和中间位宽
- 算术移位、截位、舍入和饱和
- reset 后是否 SAFE
- mode/enable 切换和流水线旧值
- correction limit 与 absolute limit
- host/RTL 寄存器地址和语义一致
- `MAGIC/VERSION`
- testbench 是否覆盖零值、极值、正负 Kp、正负 error、正反 polarity、上下限饱和和模式切换

### 7.3 实验 Gate

每次实验只允许一个最小 Gate，并记录：

- 日期、操作者、板卡身份
- commit、bitstream、`MAGIC/VERSION`
- 接线、负载、耦合、探头倍率
- IN1/IN2/OUT1/OUT2 电压范围
- SCAN 参数、PZT safe range
- Kp、Ki、polarity、bias、limits
- 示波器截图、CSV、寄存器读回
- PASS/FAIL 和停止原因

没有这些证据时，不得宣布实验 Gate 完成。

## 8. 修复循环与终止

最多允许 3 轮：

```text
Critic -> Builder repair -> Critic re-check
```

每一轮必须只处理已有验收目标和已证实问题，不得无限扩大范围。

第 3 轮后仍未通过时停止，输出：

1. 已完成项
2. 未完成项
3. 剩余 `Blocker/High`
4. 阻塞原因
5. 下一步最小安全任务
6. 需要用户完成的 GUI、Vivado、硬件或实验动作

禁止通过删除测试、降低阈值、改写需求、隐藏失败或把未执行项标为通过来结束循环。

## 9. 标准输出

### Builder 交接

```text
A. 原始目标与验收矩阵
B. 修改文件和实现位置
C. 实际运行命令与结果
D. 未修改边界
E. 未验证事项
F. 硬件/实验停止条件
G. 交给 Critic 的检查重点
```

### Critic 报告

```text
A. 独立性声明
B. 实际读取内容
C. Blocker/High/Medium/Low 问题
D. 测试与复现证据
E. 需求覆盖缺口
F. 证据等级错误
G. 修复清单
```

### Evaluator 报告

```text
A. 验收矩阵
B. 测试证据
C. GUI/硬件/闭环证据
D. 剩余风险
E. PASS / CONDITIONAL PASS / FAIL / LAB VERIFICATION REQUIRED
F. 下一步唯一动作
```
