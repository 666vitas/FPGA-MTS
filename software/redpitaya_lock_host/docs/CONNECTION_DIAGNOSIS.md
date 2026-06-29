# Connection Diagnosis

## Key Point

Ping success does not mean SCPI is available. A Red Pitaya can respond to ping while port 5000 is closed.

## Ports

- `22`: SSH service.
- `80`: Web service.
- `5000`: SCPI server.

In the current lab setup, SSH and Web can be available while SCPI is disabled. The host app must probe these services separately.

## Hostname And IP Drift

`rp-f0cb13.local` may resolve to different IP addresses, for example `192.168.137.125` or `192.168.137.158`, depending on mDNS cache, network sharing state, and Red Pitaya reconnect timing.

V2 resolves the host and displays the current IP list. If more than one IP is returned, the GUI warns the user and allows manual IP selection. Hardware control should use the selected IP rather than blindly relying on the hostname.

## Probe Checklist

1. Resolve host to IP.
2. Ping the selected target.
3. Test TCP port 22.
4. Test TCP port 80.
5. Test TCP port 5000.

If 22 is open but 5000 is closed, use SSH to start the SCPI server.

If Probe shows `SCPI True`, port 5000 is already available. Do not start `redpitaya_scpi` again; click `Connect SCPI`.

`Web False` can be expected after starting SCPI because the startup flow stops `redpitaya_nginx`.

V2 performs Probe, Start SCPI Server, Connect SCPI, Disconnect, and acquisition operations in background workers. SSH timeout, wrong password, or a failed command should be reported in the status bar and Connection log instead of freezing the GUI.

## PowerShell Launch Note

In PowerShell, run the batch file as:

```powershell
Set-Location E:\new\fpga_lock\raunjian
.\run.bat
```

`run.bat` without `.\` is not searched from the current directory by PowerShell.

## Mode Boundary

Start `redpitaya_scpi` only when using Official SCPI Mode. Starting it may load the official v0.94 overlay and may overwrite the custom FPGA bitstream.

In Custom FPGA Mode, do not start the SCPI overlay. The current custom RTL routes OUT1 to `laser_error` and OUT2 to `laser_control`, so SCPI ASG output commands are not the custom FPGA output-control path.
