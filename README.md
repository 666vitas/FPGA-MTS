# FPGA-MTS

Red Pitaya FPGA 激光频率锁定项目。长期目标是构建基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统；当前实现与实验进度必须以动态状态记录为准，不在本文件写死。

## 当前事实入口

按以下优先级判断项目状态：

1. 当前代码、寄存器定义和最终信号路由。
2. `version/STATUS.md` 顶部最新条目。
3. 当前 Gate 的最新 SOP、实验记录及 `version/HARDWARE_VALIDATION.md` 有效记录。
4. 本轮实际测试、README、历史日志和旧注释。

软件存在、自动化测试、GUI 操作、真实硬件和闭环效果是不同证据，不得互相替代。

## AI 工作入口

- `AGENTS.md`：Codex 与 Claude Code 的最短入口和模式边界。
- `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`：Gate、任务分级、验证、证据和硬件安全的详细工程规则。
- `AI_REVIEW_README.md`：Development Mode 与 GitHub Review Mode 入口。
- `version/CURRENT_REVIEW_MANIFEST.md`：仅供明确触发的 GitHub Review Mode 使用。

## 文档语言

项目说明、开发日志、实验记录、SOP 和 AI 审查默认使用中文。路径、命令、寄存器、模块、信号和模式名保留英文；引用英文资料或错误日志时补充中文解释。用户操作步骤应说明操作、预期现象、失败停止条件和 SAFE 条件。

## 基础信号映射

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
MAGIC = 0x4D545330
```

`VERSION` 从当前 RTL、host 和实际 bitstream 记录核对，不在 README 写死。

## 永久安全边界

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止 OUT2 连接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出端；禁止有源输出并联。
- 身份、通信、SAFE、范围、saturation、跳变、readback、反馈方向、接线或示波器条件异常时立即 SAFE 并停止。
- Codex 不自动增加 Kp/Ki、翻转 polarity、放宽 limit、扩大 PZT safe range、再次 LOCK 或进入下一 Gate。
- 软件、仿真、GUI 和硬件证据不能替代用户真实闭环验证。

## 主要目录

- `v0.94/rtl/`：当前 RTL。
- `v0.94/project/redpitaya.xpr`：Vivado 工程。
- `software/redpitaya_lock_host/`：Python / PySide6 上位机。
- `software/redpitaya_lock_host/docs/`：上位机说明、SOP 和开发日志。
- `version/`：状态、验证记录和长期规则。

## 上位机启动

```powershell
cd software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```
