# Test Plan

Legacy note: this file documents the V1.1 hardware-test plan. For current V2 testing, especially Official SCPI Mode vs Custom FPGA Mode, use `HARDWARE_TEST_SOP.md` and `FPGA_MODE_BOUNDARY.md`.

Current host-app development directory:

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

## Required Hardware Test Order

Follow this order. Do not connect the laser scan / PZT or PD signal before the earlier checks pass.

1. Mock mode test.
2. OUT2 connected only to an oscilloscope; confirm a 50 Hz triangle wave.
3. IN1 connected to a 1 kHz / 100 mVpp signal source; verify real acquisition.
4. IN2 connected to a 4.6 MHz / 100 mVpp signal source; use decimation <= 8 and verify real acquisition.
5. Only then connect the PD signal.
6. Before PD input is connected to Red Pitaya IN1, confirm with an oscilloscope that the PD signal is less than +/-1 V.
7. Before OUT2 is connected to the laser scan / PZT input, confirm with an oscilloscope that the OUT2 amplitude and offset are safe.

## 1. Mock Mode Test

Purpose: verify the GUI, plotting, export, display modes, and scan preview without hardware.

Steps:

1. Run `run.bat --mock` or `python -m redpitaya_lock_host.main --mock`.
2. Confirm `Mock Mode` is checked.
3. Click `Connect`.
4. Click `Start Acquisition`.
5. Confirm CH1 and CH2 update.
6. Confirm CH3 is disabled and says `unavailable until FPGA debug buffer is added`.
7. Confirm CH4 changes when frequency, amplitude, or offset changes.
8. Click `Save CSV` and verify header lines include notes, scan settings, decimation, sample rate, and mock state.
9. Click `Save PNG` and verify the four-channel layout is captured.
10. Click `Stop Acquisition`, then `Disconnect`.

Expected result: GUI stays responsive and no hardware is required.

## 2. OUT2 Oscilloscope Test

Purpose: verify scan output before connecting the laser.

Steps:

1. Connect Red Pitaya OUT2 only to an oscilloscope.
2. Run `run.bat`.
3. Leave `Mock Mode` unchecked.
4. Connect to `rp-f0cb13.local` or the Red Pitaya IP.
5. Set `frequency_hz = 50`, `amplitude_v = 0.2`, `offset_v = 0`.
6. Enable `Scan Enable`.
7. Click `Apply Scan Settings`.
8. Confirm a safe 50 Hz triangle waveform on the oscilloscope.
9. Click `Stop Scan` and confirm output stops.

Expected result: OUT2 follows settings and safe shutdown disables output.

GUI note: CH4 is a generated preview, not measured OUT2. A 50 Hz triangle wave has a 20 ms period. The preview uses an independent time axis and defaults to at least two full cycles, but the real OUT2 result must still be checked with an oscilloscope.

## 3. IN1 Real Acquisition Test

Purpose: verify Red Pitaya IN1 ADC acquisition.

Steps:

1. Keep OUT2 disconnected from the laser.
2. Connect a signal generator to IN1 with `1 kHz / 100 mVpp`.
3. Select a moderate decimation such as `1024`.
4. Click `Start Acquisition`.
5. Verify CH1 shows the waveform and stats near 100 mVpp.
6. Confirm the GUI remains responsive while acquisition is running.
7. Click `Stop Acquisition`.

Expected result: CH1 displays real measured ADC data.

If OUT2 is looped back into IN1 for real output measurement, keep the IN1 absolute input voltage below ±1 V.

## 4. IN2 REF Acquisition Test

Purpose: verify Red Pitaya IN2 can observe the external 4.6 MHz REF.

Steps:

1. Connect a 4.6 MHz / 100 mVpp signal source to IN2.
2. Set decimation to `1`, `2`, `4`, or `8`.
3. Click `Start Acquisition`.
4. Verify CH2 shows the REF waveform or a stable high-frequency trace.
5. Increase decimation above `8` and confirm the aliasing warning appears.
6. Click `Stop Acquisition`.

Expected result: CH2 displays real measured ADC data, and high decimation warns about possible aliasing.

## 5. PD Connection Test

Purpose: safely transition to the experiment PD signal.

Steps:

1. Measure the PD chain output with an oscilloscope.
2. Confirm the signal is less than +/-1 V.
3. Connect PD output to Red Pitaya IN1.
4. Start acquisition and verify CH1.

Expected result: IN1 receives the PD signal without clipping.

## 6. Exit Safety Test

Purpose: verify the app does not leave acquisition or OUT2 running.

Steps:

1. Connect to hardware.
2. Start acquisition.
3. Apply a visible OUT2 scan on an oscilloscope.
4. Close the application window.

Expected result: acquisition stops, OUT2 amplitude is set to zero, OUT2 is disabled, generator stops, and the socket closes.
