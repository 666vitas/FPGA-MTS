# Hardware Test SOP

Follow this order. Do not connect PD or laser scan / PZT until the earlier checks pass.

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
- OUT2 = `laser_control`

In Custom FPGA Mode, OUT2 remains oscilloscope-only. Do not connect it to laser scan/PZT or D2-125. The V2 host does not currently control custom FPGA parameters; future control requires RTL registers or a debug buffer.
