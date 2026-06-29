# SCPI Server Startup

## Why Startup Is Needed

`redpitaya_scpi` may be disabled or not listening on port 5000 even when the board is reachable by ping, SSH, and Web. The host app therefore includes a `Start SCPI Server` action over SSH.

## Manual Commands

On the Red Pitaya:

```sh
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

From the PC, verify:

```powershell
Test-NetConnection rp-f0cb13.local -Port 5000
```

or test the selected resolved IP:

```powershell
Test-NetConnection 192.168.137.125 -Port 5000
```

## Important Warning

Starting `redpitaya_scpi` may load the official v0.94 overlay and may overwrite the currently loaded custom FPGA bitstream. Use this action only when that behavior is acceptable for the test step.

Use this action only in Official SCPI Mode. In Custom FPGA Mode, do not start `redpitaya_scpi` if the goal is to preserve the currently loaded custom mixer/LPF/error bitstream.

## V2 GUI Flow

1. Click `Probe`.
2. If SSH port 22 is available but SCPI port 5000 is unavailable, enter SSH credentials.
3. Click `Start SCPI Server`.
4. The app starts `redpitaya_scpi`, checks `ss -lntp | grep 5000`, and probes PC-side port 5000 again.
5. If port 5000 is reachable, connect SCPI and run `*IDN?`.

## Mode Meaning

Official SCPI Mode controls Red Pitaya's official ASG and ACQ interfaces through port 5000. OUT1/OUT2 can be sine/square/triangle/sawtooth outputs in that mode.

Custom FPGA Mode is different: with the current RTL, OUT1 is `laser_error` and OUT2 is `laser_control`. They are not official ASG outputs and are not controlled by SCPI waveform settings.
