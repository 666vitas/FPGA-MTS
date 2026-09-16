# Contributing to FPGA-MTS

FPGA-MTS is a research-stage FPGA/host system that can affect real laboratory hardware. Contributions are welcome, but changes must remain reviewable across source code, verification evidence, and hardware-safety impact.

## Before opening a pull request

1. Read `docs/PROJECT_CONTEXT.md` and `docs/CURRENT_STATUS.md`.
2. Keep the change scoped to one clear purpose.
3. Do not mix generated Vivado output, unrelated cleanup, and functional changes in the same pull request.
4. If the change affects registers, state semantics, acquisition, or output behavior, update `docs/HOST_FPGA_INTERFACE.md` as needed.
5. Do not claim hardware validation unless the relevant experiment was actually performed and recorded.

## Pull request expectations

A useful pull request should state:

- what problem it solves;
- which FPGA/Host/documentation paths are affected;
- whether interfaces or hardware behavior change;
- what verification was run;
- what was not run;
- known risks or limitations;
- whether a hardware gate is required before merge or release.

For RTL changes, follow `docs/FPGA_DEVELOPMENT_RULES.md`. In general, relevant RTL simulation plus synthesis/implementation/timing evidence is expected before a change is described as release-ready.

## Hardware-affecting changes

Changes involving `OUT2`, feedback gain, polarity, output range, lock-state transitions, PZT/Scan routing, or register semantics require extra care. Do not automatically increase gain, widen hardware ranges, enable automatic relock, or bypass human approval gates.

A software, simulation, or timing result must not be presented as physical laser-lock evidence.

## Documentation contributions

Documentation improvements are encouraged, especially when they make setup, architecture, evidence boundaries, or reproducibility clearer. Current-state claims should link back to `docs/CURRENT_STATUS.md` instead of duplicating mutable status in many places.

## Third-party code and licenses

Do not copy code from papers, repositories, vendor examples, or other external sources without preserving and checking the applicable license and attribution requirements. The repository currently contains third-party reference material with multiple licenses; see `THIRD_PARTY_NOTICES.md`.

## Issues

When reporting a bug, include enough context to reproduce it where possible:

- commit or branch;
- FPGA bit/release identifier if hardware was involved;
- Host version/commit;
- Vivado/tool version when relevant;
- expected versus observed behavior;
- logs, screenshots, or measurements that do not contain secrets.

For security-sensitive or hazardous hardware behavior, follow `SECURITY.md` instead of posting sensitive details publicly.