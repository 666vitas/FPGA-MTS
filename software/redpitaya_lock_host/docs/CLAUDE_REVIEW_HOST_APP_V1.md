# CLAUDE_REVIEW_HOST_APP_V1

**审查日期**: 2026-06-26
**审查范围**: `E:\new\fpga_lock\v94\software\redpitaya_lock_host`（只读，未修改任何文件）
**审查人角色**: Red Pitaya STEMlab 125-14 / Python 上位机 / 实验自动化软件审查工程师

---

## 1. 总体结论

**当前版本可以启动 GUI 并完成 Mock 模式测试，但不适合进入硬件测试。**

原因有三：(1) 代码完全没有实现 Red Pitaya SCPI 采集命令（`ACQ:*`），连接到真实硬件后 IN1/IN2 波形显示为全零，无法验证 ADC 通路；(2) `main.py` 不接受 `--mock` 命令行参数，README 中建议的运行方式会崩溃；(3) `requirements.txt` 中 `pyyaml` 的包名大小写与 `import yaml` 不一致，虽然在 pip 安装时可以工作，但会误导用户。

以下是逐项审查结果。

---

## 2. A 类：目录和边界检查

### A1 — 项目结构 ✅

目录结构与需求完全一致：

```
software/redpitaya_lock_host/
├── README.md                  ✅
├── requirements.txt           ✅
├── config.yaml                ✅
├── run.bat                    ✅
├── docs/
│   ├── PROJECT_CONTEXT.md     ✅
│   ├── HOST_APP_DESIGN.md     ✅
│   ├── DEVELOPMENT_LOG.md     ✅
│   ├── TEST_PLAN.md           ✅
│   └── NEXT_FPGA_DEBUG_BUFFER_PLAN.md ✅
└── redpitaya_lock_host/
    ├── __init__.py            ✅
    ├── main.py                ✅
    ├── main_window.py         ✅
    ├── scpi_client.py         ✅
    ├── rp_client.py           ✅
    ├── acquisition_worker.py  ❌ 缺失
    ├── waveform_plot.py       ✅
    ├── data_logger.py         ✅
    ├── safety.py              ✅
    └── mock_client.py         ✅
```

**缺失文件**: `redpitaya_lock_host/acquisition_worker.py`。但鉴于 V1 未实现真实 ADC 数据采集，该文件在当前阶段并非阻塞项。当后续添加 SCPI 采集功能时须补上。

### A2 — weifang 引用检查 ✅

全项目代码中不包含任何对 `weifang` 目录的引用。仅在 `README.md`、`PROJECT_CONTEXT.md`、`DEVELOPMENT_LOG.md` 中以边界声明形式出现"不使用 weifang"，属于正确的项目边界标注。

### A3 — 是否会修改 FPGA 目录 ✅

代码中不存在任何打开、写入 FPGA 工程文件的逻辑。`v94/v0.94` 路径仅以字符串形式出现在文档中作为引用说明。所有文件操作（CSV 保存、PNG 保存）的目标路径均通过 `QFileDialog` 由用户选定。

---

## 3. B 类：Windows / PowerShell 启动检查

### B1 — `run.bat` 语法 ⚠️ 可用但有问题

```bat
@echo off
setlocal
cd /d "%~dp0"
python -m redpitaya_lock_host.main
endlocal
```

`cd /d "%~dp0"` 是 CMD 语法。`.bat` 文件由 CMD 执行，所以**双击或从 CMD 运行 `run.bat` 是正确的**。

但存在两个问题：

1. **没有激活虚拟环境**。README 的安装步骤创建了 `.venv`，但 `run.bat` 没有调用 `.venv\Scripts\activate`，会使用系统全局 Python。
2. **`python` 命令在部分 Windows 机器上不存在**。Microsoft Store 版本的 Python 只注册 `python3`。建议使用 `py -3` 或检测 `python`/`python3`。

### B2 — README 中的 CMD vs PowerShell 混淆 ⚠️

README 的 Install 部分：

```bat
cd /d E:\new\fpga_lock\v94\software\redpitaya_lock_host
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`cd /d` 参数在 **PowerShell 中会报错**（PowerShell 不识别 `/d` 开关）。用户在 PowerShell 中复制粘贴这段命令会失败。

**建议修复**：README 中区分 CMD 和 PowerShell 两种写法：

```powershell
# PowerShell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

或者写 `cd E:\new\fpga_lock\v94\software\redpitaya_lock_host`（PowerShell 中 `cd` 等价于 `Set-Location`，不需要 `/d`）。

### B3 — PowerShell 运行 bat ⚠️

如果用户在 PowerShell 中运行 `.bat`：

```
.\run.bat
```

这是正确的——PowerShell 会识别 `.bat` 扩展名并委托给 CMD 执行。但输出会出现在同一个 PowerShell 窗口，而 CMD 的 `@echo off` 不影响 PowerShell 的输出行为。这一点可以在 README 中简单提示。

### B4 — `requirements.txt` 依赖检查 ⚠️

```
PySide6>=6.6
pyqtgraph>=0.13
numpy>=1.24
pandas>=2.0
pyyaml>=6.0
```

问题：

1. **`pyyaml` 的 PyPI 包名应该是 `PyYAML`**。虽然 pip 不区分大小写，`pip install pyyaml` 和 `pip install PyYAML` 都会安装 `PyYAML` 包，但在 `import` 时用户看到的是 `import yaml`（全部小写），而 `requirements.txt` 里写的是 `pyyaml`，容易让新手困惑。建议写标准名称 `PyYAML>=6.0`。
2. **未明确 Python 版本下限**。建议在 README 中注明 `Python 3.10+`（已在文档中有，但 README 中缺少）。
3. **PySide6 可能安装失败**。在某些 Windows 环境下 PySide6 的 wheel 很大（~100MB），建议在 README 中提示使用 `--prefer-binary` 或说明首次安装可能较慢。

---

## 4. C 类：Python 包和入口检查

### C1 — `--mock` 参数未实现 ❌ 阻塞

**严重性：阻塞**

`main.py` 中没有 `argparse` 或任何命令行参数解析逻辑：

```python
def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow(load_config())
    window.resize(1280, 860)
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
```

如果用户执行 `python -m redpitaya_lock_host.main --mock`，`QApplication(sys.argv)` 会将 `--mock` 传给 Qt，Qt 不认识这个参数，**程序会直接退出并打印未知参数错误**。

Mock 模式的切换完全依赖 GUI 中的 `mock_check` 复选框（`main_window.py` 第 165 行，默认选中）。

**建议**：在 `main()` 中添加 argparse，或在 `sys.argv` 传给 `QApplication` 之前过滤掉自定义参数。

### C2 — `__init__.py` ✅

```python
"""Red Pitaya laser lock host application."""
__version__ = "0.1.0"
```

存在且正确，使 `redpitaya_lock_host` 成为可导入的 Python 包。

### C3 — 模块导入方式 ✅

所有模块之间使用包内相对导入（如 `from .safety import ...`），在通过 `python -m redpitaya_lock_host.main` 运行时不会出现导入错误。从 `E:\new\fpga_lock\v94\software\redpitaya_lock_host` 目录执行是正确的。

### C4 — `main.py` 未解析 `--mock` ❌ 见 C1

### C5 — `config.yaml` 加载逻辑 ✅

`load_config()` 函数正确地从 `Path(__file__).resolve().parents[1] / "config.yaml"` 加载配置，即从上位机软件根目录读取。

---

## 5. D 类：SCPI 通信检查

### D1 — `scpi_client.py` 职责边界 ✅

`scpi_client.py` 正确地保持为纯 SCPI 传输层：
- TCP 连接/断开
- 命令写入（`write`）
- 查询（`query`）
- 错误类型 `ScpiError`
- 不包含任何 Red Pitaya 业务逻辑

### D2 — `rp_client.py` 职责边界 ✅

`rp_client.py` 正确地封装了 Red Pitaya 业务操作：
- `connect()` 发送 `*IDN?` 验证连接
- `apply_triangle_scan()` 发送完整的 OUT2 三角波 SCPI 序列
- `stop_scan()` 和 `safe_shutdown()` 处理安全关闭

### D3 — TCP 端口 ✅

默认使用 TCP 5000（`scpi_client.py` 第 19 行，`config.yaml` 第 3 行），端口可在 GUI 中修改。

### D4 — `*IDN?` 验证 ✅

`rp_client.py` 第 25-28 行：连接后发送 `*IDN?`，空响应时关闭 socket 并抛异常。逻辑正确。

### D5 — OUT2 三角波 SCPI 命令顺序 ✅

`rp_client.py` 第 39-46 行：

```python
self.scpi.write("GEN:RST")                              # 1. 重置 ASG
self.scpi.write("SOUR2:FUNC TRIANGLE")                  # 2. 设置波形类型
self.scpi.write(f"SOUR2:FREQ:FIX {settings.frequency_hz:.9g}")  # 3. 频率
self.scpi.write(f"SOUR2:VOLT {settings.amplitude_v:.9g}")       # 4. 幅度
self.scpi.write(f"SOUR2:VOLT:OFFS {settings.offset_v:.9g}")     # 5. 偏置
self.scpi.write(f"OUTPUT2:STATE {'ON' if enable else 'OFF'}")  # 6. 输出使能
self.scpi.write("SOUR2:TRig:INT")                       # 7. V2 触发
```

V2 当前实现使用 `SOUR2:TRig:INT`，并在触发前设置 `OUTPUT2:STATE`。旧 `SOUR2:TRIG:IMM` 路径不再用于 V2 OUT2 Apply。

有一个细节值得注意：`float` 值格式化为 `.9g`（9 位有效数字），这对于 SCPI 命令来说精度足够了，但某些 Red Pitaya 固件版本可能对过长字符串敏感。目前未见已知问题，可以保留。

### D6 — Stop Scan / Disconnect / 退出安全序列 ✅

`rp_client.py` 的 `safe_shutdown()` 第 52-61 行：

```python
self.scpi.write("SOUR2:VOLT 0")       # 幅度归零
time.sleep(0.1)                        # 等待 100 ms
self.scpi.write("OUTPUT2:STATE OFF")   # 禁用输出
self.scpi.write("GEN:STOP")            # 停止 ASG
```

序列正确。`time.sleep(0.1)` 给 DAC 时间将输出拉到零再禁用，避免瞬态跳变。

`main_window.py` 的 `closeEvent`（第 312-318 行）在窗口关闭时调用 `safe_shutdown()`，但**没有将 `self.client` 置为 None**，这是安全的——`safe_shutdown()` 内部将 `self.idn` 置空，`self.scpi._sock` 置空，后续 `_refresh_waveforms` 调用时 `isinstance` 检查仍然安全。

### D7 — 缺少 SCPI 采集命令 ❌ 阻塞

**严重性：阻塞**

这是最大的问题。`rp_client.py` 完全没有实现任何 SCPI 采集命令：
- 无 `ACQ:RST`
- 无 `ACQ:START`
- 无 `ACQ:TRIG NOW`
- 无 `ACQ:SOUR1:DATA?`
- 无 `ACQ:SOUR2:DATA?`

这意味着**连接到真实 Red Pitaya 后，IN1/IN2 波形显示为零**（`_refresh_waveforms` 只从 `MockRedPitayaClient` 获取数据）。

`HOST_APP_DESIGN.md` 第 63 行承认了这一点：

> In real hardware mode, V1 does not yet acquire Red Pitaya ADC samples or FPGA internal debug data.

但 GUI 没有在非 mock 模式下提示用户"当前无法读取 ADC 数据"。用户连接真实硬件后看到全零波形会感到困惑。

**建议**：在下一版本中添加 `rp_client.py` 的 `read_in1()` / `read_in2()` 方法，实现完整的 `ACQ:*` SCPI 流程。

---

## 6. E 类：安全检查

### E1 — frequency_hz 范围 ✅

`safety.py` 第 34-37 行：限制 `0.1 Hz ≤ frequency_hz ≤ 1000.0 Hz`。
GUI 层 `QDoubleSpinBox.setRange(0.1, 1000.0)` 也做了同样限制（`main_window.py` 第 106 行）。

双层保护，正确。

### E2 — amplitude_v 范围 ✅

`safety.py` 第 38-40 行：限制 `0.0 V ≤ amplitude_v ≤ 1.0 V`。
GUI 层 `QDoubleSpinBox.setRange(0.0, 1.0)`（第 110 行）。

### E3 — abs(offset) + amplitude ≤ 1.0 V ✅

`safety.py` 第 42-43 行：`abs(offset_v) + amplitude_v <= MAX_OUTPUT_ABS_V`。

正确。`MAX_OUTPUT_ABS_V = 1.0`。

### E4 — amplitude 是 SCPI 幅度而非 Vpp ✅

README 第 66 行明确说明：

> `amplitude_v` is the Red Pitaya SCPI amplitude value, not Vpp. The default `0.2 V` usually corresponds to about `0.4 Vpp`.

文档准确。

### E5 — GUI 层 + safety.py 层双层保护 ✅

- GUI 层：`QDoubleSpinBox` 的 `setRange()` 限制输入
- 业务层：`main_window.py` 第 210 行 `apply_scan_settings()` 中先调用 `validate_scan_settings()`，再调用 `client.apply_triangle_scan()`
- `rp_client.py` 第 38 行 `apply_triangle_scan()` 内部也调用 `validate_scan_settings()`

双层校验正确。

### E6 — 异常时 OUT2 安全 ✅

`main_window.py` 的 `closeEvent` 无论正常关闭还是异常都会调用 `safe_shutdown()`。`disconnect_from_device()` 也是一样。

一个边缘情况：如果程序被 `kill -9` 或任务管理器强制终止，`atexit` handler 不会被调用。文档中应该提示用户：如果 OUT2 被异常保持在高状态，可以通过 Red Pitaya 的 `GEN:RST` 网页界面或 SSH 进去手动关闭。

当前代码没有注册 `atexit` handler。虽然 `closeEvent` 覆盖了大部分场景，但 `atexit` 可以覆盖 Python 层面的 `sys.exit()` 和正常退出。建议在 `safety.py` 中添加 `atexit.register()` 机制。

### E7 — `offset_spin` 范围与实际可用范围不一致 ⚠️

`main_window.py` 第 114 行：`self.offset_spin.setRange(-1.0, 1.0)`。

但实际可用范围受 `amplitude_v` 制约：`abs(offset) + amplitude ≤ 1.0`。例如用户设 `amplitude=0.5`，则 offset 实际可用范围只有 `-0.5` 到 `+0.5`。GUI 允许输入 `-0.8`，然后 Apply 时报错。

**建议**：在 `amplitude_spin.valueChanged` 信号上动态调整 `offset_spin` 的最大最小值。

---

## 7. F 类：GUI 和线程检查

### F1 — GUI 是否会卡死 ✅（当前实现正确）

当前版本所有 SCPI 操作都是同步的（`write`/`query` 直接堵塞调用线程），但由于：
1. 没有后台采集线程（因为根本没有采集）
2. SCPI 命令在 GUI 线程直接发送，但命令很短（几十字节），网络延迟 < 100ms

当前不会导致明显的 GUI 卡死。但**一旦添加 SCPI 采集轮询**，必须在后台线程中运行，否则采集的 `recv` 阻塞（尤其是 BIN 模式 16k 点传输）会让 GUI 完全卡死。

### F2 — Mock 模式不需要连接硬件 ✅

Mock 模式通过 `MockRedPitayaClient` 实现，无需网络。启动时默认选中 Mock Mode 复选框（`main_window.py` 第 165 行）。

### F3 — pyqtgraph 是否只在主线程更新 ✅

`waveform_plot.py` 的 `set_data()` 方法调用 `pg.PlotDataItem.setData()`。当前所有 `set_data` 调用都在 `_refresh_waveforms()` 中，该函数通过 `QTimer.timeout` 信号触发，`QTimer` 的回调在主线程（Qt 事件循环）中执行。正确。

如果未来添加后台采集线程，需要注意：采集线程不能直接调用 `set_data()`，必须通过 Qt Signal/Slot 机制将数据传到主线程。

### F4 — 状态栏 ✅

状态栏正确显示：
- 连接状态：`connect_to_device()` 中显示 `"Connected: {idn}"`；`disconnect_from_device()` 中显示 `"Disconnected; OUT2 safe shutdown complete"`
- SCPI 错误：通过 `_show_status_error()` 显示 `"Error: {exc}"`
- 扫描状态：`apply_scan_settings()` 中显示参数详情

### F5 — error_internal 占位 ❌ 部分问题

`main_window.py` 第 149-157 行：

```python
self.error_plot = WaveformPlot("error_internal", "placeholder")
self.error_label = QLabel(
    "error_internal unavailable until FPGA debug buffer is added"
)
```

问题：

1. **error_plot 是一个功能齐全的 pyqtgraph 控件**，可以缩放、平移、右键菜单。尽管标签说"不可用"，但 plot 本身交互完整。在 Mock 模式下，`error_internal` **被填充了非零波形**（`mock_client.py` 第 57 行：`error_placeholder = self.settings.offset_v + 0.2 * envelope`），这可能误导用户以为是真实数据。
2. **QLabel 文字可能被 plot 遮挡或被用户忽略**。建议将 error_plot 设置为不可交互（`setEnabled(False)` / `setMouseEnabled(False, False)`），或者用半透明覆盖层替代单独的 QLabel。
3. Mock 模式下 `error_internal` 不应该有非零数据——这与"不假装能读取"的要求冲突。建议 Mock 模式下 error_internal 始终为零，或者将整个 error_plot 在 V1 中设为灰色禁用状态。

---

## 8. G 类：数据保存检查

### G1 — Save CSV ✅（基本正确）

`data_logger.py` 的 `save_waveforms_csv()` 保存了 `time_s`、`in1_pd_v`、`in2_ref_v`、`error_internal_placeholder` 四列。

问题：

1. **CSV 中未写入扫描参数和实验备注**。虽然 `frame.attrs["notes"]` 设置了备注，但 `pandas.DataFrame.attrs` 不写入 CSV 文件（attrs 是 DataFrame 的内存属性，`to_csv` 不保留）。备注实际丢失了。
2. **时间轴不在第一列**。DataFrame 中列顺序是 `time_s, in1_pd_v, in2_ref_v, error_internal_placeholder`——时间轴在第一列，这是正确的。
3. **文件名由用户通过对话框指定**，不包含自动时间戳。建议默认文件名带时间戳（如 `waveforms_20260626_143052.csv`），防止覆盖。

### G2 — Save PNG ✅

`data_logger.py` 第 25-28 行：使用 `widget.grab().save()` 截图。这是 PySide6 的标准截图方法，能正确保存。

但 `save_plot_png()` 截图的是 `self.plots_panel`，包含了三个绘图区域 + error_label。如果 error_label 文字过长被截断，PNG 也会截断。问题不大。

### G3 — 保存文件名带时间戳 ❌

未实现。文件名由 `QFileDialog.getSaveFileName` 默认值决定（`waveforms.csv` / `waveforms.png`），不带时间戳。

---

## 9. 其他发现

### 9.1 `_refresh_waveforms` 始终运行 ⚠️

`QTimer` 在 `__init__` 中启动（`self.timer.start()`），且**从未停止**。即使断开连接、未连接、或窗口最小化，它仍然每 100ms 触发一次 `_refresh_waveforms()`，调用三次 `set_data()`。这浪费 CPU。

**建议**：断连后停止 timer（`self.timer.stop()`），连接成功后再启动。

### 9.2 Mock 波形时间窗口过短 ⚠️

`mock_client.py` 第 50 行：`span_s = 2e-3`（2 ms）。对于 50 Hz 三角波扫描，2 ms 只覆盖 0.1 个周期，用户几乎看不到扫描包络效果。虽然物理上 2 ms 对应 dec=256 时的 ~512 个 ADC 采样窗口，但对于用户体验来说太短。

**建议**：将 `span_s` 增大到至少 40 ms（50 Hz 的两个周期），或做成可配置参数。

### 9.3 Mock 模式下 IN2 的 4.6 MHz 波形混叠严重 ⚠️

`mock_client.py` 以 2048 点采样 2 ms 窗口，等效采样率约 1 MSPS。对 4.6 MHz 信号来说只有约 0.22 采样/周期——严重欠采样。pyqtgraph 的渲染会将欠采样正弦波显示为奇怪的拍频图案。

**建议**：Mock 模式下对 IN2（REF）信号做降频模拟或使用更高采样点数，使波形在 GUI 中看起来合理。

### 9.4 `.venv` 已存在但未被 `requirements.txt` 使用 ⚠️

`software/redpitaya_lock_host/.venv/` 目录已存在（含 Python 3.x），但 `pip list` 未验证是否安装了 `requirements.txt` 中的所有包。`run.bat` 没有激活 venv。用户可能以为装好了，实际缺包。

---

## 10. 必须修复的问题（阻塞硬件测试）

| 编号 | 文件 | 问题 | 严重性 |
|------|------|------|--------|
| M1 | `main.py` | 不接受 `--mock` 参数，`python -m redpitaya_lock_host.main --mock` 会崩溃 | 阻塞 |
| M2 | `rp_client.py` | 完全缺少 SCPI 采集命令（`ACQ:SOUR1:DATA?` 等），连接真实硬件时 IN1/IN2 显示为零 | 阻塞 |
| M3 | `main_window.py:276` | `_refresh_waveforms()` 只从 `MockRedPitayaClient` 获取数据，`RedPitayaClient` 连接后没有数据源 | 阻塞 |
| M4 | `data_logger.py:19-22` | `DataFrame.attrs` 不写入 CSV，实验备注丢失 | 中等 |
| M5 | `run.bat:3` | 未激活 venv，使用系统全局 Python | 中等 |
| M6 | `README.md:26` | `cd /d` 在 PowerShell 中报错 | 中等 |
| M7 | `main_window.py:157` | error_internal plot 在 Mock 模式下显示非零波形，与"不假装能读"冲突 | 中等 |

---

## 11. 建议优化的问题

| 编号 | 文件 | 建议 |
|------|------|------|
| S1 | `main_window.py:49-52` | timer 始终运行，断连后应停止 |
| S2 | `main_window.py:114` | `offset_spin` 范围未随 `amplitude_spin` 动态调整 |
| S3 | `mock_client.py:50` | `span_s = 2e-3` 太短，50 Hz 扫描不可见 |
| S4 | `mock_client.py:52-53` | 4.6 MHz 在 1 MSPS 等效采样下严重欠采样 |
| S5 | `safety.py` | 缺 `atexit.register()` 安全兜底 |
| S6 | `main_window.py:273` | 非 mock 模式无数据时应在 plot 上显示提示文字而非全零 |
| S7 | `data_logger.py:9` | 默认文件名应带时间戳 |
| S8 | `requirements.txt:5` | `pyyaml` 应写为标准名称 `PyYAML` |
| S9 | `main_window.py:65` | mock_check 默认选中但标签为 "Mock Mode"，建议加 tooltip 说明 |

---

## 12. 可以暂缓的问题

| 编号 | 说明 |
|------|------|
| D1 | `acquisition_worker.py` 缺失——V1 不需要，等添加 SCPI 采集时补上 |
| D2 | 无 Red Pitaya OS 版本检查（`*IDN?` 后的固件版本解析） |
| D3 | 无 LV/HV 增益检测 |
| D4 | `safety.py` 是纯函数校验，不是有状态的监控器 |
| D5 | `mock_client.apply_triangle_scan()` 参数校验与 `rp_client` 重复——可统一 |

---

## 13. 运行命令建议

当前项目可以通过以下方式运行：

**CMD（推荐用于 .bat）**:
```cmd
E:
cd E:\new\fpga_lock\v94\software\redpitaya_lock_host
.venv\Scripts\activate
python -m redpitaya_lock_host.main
```

**PowerShell**:
```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.venv\Scripts\activate
python -m redpitaya_lock_host.main
```

**直接双击 `run.bat`**（在 Windows 资源管理器中）也可以，但会使用系统 Python 而非 venv 中的 Python。

修复 M1 后，`python -m redpitaya_lock_host.main --mock` 应能正常工作并自动跳过 Mock Mode 复选框。

---

## 14. 给 Codex 的后续修复指令草案

```
请修复 E:\new\fpga_lock\v94\software\redpitaya_lock_host 上位机 V1 的以下阻塞问题：

1. main.py 添加 argparse，支持 --mock 参数：
   - 解析 --mock 后设置一个全局标志或通过 QApplication property 传递
   - 在 MainWindow 中根据该标志决定 mock_check 是否选中
   - 过滤掉 --mock 再传给 QApplication

2. rp_client.py 添加 SCPI 采集方法：
   - read_in1() -> np.ndarray  实现 ACQ:SOUR1:DATA? 查询
   - read_in2() -> np.ndarray  实现 ACQ:SOUR2:DATA?
   - 内部封装 ACQ:RST → ACQ:START → ACQ:TRIG NOW → 轮询
     ACQ:TRIG:FILL? → ACQ:SOUR1:DATA? → 解析字符串 → numpy array
   - 解析返回的 {v1,v2,...} 花括号格式
   - 添加 configure_acquisition(decimation) 方法

3. main_window.py 修复 _refresh_waveforms：
   - 区分 MockRedPitayaClient 和 RedPitayaClient
   - 对 RedPitayaClient 调用 read_in1()/read_in2()
   - 采集操作必须不阻塞 GUI（QTimer 回调本身在主线程，
     但 read_in1 同步等待网络——如果耗时 > 100ms 会卡。
     短期方案：降低刷新率到 500ms；长期方案：用 QThread）

4. data_logger.py 修复备注保存：
   - 在 CSV 文件头部写入 # 注释行，包含时间戳、实验备注、扫描参数
   - 或在 CSV 中添加 metadata_notes 列

5. run.bat 添加 venv 激活：
   @echo off
   setlocal
   cd /d "%~dp0"
   call .venv\Scripts\activate
   python -m redpitaya_lock_host.main %*
   endlocal

6. README.md 将 CMD 语法改为 PowerShell 兼容，或明确标注适用终端：
   - 添加 "For PowerShell" 和 "For CMD" 两套命令
   - “Run” 部分说明双击 run.bat 或在终端中运行

7. mock_client.py 中 error_internal 在 V1 应始终为零：
   - 修改 get_waveforms() 使 error_internal 恒为零
   - 或在 GUI 中将 error_plot 设为禁用/灰色

8. 安全增强：
   - safety.py 添加 atexit.register() 
   - main_window.py 断连后停止 QTimer

不要修改 E:\new\fpga_lock\v94\v0.94。
不要访问任何 weifang 目录。
修改后更新 docs/DEVELOPMENT_LOG.md。
```

---

*审查完成。报告保存于 `E:\new\fpga_lock\v94\software\redpitaya_lock_host\docs\CLAUDE_REVIEW_HOST_APP_V1.md`*
