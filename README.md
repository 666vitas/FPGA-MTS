# FPGA-MTS

Red Pitaya FPGA 激光频率锁定项目。当前唯一目标是在现有 SystemVerilog MTS 信号链上实现 Linien-style minimal manual lock：人工选择目标谱线和方向，FPGA 原子执行 scan-to-Kp=0 transition，再验证最小 P-only。基础 P-only 硬件通过前不开展 PI、自动锁定、自动重锁或 AI 优化。

## 当前事实入口

按以下优先级判断项目状态：

1. 当前代码、寄存器定义和最终信号路由。
2. `version/STATUS.md` 顶部最新条目。
3. 当前 Gate 的最新 SOP、实验记录及 `version/HARDWARE_VALIDATION.md` 有效记录。
4. 本轮实际测试、README、历史日志和旧注释。

软件存在、自动化测试、GUI 操作、真实硬件和闭环效果是不同证据，不得互相替代。

## 当前规则入口

- `AGENTS.md`：单开发者角色、模式和安全边界。
- `version/STATUS.md`：当前 Stage、唯一 Gate、blocker、证据和唯一实验。
- `version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md`：Linien-style Gate 工作流和完成标准。
- `version/CURRENT_REVIEW_MANIFEST.md`：当前有效代码、测试、文档根目录及历史排除。

`software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md`、`version/HARDWARE_VALIDATION.md` 和开发日志是 supporting evidence，不是规则 source of truth。其他旧 review、strict review、多角色和阶段规则均为 `HISTORICAL / NOT ACTIVE`。

## 一键验证

在仓库根目录运行：

```powershell
.\scripts\verify.ps1
```

默认检查活动规则并运行 host targeted verification。`-Scope Rules` 只查规则，`-Scope Host` 只查 host，`-FullHost` 追加完整 software tests。任一关键检查失败或超时都会返回非零退出码。

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
MODE=4 PI_LOCK candidate（基础 P-only 通过前禁止开展）
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
