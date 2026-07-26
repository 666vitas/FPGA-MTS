Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: ARCHITECTURE
Last-Updated: 2026-07-26

# FPGA Realtime ERROR-Crossing Lock Plan

## 1. Goal

The current board can generate and expose an MTS error signal, but a reliable laser lock has not been demonstrated. The next design must not ask Windows, Linux polling, or a historical PZT count to decide the exact lock instant.

The minimum reliable rule is:

```text
The host selects which spectral feature to use.
The FPGA decides the exact lock instant from the current realtime ERROR signal.
The FPGA captures the current OUT2 and runs the realtime feedback.
```

This plan learns the minimum useful locking principles from Linien without copying Linien code or adding machine learning.

## 2. Existing path that remains valid

```text
IN1 PD + IN2 REF
        ↓
laser_lock_core: mixer + LPF
        ↓
laser_error
        ├── OUT1 for observation
        ├── custom_debug_capture CH3
        └── error_setpoint_corrector
                    ↓
                lock_error
                    ↓
out2_lock_controller
                    ↓
selected_out2 → OUT2 → PZT/Scan input
```

Retain:

- mixer and LPF error generation;
- ramp generator;
- aligned PD/REF/ERROR/OUT2 capture;
- signed14 register contract;
- PZT absolute and correction limits;
- trigger-time capture of the actual current OUT2;
- SAFE, SCAN, and P_LOCK output selection;
- sticky event/generation readback;
- stale target rejection and SAFE on readback mismatch.

## 3. Root problem in the previous SIMPLE path

The old trigger treated a historical scan coordinate as the decisive lock condition:

```text
direction_match && inside_target_OUT2_window
```

That cannot distinguish:

- PZT rising/falling hysteresis;
- a zero crossing that moved between captures;
- scan-speed versus static-position offset;
- thermal drift;
- PZT creep;
- a command-side OUT2 count from the loaded physical node voltage.

A historical OUT2 value is useful only to reject neighboring spectral features. It is not the final lock point.

## 4. New target semantics

Rename the meaning conceptually:

```text
target_out2_counts  → guard_center_counts
target_window_counts → guard_half_width_counts
```

The register names are temporarily retained to avoid unnecessary protocol churn in the first patch.

The guard means:

> Only accept the requested ERROR crossing while the scan is in this approximate spectral region.

It does not mean:

> Stop at this old PZT count regardless of the current ERROR.

## 5. Gate L1: realtime ERROR crossing

The first implemented correction requires all of the following:

```text
state == ARMED
MODE == SCAN
ENABLE == 1
not saturated
scan direction matches
OUT2 is inside the guard
ERROR has first reached the requested source side
ERROR then reaches the requested destination side
```

For `NEG_TO_POS`:

```text
ERROR - SETPOINT <= -H
then
ERROR - SETPOINT >= +H
```

For `POS_TO_NEG`:

```text
ERROR - SETPOINT >= +H
then
ERROR - SETPOINT <= -H
```

The first implementation uses fixed `H = 4 counts`. This is a conservative timing-light starting point, not a final physical threshold. Hardware captures will decide whether a later CSR is justified.

The source-side state is reset if:

- the acquisition leaves ARMED;
- OUT2 leaves the guard;
- scan direction no longer matches;
- abort or runtime fault occurs.

This prevents a crossing observed elsewhere in the scan from being reused inside the target region.

## 6. Event and transition behavior

On a qualified crossing, the FPGA stores in the same clock domain:

```text
current OUT2
current ERROR
scan direction
ERROR crossing direction
config generation
```

The existing fast-control transaction then captures the actual current OUT2 as `LOCK_BIAS`, installs the active setpoint and limits, and changes to P_LOCK.

This preserves the correct no-command-jump principle:

```text
last scan command ≈ first lock bias command
```

It does not yet prove that the physical PZT/laser state will remain at the same frequency after scan removal. That must be measured with Kp=0 and then corrected by a verified nonzero P loop.

## 7. Development stages after L1

### L1-A — regression and timing

- run updated realtime crossing testbench;
- run all existing RTL and Host tests;
- classify unconstrained/no-clock paths;
- re-run routed implementation.

No bitstream before L1-A passes.

### L1-B — optional validate-only acquisition

Add a one-shot `ARM_VALIDATE` mode only after the active crossing path is stable in simulation.

Validate-only behavior:

```text
record qualified crossing event
remain in SCAN
never change OUT2, MODE, Kp, or LOCK_BIAS
```

This allows repeated comparison of actual crossing OUT2 values before enabling the actuator transition.

### L2 — P-only capture

After realtime crossing is verified on hardware:

```text
qualified crossing
→ capture actual OUT2
→ enter Kp=0 for a very short bounded diagnostic interval
→ FPGA-controlled small Kp enable
→ verify error moves toward setpoint
```

The normal workflow must eventually stop waiting indefinitely for a Windows `APPLY P` click. P enable and any gain ramp must be deterministic inside FPGA or a board-local controller, not network timed.

### L3 — lock supervisor

Only after P feedback works:

- monitor error magnitude/mean;
- monitor correction margin;
- monitor saturation and absolute limit;
- detect divergence and timeout;
- report `ACQUIRING`, `P_LOCKED`, `FAILED`, or `FAULT`;
- return to a defined safe state on failure.

No automatic relock in this phase.

### L4 — slow integral correction

Add a slow, limited integral term only if real P-only measurements show residual offset or long-term creep that P alone cannot remove.

Requirements:

- anti-windup;
- integral limit;
- reset on SAFE/SCAN/new acquisition;
- no integral during unqualified acquisition;
- hardware evidence that P-only is already stable.

## 8. Functions removed from the normal workflow

Do not delete source immediately, but remove these from the operator's normal lock path after replacement verification:

- Linux polling `lock-here`;
- direct `CAPTURE_LOCK_POINT` as the primary acquisition method;
- `HOLD SELECTED COUNT` as a lock prerequisite;
- historical OUT2 count as the final bias;
- indefinite `P_LOCK_KP0` waiting for Windows;
- manual PI mode as an operator state;
- GUI-maintained duplicate lock state.

They may remain under Engineer/legacy diagnostics until the realtime path is proven.

## 9. Functions intentionally not added now

- machine learning;
- automatic spectral-feature discovery;
- automatic relock;
- PSD analysis;
- IQ redesign;
- fast/slow dual actuator control;
- full Linien server replication;
- large GUI redesign.

## 10. Hardware acceptance sequence

After regression, constraints review, and new routed timing pass:

1. Burn one identified bitstream with matching host commit and VERSION.
2. Confirm MAGIC, VERSION, SAFE, SCAN, aligned capture, and no saturation.
3. Select one clean ERROR crossing and one scan direction.
4. Verify the event occurs only after the requested realtime crossing.
5. Confirm event OUT2 differs from the old guard center when the physical zero has moved.
6. First test Kp=0 transition continuity.
7. Then test a minimal nonzero Kp and verify the measured error decreases.
8. Require no output saturation, no correction-limit hit, no obvious spectral shift, and a controlled SAFE response.

## 11. Definition of success for the current gate

L1 is complete only when:

- historical guard hit alone cannot trigger;
- both requested crossing directions are covered in simulation;
- the event reports the actual current crossing sample;
- all prior regressions still pass;
- modified routed timing remains non-negative;
- unconstrained/no-clock paths are classified;
- hardware shows that the FPGA triggers on the current ERROR crossing rather than only on the old PZT coordinate.

L1 completion is not yet a claim of a locked laser. It is the prerequisite that makes a reliable closed-loop transition possible.
