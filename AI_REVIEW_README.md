# FPGA-MTS AI 入口

本仓库默认采用 `Development Mode`。完整行为边界见 `AGENTS.md`；高复杂度任务的独立审查与验收规则见：

```text
version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md
```

## 1. Development Mode（默认）

```text
Data source: Current local workspace
Remote access: disabled
Goal: local development, testing, documentation, and experiment support
```

新任务直接读取：

1. `AGENTS.md`
2. `version/STATUS.md` 顶部最新状态
3. 本任务直接相关的本地代码、测试、SOP 和实验记录
4. 高风险任务额外读取 `version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md`

Development Mode 不要求 Git Gate，不主动 fetch/pull，不比较 `origin/main`，也不因 GitHub 或网络不可用而阻塞本地任务。

复杂任务中的 `Critic` 属于 Development Mode 内部质量流程，不等于下面的 GitHub `Review Mode`。Critic 不得直接修改代码，也不会因此获得远端、Vivado、bitstream 或实验权限。

## 2. Review Mode（GitHub main 只读审计）

仅当用户明确输入以下任一指令时启用：

```text
@GitHub 审计
审查最新main
```

普通 `@GitHub` 开发、修复或修改文件请求不自动进入 Review Mode。

Review Mode 可以读取 GitHub、检查远端 commit 和版本状态，但只能审查，禁止修改项目文件。进入后按顺序读取：

1. `AGENTS.md` 的 Review Mode 规则
2. `version/AI_STRICT_REVIEW_ENTRY.md`
3. `version/CURRENT_REVIEW_MANIFEST.md`
4. `version/STATUS.md` 顶部
5. Manifest 指定的当前代码、测试和记录

远端访问失败只影响本次 Review，不改变 Development Mode 的本地开发能力。

## 3. 当前事实的判定方式

不同问题使用不同权威来源：

### 代码实际做了什么

```text
当前代码和最终路由
> 当前测试
> STATUS
> 说明文档和注释
```

判断 OUT1/OUT2 时必须追踪到最终 DAC 选择路径，不能只看控制器名称或旧注释。

### 当前 Stage、Gate 和下一步唯一动作

```text
version/STATUS.md 顶部最新条目
> 当前 Gate 对应的最新 SOP/实验记录
> version/HARDWARE_VALIDATION.md 中同一 Gate 的有效记录
> README 和历史日志
```

如果这些文件之间存在影响接线、输出或推进顺序的冲突，必须停止有源动作，把冲突列为 `Blocker`，先完成文档对齐或用户确认。

## 4. 本地事实与历史资料

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

历史资料只能说明过去做过什么，不能覆盖当前代码、`STATUS.md` 顶部或当前 Gate。

## 5. 证据与安全边界

继续使用：

```text
[IMPLEMENTED]
[AUTOMATED VERIFIED]
[USER GUI VERIFIED]
[USER HARDWARE VERIFIED]
[FAILED]
[NOT VERIFIED]
```

必须分开表述：

```text
软件实现
自动化验证
真实 GUI
寄存器/bitstream/上板
示波器物理量
P-only/PI 闭环
激光稳频和长期稳定性
```

固定安全原则：

- IN1=PD，IN2=REF，OUT1=`laser_error`，OUT2=`selected_out2`。
- OUT2 只能连接当前 Gate 明确授权的专用 PZT/Scan 输入和测量设备。
- 禁止接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output`，禁止有源输出并联。
- 通信、身份、saturation、越界、异常跳变或反馈方向异常时必须 SAFE。
- CH4 command estimate 不等于 loaded PZT 电压；软件 PASS 不等于硬件或闭环 PASS。
