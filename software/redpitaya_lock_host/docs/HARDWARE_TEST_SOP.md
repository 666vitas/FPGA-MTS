# 硬件测试 SOP

按本顺序执行。前面的检查没有通过之前，不要连接 PD、laser scan / PZT 或任何真实执行器。

当前上位机开发目录：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

## 1. 只做 Probe

1. 不连接任何实验信号。
2. 启动上位机。
3. 输入 `rp-f0cb13.local` 或 Red Pitaya 直接 IP。
4. 点击 `Probe`。
5. 确认 resolved IP、ping、端口 22、端口 80、端口 5000 的状态。

成功现象：GUI 显示网络和端口状态，不冻结。

失败处理：如果 IP 漂移或端口不通，先修网络，不继续接线。

## 2. 通过 SSH 启动 SCPI Server

如果端口 5000 不可用，但端口 22 可用：

1. 输入 SSH 用户名，通常是 `root`。
2. 输入 SSH 密码。
3. 点击 `Start SCPI Server`。
4. 确认 GUI 报告 5000 端口可用。

如果 Probe 已经显示 `SCPI True`，跳过本节，直接点击 `Connect SCPI`。

启动 SCPI 后 `Web False` 不一定是失败，因为 `redpitaya_nginx` 可能被停止以便 `redpitaya_scpi` 监听 5000 端口。

等效手动命令：

```sh
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

## 3. PC 侧确认端口

在 PowerShell 中运行：

```powershell
Test-NetConnection rp-f0cb13.local -Port 5000
```

或使用当前选定 IP：

```powershell
Test-NetConnection 192.168.137.125 -Port 5000
```

成功现象：`TcpTestSucceeded` 为 `True`。

## 4. 连接 SCPI

1. 点击 `Connect SCPI`。
2. 确认 `*IDN?` 返回 Red Pitaya 响应。

失败处理：如果无响应，不继续输出测试，先检查 5000 端口和 `redpitaya_scpi` 状态。

## 5. OUT2 示波器测试

本节只用于 Official SCPI Mode。

1. 只把 OUT2 接到示波器。
2. 设置 OUT2 waveform 为 `triangle`。
3. 设置 frequency 为 `50 Hz`。
4. 设置 `amplitude_v = 0.05 V`。
5. 设置 `offset_v = 0 V`。
6. Enable OUT2 并点击 `Apply`。
7. 在示波器上确认波形安全。

成功现象：示波器看到安全幅度的 50 Hz 三角波。

注意：CH4 是软件生成预览，不是实测 OUT2。50 Hz 三角波周期是 20 ms，GUI preview 只用于辅助判断；真实 OUT2 以示波器为准。

## 6. OUT1 示波器测试

本节只用于 Official SCPI Mode。

1. 只把 OUT1 接到示波器。
2. 设置 OUT1 waveform 为 `sine`。
3. 设置 frequency 为 `1 kHz`。
4. 设置 `amplitude_v = 0.05 V`。
5. 设置 `offset_v = 0 V`。
6. Enable OUT1 并点击 `Apply`。
7. 在示波器上确认波形安全。

## 7. IN1 采集测试

1. 把 signal generator 接到 IN1。
2. 使用 `1 kHz sine`、`100 mVpp`。
3. 开始 acquisition。
4. 确认 CH1 显示波形，并且 Vpp / min / max / mean 合理。

## 8. IN2 采集测试

1. 把 signal generator 接到 IN2。
2. 使用 `4.6 MHz sine`、`100 mVpp`。
3. decimation 设置为 `1`、`2`、`4` 或 `8`。
4. 开始 acquisition。
5. 确认 CH2 显示波形。

## 9. PD 连接

只有前面检查全部通过后，才允许：

1. 先用示波器测 PD signal。
2. 确认绝对电压小于 `1 V`。
3. 把 PD 接到 IN1。
4. 开始 acquisition 并验证 CH1。

如果 PD 信号接近或超过 Red Pitaya 输入范围，立即停止，不接 IN1。

## 10. Laser Scan / PZT 连接

当前 Custom FPGA 路径不允许直接接 Laser Scan / PZT。Official SCPI Mode 的安全扫描测试也必须满足以下条件：

1. 确认当前是 Official SCPI Mode。
2. 先只把 OUT2 接到示波器。
3. 从 `amplitude_v = 0.05 V` 开始。
4. 确认 amplitude 和 offset 对后级输入安全。
5. 不要直接从大 scan amplitude 开始。
6. 只有有单独安全 SOP 和用户明确授权后，才允许连接 scan / PZT。

## 11. Custom FPGA Mode 安全

加载 custom bitstream 时，当前 RTL 路由为：

- OUT1 = `laser_error`
- OUT2 = `selected_out2`

Custom FPGA Mode 下，OUT2 仍然只允许接示波器。不要连接 laser scan/PZT、D2-125、Scan input 或任何真实执行器。

当前 host 可以控制 custom FPGA register path 的 SAFE/SCAN，并且已有 HOLD/P_LOCK/PI_LOCK 候选控件；但 HOLD/P_LOCK/PI_LOCK 尚未完成 Vivado timing、bitstream 和上板验证。debug buffer、relock automation 和 actuator connection SOP 仍是后续工作。

使用 Custom FPGA Observe Mode 记录 OUT1/OUT2 手动示波器读数，并检查 OUT2/OUT1 比值。如果 OUT2 接近 +/-0.8 V、OUT2 Vpp 过大、OUT2 快速爬升或随机跳变，立即停止实验。
