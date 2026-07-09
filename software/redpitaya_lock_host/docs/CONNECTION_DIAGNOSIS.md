# 连接诊断

## 关键点

能 ping 通 Red Pitaya 不代表 SCPI 可用。Red Pitaya 可以响应 ping，但 5000 端口仍然关闭。

## 端口

- `22`：SSH service。
- `80`：Web service。
- `5000`：SCPI server。

在当前实验室环境中，SSH 和 Web 可能可用，但 SCPI 关闭。上位机必须分别探测这些服务。

## 主机名和 IP 漂移

`rp-f0cb13.local` 可能解析到不同 IP，例如 `192.168.137.125` 或 `192.168.137.158`。这取决于 mDNS 缓存、网络共享状态和 Red Pitaya 重新连接时机。

V2 会解析主机名并显示当前 IP 列表。如果返回多个 IP，GUI 会警告用户，并允许手动选择 IP。硬件控制应使用选定 IP，不要盲目依赖 hostname。

## Probe 检查顺序

1. 解析 host 到 IP。
2. ping 选定目标。
3. 测试 TCP 端口 22。
4. 测试 TCP 端口 80。
5. 测试 TCP 端口 5000。

如果 22 打开但 5000 关闭，可以在 Official SCPI Mode 下通过 SSH 启动 SCPI server。

如果 Probe 显示 `SCPI True`，说明 5000 端口已经可用。不要重复启动 `redpitaya_scpi`，直接点击 `Connect SCPI`。

启动 SCPI 后出现 `Web False` 可以是正常现象，因为启动流程可能会停止 `redpitaya_nginx`。

V2 的 Probe、Start SCPI Server、Connect SCPI、Disconnect 和 acquisition 操作都在后台 worker 中执行。SSH timeout、密码错误或命令失败应显示在状态栏和 Connection log 中，不能卡死 GUI。

## PowerShell 启动提示

在 PowerShell 中运行 batch 文件：

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\run.bat
```

不要只输入 `run.bat`，PowerShell 默认不会从当前目录搜索脚本；需要写 `.\run.bat`。

## 模式边界

只有在 Official SCPI Mode 中才启动 `redpitaya_scpi`。启动它可能加载官方 v0.94 overlay，并可能覆盖 custom FPGA bitstream。

Custom FPGA Mode 下不要启动 SCPI overlay。当前 custom RTL 中 OUT1 是 `laser_error`，物理 OUT2 是 `selected_out2`。SCPI ASG 输出命令不是 custom FPGA OUT2 的控制路径。

`selected_out2` 通过 `custom_register_bank` 和 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选模式控制。HOLD/P_LOCK/PI_LOCK 在完成 timing、bitstream 和上板验证前，只能 scope-only。
