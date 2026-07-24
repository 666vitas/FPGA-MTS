# FPGA-MTS

Red Pitaya FPGA 激光频率锁定项目。当前目标是先得到 timing-clean `LOCK_MVP_BUILD`，再完成真实、可重复的最小 P-only 锁定。deterministic ARM 源码和测试保留，但不作为第一次 P-only 锁定依赖。

## 从这里开始

当前文档权威顺序：

1. [`AGENTS.md`](AGENTS.md) — 唯一 Codex/工程入口与永久安全边界。
2. [`version/CURRENT_GATE.md`](version/CURRENT_GATE.md) — 当前唯一 Gate：`LOCK-MVP-T0`。
3. [`version/STATUS.md`](version/STATUS.md) — 当前 timing、实现和硬件事实。
4. [`version/CURRENT_REVIEW_MANIFEST.md`](version/CURRENT_REVIEW_MANIFEST.md) — 当前强制读取和排除范围。
5. [`version/DOCUMENT_INDEX.md`](version/DOCUMENT_INDEX.md) — 文档类别、用途、移动和删除索引。

长期架构说明见 [`docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md`](docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md)。它是 active spec，但权威低于 `CURRENT_GATE`。

禁止依据 Windows 修改日期、Git 时间或文件名日期判断哪个文档最新。

## 当前 Gate 摘要

用户最新 Vivado implementation：

```text
WNS  = -0.387 ns
TNS  = -5.015 ns
setup failing endpoints = 19
WHS  = +0.052 ns
hold failing endpoints = 0
```

setup timing 当前为 `[FAILED]`，bitstream 不能标记为 timing-clean。下一步只做 `LOCK_MVP_BUILD` 编译期 ARM 隔离；详细范围和验收条件只看 `version/CURRENT_GATE.md`。

## 基础信号映射

```text
IN1 = PD
IN2 = REF
OUT1 = laser_error
OUT2 = selected_out2 -> laser dedicated PZT/Scan input
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate
MAGIC=0x4D545330
```

`VERSION` 从当前 RTL、host 和实际 bitstream 记录核对，不在 README 写死。

## 主要目录

- `v0.94/rtl/` — 当前 RTL。
- `v0.94/sim/` — RTL testbench。
- `v0.94/project/redpitaya.xpr` — Vivado 工程。
- `software/redpitaya_lock_host/` — Python / PySide6 host。
- `docs/architecture/` — active spec 与长期架构。
- `docs/process/` — supporting 流程与迁移方案。
- `docs/hardware/` — 硬件 SOP 和验证记录。
- `docs/experiment_logs/` — 真实实验日志。
- `version/history/`、`version/v1/` 至 `version/v5/` — 默认排除的历史。

## 永久安全边界

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止连接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出；禁止输出并联。
- 身份、通信、SAFE、范围、saturation、跳变、readback、反馈方向或接线异常时立即 SAFE 并停止。
- 软件、仿真、timing、GUI 和真实硬件证据不能互相替代。

## 本地验证

```powershell
.\scripts\verify.ps1
```

本命令不会替代用户 Vivado implementation 或真实硬件验证。

## Host 启动

```powershell
cd software\redpitaya_lock_host
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\run.bat
```
