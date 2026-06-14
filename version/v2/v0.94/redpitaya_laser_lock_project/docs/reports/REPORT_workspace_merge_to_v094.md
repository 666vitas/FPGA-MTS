# REPORT workspace merge to v0.94

## 0. 本报告作用

本报告记录本次把 `redpitaya_laser_lock_project` 中已经完成、需要参与 Vivado 综合的项目 RTL 汇总到当前实际开发工程 `v0.94` 的结果。

本次只迁移 `v1ab_passthrough_debug` 所需文件，没有运行 Vivado，没有生成 bitstream，也没有开始 v1c mixer。

## 1. 当前目录角色

- `E:\new\fpga_lock\v94\guanfang-v0.94\v0.94` 是官方干净原版，只读，本次未修改。
- `E:\new\fpga_lock\v94\v0.94` 是当前实际开发工程，后续 Vivado 直接在这里开发。
- `E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project` 是项目资料库，继续保存文档、报告、测试 SOP、学习记录和历史版本。

## 2. 本次复制了哪些文件

已复制 `v1ab_passthrough_debug` 所需 RTL：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\laser_lock_core.sv
-> E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv

E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl\output_protect.sv
-> E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

复制后校验：

- `laser_lock_core.sv` 源文件和目标文件 SHA256 一致。
- `output_protect.sv` 源文件和目标文件 SHA256 一致。

## 3. 是否备份了旧文件

目标目录中原本已有同名文件，因此已先备份：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
-> E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv.before_workspace_merge

E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
-> E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv.before_workspace_merge
```

## 4. red_pitaya_top.sv 当前状态

已检查当前开发 top：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

搜索结果显示该文件已经包含 v1ab patch 相关内容：

- `USE_LASER_LOCK_CORE`
- `LASER_LOCK_OUTPUT_MODE`
- `laser_error`
- `laser_control`
- `i_laser_lock_core`

当前参数：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 0
```

判断：当前 `red_pitaya_top.sv` 已经应用 v1ab patch。

## 5. 后续 Vivado 需要使用哪些文件

后续 Vivado 需要看到当前开发工程 `rtl` 目录下的以下文件：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

如果 Vivado Sources 还没有包含 `laser_lock_core.sv` 和 `output_protect.sv`，需要 Add Sources 或刷新工程 Sources。

## 6. 下一步建议

由于当前 `red_pitaya_top.sv` 已经应用 v1ab patch，下一步建议：

- 打开 Vivado。
- 确认 Sources 中包含：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

- 确认 top 使用：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

- 然后 Run Synthesis。

## 7. 回退方法

如果需要回退本次 workspace merge，可从备份恢复：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv.before_workspace_merge
-> E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv

E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv.before_workspace_merge
-> E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

回退前建议先确认当前 `rtl` 文件是否已经有新的手动修改，避免覆盖后续工作。
