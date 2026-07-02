# Lock Workflow Mode

Lock Workflow Mode is the host-side process view for gradually replacing the D2-125 workflow. It is not an automatic lock controller yet.

## D2-125 Replacement Map

```text
D2-125 Ramp
-> future FPGA scan generator / current Official SCPI OUT2 Safe Scan

D2-125 Error Input
-> FPGA mixer + LPF -> laser_error

D2-125 Servo Output
-> FPGA laser_control / OUT2

D2-125 Lock/Scan switch
-> future FPGA FSM + host Lock Workflow

D2-125 Relock / Lock Quality
-> future host judgment + FPGA state machine
```

## Current Steps

1. Input Safety Check.
2. Error Signal Observe.
3. Control Output Observe.
4. Direction / Polarity Check.
5. Gain / Limit Check.
6. Ready for Low-gain Lock Test.
7. Future Lock Engage.
8. Future Relock.

Each step records wiring, what to watch on the oscilloscope, pass criteria, stop conditions, and next steps.

## Current Limits

The host cannot currently read FPGA mixer/LPF/error snapshots or write FPGA PI parameters. Those features require a future `register_bank`, `debug_buffer`, or AXI register/readout path.
