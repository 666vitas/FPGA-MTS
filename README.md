# FPGA-MTS

Red Pitaya FPGA MTS 激光频率锁定项目。

## 项目目标

当前工程围绕以下主线逐阶段推进：

```text
MTS 信号观测
-> SAFE/SCAN
-> 人工锁点选择
-> HOLD / Kp=0 无跳变验证
-> 最小 P-only 闭环
-> 后续 PI、自动重锁和参数优化
```

任何后续能力只有在对应代码、测试、bitstream、上板和实验 Gate 分别通过后，才能被描述为完成。

## 当前状态入口

动态状态不再硬编码在 README 中。每次开始开发、审查或实验时读取：

1. `AGENTS.md`
2. `version/STATUS.md` 顶部最新条目
3. 当前 Gate 对应的 SOP 和实验记录
4. Review Mode 额外读取 `AI_REVIEW_README.md`、`version/AI_STRICT_REVIEW_ENTRY.md` 和 `version/CURRENT_REVIEW_MANIFEST.md`

README、代码注释或历史日志中的旧阶段描述不得覆盖 `STATUS.md` 顶部和当前实际代码。

## 固定信号架构

除非当前任务明确授权架构变更，默认映射为：

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

判断当前 OUT1/OUT2 实现时必须检查 `v0.94/rtl/red_pitaya_top.sv` 的最终 DAC 路由，不能只看候选控制器、模块名或旧注释。

## 硬件安全边界

OUT2 的具体接线权限由当前 Stage/Gate 和对应 SOP 决定，不由 README 中的静态文字决定。

始终禁止：

- OUT2 接激光器电流调制输入
- OUT2 接 D2-125 `Servo Output`
- OUT2 接 D2-125 `Aux Output`
- 任意两个有源输出并联
- 在通信失败、`MAGIC/VERSION` 不匹配、saturation、越界、异常跳变或反馈方向异常时继续输出
- 自动提高 Kp、切换 polarity、恢复 Ki、扩大 safe range 或自动重锁

出现异常时必须立即 SAFE。

CH4=`selected_out2` 是 FPGA command/capture，不自动等于 loaded PZT 节点电压；GUI calibrated estimate、真实示波器电压、PZT loaded voltage 和光谱状态必须分开记录。

## AI 开发与独立验收

默认开发规则见 `AGENTS.md`。

高复杂度任务使用：

```text
Builder -> independent Critic -> Builder repair -> Critic re-check -> Evaluator
```

完整规则见：

```text
version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md
```

高风险任务包括 RTL、寄存器、OUT2/PZT、SAFE/SCAN/HOLD/P_LOCK、锁点选择、校准、counts/volts 映射和实验 Gate。没有真实硬件证据时，最终结论必须是 `LAB VERIFICATION REQUIRED`，不能写成锁定或稳频完成。

## 文档语言规则

本项目后续所有项目说明、开发日志、实验记录、SOP、AI 审查记录和任务说明默认使用中文。

代码标识符、文件路径、命令行、寄存器名、模块名、信号名和英文缩写保留英文原文。例如 `MAGIC`、`OUT2`、`custom_register_bank`、`v0.94/rtl/red_pitaya_top.sv`、`python -m pytest`。

引用英文论文、官方文档或错误日志时可以保留英文原文，但必须补充中文解释。

面向用户的硬件操作必须写清：

```text
先做什么
再观察什么
PASS 现象是什么
FAIL 后何时立即 SAFE
```

## 项目入口与目录

- `AGENTS.md`：AI 开发总入口
- `AI_REVIEW_README.md`：GitHub 只读审计入口
- `version/STATUS.md`：当前动态状态和下一步动作
- `version/CURRENT_REVIEW_MANIFEST.md`：当前 main 审查范围
- `version/AI_STRICT_REVIEW_ENTRY.md`：强约束审查规则
- `version/rules/20_MULTI_AGENT_MTS_DEVELOPMENT.md`：复杂任务多角色规则
- `version/HARDWARE_VALIDATION.md`：硬件 Gate 证据记录
- `software/redpitaya_lock_host/docs/`：上位机说明、SOP 和开发日志
- `v0.94/rtl/`：当前 RTL 主线
- `v0.94/project/redpitaya.xpr`：当前 Vivado 工程
- `software/redpitaya_lock_host/`：Python / PySide6 上位机

## 上位机启动

```powershell
cd software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```
