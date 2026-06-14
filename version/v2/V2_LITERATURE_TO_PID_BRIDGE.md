# V2_LITERATURE_TO_PID_BRIDGE

本文档服务于 v2 FPGA PI/PID 替代 D2-125 阶段。

## 1. 整理原则

本文件只从已有 `E:\new\fpga_lock\文献阅读` notes 中提取与 v2 直接相关的信息，不泛读 PDF，不做长篇综述。重点只看：

- Red Pitaya / STEMlab 实时控制；
- digital servo / PI / PID；
- ADC/DAC 幅度和延迟；
- fixed-point 位宽；
- output limit / saturation；
- anti-windup / freeze / hold；
- D2-125 替代的安全边界。

## 2. A 类：v2 必须参考

| 笔记 | 文件路径 | 与 v2 的关系 | 工程启发 | 是否影响 `pi_controller.sv` |
|---|---|---|---|---|
| Linien: Red Pitaya FPGA laser locking | `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\数字解调\Paper_数字解调_001_Linien_RedPitaya_FPGA_Laser_Locking.md` | 说明 Red Pitaya 可做数字解调、IIR filtering、PID/DAC 输出；实时链路必须在 FPGA。 | v2 应保持 FPGA 内实时 servo，AI/自动选锁点放后续；输出前必须做幅度缩放和限幅。 | 是。支持 `error_i -> PI -> limiter -> DAC` 的实时链路，以及 low-latency、可配置增益、debug 输出。 |
| PyRPL / Lockbox / IQ / PID | `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\数字解调\Paper_数字解调_002_PyRPL_RedPitaya_Lockbox_IQ_PID.md` | 说明 Red Pitaya FPGA 模块可路由 IQ/IIR/PID，强调 DAC 动态范围、有效位数和反馈延迟。 | v2 应设计 enable、hold、polarity、output limit、safe output；Lockbox 状态机暂不进入 v2。 | 是。支持 PI 接口中加入 `enable_i`、`hold_i`、`polarity_i`、`output_limit_i`、`reset_integrator_i`。 |
| Digital laser frequency and intensity stabilization based on STEMlab | `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\数字解调\Paper_数字解调_008_Digital_laser_frequency_and_intensity_STEMlab.md` | 证明 STEMlab/Red Pitaya 可作为 PI 控制平台，并给出 ADC/DAC、PI、延迟、输出缩放等接口约束。 | v2 第一版优先 PI；必须关注 ADC/DAC 幅度、offset、延迟和输出安全。 | 是。支持第一版只做 PI、默认安全输出、低增益上板和输出限幅。 |

## 3. B 类：可参考

| 笔记 | 文件路径 | 与 v2 的关系 | 工程启发 | 是否影响 `pi_controller.sv` |
|---|---|---|---|---|
| Compact embedded lock-in | `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\数字解调\Paper_数字解调_009_Compact_embedded_lock_in.md` | 主要支撑数字 lock-in，但其 PID 图包含 error offset、P/I/D 输出相加、freeze 输出和 freeze integrator。 | v2 可借鉴 freeze / hold / offset / PID 下游连接思想。 | 是，但只作为接口参考，不照搬 PID 参数。 |
| FPGA-guided direct modulation spectroscopy | `E:\new\fpga_lock\文献阅读\notes\04_论文笔记\数字解调\Paper_数字解调_010_FPGA_guided_direct_modulation_spectroscopy.md` | 展示 Red Pitaya / Verilog 可实现 lock-in、digital filtering、PID、反馈输出和 zero crossing locking。 | 可参考“FPGA box 在 PD 和执行器之间”的系统角色；输出到执行器前必须做模拟/数字安全调理。 | 部分影响。支持安全输出和接口调理，但 FMS 参数、PZT 输出和 PID 参数不能迁移。 |
| FPGA 定点数、位宽、溢出 | `E:\new\fpga_lock\文献阅读\notes\02_数字锁相\FPGA定点数_位宽_溢出.md` | 主题笔记强调 14-bit 输入、乘法扩位、LPF accumulator 扩位、输出 saturation。 | v2 中 P/I 乘法、积分器和输出 limiter 也必须扩位和饱和，不能无保护截断。 | 是。直接影响 fixed-point 位宽、integrator 位宽和 saturation 设计。 |
| 数字锁相总指南 | `E:\new\fpga_lock\文献阅读\notes\02_数字锁相\数字锁相_总指南.md` | 给出 Red Pitaya/FPGA 替代模拟滤波、放大、mixer/lock-in 和 mixer 后低通的文献索引。 | 用作索引，不作为单独技术依据。 | 间接影响。帮助定位相关笔记。 |

## 4. C 类：暂时不看

| 类型 | 原因 |
|---|---|
| AI/CNN 自动稳频论文 | 当前 v2 不做 AI。AI 属于 v5 慢速监督外环，不能提前挤占 PI/PID 资源和时序目标。 |
| 纯 MTS / SAS 原理论文 | 已经支撑 v1 error signal 生成。v2 当前关注 `error_i -> control_o`，不重新泛读原理。 |
| FMS / PDH 具体锁频参数 | 可做工程对照，但物理机制和参数不能直接迁移到 Rb MTS v2。 |
| Red Pitaya GUI / client-server 细节 | 当前不做 GUI，不做寄存器配置系统；先写最小可仿真的 PI core。 |

## 5. 汇总到 v2 的设计约束

- 第一版先做 PI，不优先做 D；
- PI 控制器必须是 signed fixed-point；
- P/I 乘法后必须扩位；
- integrator 必须比输出宽；
- output limiter 必须永远有效；
- 必须有 anti-windup；
- 必须有 `enable_i`，默认关闭；
- 必须有 `hold_i`，用于冻结输出或冻结积分；
- 必须有 `reset_integrator_i`；
- 必须有 `polarity_i`，用于避免正反馈；
- `pid_ce` 应把 125 MHz 时钟下的控制更新降到可调、可测、低风险的速率；
- OUT2 第一阶段只接示波器，不接激光；
- D2-125 仍作为对照基准，v2 不应删除 v1 可回退路径。

## 6. 当前缺口

- 缺 D2-125 原锁定时的 P/I/D 或等效增益记录；
- 缺 D2-125 输入/输出极性和带宽定量记录；
- 缺激光执行器输入范围、灵敏度和安全电压范围；
- 缺 Red Pitaya OUT2 实际幅度、offset、噪声和负载测试；
- 缺 `pid_ce` 更新频率的实测稳定性对比；
- 缺 `kp_i/ki_i` 的最终 Q 格式审查。

