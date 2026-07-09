# Red Pitaya Laser Lock Host V2

Red Pitaya Laser Lock Host V2 是本项目的上位机软件，用于配合 Red Pitaya FPGA 激光频率锁定实验。

它的目标不是一步到位自动锁定，而是逐步替代 D2-125 工作流：扫描、error signal 观察、control output 观察、锁定准备检查，以及后续 lock/relock 流程记录。

## 当前开发目录

所有 Red Pitaya 上位机开发都在：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

不要使用旧的独立上位机目录。Markdown 说明、SOP 和阶段记录放在 `docs/`。开发日志放在 `docs/DEVELOPMENT_LOG.md`。使用说明放在本 README 和 `docs/USAGE.md`。SCPI 说明放在 `docs/SCPI_MODE_NOTES.md`。

## 目录结构

```text
redpitaya_lock_host/
  .venv/                 # 本地 Python 虚拟环境，不提交 Git
  docs/                  # 上位机文档
  redpitaya_lock_host/   # Python 源码
  tests/                 # 上位机测试
  config.yaml            # 默认配置
  requirements.txt       # Python 依赖
  run.bat                # 正常连接模式启动脚本
  run_mock.bat           # Mock 模式启动脚本
  README.md
```

## 与 FPGA 工程的关系

上位机位于：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

FPGA / RTL / Vivado 工程位于：

```text
E:\new\fpga_lock\v94\v0.94
```

修改上位机文档或 GUI 不等于修改 RTL，不等于生成 bitstream。

## Python 环境

推荐：

```text
Official Python 3.11 + project-local .venv
```

不推荐：

```text
Anaconda base environment
```

Anaconda base 可能带来 Qt / PySide6 / DLL 冲突，例如：

```text
ImportError: DLL load failed while importing QtWidgets
```

## 首次安装

在 PowerShell 中运行：

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host

py -3.11 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

如果没有 `py` 命令，说明没有安装官方 Python Launcher。安装 official Python 3.11 后重新打开 PowerShell。

## 环境测试

```powershell
.\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
.\.venv\Scripts\python.exe -c "import yaml; print('PyYAML OK')"
```

## 启动

Mock mode：

```powershell
.\run_mock.bat
```

真实连接模式：

```powershell
.\run.bat
```

备用启动命令：

```powershell
.\.venv\Scripts\python.exe -m redpitaya_lock_host.main --mock
.\.venv\Scripts\python.exe -m redpitaya_lock_host.main
```

在 PowerShell 中不要只输入：

```powershell
run.bat
```

应使用：

```powershell
.\run.bat
```

## Custom FPGA Lock Host 主流程

当前上位机主界面默认面向项目专用 `Custom FPGA Lock Host`，不再把 `Official SCPI Mode`、`Start SCPI Server`、`Connect SCPI` 或 Official ASG OUT1/OUT2 作为主操作入口。当前 custom bitstream 中，`OUT1=laser_error`，`OUT2=selected_out2`，SCPI ASG 命令即使成功也不代表能驱动物理 OUT2。

上板示波器验证建议按下面顺序执行：

```text
Probe Registers -> Status -> SAFE -> SCAN -> Capture Bias -> LOCK -> UNLOCK / SAFE
```

`Capture Bias` 和 `LOCK` 都会读取 `OUT2_MONITOR`。`LOCK` 不使用 `lock-bias-v` 的理想电压估算，而是用当前 `OUT2_MONITOR` counts 作为 `LOCK_BIAS`，再写入 `MODE=3 P_LOCK`。当前 LOCK 只启用 P-only，`Ki/PI` 暂时禁用。

`Capture Waveform` 当前不会采集真实 custom FPGA IN1/IN2 波形，只提示后续 `debug_capture` 寄存器方案。真实 IN1/IN2、OUT1、OUT2 波形仍以示波器观察为准。

安全边界不变：未完成示波器矩阵验证和接线 SOP 前，OUT2 禁止连接 PZT、Scan input、激光器电流调制、D2-125 Servo Output 或 D2-125 Aux Output。

## Red Pitaya 连接流程

1. 点击 `Probe`。
2. 确认 SSH 可用后，不启动 `redpitaya_scpi`，直接进入 `Custom FPGA Observe`。
3. 点击 `Probe Registers`，确认找到 `MAGIC=0x4D545330`。
4. 点击 `Status`，确认 `VERSION=0x00030000` 且状态可读。
5. 点击 `SAFE`，确认 OUT2 处于安全关闭。
6. 只把 OUT2 接到示波器，再点击 `SCAN`。
7. 示波器确认三角波幅度、偏置和频率安全后，才允许进入 `Capture Bias -> LOCK`。

## GUI Custom FPGA Control

只有在 Red Pitaya FPGA 已经加载 timing-pass custom bitstream 后，才使用本路径。该路径通过 SSH + `/dev/mem` 访问 custom FPGA register bank；不启动 `redpitaya_scpi`，不使用 Official SCPI ASG 控制 Custom FPGA OUT2。

推荐顺序：

1. 用 `.\run.bat` 启动 GUI。
2. 打开 `Custom FPGA Observe` 页面。
3. `base address` 默认保持 `0x40600000`，除非 Probe 发现另一个匹配 base。
4. 点击 `Probe Registers`。
5. 点击 `Status`，确认 `MAGIC = 0x4D545330`。
6. 点击 `SAFE`。
7. OUT2 只接示波器时，再点击 `SCAN`。
8. 扫描到合适工作点后，点击 `Capture Bias` 或直接点击 `LOCK`。
9. 需要退出锁定输出时，点击 `UNLOCK / SAFE`。

如果 `MAGIC = 0x00000000`，GUI 会阻止 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 写寄存器。这通常表示没有读到 `custom_register_bank`，可能原因是没有 Program Device、加载了旧 bit file、base address 错误，或需要重新加载 timing-pass bitstream。

### v3REG-1 / v3REG-2 手动锁定最短路径

当前 Custom FPGA Control 已支持：

```text
SAFE
SCAN
HOLD
Capture Bias
LOCK
UNLOCK / SAFE
```

这些按钮走同一条寄存器路径：

```text
GUI -> SSH -> /dev/mem -> custom_register_bank -> out2_lock_controller -> selected_out2 -> DAC B / OUT2
```

推荐上板顺序：

```text
Custom FPGA Observe
-> Probe Registers
-> Status
-> SAFE
-> SCAN
-> Capture Bias
-> LOCK, with Kp=0 first
-> UNLOCK / SAFE
```

`HOLD` 输出固定电压，使用 `hold-v` 设置。`LOCK` 使用 `Kp raw`、`polarity` 和 `lock-limit-counts`，并自动用 `OUT2_MONITOR` counts 捕获 `LOCK_BIAS`。`lock-bias-v` 只保留为旧的人工参考输入，不作为一键 `LOCK` 的偏置来源。当前 `Ki/PI` 禁用，`Kp raw` 约定 `256 = 1.0x`，GUI 默认值为 0，必须人工逐步增加。

安全边界：HOLD/LOCK 第一阶段仍然只允许 OUT2 接示波器。不要把 OUT2 默认接到 PZT、激光电流、D2-125 Servo Output 或 Scan input。只有 scope-only 验证了幅度、偏置、polarity、limit 和 SAFE 关闭行为后，才允许单独制定执行器连接 SOP。

## GUI 模式

- Custom FPGA Observe Mode：通过 SSH `/dev/mem` 执行 Probe Registers、Status、SAFE、SCAN、HOLD、Capture Bias、LOCK、UNLOCK/SAFE，并记录真实接线的手动示波器读数：IN1 PD/MTS、IN2 REF、OUT1 `laser_error`、OUT2 `selected_out2`。
- Lock Workflow Mode：D2-125 替代流程 checklist，当前只做 P-only scope-only 锁定准备，不声称已经接执行器闭环锁定。
- Data & Experiment Log：导出 Markdown 实验日志到 `docs/experiment_logs/`。

debug-buffer read、IN1/IN2 自定义波形显示、高层 lock FSM control、relock 和 actuator connection SOP 仍是后续工作。

## OUT1/OUT2 预览说明

CH3 和 CH4 是生成预览，不是实测 ADC 数据。

`50 Hz` 三角波周期是 20 ms。当 `sample_count=2048`、`decimation=1024` 时，IN1/IN2 acquisition 窗口可能短于 20 ms，所以 OUT1/OUT2 预览使用独立生成的 preview time axis。

preview 配置在 `config.yaml`：

```yaml
preview:
  cycles: 2
  min_points: 1024
  max_points: 5000
```

真实 OUT2 必须用示波器确认，或在安全幅度下做 OUT2 -> IN1 回环，并保证 IN1 在 +/-1 V 内。

## Official SCPI 兼容说明

Official SCPI 相关代码仍保留在仓库中，用于历史兼容或官方 overlay/ASG 测试，但当前主界面不再把它作为项目主入口。当前锁定实验默认使用 Custom FPGA Lock Host。

Official SCPI 路径的风险：

- 通过 `redpitaya_scpi` 控制官方 ASG OUT1/OUT2 waveform。
- 可以采集 IN1/IN2。
- 启动 `redpitaya_scpi` 可能加载官方 v0.94 overlay。
- 启动 `redpitaya_scpi` 可能覆盖当前 custom FPGA bitstream。
- 如果已加载 `USE_LASER_LOCK_CORE=1` 的 custom FPGA bitstream，SCPI OUT2 命令可能成功返回，但不会驱动物理 OUT2，因为 OUT2 路由到 `selected_out2`。

当前 Custom FPGA Lock Host 路径：

- OUT1/OUT2 由 custom FPGA RTL 输出驱动。
- OUT1 通常是 `laser_error`。
- OUT2 是 `selected_out2`：`/dev/mem` -> `custom_register_bank` -> `ramp_generator` / `out2_lock_controller` -> physical OUT2。
- 该模式下 OUT1/OUT2 不由 official SCPI ASG 控制。
- 读取 FPGA 内部 `error_internal` 仍需要后续 debug buffer、register interface 或 AXI readout path。
