# 上位机 V1.1 设计说明（历史参考）

本文件记录 V1.1 设计，属于历史参考。当前 V2 的模式边界、连接流程、Official SCPI Mode 与 Custom FPGA Mode 行为，请优先阅读：

- `HOST_APP_V2_DESIGN.md`
- `FPGA_MODE_BOUNDARY.md`
- `README.md`
- `docs/USAGE.md`

## 版本定位

V1.1 把 V1 从 mock-only GUI 升级为可做 Red Pitaya 硬件测试的上位机，支持真实 IN1 / IN2 SCPI acquisition。

## 架构

- `scpi_client.py`：底层 TCP socket SCPI transport。
- `rp_client.py`：Red Pitaya 业务封装，处理 `*IDN?`、OUT2 scan control、acquisition configuration、IN1 / IN2 reads 和 safe shutdown。
- `acquisition_worker.py`：`QThread` worker，把阻塞 SCPI acquisition 放到 GUI 线程之外，并通过 Qt signals 发送 numpy arrays。
- `safety.py`：scan validation 和 `atexit` fallback shutdown registry。
- `mock_client.py`：不需要硬件的 mock client，生成 IN1 / IN2 mock waveforms，并让 `error_internal` 保持 0。
- `main_window.py`：PySide6 GUI、四通道绘图、acquisition controls、export 和 status display。
- `waveform_plot.py`：可复用 pyqtgraph waveform widget。
- `data_logger.py`：CSV metadata export 和 PNG screenshot export。
- `main.py`：config loading 和 command-line parsing，包括 `--mock`。

## 命令行流程

`main.py` 用 `argparse` 解析 `--mock`，从 Qt argument list 中移除它，然后把 `start_mock=True` 传给 `MainWindow`。这样 Qt 不会拒绝自定义参数。

## 连接流程

1. 用户选择 mock mode 或 real hardware mode。
2. real mode 打开 SCPI socket 并发送 `*IDN?`。
3. 只有连接成功后，才启用 OUT2 和 acquisition controls。
4. SCPI 异常会显示在 status bar，不应卡死 GUI。

## OUT2 Scan 流程

应用 scan settings 时发送：

```text
GEN:RST
SOUR2:FUNC TRIANGLE
SOUR2:FREQ:FIX <Hz>
SOUR2:VOLT <V>
SOUR2:VOLT:OFFS <V>
OUTPUT2:STATE ON|OFF
SOUR2:TRig:INT
```

早期 V1 笔记曾使用 `SOUR2:TRIG:IMM`。V2 使用 `SOUR2:TRig:INT`，并且放在 output state command 之后。

停止 scan 时发送：

```text
OUTPUT2:STATE OFF
GEN:STOP
```

safe shutdown 时发送：

```text
ACQ:STOP
SOUR2:VOLT 0
wait 100 ms
OUTPUT2:STATE OFF
GEN:STOP
close socket
```

## Acquisition 流程

真实硬件 acquisition 在 `AcquisitionWorker` 中运行，不在 GUI 线程中运行。

配置命令：

```text
ACQ:RST
ACQ:DATA:FORMAT ASCII
ACQ:DATA:UNITS VOLTS
ACQ:DEC <N>
ACQ:TRIG:DLY 0
```

每帧读取：

```text
ACQ:START
ACQ:TRIG NOW
poll ACQ:TRIG:FILL?
ACQ:SOUR1:DATA?
ACQ:SOUR2:DATA?
ACQ:STOP
```

worker 通过 Qt signals 发出 IN1、IN2 和 sample rate。`main_window.py` 在主线程接收信号并更新 pyqtgraph。

## 四通道显示

- CH1：`IN1 / PD`，实测 ADC voltage，显示 Vpp / min / max / mean，并在接近 +/-1 V 时警告。
- CH2：`IN2 / REF`，实测 ADC voltage，显示 stats，并在 decimation > 8 时提示 aliasing 风险。
- CH3：`OUT1 / ERROR`，V1.1 中是 disabled placeholder；V1.1 不读取 FPGA `error_internal`。
- CH4：`OUT2 / SCAN`，按当前 scan settings 生成的软件三角波预览；不是实测 OUT2 voltage。

显示模式：

- Time Mode：CH1 和 CH2 按时间绘图。
- Spectrum Mode：CH1 使用 `x = OUT2 scan preview`、`y = IN1 / PD`。
- MTS Mode：预留给未来 `x = OUT2 scan preview`、`y = error_internal` 工作流，需要 FPGA debug buffer 支持。
