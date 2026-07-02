# Usage

## Mock Mode

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\run_mock.bat
```

Mock mode does not connect to Red Pitaya. It is only used to check whether the GUI opens correctly.

## Real Connection Mode

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\run.bat
```

## GUI Modes

- Hardware Bring-up: Official SCPI Mode, Probe, Start SCPI Server, Connect SCPI, OUT2 Safe Scan, and IN1/IN2 acquisition.
- Custom FPGA Observe: manual oscilloscope readings for IN1 PD/MTS, IN2 REF, OUT1 laser_error, and OUT2 laser_control. OUT2 remains scope-only.
- Lock Workflow: D2-125 replacement checklist for input safety, error observation, control observation, polarity, gain/limit, and future lock/relock steps.
- Data Log: export Markdown experiment logs to `docs/experiment_logs/`.

## Recommended Hardware Test Order

1. Open only the software first.
2. Probe.
3. Start SCPI Server.
4. Connect SCPI.
5. Connect OUT2 to the oscilloscope.
6. Set OUT2 to `triangle / 50 Hz / 0.05 V / offset 0`.
7. Apply.
8. Confirm the OUT2 waveform on the oscilloscope.
9. Connect IN1 to a small-signal source for testing.
10. Connect IN2 to a 4.6 MHz REF small-signal source for testing.
11. Connect the experimental chain last.

## OUT1/OUT2 Preview

CH3 and CH4 are generated software previews, not measured ADC data.

The previous preview display reused the IN1/IN2 acquisition time axis. With the default `sample_count=2048` and `decimation=1024`, the acquisition window is about:

```text
2048 / (125e6 / 1024) = 16.78 ms
```

A 50 Hz triangle wave has a 20 ms period, so the old preview window was shorter than one full period and could not show a complete triangle cycle.

The preview now uses an independent time axis configured by:

```yaml
preview:
  cycles: 2
  min_points: 1024
  max_points: 5000
```

For 50 Hz, CH4 preview now covers two complete periods, about 40 ms. This preview is still not a measured OUT2 waveform.

To measure real OUT2, use an oscilloscope. A physical loopback test such as OUT2 -> IN1 is possible only with safe amplitudes, and Red Pitaya IN1/IN2 must stay within ±1 V.

## Safety Notes

Red Pitaya IN1/IN2 absolute input voltage must not exceed ±1 V.

Before connecting OUT1/OUT2 to a laser, confirm amplitude, frequency, and offset on an oscilloscope.

Do not drive the laser scan/PZT input with a large signal at the beginning.

Recommended initial OUT2 setting: `50 Hz`, `0.05 V`, `0 offset`.
