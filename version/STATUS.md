# STATUS

## 2026-07-16 v3LOCK-P0 System Identity 只读上位机准备

### Git Baseline Gate

- branch：`main`；initial/final HEAD：`4a0b7b0ecf30a215191f930f491447f7cc17a417`。
- 本轮开始和 `git fetch origin` 后均确认 working tree clean、无 rebase / merge / cherry-pick，且 `HEAD == origin/main`；Git Gate PASS。
- 本轮未执行 reset、restore、checkout、clean、rebase、commit 或 push。

### Current Stage / Gate

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: HV-1 OUT2 fixed-count physical voltage calibration
Software subtask: System Identity read-only UI preparation
```

Current Stage 和 Current Gate 未改变；软件测试通过不表示 HV-1 已通过。

### 本轮实现

- [AUTOMATED VERIFIED] 在左侧 `PZT Scan` 下方增加紧凑 `System Identity`，显示 Connection、Host、FPGA version、Identity、Mode、Output、Last probe、Bitstream 和 Host code。
- [AUTOMATED VERIFIED] `REFRESH IDENTITY` 只调用既有 `status` 路径；该路径读取 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、`STATUS`、`OUT2_MONITOR` 等现有 readback，不执行寄存器写入。
- [AUTOMATED VERIFIED] `MAGIC=0x4D545330` 且 `VERSION=0x00030001` 才显示 `Matched`；版本显示为 `v3.0.1`，模式映射为 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK，输出显示 Disabled/Enabled/Saturated。
- [AUTOMATED VERIFIED] 读取失败或 payload 不完整会清除旧 FPGA identity/version/mode/output；最近成功时间只保留为 `Last successful probe`，不会把旧状态继续显示为当前有效状态。
- [AUTOMATED VERIFIED] 错误分类区分 Authentication failed、Host unreachable、Communication lost、FPGA identity mismatch 和 Register read failed；完整底层错误只保留在 tooltip/内部诊断文本。
- [AUTOMATED VERIFIED] Identity 非 Matched 或 output Saturated 时禁用 START SCAN、RUN、SINGLE、PICK LOCK POINT、CONFIRM、LOCK HERE 和 APPLY P；既有 SAFE、MAGIC、VERSION、saturation 和 safe-range 守卫未降低。
- [AUTOMATED VERIFIED] `Bitstream` 固定显示 `Build date unavailable`，tooltip 说明当前寄存器协议未编码该信息。`Host code` 只显示本地 HEAD 短 SHA，并明确不代表已加载 bitstream。

### 当前协议限制

- 当前板端协议不提供 bitstream build date/time、Git SHA、Vivado build ID 或 bitstream filename。
- 本轮未根据本地文件日期或 Git HEAD 猜测板端 bitstream 信息，也未声称板上已加载最新程序。

### 自动化验证

- `python -m tabnanny main_window.py custom_fpga_backend.py connection_workers.py test_custom_fpga_backend.py`：通过，无输出。
- 对同四文件执行 `python -m py_compile`：通过，无输出。
- `pytest --collect-only -q tests/test_custom_fpga_backend.py`：`84 tests collected`。
- targeted：`13 passed, 71 deselected`。
- 当前测试文件：`84 passed`。
- 完整 software tests：`90 passed, 4 subtests passed`。
- `git diff --check`：通过，无输出；离屏 1450x900 只确认面板布局无明显重叠，不属于真实 Windows GUI 或硬件证据。

### 修改与未修改边界

- 修改：`main_window.py`、`test_custom_fpga_backend.py`、本 STATUS、上位机 `DEVELOPMENT_LOG.md`、`version/v3/DEVELOPMENT_LOG.md`。
- 未修改 `custom_fpga_backend.py`、`connection_workers.py`、RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION`、bitstream、`version/HARDWARE_VALIDATION.md` 或校准 SOP。
- 未运行 Vivado、未生成/烧录 bitstream、未执行真实 GUI、SCAN、LOCK HERE、APPLY P 或任何硬件校准。

### 阶段结论

```text
SYSTEM IDENTITY SOFTWARE PASS
WAITING USER HARDWARE HV-1
```

硬件证据仍为 `[NOT VERIFIED]`，HV-1 未执行。

### 下一步唯一动作

断开 PZT，使 OUT2 只连接示波器，按照 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 只执行 count=0 的 HV-1 测量，记录 readback 和示波器真实电压，然后立即 SAFE。

## 2026-07-16 v3LOCK-P0 Hardware Verification Infrastructure / HV-1 准备

### Git Baseline Gate

- 当前 branch：`main`；initial/final HEAD：`0e13f2806d7a716d3e66d365babbe2b247e59d8b`。
- 本轮开始和 `git fetch origin` 后均确认 `HEAD == origin/main`；working tree 初始 clean，无 rebase / merge / cherry-pick 状态，Git Gate PASS。
- 工程曾存在遗留 interactive rebase；用户已执行 `rebase --continue` 并恢复 `main`，后续状态为 `no rebase in progress`。已建立保险分支，只作为恢复点，不影响当前 `main`；本轮未再次执行任何 rebase、reset、clean 或 amend。

### Current Stage / Gate

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: HV-1 OUT2 fixed-count physical voltage calibration
```

- 固定开发流程已写入 `AGENTS.md` 和 `AI_REVIEW_README.md`：Stage 0 Audit -> Stage 1 Code -> Stage 2 Software Verification -> Stage 3 Hardware Verification -> Stage 4 Review。
- 软件 PASS 不等于项目 PASS；任一 Gate FAIL 阻止进入下一阶段；每次任务只保留一个 Current Stage、一个 Current Gate 和一个下一步唯一动作。
- 当前证据继续保持：`CODE/REGISTER TRACE PASS`、`GUI ABSOLUTE VOLTAGE FAIL`、`PHYSICAL ADC/DAC CALIBRATION NOT VERIFIED`、`OUT1 LOCK MEANING NOT VERIFIED`、`P-ONLY CLOSED LOOP NOT VERIFIED`。

### 本轮实现

- [IMPLEMENTED] 新增 `version/HARDWARE_VALIDATION.md`，记录 HV-1 至 HV-7、当前 evidence、OUT2 校准表、拟合占位、负载约束和停止条件；只有 HV-1 准备完成，所有硬件结果仍为 `[NOT VERIFIED]`。
- [IMPLEMENTED] 新增 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md`，本轮只允许 PZT 断开、OUT2 只接示波器、count=0 的单点流程。
- [AUTOMATED VERIFIED] 上位机审计确认现有功能足够执行当前 count=0：`hold-v=0.0000` 精确转换为 count=0；Probe/Status 返回身份、MODE、ENABLE、STATUS、OUT2_MONITOR 和 saturation；Capture Waveform 返回 CH4 raw count。
- 上位机 Python 未修改。现有 HOLD 不是通用 exact-count 校准界面，且 HOLD 不受 SCAN `OUT2_LIMIT` 保护；因此本轮禁止非零值，不把 nominal/ideal V 写成真实 V。
- `version/AI_STRICT_REVIEW_ENTRY.md` 中既有 merge conflict markers 仍是已知文档污染；本轮未获授权修复，也未使用其中旧状态覆盖 STATUS/Manifest。

### 自动化验证

- `python -m tabnanny redpitaya_lock_host tests`：通过，无输出。
- `python -m py_compile redpitaya_lock_host\main_window.py`：通过。
- `python -m py_compile redpitaya_lock_host\waveform_plot.py`：通过。
- `python -m py_compile redpitaya_lock_host\custom_fpga_backend.py`：通过。
- `python -m py_compile redpitaya_lock_host\connection_workers.py`：通过。
- `python -m py_compile scripts\custom_fpga_scan_control.py`：通过。
- `python -m pytest --collect-only -q tests`：通过，`81 tests collected`。
- `python -m pytest -q tests`：通过，`81 passed`。
- 软件验证只证明既有 SAFE/HOLD/readback/capture 路径未回归，不证明 OUT2 真实电压已经校准。

### 修改与未修改边界

- 修改：`AGENTS.md`、`AI_REVIEW_README.md`、`version/CURRENT_REVIEW_MANIFEST.md`、本 STATUS、`version/HARDWARE_VALIDATION.md`、`version/v3/DEVELOPMENT_LOG.md`、上位机 `DEVELOPMENT_LOG.md` 和 `HARDWARE_CALIBRATION_SOP.md`。
- 未修改上位机 Python、测试、RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。
- 未运行 Vivado、未生成或烧录 bitstream、未执行硬件校准、未执行 SCAN、LOCK HERE、APPLY P 或 P-only。

### 阶段结论

```text
CALIBRATION INFRASTRUCTURE CODE PASS
WAITING USER HARDWARE HV-1
```

硬件证据等级仍为 `[NOT VERIFIED]`；当前 Gate 尚未 `[USER HARDWARE VERIFIED]`。

### 下一步唯一动作

断开 PZT，使 OUT2 只连接示波器，按照 `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md` 只执行 count=0 的 HV-1 测量，记录 readback 和示波器真实电压，然后立即 SAFE。

## 2026-07-15 v3LOCK-P0 RTL/电压映射只读审查与硬件校准方案

### Git 基线与任务边界

- 仓库：`666vitas/FPGA-MTS`；branch：detached HEAD。
- initial/final HEAD：`9417832e147f4d87b142ba608c192a77f304a554`；本轮 `git fetch origin` 后 `origin/main` 为同一提交。
- 初始工作区已有用户未跟踪目录 `.claude/`；本轮保留、不读取为当前证据、不修改、不清理、不纳入任务。
- 当前阶段：v3LOCK-P0 数据链验证；不开发新锁定功能，不进入 PI、AI、自动 polarity、自动加 Kp、自动重锁或长期稳频。
- 本轮只读审查当前 RTL、寄存器、backend、GUI 和测试；只更新本 STATUS 与两份现有 `DEVELOPMENT_LOG.md`。未修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION`、bitstream 或 Python。
- `version/AI_STRICT_REVIEW_ENTRY.md` 仍含既有 merge conflict markers 和过期 v3LOCK-P0 文字；本轮按 Manifest 只读取其规则，不修复、不用其旧状态覆盖当前 RTL/STATUS。
- 未运行 Vivado、未生成/烧录 bitstream、未连接板卡、未执行新的物理实验。

### 任务 A：当前 RTL 数据流

```text
physical IN1 / IN2
  -> adc_dat_i[15:2]                         14-bit ADC raw, low 2 padding bits discarded
  -> keep raw sign bit, invert lower 13 bits 14-bit signed adc_dat[0/1]
  -> mixer_core: pd * ref                    14 x 14 -> 28-bit signed product
  -> arithmetic >>> 13 + saturation          14-bit signed mixer_signal
  -> lpf_core: first-order IIR                32-bit accumulator, 12 fractional-count bits
  -> arithmetic >>> 12 + saturation          14-bit signed lpf_signal
  -> OUTPUT_MODE=3 + output_protect           14-bit signed laser_error
       |-> custom_debug_capture CH3
       |-> ERROR_MONITOR / ERROR_SETPOINT path
       `-> DAC A / OUT1 pre-DAC code

scan_offset/amp/step/limit -> ramp_generator 15-bit internal arithmetic -> 14-bit scan_out2
lock_error(14) * Kp(14) -> 29-bit product -> >>> 8 -> 32-bit correction + 14-bit bias
SAFE / SCAN / HOLD / P_LOCK selector -> 14-bit signed selected_out2
       |-> OUT2_MONITOR / custom_debug_capture CH4
       `-> DAC B / OUT2 pre-DAC code

laser_error / selected_out2
  -> sign-extend 14 -> 15 -> existing saturation -> 14-bit signed DAC code
  -> negative-slope signed/DAC pin encoding -> ODDR -> physical OUT1 / OUT2
```

- `USE_LASER_LOCK_CORE=1`、`LASER_LOCK_OUTPUT_MODE=3`、`LASER_LOCK_CONTROL_PATH_MODE=1`；`laser_control` 仍被编译，但不进入当前 OUT2。当前 OUT2 唯一最终源是 `selected_out2`。
- `custom_debug_capture`：CH1=`adc_dat[0]`、CH2=`adc_dat[1]`、CH3=`laser_error`、CH4=`selected_out2`；四路都是 DAC/ADC 内部的 14-bit signed pre-analog counts，不是物理端口电压测量。
- `redpitaya.xpr` 的活动 top 是 `v0.94/rtl/red_pitaya_top.sv`；工程 imports 中的旧 `red_pitaya_top.sv` 条目为 `UserDisabled=1`。

### 位宽、固定点与理论缩放

| 节点 | 位宽 | 代码语义 | 归一化/Q 解释 |
|---|---:|---|---|
| `adc_dat_i` | 16 | ADC 引脚数据，最低 2 bit 为 padding | 取 `[15:2]` 后进入 14-bit 域 |
| `adc_dat`, `pd_i`, `ref_i` | signed 14 | 原始 ADC counts，范围可达 `-8192..8191` | 代码本身是 S14.0 counts；按理想满量程归一化可视为 signed Q1.13，即 `real_FS=count/8192` |
| `product_w` | signed 28 | `pd_count * ref_count`，单位 count² | 归一化解释为 Q2.26 |
| `scaled_w` / `mix_o` | 28 / signed 14 | `product >>> 13` 后饱和回 counts | `mix_count=floor_arith(pd*ref/8192)`；回到 Q1.13/count 域，无四舍五入 |
| LPF `acc_q` | signed 32 | `x<<12` 后的一阶 IIR 状态 | `acc_real_count=acc_q/4096`，即 12 个 fractional-count bits；`alpha=1/4096` |
| `lpf_signal` / `laser_error` | signed 14 | LPF 输出、OUT1/CH3 内部 code | S14.0 counts / 归一化 Q1.13；不是 ADC 输入电压，也不是已校准 OUT1 电压 |
| `error_setpoint` / `lock_error` | signed 14 | 同一 error count 域；减法先扩为 15 bit 再饱和 | S14.0 counts |
| `kp_i` | signed 14 | P-only 增益字 | 因 `>>>8`，实际比例为 `Kp/256`，可视为 signed Q6.8；当前 `Ki` 不参与输出 |
| P product / correction / bias sum | 29 / 32 / 32 | P product、限幅 correction、`LOCK_BIAS+correction` | 最后饱和/截取回 14-bit selected_out2 counts |
| `scan_out2` / `selected_out2` | signed 14 | OUT2 pre-DAC counts | S14.0 counts / nominal Q1.13 |
| 寄存器 readback | 32 | 14-bit 值在 FPGA 内 sign-extend；host 再以 low 14 bit 解 signed | 数值应与内部 count 一致，不增加精度 |

理论关系：

```text
laser_error_count ~= LPF( pd_count * ref_count / 8192 )
```

若 IN1/IN2 都是同频正弦、峰值分别为 `A_pd` / `A_ref` counts、相位差为 `phi`，理想 LPF 后 DC 约为：

```text
laser_error_DC_count ~= A_pd * A_ref * cos(phi) / (2 * 8192)
```

因此 `laser_error` 幅值同时依赖 IN1 幅值、REF 幅值、相位和 LPF 频响；它不是“IN1 电压原样换算”。

### 可能导致幅值/时间偏差的位置

1. **ADC 原始路径无通道校准**：自定义 core 直接使用 `adc_dat`，当前路径中没有 EEPROM/API 的 ADC gain、offset、LV/HV 或频率均衡参数。IN1/IN2 jumper 若为 HV，统一按 +/-1 V 显示会产生量级错误。
2. **mixer 固定缩放和相位**：`>>>13` 保持归一化 count 尺度，但乘法输出随 REF 实际幅值线性变化；正弦同频乘法天然有 `1/2` 和 `cos(phi)`；算术右移不四舍五入，负数存在最多约 1 count 的取整偏差。
3. **LPF 频响**：DC 增益约 1，但 `LPF_SHIFT=12` 对应 `alpha=1/4096`，按 125 MHz 名义时钟的一阶近似截止频率约 4.86 kHz；非 DC error 分量会衰减/移相。输出再次按 count 截断。
4. **GUI divisor 不等于官方理想 ADC divisor**：active backend 和 helper 都定义 `COUNTS_PER_VOLT=8191.0`；Red Pitaya 官方对 STEMlab 125-14 LV raw ADC 的理想公式是 `V=RAW/8192`。当前 8191 约定与 host 的 `+/-8191` 安全限幅内部自洽，但对 ADC 是 1-count endpoint convention，不是硬件校准。
5. **DAC 原始路径无通道校准**：`laser_error`/`selected_out2` 直接进入 DAC 编码，当前 custom path 没有 OUT1/OUT2 per-channel gain/offset 系数。物理输出还受板卡个体误差、温漂、线缆、scope 精度和负载影响。
6. **50 ohm / Hi-Z 负载**：STEMlab 125-14 原代 DAC 输出阻抗/标称负载为 50 ohm；同一 count 在 scope 50 ohm 与 1 Mohm/PZT 高阻负载下可能得到显著不同电压。校准结果必须连同负载方式记录，不能跨负载直接复用。
7. **scan 周期是名义值**：GUI `time_s=index*decimation/125e6`，单位换算本身一致，但它假定 ADC 时钟恰为 125 MHz。另由 RTL 周期检查，`ramp_generator` 的一次 position update 经过 divider tick 后还有一个 `update_pending` 周期，实际 step interval 约为 `(update_div+1)/clk`；当前 host 频率公式按 `update_div/clk` 计算。低速扫描误差很小，但真实 period 必须由 capture/scope 测量，不能只信 GUI command label。

### 任务 B：raw count -> register -> backend -> GUI -> physical voltage

```text
FPGA internal signed14 sample/count
  -> custom_debug_capture BRAM signed14
  -> CAPTURE_DATA_CH1..CH4: sign-extended 32-bit register read
  -> /dev/mem reads uint32
  -> helper to_signed14(): mask 0x3FFF and two's-complement decode
  -> JSON ch1_counts..ch4_counts (Python int)
  -> backend payload unchanged
  -> GUI custom_scope_data (float array, numeric value still raw count)
  -> display copy: (raw-center)/(8191*V_per_div)+position
  -> channel cards/stats: raw/8191 -> mV or V marked partly as ideal
  -> physical ADC/DAC voltage: NOT measured; requires per-channel offset/gain/load calibration
```

- [IMPLEMENTED] register/backend/GUI 的 count 数值链没有额外缩放；CSV 保存 `time_s` 与四路原始 counts。
- [IMPLEMENTED] 波形 plot 的 Y 轴是 `Channel position (div)`，不是物理 V；曲线使用居中后的 display copy，原始 counts 保留用于 stats/选点/CSV。
- [IMPLEMENTED] `mV` 仅由 nominal V 乘 1000；未发现把 mV 再当 V 的重复换算。
- [IMPLEMENTED] `time(ms)` 来自 `sample_index * decimation / 125e6 * 1000`；sample index、seconds、milliseconds 在当前 capture render 中未混用。
- [RISK] 主界面通道卡默认隐藏 counts，只显示按 8191 换算的 Vpp；tooltip 才说明 `hardware calibration not yet verified`。部分状态/锁点文本直接显示 `V` 而不是 `V ideal`。因此 operator-facing 数字很容易被误读为真实电压。
- [NOT VERIFIED] CH1/CH2 的 `count -> physical input V`、CH3/OUT1 和 CH4/OUT2 的 `count -> physical output V` 均没有当前板卡、当前 jumper、当前负载下的实测系数。

### 任务 C：最小“硬件校准模式”测试方案（仅设计，不实现）

复用现有 `MODE=2 HOLD`，不新增 RTL mode、不改寄存器、不改 GUI、不重新 Vivado。校准对象先限定为 OUT2 DAC；PZT 暂不连接。

#### 接线与前置条件

1. 只连接 `OUT2 -> oscilloscope`；禁止连接激光器电流调制、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联。
2. 明确记录 scope 输入为 `50 ohm` 或 `1 Mohm/Hi-Z`、探头倍率、带宽限制和 DC coupling；此负载信息是校准结果的一部分。
3. 先读回 `MAGIC=0x4D545330`、`VERSION=0x00030001`，执行 SAFE，并确认 scope 上 OUT2 接近 0 V、无随机跳变。

#### exact-count HOLD 序列

每个点都执行 `SAFE -> 写 HOLD_VALUE=C -> MODE=2 -> ENABLE=1 -> readback -> scope 测量 -> SAFE`；必须同时记录 `HOLD_VALUE`、`OUT2_MONITOR`、CH4 count 和 scope DC mean。

```text
第一组：C = 0, +1024, -1024, +2048, -2048, +4096, -4096 counts
第二组（第一组 PASS 后、仍只接 scope）：覆盖计划扫描区间的 min / center / max counts
每点重复 3 次；任何一次 saturation、越界、异常跳变或 readback != C，立即 SAFE 并停止。
```

拟合：

```text
V_meas = a_out2 * C + b_out2
DAC_count_per_volt_OUT2 = 1 / a_out2
zero_offset_OUT2 = b_out2

对称点快速检查：
DAC_count_per_volt_OUT2(C) = 2*C / (V(+C) - V(-C))
zero_offset_OUT2(C) = (V(+C) + V(-C)) / 2
```

PASS：readback/CH4 与命令 count 一致；极性正确且单调；无 saturation/削顶；重复值在 scope 规格允许的不确定度内；线性拟合 `R^2 >= 0.999` 且最大残差不超过实测 span 的 1%；计划扫描区间在 PZT 安全电压内保留明确余量。FAIL：出现约 2 倍负载差而未解释、非单调、明显零偏漂移、readback 不一致、残差超限、输出越界/跳变或任何通信/身份异常。

### 第一次真实 P-only 实验前必须确认的 3 个数据

1. **OUT2 count 对应真实电压**：[NOT VERIFIED] 记录 `DAC_count_per_volt_OUT2`、`zero_offset_OUT2`、scope 负载/探头/线缆，以及计划 scan min/center/max 的真实 V。
2. **OUT1 error 对应真实误差信号**：[NOT VERIFIED] 同步记录 CH3 `laser_error` counts 与 scope OUT1 的 mean/Vpp/极性，拟合 `V_OUT1=a_out1*CH3_count+b_out1`；若要与输入物理电压理论值比较，还必须先确认 IN1/IN2 LV/HV 和 ADC gain/offset。
3. **scan waveform 对应 PZT 输入变化**：[NOT VERIFIED] OUT2 scope-only 校准 PASS 后，才把 OUT2 单独接激光器专用 PZT/Scan 输入，并用 Hi-Z 测量实际 PZT 节点的 `Vmin/Vmax/Vpp/period/polarity`，同时保存 CH4 counts；禁止连接电流调制端或任何输出端并联。

### 当前能否相信 GUI 显示电压

结论：**不能把当前 GUI 的 mV/V 当作真实物理电压；只能相信其为基于 raw count 的 nominal/ideal estimate。**

- 可相信到代码层：通道身份、raw signed counts、寄存器回读、backend 解码、GUI 原始数组和相对波形形状。
- 暂不可相信：绝对 ADC 输入电压、绝对 OUT1/OUT2 电压、跨 50 ohm/Hi-Z 负载复用的电压、GUI 标称 scan frequency 等同于实测 period。
- 软件测试通过只证明换算逻辑按 `8191.0` 一致执行，不证明 Keysight/scope/Red Pitaya/PZT 上的物理电压正确。

### 自动化验证与证据等级

- `python -m tabnanny ...`：通过，无输出。
- `python -m py_compile ...`：通过。
- `pytest --collect-only -q tests/test_custom_fpga_backend.py`：`75 tests collected`。
- targeted pytest：`31 passed, 44 deselected`。
- current file：`75 passed`。
- full software tests：`81 passed, 4 subtests passed`。
- pytest 均有 1 条非功能 warning：sandbox 无权创建 `.pytest_cache`；测试本身通过，未产生项目改动。
- `git diff --check`：通过，无输出。
- [AUTOMATED VERIFIED] Python count 解码、nominal 8191 换算、GUI display-copy/time-axis 行为按当前代码通过。
- [USER GUI VERIFIED] 继承既有证据：真实四通道非零 capture 和 GUI 波形可见。
- [BOARD EXPERIMENT VERIFIED] count/V、OUT1 物理 error、PZT 节点 scan：均未验证。
- [CLOSED-LOOP VERIFIED] 未验证；本轮不执行 LOCK HERE 或非零 Kp。

### 当前阶段结论与下一步唯一动作

`CODE/TRACE PASS / PHYSICAL VOLTAGE NOT CALIBRATED / WAITING BOARD EXPERIMENT`

下一步唯一动作：**只接 OUT2 到示波器，使用现有 MODE=2 HOLD 完成 exact-count 多点测量，产出当前负载下的 `DAC_count_per_volt_OUT2` 与 `zero_offset_OUT2`；未得到这两个数据前不进入 LOCK HERE/P-only。**

## 2026-07-15 专用示波器界面与人工锁点

### Git 基线

- branch：detached HEAD（当前提交与 GitHub `main` 一致）。
- HEAD：`d63a2b7610865d1ee8274e640ec485211a891a74`。
- origin/main：`d63a2b7610865d1ee8274e640ec485211a891a74`；首次 `git fetch origin` 遇到 TLS EOF，随后 `git ls-remote origin refs/heads/main` 实时确认同一提交。
- 初始工作区：clean，无未提交修改，无 rebase/merge 状态。
- 修改后工作区：`AGENTS.md`、`AI_REVIEW_README.md`、`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`、本状态和上位机开发日志有未提交修改；未 staged、未 commit、未 push。

### 当前项目阶段

- 版本：v3LOCK-P0。
- 当前子阶段：专用数字示波器界面、Direct ERROR Zero Crossing 人工锁点和最小 P-only 锁定准备。
- 当前阶段目标：真实 capture 可读显示，人工选择并 Confirm 锁点，保留 `LOCK HERE -> Kp=0 -> APPLY P` 安全路径。
- 明确不进入：PI_LOCK、自动 polarity、自动增加 Kp、自动重锁、AI 自动识峰/参数优化、长期稳频结论。

### 用户已验证

- [USER GUI VERIFIED] 旧界面已连接真实 Red Pitaya `custom_debug_capture`，time(ms) 模式可显示真实波形且不再空图。
- [USER GUI VERIFIED] CH4 可见重复三角扫描，CH3 有非零 `laser_error` 波形，CH1 有非零 PD/IN1 波形，约 100 ms 窗口可观察多个扫描周期。
- [NOT VERIFIED] 本轮重新设计的通道卡、volts/div、AUTO SET、ground marker 和 Direct ERROR 点击尚未由用户在真实 Windows GUI 验证。

### 代码已实现

- [AUTOMATED VERIFIED] 主界面改为顶部四通道状态卡、中间默认 time(ms) Time Scope、底部 RUN/STOP/SINGLE/AUTO SET 与 SCAN/选点/锁定操作栏。
- [AUTOMATED VERIFIED] 通道卡以 `counts / COUNTS_PER_VOLT` 显示 Vpp/min/max/mean/DC offset 和 mV/div 或 V/div；tooltip 明确为 ideal conversion，未声称硬件校准。
- [AUTOMATED VERIFIED] CH4 黄色、CH3 蓝色、CH1 绿色、CH2 橙色；CH4/CH3/CH1 默认显示，CH2 默认隐藏；每通道独立 volts/div、position、Channel Auto 和 ground line。
- [AUTOMATED VERIFIED] `AUTO SET` 只修改显示副本，按当前 Vpp 选择 1/2/5 volts/div，不修改 raw capture、FPGA、扫描或锁定参数。
- [AUTOMATED VERIFIED] counts、寄存器回读、原始 display gain、连接参数和完整诊断信息只位于默认折叠的 `Advanced / Engineer Details`。
- [AUTOMATED VERIFIED] 默认 `Direct ERROR Zero Crossing` 在点击附近寻找最近有效 CH3 过零，检查边缘、斜率、CH4 ramp direction、PZT safe range 和 saturation，只生成 `pending_lock_point`；`CH1 Peak Assisted` 保留在 Engineer Details。
- [AUTOMATED VERIFIED] Confirm 后才生成 `selected_lock_point`；未 Confirm 阻止 `LOCK HERE`；首次 `LOCK HERE` 强制 Kp=0；非零已应用 Kp 时阻止直接切换 polarity；不自动 Confirm、LOCK HERE、APPLY P、加 Kp、改 polarity 或重锁。
- [AUTOMATED VERIFIED] `AGENTS.md` 与 `AI_REVIEW_README.md` 已固化统一读取、Git、安全、证据等级、分层验证、状态记录和标准交接流程；项目继续不使用自定义 skill。

### 当前上位机完整能力

- 连接：[IMPLEMENTED] SSH/网络 Probe、状态输出和通信错误记录。
- 身份检查：[AUTOMATED VERIFIED] `MAGIC`/`VERSION` 校验失败时阻止危险操作并给出简明主界面告警。
- SAFE / SCAN：[AUTOMATED VERIFIED] SAFE 始终显示；SCAN 参数仍由既有 backend 和安全范围约束。
- capture：[AUTOMATED VERIFIED] Capture Waveform、SINGLE、四通道 raw capture、time/index 保留、CSV/PNG 导出保留。
- live：[AUTOMATED VERIFIED] RUN/STOP、`capture_in_flight` 防重入、失败停止 Live。
- project oscilloscope UI：[AUTOMATED VERIFIED] 四通道卡、默认 Time Scope、time/div/window/sample rate/scan period/cycles、独立 volts/div/position/ground marker、AUTO SET。
- voltage measurement：[AUTOMATED VERIFIED] ideal counts-to-voltage 显示；[NOT VERIFIED] 与 Keysight 或硬件精密校准的一致性。
- manual lock point：[AUTOMATED VERIFIED] Direct ERROR 默认选点和 Advanced CH1 assisted 均只创建 pending。
- Confirm / LOCK HERE / APPLY P：[AUTOMATED VERIFIED] Confirm 语义、Kp=0 首次守卫、Kp `0/4/8/16/32`、polarity 回零守卫和不覆盖锁点语义。
- safety：[AUTOMATED VERIFIED] saturation、OUT2 safe range、身份/通信失败、新 capture 清除 pending/selected、窗口关闭 SAFE 等旧安全测试继续通过。

### 当前整个项目进度

- 数字 mixer：[USER GUI VERIFIED] 当前真实 capture 中 CH3 有非零 error 波形；本轮未重新审查 RTL。
- 数字 LPF：[USER GUI VERIFIED] 当前真实 capture 中 CH3 有非零 `laser_error` 波形；精密频响未在本轮验证。
- OUT1 error：[USER GUI VERIFIED] GUI 已显示真实非零 CH3；绝对电压校准 [NOT VERIFIED]。
- OUT2 scan：[USER GUI VERIFIED] GUI 已显示 CH4 重复三角扫描；本轮新界面尚待复验。
- 四通道 capture：[USER GUI VERIFIED] 真实数据已显示；自动化回归亦通过。
- 上位机示波器：[AUTOMATED VERIFIED] 本轮专用界面代码与测试通过；新界面 [NOT VERIFIED] 用户 GUI。
- Direct ERROR Zero Crossing / Confirm / LOCK HERE / Kp=0：[AUTOMATED VERIFIED]；真实点击、切换时机和无跳变 [NOT VERIFIED]。
- P-only：[IMPLEMENTED] 最小手动路径存在；非零 Kp 闭环效果、方向和激光锁定 [NOT VERIFIED]。
- PI：[NOT VERIFIED] 当前不启用。
- 自动重锁：[NOT VERIFIED] 未实现。
- AI 优化：[NOT VERIFIED] 未实现。

### 自动化验证

- `python -m tabnanny redpitaya_lock_host/main_window.py tests/test_custom_fpga_backend.py`：通过，无输出。
- `python -m py_compile redpitaya_lock_host/main_window.py tests/test_custom_fpga_backend.py`：通过。
- collected：`pytest --collect-only -q tests/test_custom_fpga_backend.py`，`72 tests collected`。
- targeted：`pytest -q tests/test_custom_fpga_backend.py -k "scope or voltage or channel or lock_point or confirm or lock_here or safety"`，最终 `39 passed, 33 deselected`。
- current file：`pytest -q tests/test_custom_fpga_backend.py`，`72 passed`。
- full tests：`pytest -q tests`，`78 passed, 4 subtests passed`。
- 完整 `py_compile`：`main_window.py`、`waveform_plot.py`、`custom_fpga_backend.py`、`connection_workers.py`、`custom_fpga_scan_control.py` 全部通过。
- `git diff --check`：无输出。
- 离屏布局检查：1600x950 截图中三段式布局无明显重叠；离屏字体缺失导致文字方框，不属于真实 Windows GUI 验证。

### 尚未验证

- 本轮新 GUI 在真实 Windows 字体、DPI 和真实 Red Pitaya capture 下的视觉与交互。
- counts 到真实电压的精密校准、GUI mV/V 与 Keysight 绝对一致性。
- Direct ERROR 真实点击、pending marker、Confirm 后 selected 参数。
- `LOCK HERE` 真实时机、Kp=0 OUT2 无跳变、polarity、Kp=4/8/16/32、P-only 真实闭环和长期稳频。

### 未修改边界

- RTL：未修改、未读取实现细节。
- Vivado：未运行 synthesis / implementation / Generate Bitstream。
- 寄存器：未修改地址或语义。
- MAGIC / VERSION：未修改。
- bitstream：未生成、未烧录。

### 当前阶段结论

`CODE PASS / WAITING GUI`

### 下一步唯一动作

用户在真实 Windows GUI 和当前 Red Pitaya capture 下使用默认 `Direct ERROR Zero Crossing` 选择一个 CH3 过零点并点击 `CONFIRM`，只检查 marker、候选电压和 selected 参数，不执行 `LOCK HERE`。

## 2026-07-15 上位机测试尾部污染与 time(ms) target window 修复

- 初始状态：`HEAD=b061a3b22f8fd1888c6a8456dfbd5fd7b497ee7a`，工作区处于既有的 `main` interactive rebase 编辑状态，开始修改前工作区无未提交改动；本轮未继续、终止或改写 rebase。
- 测试文件根因：`tests/test_custom_fpga_backend.py` 尾部存在错误缩进的 `return`、残留的旧函数体，以及 `test_single_plot_curves_rendered_with_data_after_capture` 和 `test_default_ch2_hidden_ch1_ch3_ch4_visible` 的重复顶层定义。已只重建受污染尾部，最终共 64 个测试函数，AST 检查 `duplicates: []`。
- GUI 修复：`_update_lock_point_markers()` 在 OUT2 counts 轴继续使用 `target_window_counts`；在 time(ms) 轴使用目标索引附近的 `delta_counts / delta_time_ms` 换算窗口半宽。局部扫描速度无效或数据不足时隐藏 region，避免除零和数量级错误。target/zero marker 继续使用 `_scope_x_value(index)`。
- 保留行为：BASIC LOCK capture 找到候选后停止在 `CANDIDATE_FOUND`，清空队列并等待用户点击 CH1 与 Confirm；不自动 Confirm，不自动执行 `LOCK HERE`。候选 marker 继续跟随当前 X 轴。
- 验证：`tabnanny` 通过；指定文件 `py_compile` 通过；`pytest --collect-only -q tests/test_custom_fpga_backend.py` 收集 64 项；targeted pytest 为 `7 passed, 57 deselected`；该测试文件为 `64 passed`；完整上位机 tests 为 `70 passed, 4 subtests passed`；`git diff --check` 无输出。
- 验证边界：本轮只完成上位机软件自动化验证。未运行真实 GUI 操作和上板实验；未修改 RTL、Vivado 工程、寄存器地址/语义、MAGIC、VERSION 或 bitstream；未运行 Vivado、未生成 bitstream、未烧录。结论止于等待用户 GUI / 上板验证。
- 下一步唯一任务：用户启动上位机，在安全接线下检查 OUT2 counts 与 time(ms) 切换时 target marker、zero marker 和 target window 的中心及宽度是否正确。

## 2026-07-14 Claude Code Takeover — v3LOCK-P0 Codex 修复接管与完成

- 本轮任务：接管 Codex 未完成的 v3LOCK-P0 Host Lock Point Selector 修复，只改上位机，不改 RTL/Vivado/bitstream/寄存器。
- 执行 Agent：Claude Code（接管）。修改文件：`main_window.py`、`tests/test_custom_fpga_backend.py`、`AGENTS.md`、`version/STATUS.md`、`docs/DEVELOPMENT_LOG.md`。删除文件：`before_claude_takeover.patch`。

**接管修复（四项）：**
1. **`_find_and_render_basic_candidates()` 不再自动写入 `pending_lock_point`**：
   - 根因：旧代码在自动候选检测成功后直接调用 `resolve_lock_point_selection` 并将结果写入 `self.pending_lock_point`，与 `_on_custom_scope_clicked` 的语义冲突。
   - 修复：删除自动选择代码块；`pending_lock_point` 仅由用户点击 `_on_custom_scope_clicked` 设置。
2. **候选 marker 坐标跟随 X 轴**：
   - 根因：`_find_and_render_basic_candidates` 中的 marker 位置硬编码为 `data["time_s"][candidate.index]`，不跟随 X 轴 OUT2 counts / time(ms) 切换。
   - 修复：改用 `self._scope_x_value(candidate.index)`。`_refresh_scope_display` 已有 `_update_lock_point_markers` 调用，X 轴切换自动刷新。
3. **ramp/delta_out2 阈值回退到 `0.5`**：
   - 根因：Codex 将 `abs(median_ramp) <= 1e-9` 误改为 `<= 1e-9`（浮点 epsilon），对整数 DAC counts 完全错误。
   - 修复：三处阈值统一回退到 `< 0.5`（整数 count 语义：0.5 counts/sample 以上才算有效 ramp）。
4. **AGENTS.md Project Skill 段移除**：用户已删除 `.agents/skills/mts-redpitaya-project/`，AGENTS.md 中对应段落已移除。
5. **`before_claude_takeover.patch` 已 git rm**。
6. **测试断言修正**：`test_custom_scope_render_payload_shows_curves_range_and_candidate` 中 `pending_lock_point is not None` → `is None`（自动检测不再写入 pending）。

**测试状态：** 代码已完成，待用户手动运行 pytest 和 py_compile（VM workspace 不可用）。

**结论：** Lock Point Selector 上位机代码与测试完成，等待用户真实 GUI、capture 和人工选点验证。即使全部软件测试通过，结论也只能是"等待验证"。

---

## 2026-07-14 v3LOCK-P0 Host Lock Point Selector 最小实现与审查

- 本轮任务：v3LOCK-P0 Host Lock Point Selector，只改上位机，不改 RTL，不运行 Vivado，不生成 bitstream，不烧录。
- 执行 Agent：Claude Code. 修改文件：`main_window.py`、`tests/test_custom_fpga_backend.py`、`version/STATUS.md`、`docs/DEVELOPMENT_LOG.md`。

**审查结论：**
- 已有功能基本完整：`resolve_lock_point_selection()`（含 CH1 峰搜索、CH3 过零、CH4 ramp 方向）、`_on_custom_scope_clicked`、`_confirm_pending_lock_point`、marker 显示、LOCK HERE 守卫、APPLY P 守卫、X 轴 OUT2 counts / time(ms) 切换。
- 发现并修复的问题：
  1. `_update_lock_point_markers` 中 `custom_target_window_region.setVisible(False)` 重复调用（line 1719-1720）已删除。
  2. 测试中 `pending_lock_point` 断言与代码行为不一致：`_render_custom_capture_payload` 在新 capture 时清除 `pending_lock_point` 是正确行为（避免旧 capture 的 lock point 被新 capture 误用），但旧测试错误地期望 `pending_lock_point` 在 render 后仍存在。已修正三处测试断言并适配 OUT2 counts 坐标。
  3. 添加 11 项 `resolve_lock_point_selection` 单元测试，覆盖：CH1 峰 -> CH3 过零、多过零斜率优先、斜率接近时距离优先、ramp rising/falling、ramp 不可用时拒绝、无过零拒绝、PZT 安全范围外拒绝、边缘拒绝、saturated 拒绝、字段完整性。
- 当前实现功能（完整清单）：
  - Select Target Transition 入口
  - CH1 peak selection（局部搜索，search_radius 限制）
  - CH3 laser_error zero crossing resolver（异号判据，优先 |dError/dOut2| 最大者）
  - target_out2_counts / target_out2_volts / error_setpoint_counts / slope / ramp_direction
  - target window shaded region（跟随 X 轴）
  - marker（target peak + zero crossing）跟随 X 轴
  - Confirm Lock Point（不写 FPGA，不写寄存器，不自动 LOCK，不自动 APPLY P）
  - LOCK HERE 必须 Confirm 后可用
  - APPLY P 只允许 Kp 0/4/8/16/32，不覆盖 LOCK_BIAS / ERROR_SETPOINT
- 当前仍不是 FPGA real-time autolock，仍不是完整闭环稳频。
- 下一阶段如果 50 Hz 下 LOCK HERE 仍不可靠，需要 FPGA Arm Lock Gate。

**PASS 判据：**
- 上位机 py_compile 通过（main_window.py, waveform_plot.py, custom_fpga_backend.py, custom_fpga_scan_control.py）
- pytest 全部通过（含新增 11 项 resolve_lock_point_selection 测试）
- 点击 CH1/PD 目标峰后，GUI 正确显示 pending lock point 参数
- Confirm 后 selected_lock_point 包含所有必需字段
- LOCK HERE 未 Confirm 时被阻止
- APPLY P 不覆盖锁点寄存器

**FAIL 判据：**
- capture 返回数据但 GUI 不显示曲线
- 点击后无 pending_lock_point 或无 marker
- pending_lock_point 被新 capture 错误保留（安全风险）
- 任何 RTL/Vivado/bitstream 被本轮修改

**尚未执行（需用户手动）：**
- 上位机 py_compile 验证
- pytest 运行
- 上板验证完整 Lock Point Selector 工作流

## 当前状态快照（生成于 2026-07-13）

```text
记录生成时间：2026-07-13
执行 Agent：Codex（默认）；Claude Code 仅在 Codex 额度不足或用户明确指定时接管
记录时本地 branch：HEAD detached；该值只是本次记录环境，不是长期项目状态
记录时本地 HEAD：dd4770de296574cb0d5625cf44c9105f7ee697e5；该值只用于追溯本次快照
GitHub 主线：main；接管时以实际 `git rev-parse HEAD`、`git status --short --branch` 和用户 push 后的 GitHub main 为准
当前版本：v3LOCK-P0
当前子阶段：Custom FPGA Scope 简易台式示波器式分层显示
已完成并验证：synthesis / implementation / timing 已完成；bitstream 已生成并烧录；MAGIC=0x4D545330；VERSION=0x00030001；用户截图已证明 custom_debug_capture 返回四通道非零数据；GUI 已从空白 plot 修复为可显示真实 capture 曲线；本轮上位机测试与 py_compile 已通过
代码完成但等待用户实验验证：CH4/OUT2 上层、CH3/error 中层、CH1/PD 下层、CH2 默认隐藏的显示副本布局；该布局不改原始 capture、原始 stats、marker 时间/index、FPGA 寄存器或扫描/锁定参数
仍等待实验验证：HOLD 真实行为、LOCK HERE 真实切换、P_LOCK 真实 PZT 闭环、polarity 和小 Kp、长时间稳频、FSM 自动重锁、AI 参数优化
当前不启用：KI、integral、PI_LOCK 实验主线、自动 polarity、自动增加 Kp、自动重锁、AI 自动识峰
当前问题：本地代码已消除共用原始 Y 轴的压缩；仍等待真实板上 capture 确认分层显示便于观察且不影响选点
当前允许修改范围：本轮已完成上位机显示层、测试、状态和日志修改；不需要 RTL、不需要 Vivado、不需要生成 bitstream、不需要重新烧录
当前用户实验操作：重新启动上位机，执行 Probe Registers -> Status -> SCAN -> Capture Waveform；确认 CH4 位于上方、CH3 位于中间、CH1 位于下方、CH2 默认隐藏；点击 CH1 后确认 target/zero marker 仍落在原始时间位置
PASS：capture 四通道数据非零；CH1/CH3 不再被 OUT2 直流偏置压缩；`Scope Default` 恢复默认层位；stats 仍为原始 counts；marker 与点击时间正确；无异常输出
FAIL：capture 已返回数据但图仍空白；CH1/CH3 仍不可辨识；显示控件改变原始数据、stats、marker 或 FPGA 参数；通信/寄存器身份错误；OUT2 出现越界、饱和或异常跳变
必须 SAFE：OUT2 越界或接近安全 limit、saturation、通信失败、MAGIC/VERSION 异常、异常跳变、反馈方向疑似错误，或准备连接激光器电流调制/D2-125 输出/任何并联输出时
下一步唯一任务：用户上板验证 Custom FPGA Scope 分层显示与人工选点 marker 映射
```

## 2026-07-12 修复 Custom FPGA Scope 曲线不显示：四通道合并为单窗口

本次问题：新 bitstream 烧录后 `Capture Waveform` 返回真实 points，统计量非零（IN1/PD, IN2/REF, OUT1/laser_error, OUT2/selected_out2 Vpp > 0），但右侧四个独立 ChannelPanel plot 黑框没有显示曲线。

根因：四个独立 `WaveformPlot`（GraphicsLayoutWidget）通过 2×2 QGridLayout 排布，`ChannelPanel.apply_display_range()` 与 `_update_custom_scope_visibility()` 的交互可能导致 curve setVisible 状态与 plot 渲染不同步，且四个大窗口占用空间太大。

修复方式：把四个独立大窗口收敛为紧凑的 `Custom FPGA Scope` 单窗口，使用单个 `pg.PlotWidget`，四条曲线（CH1/CH2/CH3/CH4）在同一 plot 叠加显示。

本轮只改上位机 Python（`main_window.py` + tests），不修改 RTL / testbench / Vivado project / bitstream；不运行 Vivado，不需重新 bitstream，不需重新烧录。

修改文件：`main_window.py`、`tests/test_custom_fpga_backend.py`、`docs/DEVELOPMENT_LOG.md`、`version/STATUS.md`。

测试结果：`.venv\Scripts\python.exe -m pytest tests` 在上位机目录通过，`49 passed`；`py_compile` 通过。

上板预期：`Capture Waveform` 后 Custom FPGA Scope 单窗口中应叠加显示 CH1/CH3/CH4 三条曲线，CH2 默认隐藏；stats 显示四通道非零 Vpp；点击 CH1 目标峰附近后 target/zero marker 正确显示；safe range 越限时提示当前值和建议。

PASS 判据：capture points 非空 → 曲线在单 plot 中显示 → stats 非零 Vpp → placeholder hidden。FAIL 判据：capture 返回数据但 GUI 不显示曲线、placeholder 仍可见、stats 为 0、任何 RTL/Vivado/bitstream 被修改。

下一步唯一任务：用户重新启动上位机，`Probe Registers -> Status -> SCAN -> Capture Waveform`，确认单窗口中有三条叠加曲线（CH1/CH3/CH4）。

## 2026-07-12 v3LOCK-P0 上位机准实时观察与人工锁点工作台

本次目标：只修改上位机 Python 和既有文档记录，实现用于 10 Hz PZT 扫描的实验工作台：准实时 capture、四通道独立显示、人工点击 PD 后解析 CH3/error 过零、Confirm 后才允许 `LOCK HERE`，并保持最小 P-only `APPLY P` 链路。

修改文件：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`、`software/redpitaya_lock_host/tests/test_custom_fpga_backend.py`、`version/STATUS.md`、`version/v3/DEVELOPMENT_LOG.md`、`software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md`。继续沿用既有 `custom_fpga_backend.py` / `custom_fpga_scan_control.py` 的 `lock-here` 与 `update-p-lock` 寄存器语义，未修改 RTL、Vivado 工程、bitstream、寄存器地址或寄存器语义。

实现功能：新增 `Start Live`、`Stop Live`、`Capture Once`、`refresh interval 500/1000/2000 ms`；Live 使用 `capture_in_flight` 防重入，并且只在 capture 完成、GUI 更新和安全检查后用 single-shot timer 安排下一次 capture。右侧改为四个独立 `WaveformPlot`：CH1 IN1/PD、CH3 OUT1/laser_error、CH4 OUT2/selected_out2、CH2 IN2/REF；每通道有 `Visible`、`Auto Y`、`Scale counts/div`、`Center counts`、`Reset`，这些只改变显示范围和可见性，不改原始 capture 数据、不写 FPGA。新增 `Lock View` / `REF Debug`：Lock View 默认 CH1/CH3/CH4、隐藏 CH2、capture length 2048 并按 scan freq 估算一个扫描周期；REF Debug 默认只显示 CH2，decimation 只选 1/2/4/8，并提示不能同时完整显示 10 Hz 慢扫描周期。

人工锁点：新增 `Select Target Transition` 与 `Confirm Lock Point`。用户必须先在 CH1/PD 图点击目标峰附近；GUI 记录 clicked index/time/OUT2，再在附近窗口搜索 CH3 laser_error 有效零交叉，检查局部 Vpp、斜率、capture 边缘、OUT2 安全范围和 saturation；找到后只生成 pending lock point，并在四通道画 target peak marker 与 resolved zero-crossing marker。只有 `Confirm Lock Point` 会更新 `selected_lock_point`；`LOCK HERE` 必须已有 confirmed lock point。

最小 P-only 行为：`LOCK HERE` 仍等待 OUT2 进入 confirmed target window 后触发 FPGA `CAPTURE_LOCK_POINT`，由 FPGA 同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS` 并进入 `MODE=3 P_LOCK`，Kp 从 0 开始。`APPLY P` 仍只允许 Kp `0/4/8/16/32` 和 polarity 手动更新；不覆盖 `LOCK_BIAS` / `ERROR_SETPOINT`，不触发重新捕获，不启用 Ki/Kd，不自动增加 Kp，不自动判断 polarity，不自动重锁。

安全行为：capture 失败、SSH 失败、MAGIC/VERSION 异常、capture timeout、saturation、OUT2 超出配置 PZT safe range、`LOCK_ERROR` 连续超阈值、用户 SAFE/ABORT/Stop Live 或窗口关闭都会停止 Live 并提示 SAFE；不会自动提高 Kp、切 polarity 或重新 LOCK HERE。

尚未实现/未声明：未做 AI 自动识峰、自动重锁 FSM、自动 PID 调参、自动 polarity 判断、Ki/Kd、真实激光闭环完成声明；未运行 Vivado，未生成 bitstream，未烧录，未上板验证本轮 GUI 工作台。

测试结果：`.venv\Scripts\python.exe -m pytest tests` 在上位机目录通过，`42 passed`；`py_compile` 通过，覆盖 `custom_fpga_scan_control.py`、`custom_fpga_backend.py`、`connection_workers.py`、`main_window.py`、`waveform_plot.py`。

上板预期现象：烧录当前 `VERSION=0x00030001` bitstream 后，先读 `MAGIC=0x4D545330` / `VERSION=0x00030001`；SCAN 时 Live 约 1 Hz 刷新四通道，CH1/CH3/CH4 在 Lock View 可见且 CH2 默认隐藏；点击 CH1 峰附近后，GUI 应在 CH3 附近解析出过零并显示两类 marker；Confirm 后 `LOCK HERE` 等待 OUT2 回到 target window，进入 P_LOCK Kp=0，随后用户手动 `APPLY P` 小步测试。

PASS 判据：Live 不重入且 Stop 后不再 capture；capture 完成后才安排下一次刷新；四通道曲线和显示控制正常且不改原始数据；无有效 CH3 过零时拒绝 Confirm；未 Confirm 时 `LOCK HERE` 被阻止；`APPLY P` 不改 `LOCK_BIAS` / `ERROR_SETPOINT`；异常能停止 Live 并提示 SAFE。FAIL 判据：GUI 明明收到 capture 却不显示；Live 重入；Stop 后仍 capture；点击 PD 峰后把峰顶直接当锁点；未 Confirm 也能 LOCK HERE；APPLY P 重新捕获或覆盖锁点；任何 RTL/Vivado/bitstream 被本轮修改。

下一步唯一任务：用户上板按 `SCAN -> Lock View Live/Capture Once -> CH1 点击目标峰附近 -> Confirm Lock Point -> LOCK HERE -> Kp=0/4/8/16/32 手动 APPLY P -> 判断 polarity -> 异常 SAFE` 做真实工作台验证，并记录 capture/LOCK HERE 现象。

## 2026-07-12 PZT 基础稳频主线纠正与最小闭环

项目最终目标固定为：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。当前阶段只做最简单、可人工操作的 PZT 基础稳频：`OUT2 -> 激光器专用 PZT / Scan 输入`，`SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE`。

当前有效安全边界：OUT2 的目标执行器就是激光器专用 PZT / Scan 输入；`MODE=1 SCAN` 和 `MODE=3 P_LOCK` 使用同一个 PZT 接口。必须限制 OUT2 幅度、偏置、`LOCK_CORRECTION_LIMIT` 和 `LOCK_LIMIT`，反馈方向错误、输出接近 limit、持续 saturation、通信失败或波形异常时立即 SAFE。禁止 OUT2 接激光器电流调制输入，禁止接 D2-125 Servo Output / Aux Output，禁止两个设备输出端并联。

当前代码审查结论：RTL 已具备 `SCAN` 输出到 `selected_out2 -> DAC B / OUT2`、`CAPTURE_LOCK_POINT` 同拍捕获 `ERROR_SETPOINT` 与 `LOCK_BIAS`、`P_LOCK` 使用 `laser_error - ERROR_SETPOINT` 后的 `lock_error`、Kp=0 无扰保持 `LOCK_BIAS`、P correction 受 `LOCK_CORRECTION_LIMIT` 限制、最终 OUT2 受绝对 `LOCK_LIMIT` / DAC limit 限制、SAFE 退出。上位机已具备 `SCAN -> Capture Waveform -> 点击目标 -> LOCK HERE -> Apply Kp -> UNLOCK / SAFE` 的最小人工闭环路径；本次新增 `Apply Kp`，只更新 Kp / polarity / limit，不重新捕获 `LOCK_BIAS` 或 `ERROR_SETPOINT`。

当前仍缺失：尚未由用户反馈完成新 bitstream 烧录后的 PZT 基础稳频闭环实测；尚未证明 `custom_debug_capture` 上板 waveform 数据完整可用；尚未证明 LOCK HERE 后小 Kp 能在真实 PZT 上长期保持色散过零点；尚未实现 AI 自动识峰、自动重锁、复杂 PID、Ki/integral 或深度学习参数优化。下一步唯一任务：用户上板按 `SCAN -> 选择锁点 -> LOCK HERE -> 小步 Kp -> 判断 polarity -> 基础稳频 -> SAFE` 做实测记录。

## 2026-07-11 v3LOCK-P0 用户手动 Vivado timing PASS，下一步唯一任务是 Generate Bitstream

当前验证等级：代码与 testbench 已通过；用户手动 `red_pitaya_top` synthesis / implementation / timing 已通过。Implemented Design 已确认存在 `i_custom_debug_capture`、`i_custom_register_bank`、`i_error_setpoint_corrector`。Timing：Setup WNS `+0.031 ns`、TNS `0.000 ns`、Failing Endpoints `0`；Hold WHS `+0.048 ns`、THS `0.000 ns`、Failing Endpoints `0`；Pulse Width WPWS `+1.000 ns`、TPWS `0.000 ns`、Failing Endpoints `0`；Vivado 显示 `All user specified timing constraints are met.`

仍未完成：尚未证明 bitstream 已生成；尚未烧录；尚未读取新 `VERSION=0x00030001`；尚未完成 SAFE/SCAN 示波器回归；尚未验证 `custom_debug_capture` 上板工作；尚未验证 `LOCK HERE`；尚未真实闭环锁定激光。

关键阻塞：timing PASS 不等于 bitstream、烧录、PZT 基础稳频或锁定通过。OUT2 目标执行器是激光器专用 PZT / Scan 输入，但必须限幅、限偏置、小 Kp、异常 SAFE；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，也禁止与任何 D2-125 输出并联。

## 2026-07-11 v3LOCK-P0 LOCK HERE 与 FPGA 同拍锁点捕获候选

本次按最新安全纠正收敛为第一版人工选点：历史 `board(1).csv` 中的 `54 counts`、`0.704 V`、`0.784 V`、`49.75 Hz` 以及任何峰值/基线/扫描位置，只允许作为问题分析证据，禁止作为 RTL、Python、GUI、测试默认值或锁点配置。
新增候选协议 `VERSION=0x00030001`：`ERROR_SETPOINT`、`LOCK_ERROR_MONITOR`、`CAPTURE_LOCK_POINT`。`CAPTURE_LOCK_POINT` 在 FPGA `clk_i` 域同拍锁存 `ERROR_SETPOINT <= ERROR_MONITOR` 与 `LOCK_BIAS <= OUT2_MONITOR`，并进入 `MODE=3 P_LOCK`；P_LOCK 使用 `lock_error = saturate_14bit(laser_error - error_setpoint)`，不再直接使用原始 `laser_error`。
上位机主流程改为 `SCAN -> Capture Waveform -> 点击当前波形目标 -> LOCK HERE -> FPGA 等待当前 OUT2 重新进入所选窗口 -> 同拍捕获 -> Kp=0/Ki=0 P_LOCK -> 小 Kp 后续人工验证 -> SAFE`。第一版不做 AI、不做自动识峰、不恢复 Ki/integral、不使用历史 LOCK_BIAS。
本次已运行 Python 静态检查、pytest 与 XSim 行为仿真；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未接板子。P_LOCK/LOCK HERE 仍必须先 OUT2 示波器验证，禁止声称已闭环锁定或已替代 D2-125。

## 2026-07-11 custom_debug_capture BRAM 修复，等待用户手动 Vivado implementation 验证

用户手动 Vivado place_design 失败：`custom_debug_capture` 的四通道 4096 深度存储被推断为 LUTRAM / RAM64M / RAM64X1D，触发 `[Place 30-484]`，`LUTRAM/SRL capable slices` 需求 `1630 / 1500`，利用率 `108.667%`。
本次只修改 `v0.94/rtl/custom_debug_capture.sv` 和对应 testbench：为 `mem_ch1..mem_ch4` 添加 `(* ram_style = "block" *)`，删除组合读，改为 1 个 `clk_i` 周期延迟的同步读，目标是让 Vivado 推断 Block RAM。
四通道功能保持不变：CH1=IN1/adc_dat[0]，CH2=IN2/adc_dat[1]，CH3=laser_error，CH4=selected_out2；默认 `DEPTH=4096` 保持不变，未降级通道。
未修改 Auto Lock / P_LOCK / KI / correction limit；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未接板子，未运行 Auto Lock。下一步由用户手动重新运行 Vivado synthesis / implementation，并确认不再出现 `[Place 30-484]`，且 timing 满足 `WNS >= 0, TNS = 0, Failing Endpoints = 0`。

## 2026-07-10 Auto Lock candidate 与单窗口 debug capture 第一版

本轮进入 Auto Lock candidate：新增 P-only `LOCK_CORRECTION_LIMIT`，默认 `128 counts`，`MODE=3 P_LOCK` 的 correction 先被限制后再叠加 `LOCK_BIAS`，最终仍受绝对 DAC limit 保护；`MODE=4 PI_LOCK` 继续退化为 P_LOCK，`KI / integral` 不恢复。
上位机新增 `ARM AUTO LOCK` / `ABORT AUTO LOCK` 候选流程：必须先处于 SCAN，自动寻找 error 过零点，写 `LOCK_BIAS` 和 correction limit，强制 `Kp=0`、`Ki=0` 后进入 `MODE=3 P_LOCK`，再只允许自动小步 `Kp=4/8/16/32`；失败立即 SAFE。
GUI 右侧改为单窗口 `Custom FPGA Scope`，新增 `custom_debug_capture` 候选寄存器读取 IN1 / IN2 / OUT1 / OUT2；没有新 bitstream 或 capture 数据时显示 `custom_debug_capture not available`，不画 0 误导用户。
OUT2 当前已接 PZT / Scan，因此 correction limit 是安全必要条件；本轮未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未上板验证，禁止声称已完成激光稳频或 FPGA 已替代 D2-125。

## 2026-07-10 当前 main 主线同步

v3REG-0 SAFE/SCAN 已由用户上板验证：base address `0x40600000`，`MAGIC=0x4D545330`，`VERSION=0x00030000`，GUI / monitor 已可控制 OUT2 三角波并可 SAFE 关闭。
GitHub main 已包含 HOLD / P_LOCK / PI_LOCK 候选，但这些候选尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
当前 LOCK 目标缩小为 P-only：`MODE=3 P_LOCK` 是下一步验证重点；`MODE=4 PI_LOCK` 暂时退化为 P_LOCK，`KI / integral` 当前不要恢复。
当前 PZT 基础稳频主线允许 OUT2 接激光器专用 PZT / Scan 输入；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联；禁止声称 FPGA 已经完成全自动锁定或替代 D2-125。

## 2026-07-09 Custom FPGA Lock Host GUI 启动修复

本次只修复上位机 GUI：移除主界面对旧 Official SCPI `self.out1/self.out2` 控件的无条件依赖，解决 `run_mock.bat` 启动 `AttributeError`。
主界面仍保持 Custom FPGA Lock Host，不恢复 Official SCPI/ASG 主工作流。
未修改 RTL，未运行 Vivado，未生成 bitstream；当前有效主线以 2026-07-12 PZT 基础稳频段落为准。

## 2026-07-09 上位机主线收敛为 Custom FPGA Lock Host

上位机主界面不再暴露 Official SCPI/ASG 操作入口，默认流程改为 `Probe Registers -> Status -> SAFE -> SCAN -> Capture Bias -> LOCK -> UNLOCK/SAFE`。
`LOCK` 当前为 P-only：先读取 `OUT2_MONITOR` counts 作为 `LOCK_BIAS`，再写入 `MODE=3 P_LOCK`；不使用 `lock-bias-v` 理想电压估算捕获偏置。
`IN1/IN2` 自定义波形显示仍未实现，只记录 `debug_capture` 寄存器方案；本次未修改 RTL、未运行 Vivado、未生成 bitstream。
当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入；禁止连接激光器电流调制输入或 D2-125 输出。

## 2026-07-09 v3REG P-only timing 修复，等待用户手动 Vivado 验证

用户手动 Vivado implementation 报告当前候选存在严重 timing fail：`WNS=-10.361 ns`、`TNS=-16400.330 ns`、`Failing Endpoints=6099`，疑似来自 `out2_lock_controller` 的 error->P/PI->clamp 长组合路径。
本次将当前 LOCK 目标缩小为 P_LOCK：`MODE=3` 为流水线 P-only；`MODE=4 PI_LOCK` 暂时退化为 P_LOCK，`KI / integral` 在当前 RTL 中禁用。
Register map 和上位机命令保持不变；上位机仍可写 `KI`，但当前 RTL 不使用 `KI`。
Codex 本次不运行 Vivado，不运行 synthesis / implementation，不生成 bitstream，不声称 timing 通过。
当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入；必须限幅、限偏置、小 Kp、异常 SAFE，禁止接激光器电流调制或 D2-125 输出。

## 当前主线

当前主线 = v3REG-0 SAFE/SCAN 已由用户上板验证通过；GitHub main 的 RTL 已包含 v3REG-1 / v3REG-2 候选逻辑，但 HOLD / P_LOCK / PI_LOCK 尚未完成 Vivado synthesis / implementation / timing / bitstream / 上板验证。

```text
OUT1 = laser_error = mixer + LPF error observation
OUT2 = selected_out2
  MODE=0 SAFE: OUT2 = 0
  MODE=1 SCAN: OUT2 = ramp_generator
  MODE=2 HOLD: OUT2 = HOLD_VALUE
  MODE=3 P_LOCK: OUT2 = clamp(LOCK_BIAS + POLARITY * KP * error, LOCK_LIMIT)
  MODE=4 PI_LOCK: 当前暂时退化为 P_LOCK；KI / integral 当前不要恢复
laser_control / pi_controller_seq = 内部候选/历史路径，不是当前 DAC B / OUT2 最终输出
```

v3REG-0 已验证内容：Red Pitaya 加载 `/root/red_pitaya_top.bit.bin` 后，`0x40600000` 可读到 `MAGIC=0x4D545330`、`VERSION=0x00030000`，GUI/monitor SAFE/SCAN 可控制 OUT2 三角波并可 SAFE 关闭。

v3REG-1 / v3REG-2 当前状态：代码和仿真候选已存在，包含 `HOLD_VALUE / KP / POLARITY / LOCK_BIAS / LOCK_LIMIT / ERROR_MONITOR / CONTROL_MONITOR / KI / INTEGRAL_RESET`。这些模式还没有通过 Vivado timing、没有生成新 bitstream、没有烧录、没有上板验证。

强制安全边界：OUT2 只允许接激光器专用 PZT / Scan 输入；禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联；禁止声称已经完成全自动锁定或已经替代 D2-125。

## 2026-07-05 GUI Custom FPGA Control v1 已接入

上位机 PySide6 GUI 已新增 Custom FPGA Control v1：Probe Registers / Status / SAFE / SCAN。
该路径通过 SSH + `/dev/mem` 访问 `custom_register_bank`，不启动 `redpitaya_scpi`，不使用 Official SCPI ASG 控制 Custom FPGA OUT2。
SAFE / SCAN 写寄存器前必须读到 `MAGIC = 0x4D545330`；`MAGIC = 0x00000000` 时 GUI 提示重新 Probe、检查 Program Device / 旧 bit / base address / timing-pass bitstream。
本次未修改 RTL，未生成 bitstream。

## 2026-07-05 v3REG-0 status 可读但 MAGIC 为 0，已新增只读 probe

用户通过 SSH 执行 `status` 已成功，但读到 `magic/version = 0x00000000`，因此不能 `safe` / `scan`。
脚本新增只读 `probe`，扫描 `0x40000000` 到 `0x40700000` 的 1 MiB base，逐项输出 magic/version。
若 `probe` 全 0，优先重新 Program Device / 重新加载当前 timing-pass 的 `red_pitaya_top.bit`；不要因未打开网页 App 就排除 bitstream 加载问题。

## 2026-07-05 v3REG-0 host SSH quoting 与烧录顺序 SOP 已修正

`custom_fpga_scan_control.py` 已修复 Windows PowerShell -> SSH -> remote bash 的 `python3 -c` quoting，避免远端 bash 误解析 Python 代码。
实验顺序明确为：先 Generate Bitstream 并把 timing-clean bitstream 加载/烧录进 Red Pitaya FPGA，再运行上位机脚本。
Red Pitaya 网页界面不是本阶段必需条件；VPN 可能影响网页、`.local` 或 SSH，建议关闭 VPN 或使用板子实际 IP。
烧录后第一步仍是 `status`，必须读到 `MAGIC=0x4D545330`；之后才允许 `safe` / `scan`。当前 PZT 基础稳频主线下，OUT2 只允许接激光器专用 PZT / Scan 输入。

## 2026-07-05 v3REG0_TIMING_FIX_2 用户手动 Vivado implementation timing PASS

用户手动 Vivado implementation 已通过：`WNS = +0.322 ns`，`TNS = 0.000 ns`，`Failing Endpoints = 0`。
允许进入 Generate Bitstream；当前有效主线已纠正为 OUT2 目标执行器是激光器专用 PZT / Scan 输入。
禁止接激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，禁止任何输出端并联。

## 2026-07-05 v3REG0_TIMING_FIX_2 已拆分 ramp_generator 三角波更新路径

用户手动 Vivado 仍剩 1 条 setup fail：`step_q_reg[5]/C -> direction_up_q_reg/D`，WNS/TNS 均为 `-0.085 ns`。
本次只修改 `v0.94/rtl/ramp_generator.sv`，把 tick 后的位置更新拆成候选计算拍和边界/方向提交拍，切断 `step_q` 同周期影响 `direction_up_q` 的路径。
本地 `xvlog -sv rtl/ramp_generator.sv` 通过，0 error；未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录。
用户下一步：Vivado `Reset Runs -> Run Synthesis -> Run Implementation -> Timing Summary`，通过标准仍为 `WNS >= 0, TNS = 0, Failing Endpoints = 0`。

## 2026-07-05 v3REG0_TIMING_FIX_1 已修复 ramp_generator 配置长路径，等待用户重新跑 Vivado

用户手动 Vivado implementation timing failed：

```text
WNS = -3.697 ns
TNS = -274.520 ns
Failing Endpoints = 830

Worst path:
From: i_custom_register_bank/.../C
To:   i_ramp_generator/.../D
Logic Levels = 18
High Fanout = 30
Total Delay = 11.685 ns
Requirement = 8.000 ns
```

结论：v3REG-0 当前不能 Generate Bitstream，不能烧录，不能上板。

本次只做最小 timing 修复：在 `ramp_generator.sv` 内部增加本地配置寄存器 `offset_q / amp_q / step_q / update_div_q / update_div_m1_q / limit_q`。`custom_register_bank` 输出不再直接进入三角波位置更新、限幅和 tick 判断的深组合逻辑；tick 判断改为使用已寄存的 `update_div_m1_q`。

本次未修改 `red_pitaya_top.sv`，未修改 `custom_register_bank.sv`，未修改 `laser_lock_core.sv`，未修改 PI/mixer/LPF/output_protect，未修改 XDC/constraints，未修改 Vivado project structure。未运行 Vivado synthesis / implementation，未生成 bitstream / bin，未烧录 Red Pitaya。

本地语法检查：

```text
xvlog -sv rtl/ramp_generator.sv
结果：0 error
```

用户下一步必须手动 Vivado `Reset Runs`，重新 `Run Synthesis`，重新 `Run Implementation`。通过标准仍然是：

```text
WNS >= 0
TNS = 0
Failing Endpoints = 0
```

只有 timing 通过后才允许继续 Generate Bitstream；在此之前禁止烧录和上板。

## 2026-07-05 v3REG-0 P0-1 host MAGIC 预校验已修复，等待用户手动 Vivado 和示波器验证

本次只修复上位机脚本安全阻塞项，不修改 RTL 功能逻辑。

修复内容：

```text
software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py

safe:
  打开 RegisterWindow
  -> require_magic()
  -> ENABLE=0
  -> MODE=0
  -> 打印 status

scan:
  打开 RegisterWindow
  -> require_magic()
  -> ENABLE=0
  -> 写 SCAN_OFFSET / SCAN_AMP / SCAN_STEP / SCAN_UPDATE_DIV / OUT2_LIMIT
  -> MODE=1
  -> ENABLE=1
  -> 打印 status
```

如果 `MAGIC != 0x4D545330`，脚本会立即非零退出，并且不会写 `MODE`、`ENABLE`、`SCAN_OFFSET`、`SCAN_AMP`、`SCAN_STEP`、`SCAN_UPDATE_DIV`、`OUT2_LIMIT` 等任何寄存器。错误信息会显示实际 magic、期望 magic，并提示旧 bitstream、base address 错误或 `sys[6]` 未连接 `custom_register_bank`。

本次未修改 RTL，未运行 Vivado synthesis / implementation，未生成 bitstream / bin，未烧录 Red Pitaya，未连接 Red Pitaya 执行真实 `safe` / `scan`，未执行 git add / commit / push。

用户下一步仍然是：手动 Vivado synthesis / implementation，timing 通过后生成 bitstream，烧录后只接 OUT2 到示波器，先运行 `status` 确认 `MAGIC=0x4D545330`，再做 SAFE/SCAN 示波器验证。

## 2026-07-04 v3REG-0 最小 register_bank 与 OUT2 host-controlled SCAN 已实现，等待用户手动 Vivado 和示波器验证

本次实现目标是关闭“只能编译时硬编码 OUT2 三角波”的限制，新增最小运行时参数链路：

```text
上位机 SSH
-> Red Pitaya Linux /dev/mem
-> PS M_AXI_GP0
-> sys_bus_if / sys[6]
-> custom_register_bank
-> ramp_generator
-> OUT2
```

当前只支持：

```text
SAFE: OUT2 = 0
SCAN: OUT2 = offset + triangle
```

默认参数：

```text
offset = 0.85 V ~= 6962 counts
amp = +/-0.05 V ~= 410 counts
freq ~= 50 Hz
limit = +/-1 V ~= 8191 counts
```

安全边界不变：本阶段只允许 OUT2 接示波器；不接 Scan/PZT，不接激光器，不接 D2-125 Servo Output，不接 D2-125 Aux Output，不和 D2-125 Aux Output 并联，不声称已经闭环锁定。

Codex 本次未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录 Red Pitaya，未连接 Red Pitaya 网络，未执行 git add / commit / push。

## 2026-07-02 v2B3_scope_safe only-p 上板示波器测试 PASS WITH NOTES

本次记录用户完成的 `v2B3_scope_safe / only-p.csv` 上板示波器数据。该版本使用 `Ki=0` 与 `output_limit=819`，目标是验证 `CONTROL_PATH_MODE=1` 下 `pi_controller_seq` 的 P 路径在示波器-only 条件下是否安全可解释。

本次只记录 Markdown；未修改 RTL，未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

```text
Board OUT1 / CH1:
Vpp ≈ 0.04874 V
min ≈ -0.01209 V
max ≈ +0.03665 V
RMS ≈ 0.01007 V
mean ≈ +0.00868 V

Board OUT2 / CH4:
Vpp ≈ 0.02410 V
min ≈ -0.00177 V
max ≈ +0.02233 V
RMS ≈ 0.00888 V
mean ≈ +0.00850 V
```

实验判断：

```text
OUT1 error observation 正常，Vpp 约 48.74 mV。
OUT2 Vpp 约 24.10 mV，mean 约 +8.50 mV。
OUT2 不再贴 -0.2 V。
OUT2 不再贴近负向 output_limit。
OUT2 / OUT1 Vpp ≈ 0.02410 / 0.04874 ≈ 0.494。
Ki=0 scope-safe 修正有效。
v2B3_scope_safe 可以判定为 PASS WITH NOTES，并准备关闭。
```

Notes：

```text
这不是闭环锁定。
这不代表 FPGA 已经替代 D2-125。
这不允许直接进入 OUT2 接 Scan/PZT。
OUT2 仍只允许接示波器。
```

记录文件：

```text
version/v2/V2B3_SCOPE_SAFE_ONLY_P_TEST_RECORD.md
```

## 2026-07-02 v2B3 only-pi 示波器测试未通过，进入 v2B3_scope_safe

本次记录用户上传的 `only-pi.csv` / `only-pi_timeseries.png` 示波器测试结论，并生成下一版 `v2B3_scope_safe` 安全修正。Codex 本次只做 Markdown 记录和 `laser_lock_core.sv` 小范围默认参数安全修正；未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

本次 only-pi 不是 v2B3 通过数据。

```text
OUT1 正常：
Board OUT1 / CH1 能看到 FPGA mixer + LPF 后的 error-like 信号。
Vpp ≈ 0.05385 V，min ≈ -0.02714 V，max ≈ +0.02671 V，RMS ≈ 0.009618 V。

OUT2 未通过：
Board OUT2 / CH4 长期贴在约 -0.2 V 附近。
Vpp ≈ 0.01497 V，min ≈ -0.2036 V，max ≈ -0.1886 V，RMS ≈ 0.1991 V，mean ≈ -0.199 V。
```

判断：

```text
OUT1 error observation 链路基本正常。
OUT2 只剩约 15 mVpp 小动态，不是 v2B3 通过现象。
OUT2 更像是 control_o 被负向 output_limit 限幅，而不是 Red Pitaya +/-1 V 满量程物理削顶。
疑似 sequential PI 的积分项在同号 error 下累积，把 control_o 推到负向 output_limit。
```

同步记录的其他通道：

```text
CH2:
Vpp ≈ 0.151 V
min ≈ 0.593 V
max ≈ 0.744 V
RMS ≈ 0.6554 V

CH3:
Vpp ≈ 2.443 V
min ≈ -1.102 V
max ≈ +1.341 V
RMS ≈ 0.3496 V
```

CH3 外部 D2-125 / analog error 相关信号较大，不能直接进入 Red Pitaya IN1/IN2。IN1/IN2 仍必须保持在 `+/-1 V` 内。

本轮 `v2B3_scope_safe` RTL 参数安全修正：

```text
v0.94/rtl/laser_lock_core.sv

PID_KI_DEFAULT: 16'sd16 -> 16'sd0
PID_OUTPUT_LIMIT_DEFAULT: 14'd1500 -> 14'd819
```

含义：

```text
Ki=0：先关闭积分项，验证 CONTROL_PATH_MODE=1 下 pi_controller_seq 的 P 路径是否安全。
output_limit=819：约等于 +/-0.10 V。
如果 OUT2 仍然偏置明显或接近 limit，下一轮再降到 410 counts，约 +/-0.05 V。
```

当前安全边界：

```text
本次不能进入真实反馈测试。
OUT2 仍只能接示波器。
禁止 OUT2 接激光器。
禁止 OUT2 接 D2-125 Servo Output 三通。
禁止 OUT2 接 D2-125 Aux Output。
禁止 OUT2 接激光器电源 Scan / PZT。
禁止 OUT2 与任何 D2-125 输出并联。
IN1/IN2 必须在 +/-1 V 内。
```

记录文件：

```text
version/v2/V2B3_ONLY_PI_SCOPE_TEST_RECORD.md
```

## 2026-07-01 Aux/PZT 实验数据记录与路线更新

本次只记录用户最新确认的 D2-125 Aux Output / Scan-PZT 数据，并更新后续 scan/lock 开发计划。Codex 本次未修改 RTL，未运行 Vivado，未综合、实现、生成 bit/bin，也未烧录 Red Pitaya。

最新实验结论：

```text
ramp-aux-unlock.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.1173 V
  min = 0.7505 V
  max = 0.8678 V
  mean 约 0.8087 V
  主频约 52.68 Hz

ramp-aux-unlock1.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.0626 V
  min = 0.7767 V
  max = 0.8393 V
  mean 约 0.8096 V
  主频约 52.68 Hz

ramp-aux-locking.csv:
  CH4 = D2-125 Aux Output
  Vpp = 0.0169 V
  min = 0.8031 V
  max = 0.8200 V
  mean 约 0.8130 V
```

新的物理认识：

```text
D2-125 Aux Output 不是单纯从 0 V 开始的三角波。
Ramp / Unlock 状态约为 0.81 V DC offset + 0.063~0.117 Vpp triangle，主频约 52.7 Hz。
Lock 状态约为 0.813 V hold + 0.0169 Vpp residual / slow correction。
```

因此，Red Pitaya OUT2 后续如果替代 D2-125 Aux Output，应按下面路线实现：

```text
SCAN:   OUT2 = scan_offset + triangle
HOLD:   OUT2 = captured_vlock
P_LOCK: OUT2 = captured_vlock + Kp * error
PI_LOCK:OUT2 = captured_vlock + Kp * error + Ki * integral(error)
```

当前能力边界仍然是：

```text
历史记录：当时 FPGA 只有 mixer + LPF + 简单 P/PI candidate。
当前 main 纠偏：现在已经有 custom_register_bank 和 selected_out2 scan/lock mode selector。
当前 main 纠偏：上位机已经能在 Custom FPGA Mode 下写 SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 候选寄存器。
当前仍然不能声称已经实现 PZT 锁定。
```

记录文件：

```text
version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md
```

## 2026-06-30 v2B3 mode=1 sequential PI 时序通过记录

这里记录的是用户手动运行 Vivado Implementation 后给出的结果，只作为项目状态记录。
Codex 本次没有运行 Vivado，没有综合、实现、生成 bitstream，也没有烧录 Red Pitaya。

```text
2026-06-xx 用户手动 Vivado Implementation:
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
结论：mode=1 sequential PI 候选版本 timing clean。
```

边界说明：

```text
timing clean != 已经锁定激光
timing clean != 已经完成 D2-125 替代
timing clean != 允许把 OUT2 接到激光器
```

下一步仍然只能做示波器验证：

```text
OUT1 -> 示波器：确认 FPGA laser_error / error observation 正常
OUT2 -> 示波器：当前 main 应确认 selected_out2；历史 sequential PI/laser_control 只作为内部候选路径
当前阶段 OUT2 禁止连接激光器、D2-125 Servo Output、D2-125 Aux/Scan，
也禁止连接任何真实执行器通道。
```

## 2026-06-23 v2B3 mode=1 上板候选已准备，等待用户手动 timing 验证

当前实际实验接线记录：

```text
PD -> v1 既有带通/放大链路 -> Red Pitaya IN1
同路解调 REF -> Red Pitaya IN2
OUT1 -> 板内 mixer + LPF 后的 FPGA demodulated error -> 示波器 CH2
OUT2 -> 当前代码产生的 shadow/sequential control -> 示波器 CH4
```

v2B1 timing-safe P-only Shadow Control 上板验证已完成：`mixer.csv` 的 OUT2/OUT1 Vpp 为 `0.515`，`no-mixer.csv` 为 `0.555`；OUT2 没有打到 `+/-1 V`，证明 OUT2 安全输出通道已打通，但这不是激光锁定实验，也不能声称替代 D2-125。

本轮顶层已新增 `LASER_LOCK_CONTROL_PATH_MODE=1` 并显式传给 `laser_lock_core`。这使下一次用户手动生成的候选工程选择 v2B3 sequential PI；OUT1/OUT2 顶层 DAC 路由保持不变。该候选尚未完成新的 Vivado timing 或示波器验证，因此 OUT2 仍只能接示波器。

## 2026-06-22 v2B2/v2B3 sequential PI RTL/SIM 完成，等待 Vivado timing

v2B1 已关闭：OUT2 timing-safe P-only 安全输出已完成上板示波器验证，记录的 implementation 为 `WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`，且 OUT2/OUT1 实测约为 `0.515` 与 `0.555`。

本轮新增 `pi_controller_seq.sv`，使用七状态顺序更新：`IDLE -> CAPTURE -> P_CALC -> I_CALC -> I_UPDATE -> SUM -> LIMIT`。完整 PI 算法保持 P、I、offset、对称限幅和 anti-windup 语义，但乘法、积分更新、求和、限幅分拍寄存，避免旧完整 PI 的单条长组合路径。

`laser_lock_core.sv` 现在使用：

```text
CONTROL_PATH_MODE=0：timing-safe P-only Shadow Control，当前默认回退路径。
CONTROL_PATH_MODE=1：新的 pi_controller_seq sequential PI，v2B3 目标路径。
CONTROL_PATH_MODE=2：旧 pi_controller，仅参考/仿真，不作默认板级路径。
```

本轮 XSim：

```text
tb_pi_controller_seq: tests=35 pass=35 fail=0
tb_laser_lock_core_v2b1_shadow_pi_dc_error: tests=27 pass=27 fail=0
```

当前仍不能声称 sequential PI 已 timing-clean 上板，也不能将 OUT2 接激光器、D2-125 Servo Output 或 Scan。下一步由用户手动把 `pi_controller_seq.sv` 加入 Vivado Design Sources 后检查 timing；只有 XSim、Vivado timing、OUT2 示波器都通过，才讨论低增益闭环。

## 2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成

本次由用户完成 Vivado 重新综合、实现、bitstream 生成和 Red Pitaya 烧录；记录的 timing 结果为：

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
```

本轮接线仅为 `OUT1 -> 示波器`、`OUT2 -> 示波器`。OUT2 没有接激光器、D2-125、Scan 或 Servo Output。

### 上板数据

| 数据文件 | OUT2 shadow control | Board OUT1 error | OUT2 / OUT1 | 其他同步观察 |
|---|---:|---:|---:|---|
| `mixer.csv` | Vpp `0.01771 V`，RMS `0.007694 V` | Vpp `0.03439 V`，RMS `0.003643 V` | `0.515` | Saturated absorption peak：Vpp `0.1893 V`，RMS `0.8157 V`；D2-125 error：Vpp `1.829 V`，RMS `0.3469 V` |
| `no-mixer.csv` | Vpp `0.02644 V`，RMS `0.006752 V` | Vpp `0.04768 V`，RMS `0.004388 V` | `0.555` | Saturated absorption peak：Vpp `0.1793 V`，RMS `0.8147 V`；D2-125 error：Vpp `0.0402 V`，RMS `0.2935 V` |

比例计算：

```text
mixer.csv:    0.01771 / 0.03439 = 0.515
no-mixer.csv: 0.02644 / 0.04768 = 0.555
```

### 实验结论

```text
2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成。

1. OUT1 能输出 FPGA mixer+LPF 后的 error signal，幅度为几十 mVpp。
2. OUT2 能输出由 OUT1 派生的 P-only shadow control。
3. OUT2 / OUT1 比例约为 0.5。
4. OUT2 没有打到 +/-1 V。
5. OUT2 没有出现明显失控、饱和或积分爬升。
6. 该现象与 RTL 中 protected_error >>> 1 的 timing-safe P-only 设计一致。

阶段结论：v2B1 的 OUT2 控制输出通道已经打通。
当前版本可作为“OUT2 安全输出验证通过”的实验记录。
```

### 小白解释：为什么 OUT1 / OUT2 只有几十 mV

这是安全测试版本的正常现象，不是失败。OUT2 当前不是完整 PI/PID 的大范围控制量，而是将 `protected_error` 做 `>>> 1` 后的半幅 P-only 输出；同时没有数字增益放大、没有积分累积，因此 OUT1 和 OUT2 都保持在较小幅度，便于先验证 OUT2 输出通道是否安全、方向是否合理。

### 仍然有效的限制

```text
当前版本不是完整 PI。
当前版本不是 PID。
当前版本不能锁定激光。
当前版本不能声称替代 D2-125。
OUT2 仍然只能接示波器。
OUT2 禁止接激光器。
OUT2 禁止接 D2-125 Servo Output。
OUT2 禁止接 Scan。
D2-125 DC Error 禁止接 Red Pitaya IN1。
```

## 2026-06-16 当前主线：v2B1 timing-safe P-only Shadow Control（当前有效）

手动 Vivado Implementation 已暴露一个关键 timing 问题：完整 `pi_controller.sv` 直接放进 v2B1 主工程路径时，125 MHz 下未通过时序，记录现象约为 `WNS=-10.995 ns`、`TNS=-5029 ns`。最差路径位于：

```text
i_laser_lock_core/u_output_protect/data_o_reg
-> i_laser_lock_core/i_pi_controller
-> control_o_reg
```

该路径穿过 DSP48E1、CARRY4、48-bit integrator、anti-windup freeze、integrator_accepted、P+I+offset limiter 和 `control_o` 更新逻辑。结论是：完整 PI 算法仍然保留为 v2A 已验证核心，但不能再作为 v2B1 默认上板路径。

当前有效 RTL 策略：

```text
v0.94/rtl/pi_controller.sv：不修改，保留完整 PI + anti-windup，供后续 v2B2/v2B3 流水线化使用。
v0.94/rtl/laser_lock_core.sv：默认 USE_FULL_PI_CONTROLLER=0，使用 timing-safe P-only Shadow Control。
OUT1：继续观察 FPGA mixer+LPF error。
OUT2：只输出很小的 P-only shadow control，只接示波器。
```

当前默认板级链路：

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o / OUT1

同一个 protected_error
-> timing-safe P-only Shadow Control
-> control_o / OUT2
```

OUT2 预期：约为 OUT1 error 的 1/2，并受 `PID_OUTPUT_LIMIT_DEFAULT=1500` 限制，约 `+/-0.18 V`。当前仍不能接激光器，不能接 D2-125 Servo Output，不能接 Scan，不能声称已经闭环替代 D2-125。

本轮独立 XSim 回归：

```text
xvlog：0 error，0 warning
xelab：0 error，0 warning
xsim：tests=18 pass=18 fail=0
日志：v0.94/xvlog.log，v0.94/xelab.log，v0.94/xsim.log
```

## 2026-06-14 当前主线：v2B1 FPGA MTS Error Shadow PI（当前有效）

当前安全主线已经从旧的“D2-125 DC Error -> Red Pitaya IN1”旁路方案，修正为使用 Red Pitaya 自身 IN1/IN2 生成 FPGA 内部 error，并把该 error 同时送到 OUT1 观察和 OUT2 Shadow PI 控制输出。

### 当前硬件接线边界

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> 外部 REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器 CH2：FPGA mixer+LPF error，当前约 0.12~0.15 V
Red Pitaya OUT2 -> 示波器 CH4：FPGA P-only control
```

禁止：

```text
D2-125 DC Error -> Red Pitaya IN1
D2-125 Servo Output -> Red Pitaya IN1
Red Pitaya OUT2 -> 激光器
Red Pitaya OUT2 -> D2-125 Servo Output 三通
Red Pitaya OUT2 -> 激光器电源 Scan
任何超过 +/-1 V 的信号进入 IN1/IN2
```

### 当前代码状态

```text
v0.94/rtl/laser_lock_core.sv：
control_o 不再固定为 0，已接入 pi_controller。

v0.94/rtl/red_pitaya_top.sv：
OUT1 / DAC A 仍为 laser_error；
历史记录：当时 OUT2 / DAC B 曾改为 laser_control。当前 main 中 OUT2 / DAC B 的最终输出为 selected_out2。

v0.94/rtl/pi_controller.sv：
本次未修改，继续使用 v2A 已完成的 PI 控制器核心。

v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：
新增 v2B1 Shadow PI 行为仿真。
```

### 初始参数

```text
PID_ENABLE_DEFAULT = 1
PID_HOLD_DEFAULT = 0
PID_RESET_INTEGRATOR_DEFAULT = 0
PID_POLARITY_DEFAULT = 0
PID_KP_DEFAULT = 16'sd2048
PID_KI_DEFAULT = 16'sd0
PID_OFFSET_DEFAULT = 14'sd0
PID_OUTPUT_LIMIT_DEFAULT = 14'd1500
PID_UPDATE_HZ = 10_000
```

含义：

```text
Kp=2048：OUT2 约为 OUT1 error 的 1/2
Ki=0：避免 OUT2 积分慢慢爬升
output_limit=1500：约 +/-0.18 V，防止 OUT2 接近 +/-1 V
```

### 独立仿真状态

```text
xvlog：0 error
xelab：0 error
xsim：SUMMARY tests=13 pass=13 fail=0
```

### 本轮不执行

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

Vivado、bitstream、bin 和烧录由用户手动完成。

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前执行路线。禁止把 D2-125 DC Error 或 D2-125 Servo Output 接入 Red Pitaya IN1。当前有效主线见本文档最前面的“v2B1 FPGA MTS Error Shadow PI”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，也不是 FPGA 直接替代 D2-125。当前下一步定义为：

```text
v2B1 Shadow PI DC Error 旁路测试

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

当前真实接线：

```text
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 三通 -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3，后续接 Red Pitaya IN1
Red Pitaya OUT2 -> 后续示波器 CH4
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
对应
error_i -> pi_controller.sv -> control_o
```

v2A2 独立仿真报告结论：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只证明 `pi_controller.sv` 独立 testbench 通过，不证明它已进入主工程、已接 OUT2、已生成 bitstream、已上板或已控制激光。

下一步代码边界：

```text
允许修改：
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/red_pitaya_top.sv

允许新建：
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv

禁止修改：
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
```

本轮文档任务不修改任何 `.sv`，不运行 XSim，不运行 Vivado，不生成 bitstream，不上板。

## 2026-06-15 注释与路线清理状态

本轮允许对 RTL/SIM 增加解释性注释，但不允许改变功能逻辑。当前已经把 v2B1 的有效路线固定为：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> error_o -> OUT1
error_o -> pi_controller -> control_o -> OUT2
```

所有后续文档和代码注释都必须把 `D2-125 DC Error -> Red Pitaya IN1` 视为历史废弃路线，不得作为当前接线方案。OUT1 在 v2B1-v2F 继续作为 error observation；OUT2 第一阶段只接示波器。

## 当前阶段

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 当前协作原则

每个子阶段最多一次 Claude Code 集中审查和一次 Codex 修正。通过回归仿真后关闭子阶段，不再循环审查。

## v1 状态

v1 已完成 FPGA 数字解调基础链路：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

含义：FPGA 已经能产生可用于 D2-125 的 error-like signal。当前真正闭环控制激光的仍然是 D2-125。

## v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

v2 目标链路：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器。

## v2 阶段图

```text
v2A：独立数字 PI 核心
  v2a-1：P-only
  v2a-2：I + anti-windup

v2B：系统接口和主工程集成
v2C：Vivado 综合、实现、时序、DRC 和 bitstream
v2D：OUT2 示波器空载上板测试
v2E：真实 MTS error 输入、OUT2 开环观察
v2F：低增益闭环替代 D2-125
v2G：FPGA PI 与 D2-125 性能对比
```

## v2A 当前记录

- v2a-1：P-only 已关闭；不再重复 GPT 或 Claude Code 审查。
- v2a-2：I 通道、integrator 和 anti-windup 已完成初次实现和独立 XSim 回归；等待一次 Claude Code 集中审查。

## v2B 开始前必须回答

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 当前禁止事项

- 不修改 RTL，除非用户另行明确授权。
- 不运行 XSim，除非用户另行明确授权。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 关键文档

- `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_GOAL_AND_CHAIN.md`
- `E:\new\fpga_lock\v94\version\v2\V2_DEVELOPMENT_ROADMAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_NEXT_STEPS.md`
- `E:\new\fpga_lock\v94\version\v2\GPT_REVIEW_V2_SUMMARY.md`

## 2026-07-12 v3LOCK-P0 APPLY P host fix
- 本次只修改上位机，不修改 RTL / testbench / Vivado project。
- 新增 `update-p-lock` / GUI `APPLY P`：LOCK HERE 后仅小步更新 Kp/polarity，不重新捕获或覆盖 `ERROR_SETPOINT` / `LOCK_BIAS`。
- Kp 仅允许 `0, 4, 8, 16, 32`；非零 Kp 下禁止直接翻转 polarity，需先 APPLY P 到 Kp=0。
- 已通过 `py_compile` 和 `python -m pytest tests`；未运行 Vivado、未生成 bitstream、未烧录、未声明真实稳频完成。
- 下一步唯一人工任务：上板按 `SCAN -> 选择过零点 -> LOCK HERE -> APPLY P 小步 Kp -> 判断 polarity -> 异常 SAFE` 验证。

## 2026-07-12 BASIC LOCK 小白版上位机收敛
- 本次只修改上位机与现有日志，不修改 RTL / testbench / Vivado project。
- 修复 `Custom FPGA Scope` 黑屏风险：显式设置黑底亮轴、亮字、曲线颜色、placeholder 引用和 CH3/CH4 显示 range。
- 新增 BASIC LOCK 顶层入口：用户只需输入 PZT safe min/max，自动计算 offset/amp/freq/step/capture decimation，并用当前 capture 寻找候选 zero crossing。
- BASIC LOCK 仍不是 AI、不是自动重锁、不是长期稳频证明；失败或异常必须 SAFE。
- 已通过 `py_compile` 和 `python -m pytest tests`，结果 `28 passed`；未运行 Vivado、未生成 bitstream、未烧录。
## 2026-07-12 BASIC LOCK 联调阻塞修复
- 本次只修改上位机和现有日志，不修改 RTL / testbench / Vivado project，不运行 Vivado，不生成 bitstream，不烧录。
- 修复 BASIC LOCK 内部 SAFE 步骤会清空自身状态机的问题；内部流程可继续 SAFE -> SCAN -> CAPTURE -> CANDIDATE_FOUND -> CAPTURE_LOCK_POINT -> P_LOCK。
- 启动时自动做只读 status 探测，显示 MAGIC / VERSION / MODE / ENABLE / STATUS / OUT2；失败时显示通信或寄存器原因，不再只显示 `--`。
- `custom_debug_capture` 无数据时明确提示真实 FPGA capture 接口不可用，不伪造波形；无完整波形寄存器时不能替代为 status 单点采样。
- LOCK HERE 成功后停在 MODE=3 P_LOCK 且 Kp=0；后续 Kp 仍需用户手动 APPLY P，禁止自动 Ki/PI。
