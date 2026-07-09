# 文档语言与风格规则

## 1. 默认语言

后续 Codex、Claude、GPT 或人工维护的项目说明、开发日志、实验记录、SOP、AI 审查记录、任务说明，默认使用中文书写。

禁止生成只有英文说明、没有中文解释的项目文档。

## 2. 必须保留英文原文的内容

以下内容不要翻译：

- 文件路径，例如 `E:\new\fpga_lock\v94\...`、`v0.94/rtl/red_pitaya_top.sv`
- 命令，例如 `fpgautil -b /root/red_pitaya_top.bit.bin`、`python -m pytest`
- 代码块中的代码
- 寄存器名，例如 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`SCAN_OFFSET`、`OUT2_MONITOR`、`HOLD_VALUE`、`KP`、`KI`、`LOCK_BIAS`
- FPGA / 硬件名，例如 Red Pitaya、Vivado、SCPI、SSH、GPIO、DAC、ADC、OUT1、OUT2、IN1、IN2
- 模块名，例如 `custom_register_bank`、`ramp_generator`、`out2_lock_controller`、`laser_lock_core`、`mixer_core`、`lpf_core`
- 版本名和模式名，例如 v3REG-0、v3REG-1、v3REG-2、SAFE、SCAN、HOLD、P_LOCK、PI_LOCK
- Vivado 报告术语，例如 `WNS`、`TNS`、`Failing Endpoints`
- 英文论文、官方文档、错误日志的原文引用

如果保留英文论文、官方文档或错误日志原文，必须补充中文解释。

## 3. 面向用户的写法

面向用户的操作步骤必须用中文，并尽量写成下面的结构：

```text
先做什么
再看什么
成功现象是什么
失败后停止做什么
禁止继续做什么
```

实验 SOP 必须写清：

- 目标
- 接线
- 正常现象
- 停止条件
- 通过标准
- 是否允许烧录
- 是否允许接激光器
- 是否允许接 Scan/PZT
- 需要保存哪些数据

## 4. 当前项目默认安全写法

默认情况下，面向用户的文档必须明确写出：

```text
当前 OUT2 只允许接示波器。
当前不能声称 FPGA 已经完整替代 D2-125。
当前不能声称 FPGA 已经独立真实锁定激光。
涉及 Vivado 的任务必须明确是否允许运行 synthesis / implementation / Generate Bitstream。
```

## 5. 历史文档引用规则

`version/v1/`、`version/v2/`、旧 review、旧 roadmap、旧实验记录只能作为历史资料。除非用户明确要求回顾历史，否则不能把旧历史文档当作当前主线结论。

当前主线结论以 `version/STATUS.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 为准。
