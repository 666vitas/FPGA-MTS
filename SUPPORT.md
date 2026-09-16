# Support

FPGA-MTS is a research-stage open-source project. Support is handled through the repository rather than through a commercial service channel.

## Questions and reproducibility problems

Open a GitHub issue when you have a concrete problem involving:

- installation or environment setup;
- reproducing documented Host or RTL behavior;
- unclear repository structure or maintained entry points;
- FPGA/Host interface behavior;
- a proposed bounded enhancement;
- a discrepancy between documentation and current source/evidence.

Before filing, check [`README.md`](README.md), [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md), and [`ROADMAP.md`](ROADMAP.md).

## Hardware problems

For hardware-affecting reports, include enough information to separate software state from physical state:

- FPGA source commit and candidate/release identity;
- Host version/commit when relevant;
- Red Pitaya model;
- actual connections for IN1/IN2/OUT1/OUT2;
- SAFE/SCAN/HOLD/P_LOCK state;
- amplitude/offset/limit/polarity values;
- whether the observation came from GUI/readback, oscilloscope, or the loaded PZT node;
- what happened immediately before the failure.

Do not connect two active outputs together or use an unverified output path merely to reproduce a report.

## Security or unsafe-output reports

Do **not** open a normal public issue for a security vulnerability or a report that could expose a dangerous hardware-control weakness before mitigation is available. Follow [`SECURITY.md`](SECURITY.md).

## What support does not imply

Maintainer guidance does not convert a research prototype into certified laboratory equipment. Contributors and users remain responsible for validating voltage ranges, actuator compatibility, optical/electrical safety, and experimental suitability for their own setup.