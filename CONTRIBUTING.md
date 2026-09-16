# Contributing to FPGA-MTS

FPGA-MTS is a research-stage FPGA/host system that can affect real laboratory hardware. Contributions are welcome, but changes must remain reviewable across source code, verification evidence, and hardware-safety impact.

## Before opening work

1. Read [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md), [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md), and [`ROADMAP.md`](ROADMAP.md).
2. Check existing issues and pull requests so a new change does not recreate obsolete work or compete with the current gate.
3. Use the structured GitHub issue forms for bugs, enhancements, or hardware validation when the work benefits from public tracking.
4. Keep the change scoped to one clear purpose.
5. Do not mix generated Vivado output, unrelated cleanup, and functional changes in the same pull request.
6. If the change affects registers, state semantics, acquisition, or output behavior, update `docs/HOST_FPGA_INTERFACE.md` as needed.
7. Do not claim hardware validation unless the relevant experiment was actually performed and recorded.

Maintainer responsibilities and merge authority are documented in [`MAINTAINERS.md`](MAINTAINERS.md).

## Pull request expectations

A useful pull request should state:

- what problem it solves;
- which FPGA/Host/documentation paths are affected;
- whether interfaces or hardware behavior change;
- what verification was run;
- what was not run;
- known risks or limitations;
- whether a hardware gate is required before merge or release;
- whether third-party provenance or licensing is affected.

For RTL changes, follow [`docs/FPGA_DEVELOPMENT_RULES.md`](docs/FPGA_DEVELOPMENT_RULES.md). In general, relevant RTL simulation plus synthesis/implementation/timing evidence is expected before a change is described as release-ready.

A pull request may be closed rather than merged when its baseline has been superseded by later work. In that case, the maintainer should record why the branch is obsolete so future contributors do not treat it as a second active implementation.

## Evidence vocabulary

Use evidence labels precisely in issue/PR prose:

- **source inspected** — code/documentation was read;
- **test passed** — a named automated test was actually executed;
- **timing/build passed** — the cited Vivado reports correspond to the cited source baseline;
- **board observed** — behavior was measured on the Red Pitaya;
- **physical lock observed** — the laser/actuator path was physically exercised and the observation conditions are recorded.

Do not collapse these into a generic "works" statement.

## Hardware-affecting changes

Changes involving `OUT2`, feedback gain, polarity, output range, lock-state transitions, PZT/Scan routing, or register semantics require extra care. Do not automatically increase gain, widen hardware ranges, enable automatic relock, or bypass human approval gates.

A software, simulation, or timing result must not be presented as physical laser-lock evidence.

When recording a hardware result, include the FPGA source commit, candidate/release identity, bitstream hash when available, Host/interface identity, Red Pitaya model, physical wiring, relevant limits, and the measurement source. The hardware-validation issue form is designed for this purpose.

## Documentation contributions

Documentation improvements are encouraged, especially when they make setup, architecture, evidence boundaries, or reproducibility clearer. Current-state claims should link back to `docs/CURRENT_STATUS.md` instead of duplicating mutable status in many places.

The clean-clone workflow is an active maintenance item in [issue #5](https://github.com/666vitas/FPGA-MTS/issues/5). Until it is closed, do not upgrade maintainer-local paths or commands into portable instructions without reproducing them from an appropriate environment.

## Third-party code and licenses

Do not copy code from papers, repositories, vendor examples, or other external sources without preserving and checking the applicable license and attribution requirements. The repository currently contains third-party reference material with multiple licenses; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

The top-level licensing/provenance audit is tracked in [issue #4](https://github.com/666vitas/FPGA-MTS/issues/4). Do not resolve that issue by silently relicensing upstream material.

## Issues and support

When reporting a bug, include enough context to reproduce it where possible:

- commit or branch;
- FPGA bit/release identifier if hardware was involved;
- Host version/commit;
- Vivado/tool version when relevant;
- expected versus observed behavior;
- logs, screenshots, or measurements that do not contain secrets.

See [`SUPPORT.md`](SUPPORT.md) for reporting routes. For security-sensitive or hazardous hardware behavior, follow [`SECURITY.md`](SECURITY.md) instead of posting sensitive details publicly.