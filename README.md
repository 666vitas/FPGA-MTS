# FPGA-MTS

Red Pitaya FPGA 激光频率锁定项目。

## 当前主线

当前状态入口以 `version/STATUS.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 为准。当前主线结论：

- v3REG-0 SAFE/SCAN 已由用户上板验证。
- 当前 RTL 已包含 v3REG-1 / v3REG-2 候选：HOLD / P_LOCK / PI_LOCK。
- HOLD / P_LOCK / PI_LOCK 尚未完成 Vivado timing、bitstream、烧录和上板验证。
- OUT1 = `laser_error`，用于 mixer + LPF error observation。
- OUT2 = `selected_out2`，不是 `laser_control`。
- 当前只允许 OUT2 接示波器；禁止接 PZT、Scan input、激光器、D2-125 Servo Output 或 D2-125 Aux Output。

## 文档语言规则

本项目后续所有项目说明、开发日志、实验记录、SOP、AI 审查记录、Codex/Claude/GPT 任务说明，默认使用中文书写。

代码标识符、文件路径、命令行、寄存器名、模块名、信号名、英文缩写保留英文原文。例如 `MAGIC`、`OUT2`、`custom_register_bank`、`v0.94/rtl/red_pitaya_top.sv`、`python -m pytest` 不翻译。

如果引用英文论文、官方文档或错误日志，可以保留英文原文，但必须补充中文解释。

面向用户的操作步骤必须用中文，并尽量写成“先做什么、再看什么、成功现象是什么、失败后停止做什么”的形式。

禁止生成只有英文说明、没有中文解释的项目文档。

## 项目入口与目录

- `version/STATUS.md`：当前状态入口。
- `AI_REVIEW_README.md`：AI 审查入口。
- `version/rules/`：长期规则目录。
- `software/redpitaya_lock_host/docs/`：上位机相关说明、SOP、开发日志。
- `v0.94/rtl/`：当前 RTL 主线。
- `v0.94/project/redpitaya.xpr`：当前 Vivado 工程。
- `software/redpitaya_lock_host/`：Python / PySide6 Red Pitaya 上位机软件。
- `version/`：项目状态、实验记录、阶段记录。

## 上位机启动

```powershell
cd software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```
