# 测试计划（历史 V1.1 参考）

本文件记录 V1.1 硬件测试计划，属于历史参考。当前 V2 测试，尤其是 Official SCPI Mode 与 Custom FPGA Mode 的边界，请优先阅读：

- `HARDWARE_TEST_SOP.md`
- `FPGA_MODE_BOUNDARY.md`
- `USAGE.md`

当前上位机开发目录：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

## 必须遵守的硬件测试顺序

按顺序执行。前面的检查没有通过之前，不要连接 laser scan / PZT 或 PD signal。

1. Mock mode test。
2. OUT2 只接示波器，确认 50 Hz 三角波。
3. IN1 接 1 kHz / 100 mVpp signal source，验证真实 acquisition。
4. IN2 接 4.6 MHz / 100 mVpp signal source，使用 decimation <= 8 并验证真实 acquisition。
5. 只有前面通过后，才连接 PD signal。
6. PD 接入 Red Pitaya IN1 之前，必须先用示波器确认 PD signal 小于 +/-1 V。
7. OUT2 接入 laser scan / PZT input 之前，必须先用示波器确认 OUT2 amplitude 和 offset 安全。

## 1. Mock Mode Test

目的：不连接硬件，验证 GUI、plotting、export、display modes 和 scan preview。

步骤：

1. 运行 `run.bat --mock` 或 `python -m redpitaya_lock_host.main --mock`。
2. 确认 `Mock Mode` 已选中。
3. 点击 `Connect`。
4. 点击 `Start Acquisition`。
5. 确认 CH1 和 CH2 更新。
6. 确认 CH3 disabled，并显示 `unavailable until FPGA debug buffer is added`。
7. 修改 frequency、amplitude 或 offset，确认 CH4 随之变化。
8. 点击 `Save CSV`，确认 header lines 包含 notes、scan settings、decimation、sample rate 和 mock state。
9. 点击 `Save PNG`，确认四通道布局被保存。
10. 点击 `Stop Acquisition`，再点击 `Disconnect`。

成功现象：GUI 保持响应，不需要硬件。

## 2. OUT2 示波器测试

目的：连接激光前，先验证 scan output。

步骤：

1. Red Pitaya OUT2 只接示波器。
2. 运行 `run.bat`。
3. 不勾选 `Mock Mode`。
4. 连接到 `rp-f0cb13.local` 或 Red Pitaya IP。
5. 设置 `frequency_hz = 50`、`amplitude_v = 0.2`、`offset_v = 0`。
6. Enable `Scan Enable`。
7. 点击 `Apply Scan Settings`。
8. 在示波器上确认安全的 50 Hz triangle waveform。
9. 点击 `Stop Scan`，确认输出停止。

成功现象：OUT2 跟随设置变化，safe shutdown 能关闭输出。

注意：CH4 是生成预览，不是实测 OUT2。50 Hz 三角波周期为 20 ms。真实 OUT2 仍必须用示波器检查。

## 3. IN1 真实采集测试

目的：验证 Red Pitaya IN1 ADC acquisition。

步骤：

1. 保持 OUT2 不接激光。
2. 把 signal generator 接到 IN1，使用 `1 kHz / 100 mVpp`。
3. 选择适中 decimation，例如 `1024`。
4. 点击 `Start Acquisition`。
5. 确认 CH1 显示波形，stats 接近 100 mVpp。
6. acquisition 运行时确认 GUI 仍响应。
7. 点击 `Stop Acquisition`。

成功现象：CH1 显示真实 ADC 数据。

如果用 OUT2 -> IN1 回环测真实输出，必须保证 IN1 绝对输入电压低于 +/-1 V。

## 4. IN2 REF 采集测试

目的：验证 Red Pitaya IN2 可以观察外部 4.6 MHz REF。

步骤：

1. 把 4.6 MHz / 100 mVpp signal source 接到 IN2。
2. decimation 设置为 `1`、`2`、`4` 或 `8`。
3. 点击 `Start Acquisition`。
4. 确认 CH2 显示 REF waveform 或稳定高频 trace。
5. 把 decimation 提高到 `8` 以上，确认 aliasing warning 出现。
6. 点击 `Stop Acquisition`。

成功现象：CH2 显示真实 ADC 数据，高 decimation 会提示 aliasing 风险。

## 5. PD 连接测试

目的：安全切换到实验 PD signal。

步骤：

1. 先用示波器测 PD chain output。
2. 确认信号小于 +/-1 V。
3. 把 PD output 接到 Red Pitaya IN1。
4. 开始 acquisition 并验证 CH1。

成功现象：IN1 接收到 PD signal 且没有 clipping。

## 6. 退出安全测试

目的：确认 app 不会在退出后留下 acquisition 或 OUT2 输出。

步骤：

1. 连接硬件。
2. 开始 acquisition。
3. 在示波器上应用一个可见 OUT2 scan。
4. 关闭应用窗口。

成功现象：acquisition 停止，OUT2 amplitude 设为 0，OUT2 disabled，generator stop，socket close。
