# Maintainers

FPGA-MTS is currently maintained as a small research open-source project.

## Primary maintainer

- **[@666vitas](https://github.com/666vitas)** — primary maintainer and repository owner

The primary maintainer is responsible for:

- defining the active FPGA/Host development gate;
- triaging issues and closing obsolete work rather than leaving competing baselines open;
- reviewing and merging pull requests;
- maintaining the Host/FPGA interface contract;
- keeping simulation, timing, build, board, and laser-lock evidence distinct;
- approving release candidates and preserving rollback/provenance information;
- enforcing the hardware-safety boundary for `OUT2`, PZT/Scan, gain, polarity, limits, and SAFE behavior;
- maintaining third-party attribution and license provenance.

## Decision model

FPGA-MTS currently uses a maintainer-led model. For changes that affect hardware behavior, interface semantics, safety limits, or release evidence, the primary maintainer makes the final merge/release decision after the required verification is recorded.

A contribution is not accepted merely because it compiles or because a generated bitstream exists. The evidence required depends on the change:

- documentation-only changes: scope/diff review;
- Host changes: targeted tests and interface review as applicable;
- RTL changes: targeted simulation plus the current FPGA verification requirements;
- hardware-affecting changes: explicit safety impact and, when required by the active gate, board/lab validation;
- release changes: source identity, build identity, hashes, verification evidence, and known limitations.

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/FPGA_DEVELOPMENT_RULES.md`](docs/FPGA_DEVELOPMENT_RULES.md), and [`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md).

## Maintenance transparency

Current work should be visible through GitHub issues and pull requests when it represents a discrete maintainer responsibility. Historical branches, experiments, and generated assets are not treated as active work merely because they remain in Git history.

The current public maintenance priorities are tracked in [`ROADMAP.md`](ROADMAP.md).

## Adding maintainers

Additional maintainers may be added when they have demonstrated sustained contribution to the project and can review changes within the project's evidence and hardware-safety model. Repository access alone is not sufficient; the maintainer list and `CODEOWNERS` should be updated together when responsibility changes.