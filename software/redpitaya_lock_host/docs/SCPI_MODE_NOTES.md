# SCPI 模式说明

## SCPI 端口

```text
SCPI server port: 5000
SSH port: 22
Web port: 80
```

能 ping 通 Red Pitaya 不代表 SCPI 可用。

`SSH True` 不代表 `SCPI True`。

`Web False` 不一定影响上位机使用。

## 启动 SCPI Server

在 Red Pitaya 板端运行：

```bash
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

注意：启动 `redpitaya_scpi` 可能加载官方 overlay，可能覆盖当前 custom FPGA bitstream。Custom FPGA Mode 下如果目标是保留当前自定义 bitstream，不要启动 `redpitaya_scpi`。

## 手动 OUT2 测试

PowerShell 最小测试命令：

```powershell
python -c "import socket,time; h='192.168.137.180'; s=socket.create_connection((h,5000),5); cmds=['GEN:RST','SOUR2:FUNC TRIANGLE','SOUR2:FREQ:FIX 50','SOUR2:VOLT 0.05','SOUR2:VOLT:OFFS 0','OUTPUT2:STATE ON','SOUR2:TRig:INT']; [s.sendall((c+'\r\n').encode()) or time.sleep(0.1) for c in cmds]; s.close()"
```

把 `192.168.137.180` 替换为当前 Red Pitaya IP 地址。

`50 Hz` 三角波周期为：

```text
1 / 50 Hz = 20 ms
```

GUI 的 CH4 面板是软件生成的预览，不是实测 OUT2。真实 OUT2 必须用示波器确认；如果做 OUT2 -> IN1 物理回环，必须保证 IN1/IN2 在 +/-1 V 范围内。

## 停止输出

```powershell
python -c "import socket,time; h='192.168.137.180'; s=socket.create_connection((h,5000),5); cmds=['SOUR1:VOLT 0','SOUR2:VOLT 0','OUTPUT1:STATE OFF','OUTPUT2:STATE OFF','GEN:STOP']; [s.sendall((c+'\r\n').encode()) or time.sleep(0.1) for c in cmds]; s.close()"
```

## SCPI 输出命令顺序

V2 client 按下面顺序应用 OUT1/OUT2 设置：

```text
SOURn:FUNC
SOURn:FREQ:FIX
SOURn:VOLT
SOURn:VOLT:OFFS
OUTPUTn:STATE ON/OFF
SOURn:TRig:INT
```

V2 OUT2 apply 不使用旧的 `SOUR2:TRIG:IMM` 路径。
