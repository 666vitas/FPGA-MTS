# FPGA Bit Release Process

- Status: ACTIVE
- Authority: bitstream 发布与追溯
- Last-Updated: 2026-09-04
- Release root: E:\new\fpga_lock\releases

## 原则

bitstream 是可执行构建产物，不是源码。源码、约束、工程配置和可重复构建步骤保留在 v94；正式 bit 只放在 E:\new\fpga_lock\releases 下，并与唯一源码版本、工具版本和测试结果绑定。

本规范不复制历史 bit，也不以改扩展名代替 Bootgen 转换；每次新构建使用新的不可覆盖 release 目录。

## 正式 release 前置条件

1. 当前 Gate 和发布目的明确。
2. FPGA 源码工作树干净，并有唯一 Git commit。
3. Host 有可识别的 version/commit。
4. HOST_FPGA_INTERFACE 中的 Interface version 已确定。
5. 定向仿真和必需回归通过。
6. Vivado 综合、实现、DRC/CDC/Methodology 和 timing 对应同一 commit。
7. bit 由上述实现结果生成，文件 hash 已计算。
8. CURRENT_STATUS 和 CHANGELOG 已更新。

不满足条件的 bit 只能作为 candidate、historical 或 unknown 保存，不能命名为 current、final 或 release。

## 目录与命名

建议 release_name：YYYYMMDD_<GATE>_<short-commit>

每个 release 使用独立且不可覆盖的目录：

    E:\new\fpga_lock\releases\<release_name>\
        red_pitaya_top.bit
        red_pitaya_top.bit.bin
        RELEASE_MANIFEST.md
        timing_summary.rpt
        test_result.md

其中 bit、由同一 bit 通过 Vivado 匹配版本 Bootgen (`-arch zynq -process_bitstream bin`) 生成的 `.bit.bin` 与 RELEASE_MANIFEST.md 为候选/正式 release 的必需项；timing 和 test evidence 可保留原始报告或由 manifest 指向不可变证据。已有 release 不得原地替换 bit；任何重建都使用新的 release_name。

## RELEASE_MANIFEST 必需内容

每个 release 至少包含：

- release_name
- bit 文件名、大小和 SHA256
- bit.bin 文件名、大小和 SHA256，以及 Bootgen 命令/版本
- FPGA repository、branch 和完整 Git commit
- FPGA 工作树 clean 状态
- Host version/commit
- Interface version
- Vivado project、top、device 和 Vivado version
- 标准 run（默认 `synth_1` → `impl_1`）及完整 run properties；若为独立 candidate run 必须说明与用户 XPR 的等价配方
- build start/end time 和时区
- 仿真结果
- 综合/实现结果
- WNS、TNS、WHS、THS 和未约束路径数量
- DRC/CDC/Methodology 结果
- 板级 test result
- 已知限制和回退 release
- 发布人/确认人

## Manifest 模板

### Identity

- release_name:
- status: CANDIDATE / RELEASED / REJECTED / RETIRED
- bit:
- bit_sha256:
- build_time:

### Source

- FPGA commit:
- FPGA worktree clean:
- Host version/commit:
- Interface version:
- XPR:
- Top:
- Device:
- Vivado version:

### Verification

- Simulation:
- Synthesis:
- Implementation:
- Timing:
- DRC/CDC/Methodology:
- Board test:
- Laser lock test:
- Evidence paths:

### Decision

- Known limitations:
- Rollback release:
- Approved by:
- Approval date:

## 发布状态

- CANDIDATE：构建完成，但板级或实验验证未闭合。
- RELEASED：达到当前 Gate 规定的发布证据并获人工确认。
- REJECTED：测试失败，不得用于后续实验。
- RETIRED：曾发布但已被替代；保留追溯，不删除。

## 实验绑定

每次板级或激光器实验必须记录 release_name、bit SHA256、FPGA commit、Host version、Interface version、板卡标识、接线、参数、仪器和原始数据路径。无法完成该绑定的实验结果只能作为探索性记录，不能关闭 Gate。
