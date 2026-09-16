# Source provenance and license boundaries

This file records the current high-level provenance model for FPGA-MTS. File-level copyright/license notices remain authoritative.

## Project-owned contributions

Unless a file or directory states otherwise, original FPGA-MTS contributions are licensed under the repository root `LICENSE` (BSD 3-Clause).

This category includes project-specific Host code, project-specific RTL/control logic, tests, maintenance scripts, and documentation created for FPGA-MTS, subject to any embedded third-party notices that may apply to an individual file.

## Red Pitaya-derived integration

The active FPGA design includes Red Pitaya-derived integration material, most visibly the `red_pitaya_top` lineage. The repository also retains an upstream Red Pitaya FPGA snapshot under:

```text
reference/open source/RedPitaya-FPGA-master/
```

The included upstream license is BSD-style and its copyright, conditions, and disclaimer must be preserved. The root BSD 3-Clause license does not remove or replace Red Pitaya notices attached to derived files.

## Linien reference snapshot

```text
reference/open source/linien/linien-master/
```

This tree is retained for engineering comparison/reference and includes its upstream GNU GPLv3 license and copyright notices. It is not relicensed by the FPGA-MTS root license.

The maintained project documents describe Linien as an architectural/reference influence; the current build authority is the FPGA-MTS source and interface documentation, not this reference snapshot.

## redpid reference snapshot

```text
reference/open source/redpid-master/
```

This tree retains its upstream GNU GPLv3 `COPYING` file and source notices. It is not relicensed by the FPGA-MTS root license.

## Vivado / AMD-Xilinx generated material

Tracked Vivado-generated project/run material can contain Xilinx/AMD copyright notices or tool-generated content. Those files retain their own vendor terms and notices and are not granted new rights by the FPGA-MTS root license.

Generated implementation evidence is also not the authority for source ownership or current release status.

## Historical and reference material

The repository contains historical experiments, reports, reference projects, and engineering notes. Public availability does not mean all such material is project-owned. Before copying a file out of its existing context, check:

1. the file header;
2. the nearest directory-level license/copyright notice;
3. `THIRD_PARTY_NOTICES.md`;
4. this provenance document.

## Root license interpretation

The root `LICENSE` applies to original FPGA-MTS contributions **except where another notice applies**. It does not relicense:

- GPL-licensed Linien/redpid reference trees;
- Red Pitaya material beyond the rights supplied by its upstream BSD license;
- AMD/Xilinx vendor-generated content;
- any other file carrying a different explicit license or copyright restriction.

If provenance is unclear for a file that is intended to move from `reference/` into an active build path, treat that as a blocker until the source and license are recorded.