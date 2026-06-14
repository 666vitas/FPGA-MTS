# WORKSPACE RTL MIGRATION PLAN

## 0. 本文件作用

本文件是把项目 RTL 从 `E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl` 复制到当前开发区 `E:\new\fpga_lock\v94\v0.94\rtl` 的迁移计划。

本计划只说明后续要执行的迁移步骤和注意事项。当前阶段不复制 Verilog/SystemVerilog 文件，不运行 Vivado，不删除任何文件。

## 1. 为什么要迁移

- Vivado 工程默认更容易使用 `v0.94\rtl` 下的文件。
- 可以减少 Add Sources 和路径混乱。
- 后续可以直接基于官方例程继续开发。
- `redpitaya_laser_lock_project` 继续作为项目资料和记录中心。

## 2. 当前要复制的文件

只复制当前 v1ab 需要的文件。

源文件：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\output_protect.sv
```

目标文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

## 3. 暂时不复制的文件

暂时不复制：

- `adc_frontend.sv`
- `mixer_core.sv`
- `lpf_core.sv`
- `mts_demod_core.sv`
- `pid_lock_core.sv`
- 其他后续版本暂时不用的模块

原因：

当前 v1ab 不需要这些模块。暂时不复制可以避免 Vivado Sources 和项目结构变得混乱。

## 4. 如果目标文件已存在怎么办

如果 `E:\new\fpga_lock\v94\v0.94\rtl` 下已经存在同名文件，先备份，再复制新文件。

备份文件名：

```text
laser_lock_core.sv.before_migration
output_protect.sv.before_migration
```

不要在未备份的情况下覆盖已有文件。

## 5. 复制后 Vivado 应该怎么用

Vivado 后续直接使用：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

如果它们已经在 `rtl` 目录中，Vivado 仍可能需要 Add Sources 或刷新工程 Sources。

## 6. redpitaya_laser_lock_project 以后还保留什么

`redpitaya_laser_lock_project` 继续保留项目资料、测试记录、学习记录和历史版本。

保留：

- `docs`
- `reports`
- `board_tests`
- `beginner_roadmap`
- `patches`
- `sim`
- `experiment_logs`

## 7. 风险

- 可能出现两个版本不同步。
- 后续修改 RTL 时要明确修改的是 `v0.94\rtl` 中的实际综合版本。
- `redpitaya_laser_lock_project` 中保留历史版本和文档记录。

## 8. 下一步

等待用户确认后，再执行复制，并生成：

```text
REPORT_workspace_rtl_migration_done.md
```
