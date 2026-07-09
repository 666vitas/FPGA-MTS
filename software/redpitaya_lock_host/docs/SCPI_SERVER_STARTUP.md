# SCPI Server 启动说明

## 为什么需要启动

Red Pitaya 能 ping 通、SSH 可用、Web 可用，并不代表 `redpitaya_scpi` 已经在 5000 端口监听。所以上位机提供了通过 SSH 执行的 `Start SCPI Server` 操作。

## 手动命令

在 Red Pitaya 上运行：

```sh
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

在 PC 上验证：

```powershell
Test-NetConnection rp-f0cb13.local -Port 5000
```

也可以测试当前解析出的 IP：

```powershell
Test-NetConnection 192.168.137.125 -Port 5000
```

## 重要警告

启动 `redpitaya_scpi` 可能加载官方 v0.94 overlay，并可能覆盖当前已经加载的 custom FPGA bitstream。只有在当前测试步骤允许这种行为时，才可以启动。

该操作只用于 Official SCPI Mode。Custom FPGA Mode 下，如果目标是保留当前 custom mixer / LPF / register bitstream，不要启动 `redpitaya_scpi`。

## V2 GUI 操作流程

1. 点击 `Probe`。
2. 如果 SSH 端口 22 可用但 SCPI 端口 5000 不可用，输入 SSH 凭据。
3. 点击 `Start SCPI Server`。
4. 上位机会启动 `redpitaya_scpi`，检查 `ss -lntp | grep 5000`，并从 PC 侧再次探测 5000 端口。
5. 如果 5000 端口可连接，再连接 SCPI 并运行 `*IDN?`。

## 模式含义

Official SCPI Mode 通过 5000 端口控制 Red Pitaya 官方 ASG 和 ACQ 接口。在该模式下，OUT1/OUT2 可以作为 sine / square / triangle / sawtooth 输出。

Custom FPGA Mode 不同：当前 RTL 中 OUT1 是 `laser_error`，OUT2 是 `selected_out2`。它们不是官方 ASG 输出，也不由 SCPI waveform 设置控制。
