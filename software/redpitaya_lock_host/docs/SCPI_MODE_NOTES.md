# SCPI Mode Notes

## SCPI Ports

```text
SCPI server port: 5000
SSH port: 22
Web port: 80
```

Ping success does not mean SCPI is available.

SSH True does not mean SCPI True.

Web False does not necessarily affect host-app use.

## Start SCPI Server

Run these commands on the Red Pitaya board:

```bash
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

## Manual OUT2 Test

PowerShell minimum test command:

```powershell
python -c "import socket,time; h='192.168.137.180'; s=socket.create_connection((h,5000),5); cmds=['GEN:RST','SOUR2:FUNC TRIANGLE','SOUR2:FREQ:FIX 50','SOUR2:VOLT 0.05','SOUR2:VOLT:OFFS 0','OUTPUT2:STATE ON','SOUR2:TRig:INT']; [s.sendall((c+'\r\n').encode()) or time.sleep(0.1) for c in cmds]; s.close()"
```

Replace `192.168.137.180` with the current Red Pitaya IP address.

For a `50 Hz` triangle wave, the period is:

```text
1 / 50 Hz = 20 ms
```

The GUI CH4 panel is a generated preview, not a measured OUT2 signal. It now uses a dedicated preview time axis so low-frequency output settings such as `triangle / 50 Hz / 0.05 V / offset 0` show complete cycles. Real OUT2 must still be verified with an oscilloscope, or with a carefully limited physical loopback from OUT2 to IN1. Keep IN1/IN2 within ±1 V.

## Stop Output

```powershell
python -c "import socket,time; h='192.168.137.180'; s=socket.create_connection((h,5000),5); cmds=['SOUR1:VOLT 0','SOUR2:VOLT 0','OUTPUT1:STATE OFF','OUTPUT2:STATE OFF','GEN:STOP']; [s.sendall((c+'\r\n').encode()) or time.sleep(0.1) for c in cmds]; s.close()"
```

## SCPI Output Command Order

The V2 client applies OUT1/OUT2 settings in this order:

```text
SOURn:FUNC
SOURn:FREQ:FIX
SOURn:VOLT
SOURn:VOLT:OFFS
OUTPUTn:STATE ON/OFF
SOURn:TRig:INT
```

Do not use the old `SOUR2:TRIG:IMM` command path for V2 OUT2 apply.
