# Thesis FPGA Lock Project

This directory is a clean-room project skeleton for implementing the FPGA
signal-processing chain described in the thesis:

1. Generate a triangle scan for the laser PZT.
2. Generate a sinusoidal modulation for the laser current.
3. Acquire the saturated-absorption PD signal from the ADC.
4. Demodulate the signal with in-phase and quadrature references.
5. Estimate and compensate phase delay.
6. Generate an error signal.
7. Run fast and slow PID loops for current and PZT control.

The implementation is intentionally kept separate from Linien. We can study
Linien for ideas, but the modules here should stay understandable and owned by
you.

## Proposed build order

1. `scan_generator.py`
   Output a controllable triangle wave and confirm DAC behavior.
2. `dds.py`
   Generate sinusoidal modulation and quadrature references.
3. `iq_demod.py`
   Multiply ADC input with I/Q references and low-pass the results.
4. `phase_tracker.py`
   Estimate the phase delay from the I/Q outputs and rotate the reference.
5. `error_signal.py`
   Select the in-phase component as the lock error signal.
6. `pid_incremental.py`
   Build fast and slow control loops.
7. `top.py`
   Wire the full chain to ADC, DAC, and control/status registers.

## First milestone

The first hardware milestone is modest on purpose:

- ADC input is sampled.
- Triangle scan is produced.
- One DAC outputs the scan waveform.
- The other DAC outputs the modulation waveform.
- A host can read back raw ADC and scan values.

Once that works, we add demodulation and locking.
