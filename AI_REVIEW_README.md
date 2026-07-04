# AI Review Entrypoint

本仓库的 AI / GPT / Codex / Claude 审查必须先读本文件。

## 唯一主线

```text
PRIMARY_BRANCH = main
PRIMARY_STATUS = version/STATUS.md
PRIMARY_MANIFEST = version/CURRENT_REVIEW_MANIFEST.md
PRIMARY_RULES = version/AI_STRICT_REVIEW_ENTRY.md
PRIMARY_RTL_PATH = v0.94/rtl
PRIMARY_PROJECT = v0.94/project/redpitaya.xpr
```

当前主线结论以 `version/STATUS.md` 的“当前主线”段落和 `version/CURRENT_REVIEW_MANIFEST.md` 为准。

## 强制审查入口

任何 AI 审查都必须按下面顺序读取：

1. `AI_REVIEW_README.md`
2. `version/AI_STRICT_REVIEW_ENTRY.md`
3. `version/CURRENT_REVIEW_MANIFEST.md`
4. `version/STATUS.md`
5. `v0.94/project/redpitaya.xpr`
6. manifest 中列出的当前 RTL 文件

## 禁止作为当前结论依据的路径

除非用户明确要求回顾历史，否则审查当前状态时禁止读取或引用：

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

当前主线是 `v3REG-0 register-controlled OUT2 SAFE/SCAN`：

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2 = custom_register_bank + ramp_generator SAFE/SCAN
laser_control / pi_controller_seq = 后续候选，不是当前 OUT2 输出
```

安全边界：本阶段只允许 OUT2 接示波器；不接 Scan/PZT，不接激光器，不接 D2-125 Servo Output，不接 D2-125 Aux Output，不和 D2-125 输出并联，不声称已经闭环锁定。

## 审查输出要求

每个审查结论必须写清楚：

```text
已从当前 RTL 直接确认的事实
只从文档记录确认、尚未由 RTL/实验验证的事实
不能确认的事实
禁止推进的实验动作
下一步最小安全动作
```

所有关键结论必须引用具体文件和行号；没有行号证据时只能写“未确认”。
