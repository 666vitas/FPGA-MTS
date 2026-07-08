# Hardware Test SOP

Follow this order. Do not connect PD or laser scan / PZT until the earlier checks pass.

Current host-app development directory:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

## 1. Probe Only

1. Do not connect any experiment signal.
2. Run the host app.
3. Enter `rp-f0cb13.local` or a direct Red Pitaya IP.
4. Click `Probe`.
5. Confirm the resolved IP, ping state, port 22, port 80, and port 5000.

## 2. Start SCPI Server Over SSH

If port 5000 is not available but port 22 is available:

1. Enter SSH username, usually `root`.
2. Enter SSH password.
3. Click `Start SCPI Server`.
4. Confirm the GUI reports port 5000 availability.

If Probe already shows `SCPI True`, skip this section and click `Connect SCPI`.

`Web False` is not automatically a failure after SCPI startup; `redpitaya_nginx` is stopped so `redpitaya_scpi` can listen on port 5000.

Manual equivalent:

```sh
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

## 3. PC-Side Port Confirmation

From PowerShell:

```powershell
Test-NetConnection rp-f0cb13.local -Port 5000
```

or use the selected resolved IP:

```powershell
Test-NetConnection 192.168.137.125 -Port 5000
```

`TcpTestSucceeded` should be `True`.

## 4. Connect SCPI

1. Click `Connect SCPI`.
2. Confirm `*IDN?` returns a Red Pitaya response.

## 5. OUT2 Oscilloscope Test

Use Official SCPI Mode for this test.

1. Connect OUT2 only to an oscilloscope.
2. Set OUT2 waveform to `triangle`.
3. Set frequency to `50 Hz`.
4. Set `amplitude_v = 0.05 V`.
5. Set `offset_v = 0 V`.
6. Enable OUT2 and click `Apply`.
7. Confirm the oscilloscope waveform is safe.

Note: CH4 is a generated preview, not a measured OUT2 signal. A 50 Hz triangle wave has a 20 ms period; the GUI preview now uses an independent time axis and defaults to at least two complete cycles. The oscilloscope remains the authority for real OUT2.

## 6. OUT1 Oscilloscope Test

Use Official SCPI Mode for this test.

1. Connect OUT1 only to an oscilloscope.
2. Set OUT1 waveform to `sine`.
3. Set frequency to `1 kHz`.
4. Set `amplitude_v = 0.05 V`.
5. Set `offset_v = 0 V`.
6. Enable OUT1 and click `Apply`.
7. Confirm the oscilloscope waveform is safe.

## 7. IN1 Acquisition Test

1. Connect a signal generator to IN1.
2. Use `1 kHz sine`, `100 mVpp`.
3. Start acquisition.
4. Confirm CH1 shows the waveform and reasonable Vpp / min / max / mean.

## 8. IN2 Acquisition Test

1. Connect a signal generator to IN2.
2. Use `4.6 MHz sine`, `100 mVpp`.
3. Set decimation to `1`, `2`, `4`, or `8`.
4. Start acquisition.
5. Confirm CH2 shows the waveform.

## 9. PD Connection

Only after the earlier checks pass:

1. Measure PD signal with an oscilloscope.
2. Confirm absolute voltage is less than `1 V`.
3. Connect PD to IN1.
4. Start acquisition and verify CH1.

## 10. Laser Scan / PZT Connection

Before connecting OUT2 to laser scan / PZT:

1. Confirm the current mode is Official SCPI Mode if this is an SCPI scan test.
2. Confirm OUT2 on an oscilloscope.
3. Start with `amplitude_v = 0.05 V`.
4. Confirm amplitude and offset are safe for the laser input.
5. Do not directly start with a large scan amplitude.
6. Only then connect OUT2 to scan / PZT.

## 11. Custom FPGA Mode Safety

When the custom bitstream is loaded, the current RTL routes:

- OUT1 = `laser_error`
- OUT2 = `selected_out2`

In Custom FPGA Mode, OUT2 remains oscilloscope-only. Do not connect it to laser scan/PZT, D2-125, or Scan/PZT. The current host can control the custom FPGA register path for SAFE/SCAN and has HOLD/P_LOCK/PI_LOCK candidate controls, but HOLD/P_LOCK/PI_LOCK have not completed Vivado timing, bitstream, or board validation. Debug buffers, relock automation, and actuator connection SOP remain future work.

Use Custom FPGA Observe Mode to enter manual scope readings for OUT1/OUT2 and check the OUT2/OUT1 ratio. If OUT2 approaches +/-0.8 V, if OUT2 Vpp is too large, or if OUT2 rapidly climbs/jumps, stop the experiment.
