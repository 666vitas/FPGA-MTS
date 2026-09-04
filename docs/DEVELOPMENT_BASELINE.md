# FPGA-MTS Development Baseline

- Status: ACTIVE
- Authority: final development baseline
- Freeze-Date: 2026-09-04
- Scope: LOCK-MVP-L1 后续 FPGA/Host 优化开发

本文件记录目录冻结后的开发基线。它不是第二套状态系统；当前事实状态仍以
`docs/CURRENT_STATUS.md` 为准，接口以 `docs/HOST_FPGA_INTERFACE.md` 为准。

## 当前入口

| 项目 | 基线 |
| --- | --- |
| 当前 FPGA 入口 | `v0.94/project/redpitaya.xpr` |
| 当前 Top | `red_pitaya_top` |
| 当前 Host | `software/redpitaya_lock_host` |
| 当前 skill | `.agents/skills` |
| 当前 Gate | `LOCK-MVP-L1` |

## 当前实验目标

FPGA OUT2 控制 PZT，实现 MTS error zero crossing 对应锁定。

## 当前禁止

- AI自动锁定
- PI
- 第二板
- Daisy开发

## 冻结后的开发边界

后续只在既有目录和既有入口内进行 FPGA/Host 代码优化、必要测试以及固定
入口文档更新。历史材料仅可从 `archive/obsolete/` 追溯，不作为当前开发依据。
