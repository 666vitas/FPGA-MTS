# Next FPGA Debug Buffer Plan

## Goal

Phase 2 should add a controlled way for the host app to read FPGA internal `error_internal` data. This document is only a plan. V1 does not modify FPGA RTL, Vivado project files, or bitstreams.

## Candidate Approach

1. Identify the internal fixed-point signal corresponding to `error_internal` in the FPGA design under `E:\new\fpga_lock\v94\v0.94`.
2. Add a small debug capture buffer in FPGA logic.
3. Trigger capture from either a simple register bit or a known timing event.
4. Store decimated `error_internal` samples in BRAM or an AXI-accessible buffer.
5. Expose buffer metadata:
   - sample count
   - sample rate or decimation factor
   - fixed-point format
   - overflow or clipping flags
6. Add a host read path that can fetch one capture frame without disturbing OUT2 scan control.
7. Convert fixed-point samples to engineering units in host software.
8. Display the captured internal error trace in the existing `error_internal` plot.

## Host Software Changes Needed Later

- Add a debug-buffer client module.
- Add a capture button and trigger state display.
- Add fixed-point scaling configuration to `config.yaml`.
- Add CSV columns for raw and scaled `error_internal`.
- Keep mock mode capable of generating compatible debug frames.

## Validation Plan Later

1. Simulate or inspect fixed-point width and scaling.
2. Test buffer readout with a known injected waveform.
3. Compare OUT1 oscilloscope signal against captured internal error trend.
4. Verify debug readout does not change OUT2 scan behavior.

## Explicit Non-Goals For V1

- No FPGA RTL edits.
- No Vivado project edits.
- No bitstream generation.
- No claim that real `error_internal` is readable today.
