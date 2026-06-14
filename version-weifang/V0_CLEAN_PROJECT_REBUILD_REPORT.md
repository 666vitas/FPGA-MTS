# V0_CLEAN_PROJECT_REBUILD_REPORT

## 0. 本报告作用

本报告记录本次“新平台项目清理与重建”的结果。

目标不是继续在旧的 `v-weifang` 上直接开发，而是建立一个更干净的新工作区：

`E:\new\fpga_lock\v94\v-weifang-clean`

同时建立新的版本记录目录：

`E:\new\fpga_lock\v94\version-weifang`

本次只做目录审查、可复用文件迁移和文档生成。没有修改 `v0.94`，没有修改 `v-weifang`，没有运行 Vivado，没有生成 bitstream。

## 1. 扫描了哪些目录

本次只读递归扫描了以下两个目录：

1. `E:\new\fpga_lock\v94\v0.94`
2. `E:\new\fpga_lock\v94\v-weifang`

两个目录结构基本相同，都包含：

- `rtl`
- `sim`
- `sdc`
- `ip`
- `project`
- `redpitaya_laser_lock_project`
- `exp`
- `.Xil`

其中 `project` 和 `exp` 中包含较多 Vivado 自动生成文件、仿真缓存、IP 缓存和历史构建产物，不适合整体复制到新项目。

## 2. 发现了哪些核心文件

### 2.1 Red Pitaya 顶层和接口相关

发现并复制到 clean 工程的核心顶层文件：

| 作用 | 源文件 | clean 目标 |
|---|---|---|
| Red Pitaya 当前开发 top | `E:\new\fpga_lock\v94\v-weifang\rtl\red_pitaya_top.sv` | `E:\new\fpga_lock\v94\v-weifang-clean\rtl\red_pitaya_top.sv` |
| Red Pitaya PS/AXI wrapper | `E:\new\fpga_lock\v94\v-weifang\rtl\red_pitaya_ps.sv` | `E:\new\fpga_lock\v94\v-weifang-clean\rtl\red_pitaya_ps.sv` |
| Vivado block design wrapper 参考 | `E:\new\fpga_lock\v94\v-weifang\project\redpitaya.srcs\sources_1\bd\system\hdl\system_wrapper.v` | `E:\new\fpga_lock\v94\v-weifang-clean\fpga\bd\system_wrapper.v` |
| Vivado block design Tcl 参考 | `E:\new\fpga_lock\v94\v-weifang\project\redpitaya.srcs\sources_1\bd\system\hw_handoff\system_bd.tcl` | `E:\new\fpga_lock\v94\v-weifang-clean\fpga\bd\system_bd.tcl` |

说明：`system_wrapper.v` 和 `system_bd.tcl` 来自 Vivado 工程中的 block design 目录。它们不是普通 RTL 教学模块，但对重建 Red Pitaya PS/PL 工程很有参考价值。

### 2.2 ADC / DAC / 官方 Red Pitaya 支撑 RTL

`red_pitaya_top.sv` 中仍使用官方 Red Pitaya 结构，包括：

- ADC 数据输入转换；
- DAC A / DAC B 求和、饱和和 ODDR 输出；
- `red_pitaya_pll`；
- `red_pitaya_hk`；
- `red_pitaya_scope`；
- `red_pitaya_asg`；
- `red_pitaya_pid`；
- `red_pitaya_ams`；
- `sys_bus_if`、AXI 相关接口。

因此本次复制了官方导入 RTL 源码副本：

`E:\new\fpga_lock\v94\v-weifang\project\redpitaya.srcs\sources_1\imports\RedPitaya-FPGA-master\rtl`

到：

`E:\new\fpga_lock\v94\v-weifang-clean\rtl\redpitaya_official`

该目录包含 90 个官方 RTL / Verilog 源文件，用作 clean 工程的官方支撑源码参考。

### 2.3 当前 MTS / laser lock 核心 RTL

| 模块 | clean 目标 | 当前作用 |
|---|---|---|
| `laser_lock_core.sv` | `v-weifang-clean\rtl\laser_lock_core.sv` | 统一选择 passthrough、raw mixer、mixer + LPF 输出 |
| `mixer_core.sv` | `v-weifang-clean\rtl\mixer_core.sv` | signed `14-bit × 14-bit` 数字 mixer |
| `lpf_core.sv` | `v-weifang-clean\rtl\lpf_core.sv` | mixer 后一阶 IIR 低通 |
| `output_protect.sv` | `v-weifang-clean\rtl\output_protect.sv` | 输出保护 / reset 和 enable 安全输出 |

当前 clean top 中观察到：

- `USE_LASER_LOCK_CORE = 1'b1`
- `LASER_LOCK_OUTPUT_MODE = 3`

也就是说当前 top 默认路径是：

`IN1 × IN2 -> mixer_core -> lpf_core -> output_protect -> OUT1`

### 2.4 旧项目候选 RTL

以下文件不是当前 clean top 的直接主线，但后续可能有参考价值，因此放入：

`E:\new\fpga_lock\v94\v-weifang-clean\rtl\legacy_candidates`

| 文件 | 说明 |
|---|---|
| `adc_frontend.sv` | 旧项目 ADC 前端候选 |
| `mts_demod_core.sv` | 旧 MTS demod 集成候选 |
| `pid_lock_core.sv` | 旧 PID 候选，当前不用于 v1 |
| `red_pitaya_top_laser.sv` | 旧 top patch 候选，当前不作为 clean top |

### 2.5 testbench

复制到：

`E:\new\fpga_lock\v94\v-weifang-clean\tb`

| 文件 | 说明 |
|---|---|
| `tb_mixer_core.sv` | v1c mixer 单模块 testbench |
| `tb_lpf_core.sv` | v1d LPF 单模块 testbench |
| `tb_laser_lock_core_v1c.sv` | v1c core 集成 testbench |
| `tb_laser_lock_core_v1d.sv` | v1d core 集成 testbench |
| `tb_laser_lock_core.sv` | laser_lock_core 通用 testbench |

旧候选 testbench 放入：

`E:\new\fpga_lock\v94\v-weifang-clean\tb\legacy_candidates`

包括：

- `tb_laser_lock_core_v1ab.sv`
- `tb_pid_lock_core.sv`

### 2.6 constraints

复制到：

`E:\new\fpga_lock\v94\v-weifang-clean\constraints`

包括：

- `red_pitaya.xdc`
- `red_pitaya_4ADC.xdc`
- `red_pitaya_4adc_test.xdc`

当前 STEMlab 125-14 主线优先使用 `red_pitaya.xdc`，其他约束文件只作为板型/历史参考。

### 2.7 scripts / Tcl

复制到：

`E:\new\fpga_lock\v94\v-weifang-clean\scripts`

包括：

- `systemZ10.tcl`
- `systemZ20.tcl`
- `systemZ20_14.tcl`
- `notes_build_steps.md`

这些脚本用于参考 Red Pitaya PS/block design 建立方式。正式重建 Vivado 工程前仍需要人工确认适用板型和 Vivado 版本。

### 2.8 文档

复制到：

`E:\new\fpga_lock\v94\v-weifang-clean\docs`

主要包括：

- `PROJECT_REVIEW_V0_94.md`
- `README_DOCS_INDEX.md`
- `V1AB_SKILL_BASED_CODE_REVIEW.md`
- `red_pitaya_laser_lock_code_map.md`
- `project_master`
- `integration`
- `learning`
- `board_tests`

同时，为了保留当前已经完成的 v1c / v1d / v1e 实验主线，把当前版本记录中的 v1 文档复制为参考：

`E:\new\fpga_lock\v94\v-weifang-clean\docs\version_v1_reference`

包括：

- `V1_EXPERIMENT_REPORT.md`
- `V1_GOAL_AND_CHAIN.md`
- `V1_NEXT_STEPS.md`
- `V1_CODE_REVIEW.md`
- `FPGA_MTS_STEP_BY_STEP_ANALOG_REPLACEMENT_GUIDE.md`
- `V1D_LITERATURE_TO_DEVELOPMENT_BRIDGE.md`
- `V1G_DIGITAL_GAIN_OUTPUT_SCALING_PLAN.md`
- `V1_LOCKING_ROADMAP_FPGA_TO_SERVO.md`

## 3. 哪些文件已复制到 v-weifang-clean

clean 工程已建立以下目录：

- `rtl`
- `tb`
- `fpga`
- `constraints`
- `scripts`
- `docs`
- `build`
- `exp_data`
- `analysis`
- `ai`

核心文件已复制：

1. 当前顶层与 Red Pitaya 接口：
   - `rtl\red_pitaya_top.sv`
   - `rtl\red_pitaya_ps.sv`
   - `fpga\bd\system_wrapper.v`
   - `fpga\bd\system_bd.tcl`

2. 当前 v1 DSP 链路：
   - `rtl\laser_lock_core.sv`
   - `rtl\mixer_core.sv`
   - `rtl\lpf_core.sv`
   - `rtl\output_protect.sv`

3. 官方 Red Pitaya 支撑源码：
   - `rtl\redpitaya_official\...`

4. testbench：
   - `tb\tb_mixer_core.sv`
   - `tb\tb_lpf_core.sv`
   - `tb\tb_laser_lock_core_v1c.sv`
   - `tb\tb_laser_lock_core_v1d.sv`

5. 约束：
   - `constraints\red_pitaya.xdc`
   - `constraints\red_pitaya_4ADC.xdc`
   - `constraints\red_pitaya_4adc_test.xdc`

6. Tcl / 构建参考：
   - `scripts\systemZ10.tcl`
   - `scripts\systemZ20.tcl`
   - `scripts\systemZ20_14.tcl`

7. 文档：
   - `docs\project_master\...`
   - `docs\integration\...`
   - `docs\learning\...`
   - `docs\version_v1_reference\...`

## 4. 哪些文件没有复制，原因是什么

以下类型没有复制：

| 未复制内容 | 原因 |
|---|---|
| `.Xil` | Vivado 临时目录，包含机器/会话缓存 |
| `project\redpitaya.cache` | Vivado IP cache，不适合作为 clean 源码 |
| `project\redpitaya.hw` | hardware manager / 硬件缓存 |
| `project\redpitaya.sim` | 仿真运行结果，不是源码 |
| `project\redpitaya.ip_user_files` | IP 生成和仿真文件，容易带旧路径依赖 |
| `exp\v1\...` | 历史 synth/impl 输出，属于构建产物 |
| `.jou` / `.log` / `.str` | Vivado 日志和会话文件 |
| bit / bin 输出文件 | 本次目标是 clean 重建，不继承旧 bitstream |
| 无关截图和临时文件 | 不属于可综合源码或主线文档 |
| 重复备份文件 | 避免 clean 工程再次混乱 |
| `project\redpitaya.xpr` | 可能包含旧路径、旧 sources、旧 BD/IP 状态；暂不复制，后续建议用 clean sources 重新建立工程 |

特别说明：

`project\redpitaya.srcs\sources_1\imports\RedPitaya-FPGA-master\rtl` 中的官方 RTL 源码副本已经复制，因为它是可复用源码。  
但 `project\redpitaya.srcs` 下面的 IP、BD、仿真、OOC 产物没有整体复制，因为这些内容很容易携带旧工程路径和 Vivado 自动生成状态。

## 5. 当前新项目中已有功能

当前 `v-weifang-clean` 已有：

1. Red Pitaya `red_pitaya_top.sv` 顶层参考；
2. ADC 到 FPGA 的 `adc_dat[0]` / `adc_dat[1]` 数据路径；
3. DAC A / OUT1 输出路径；
4. `mixer_core.sv`；
5. `lpf_core.sv`；
6. `output_protect.sv`；
7. `laser_lock_core.sv` 中的 `OUTPUT_MODE=0/1/2/3`；
8. v1c / v1d testbench；
9. Red Pitaya 约束文件；
10. Red Pitaya 官方支撑 RTL。

当前 clean top 的主线功能是：

`IN1 -> adc_dat[0]`

`IN2 -> adc_dat[1]`

`adc_dat[0] × adc_dat[1] -> mixer_core -> lpf_core -> output_protect -> DAC A / OUT1`

## 6. 当前新项目缺失功能

当前缺失或尚未作为主线实现：

1. 内部 `4.6 MHz` NCO / DDS；
2. 内部 `sin/cos` 数字参考；
3. I/Q 双路解调；
4. 数字 BPF；
5. 原始 PD 直入时的前置 DC remove；
6. 原始 PD 直入时的数字 gain / 自动增益；
7. OUT2 调试输出方案；
8. 新 clean Vivado `.xpr` 工程；
9. 面向 `v-weifang-clean` 的一键 build Tcl；
10. 新平台上板 SOP；
11. AI 数据采集和状态识别链路。

## 7. 是否已有 mixer

有。

当前 clean 工程已有：

`E:\new\fpga_lock\v94\v-weifang-clean\rtl\mixer_core.sv`

它对应真实链路中的 `ZFM-3+ mixer` 的 FPGA 等效部分：signed 数字乘法。

## 8. 是否已有 LPF

有。

当前 clean 工程已有：

`E:\new\fpga_lock\v94\v-weifang-clean\rtl\lpf_core.sv`

它对应 mixer 后低频 / 差频 / 基带提取，不是 PD 前级的 `10 MHz LPF`，也不是 `1.8 MHz HPF`。

## 9. 是否已有 NCO/DDS

没有发现本项目专用的 `NCO` / `DDS` / `phase accumulator` / `sin` / `cos` 参考模块。

官方 Red Pitaya 源码中存在 `asg` 相关波形发生器模块，但它不是当前 MTS 数字解调所需的内部 `4.6 MHz sin/cos REF` 模块。

因此结论是：

当前没有可直接用于新实验的内部 NCO/DDS。

## 10. 是否已有内部 sin/cos 参考

没有。

当前 v1c/v1d/v1e 代码仍然依赖：

`IN2 = 外部 4.6 MHz REF`

没有发现内部生成 `4.6 MHz sin` / `4.6 MHz cos` 并送入 mixer 的主线代码。

## 11. 是否仍然依赖外部 IN2 REF

是。

当前 `red_pitaya_top.sv` 将：

- `adc_dat[0]` 接入 `laser_lock_core.pd_i`
- `adc_dat[1]` 接入 `laser_lock_core.ref_i`

因此当前 mixer 的 REF 来自 Red Pitaya `IN2`。

如果新实验要“PD 原始信号直接进 IN1，并由 FPGA 内部生成 4.6 MHz 参考”，下一步必须先设计 NCO/DDS 和 `laser_lock_core` 的新模式，而不是直接上板。

## 12. 下一步最小可行实验建议

建议不要马上写完整 MTS 数字链路。最小下一步应该是：

1. 先写设计说明：`internal_nco_ref_core` 或 `nco_ref_core`；
2. 明确 NCO 输出：
   - `sin_ref_o`
   - `cos_ref_o`
   - signed 14-bit 或更宽内部位宽；
3. 先不接真实 PD，先用 testbench 验证：
   - 相位累加器频率是否约 `4.6 MHz`；
   - `sin/cos` 是否正交；
   - 幅度是否安全；
4. 再设计新模式：
   - `OUTPUT_MODE=4`：`IN1 × internal sin_ref -> LPF -> OUT1`
   - `OUT2` 可输出 `internal sin_ref` 或 raw mixer 作为调试；
5. 再做 Vivado 仿真和 synthesis；
6. 上板第一步不要接 D2-125，只接示波器：
   - `IN1` 先接信号源 `4.6 MHz sine`；
   - 内部 NCO 也设 `4.6 MHz`；
   - `OUT1` 应看到低频 / DC-like 分量；
   - `OUT2` 建议输出内部参考或 raw mixer，帮助确认 NCO 是否真的工作。

当前最重要的工程边界：

不要把“已经有 mixer+LPF”误认为“已经有内部参考”。  
新平台最大缺口是内部 `NCO/DDS sin/cos REF`。
