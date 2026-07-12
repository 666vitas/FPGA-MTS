# AI 审查入口

本仓库的 AI / GPT / Codex / Claude 审查必须先读本文件，再读当前状态文件和 manifest。

## 唯一主线入口

```text
PRIMARY_BRANCH = main
PRIMARY_STATUS = version/STATUS.md
PRIMARY_MANIFEST = version/CURRENT_REVIEW_MANIFEST.md
PRIMARY_RULES = version/AI_STRICT_REVIEW_ENTRY.md
PRIMARY_RTL_PATH = v0.94/rtl
PRIMARY_PROJECT = v0.94/project/redpitaya.xpr
```

当前主线结论以 `version/STATUS.md` 的“当前主线”段落和 `version/CURRENT_REVIEW_MANIFEST.md` 为准。

## 强制读取顺序

任何 AI 审查都必须按下面顺序读取：

1. `AI_REVIEW_README.md`
2. `version/AI_STRICT_REVIEW_ENTRY.md`
3. `version/CURRENT_REVIEW_MANIFEST.md`
4. `version/STATUS.md`
5. `v0.94/project/redpitaya.xpr`
6. manifest 中列出的当前 RTL 文件

## 禁止作为当前结论依据的路径

除非用户明确要求回顾历史，否则审查当前状态时禁止把以下路径当作当前 main 结论依据：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
v0.94/redpitaya_laser_lock_project/docs/old/**
**/*.before_*
**/*before*
**/old/**
```

这些路径只能作为历史资料，不能覆盖当前主线判断。

## 当前阶段简述

当前主线：

```text
项目最终目标：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
当前最小主线：PZT 基础稳频，人工 SCAN -> 选择色散过零点 -> LOCK HERE -> P-only 小增益反馈 -> SAFE。
```

信号含义：

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
laser_control / pi_controller_seq = 内部候选或历史路径，不是当前 DAC B / OUT2 最终输出
```

当前执行器边界：OUT2 的目标执行器是激光器专用 PZT / Scan 输入；SCAN 和 P_LOCK 使用同一个 PZT 接口。必须限制 OUT2 幅度、偏置和 `LOCK_CORRECTION_LIMIT`，异常立即 SAFE。禁止 OUT2 接激光器电流调制输入，禁止接 D2-125 Servo Output / Aux Output，禁止两个设备输出端并联。当前不能声称已完成全自动锁定或替代 D2-125。

## 审查输出要求

每个审查结论必须写清：

```text
已经从当前 RTL 直接确认的事实
只从文档记录确认、尚未由 RTL 或实验验证的事实
不能确认的事实
禁止推进的实验动作
下一步最小安全动作
```

关键结论必须引用具体文件和行号；没有行号证据时只能写“未确认”。

## 文档语言要求

审查记录默认使用中文。代码标识符、文件路径、命令、寄存器名、模块名、信号名、英文缩写保留英文原文；如果引用英文错误日志或官方文档，必须补充中文解释。
