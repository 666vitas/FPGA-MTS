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
v3REG-0 SAFE/SCAN 已由用户上板验证。
当前 RTL / software 已包含 v3REG-1 / v3REG-2 候选：HOLD / P_LOCK / PI_LOCK。
HOLD / P_LOCK / PI_LOCK 尚未完成 Vivado timing、bitstream、烧录和上板验证。
```

信号含义：

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
laser_control / pi_controller_seq = 内部候选或历史路径，不是当前 DAC B / OUT2 最终输出
```

安全边界：当前只允许 OUT2 接示波器；禁止接 Scan/PZT、激光器、D2-125 Servo Output、D2-125 Aux Output；不能声称已经闭环锁定，不能声称已经替代 D2-125。

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
