# CURRENT_REVIEW_MANIFEST

本文件只用于 `Review Mode`，不是 Development Mode 的启动入口。

## Review Mode 触发与边界

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 时读取本 Manifest，并允许访问 GitHub remote。

- 数据源：GitHub `main`。
- 目标：检查 commit、push 状态、版本差异和项目证据。
- 允许：`git fetch`、检查 `origin/main`、读取 GitHub online、比较 commit/diff。
- 禁止：修改代码、测试、RTL、Vivado 工程、寄存器、bitstream 或项目逻辑。
- remote 失败：报告本次 Review 不完整；不得把网络检查变成 Development Mode 的默认 Gate。

Development Mode 只使用当前本地 workspace，不要求读取本文件，不 fetch，也不比较 `origin/main`。

## 当前审查范围

```text
Repository: 666vitas/FPGA-MTS
Primary branch: main
Primary RTL root: v0.94/rtl
Primary Vivado project: v0.94/project/redpitaya.xpr
Primary status: version/STATUS.md
Hardware validation: version/HARDWARE_VALIDATION.md
Host calibration SOP: software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md
Strict review template: version/AI_STRICT_REVIEW_ENTRY.md
```

Review 开始时先读取 GitHub `main` 对应版本的 `STATUS.md` 顶部，再用当前代码验证状态文字。`AI_STRICT_REVIEW_ENTRY.md` 中的旧状态或既有 conflict markers 不得覆盖当前代码和 STATUS。

## 当前代码审查文件

RTL / Vivado：

```text
v0.94/project/redpitaya.xpr
v0.94/rtl/red_pitaya_top.sv
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/custom_register_bank.sv
v0.94/rtl/ramp_generator.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/pi_controller_seq.sv
v0.94/rtl/pi_controller.sv
```

上位机与记录按审查问题选择当前 `software/redpitaya_lock_host/` 代码、测试、`version/STATUS.md`、`version/HARDWARE_VALIDATION.md` 和相关 `DEVELOPMENT_LOG.md`。

## 当前项目基线

以下是本地 STATUS 记录的审查起点，Review Mode 必须用 GitHub `main` 实际文件复核，不能直接当作远端结论：

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK，当前不作为实验主线
MAGIC = 0x4D545330
VERSION = 0x00030001
```

当前本地状态仍要求区分：代码实现、自动化验证、用户 GUI、用户硬件和闭环证据。不得把 nominal/ideal GUI 电压写成真实物理电压，不得把软件 PASS 写成硬件或闭环 PASS。

## 禁止作为当前 main 依据的历史路径

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
v0.94/redpitaya_laser_lock_project/docs/old/**
**/old/**
**/*.before_*
**/*before*
```

## 安全结论

- OUT2 只能连接经确认的目标接口；禁止连接激光器电流调制、D2-125 Servo Output、D2-125 Aux Output，禁止任何有源输出并联。
- 通信、身份、saturation、输出越界、异常跳变或反馈方向异常时必须 SAFE。
- 没有明确实验记录时，不得声称已经闭环锁定、替代 D2-125、完成自动重锁或 AI 参数优化。

## Review 输出

```text
A. 实际读取文件
B. GitHub main / commit 状态
C. 当前代码直接证据
D. 文档与实验记录证据
E. 未验证事项和风险
F. 旧版本污染
G. 禁止动作
H. 审查结论
```

Review Mode 只交付报告，不实施修复。
