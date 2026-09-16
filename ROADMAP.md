# FPGA-MTS Roadmap

This roadmap describes the public maintenance priorities for the repository. It is intentionally narrower than the long-term research vision: current work should first make the existing FPGA/Host system reproducible, auditable, safe, and physically validated.

Authoritative implementation status remains in [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md). This file is a maintainer-facing roadmap, not a substitute for verification evidence.

## Current milestone — LOCK-MVP-L1

**Objective:** demonstrate a real, repeatable PZT P-only laser lock using the current Red Pitaya FPGA/Host stack while preserving explicit SAFE behavior and traceable experiment identity.

The current milestone is complete only when the required hardware evidence is recorded. Simulation, routed timing, a GUI state, or a generated bitstream cannot independently close this milestone.

Tracked work:

- [#6 — Hardware validation: close the LOCK-MVP-L1 sustained P-only lock gate](https://github.com/666vitas/FPGA-MTS/issues/6)

## Open-source readiness

Before presenting FPGA-MTS as an easily reusable open-source package, two repository-level gaps should be closed:

- [#4 — Licensing: complete provenance audit and select a top-level OSS license](https://github.com/666vitas/FPGA-MTS/issues/4)
- [#5 — Reproducibility: document a clean clone-to-test workflow without laser hardware](https://github.com/666vitas/FPGA-MTS/issues/5)

These are not cosmetic tasks. Clear licensing and a reproducible no-laser entry path determine whether outside users can safely understand, test, and contribute to the project.

## First traceable release

After the hardware gate closes, publish the first release whose source, Host/interface state, bitstream hashes, Vivado inputs, verification reports, and board/laser evidence are all linked.

- [#7 — Release readiness: publish the first hardware-validated, traceable FPGA-MTS release](https://github.com/666vitas/FPGA-MTS/issues/7)

A release must not be promoted from `CANDIDATE` to `RELEASED` solely because synthesis/implementation succeeded.

## Later research directions

The following remain intentionally behind the current milestone:

- PI/Ki control and validated integral action;
- automatic relock and recovery logic;
- broader actuator architectures or dual-loop control;
- automatic phase/scan optimization;
- improved waveform visualization and operator guidance;
- data-driven or machine-learning parameter recommendation.

These directions should only be promoted into an active gate after the deterministic baseline is reproducible and physically validated.

## How to contribute

The most useful contributions at the current stage are those that improve:

- reproducibility from a clean clone;
- verification coverage and evidence quality;
- Host/FPGA interface clarity;
- release provenance;
- hardware-safety documentation;
- bounded, testable improvements to the current lock path.

Before proposing hardware-affecting changes, read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`MAINTAINERS.md`](MAINTAINERS.md), and [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md).