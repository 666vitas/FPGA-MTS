# Roadmap

## What we are building

An FPGA-based laser locking signal chain inspired by the thesis, but implemented
as our own project.

## Module order

1. `TriangleScan`
   Verify slow scan output for the PZT path.
2. `QuadratureDDS`
   Verify modulation output and quadrature references.
3. `IQDemodulator`
   Verify that a known tone produces the expected I/Q values.
4. `PhaseTracker`
   Verify that measured phase follows an injected phase offset.
5. `IncrementalPID`
   Verify step response and saturation behavior.
6. `ThesisLockTop`
   Integrate the chain and expose host-visible registers.

## Suggested chapter-to-code mapping

- Thesis 3.2.1 -> `logic/scan_generator.py`
- Thesis 3.2.2 -> `logic/dds.py`, `logic/iq_demod.py`
- Thesis 3.2.3 -> `logic/pid_incremental.py`
- Thesis 3.2.4 -> `logic/phase_tracker.py`

## Immediate next coding step

The next step should be to make `TriangleScan` and `QuadratureDDS` testable with
small simulations. Once we can trust the generated waveforms, the rest of the
chain becomes much easier to debug.
