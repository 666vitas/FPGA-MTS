# V1_DIRECT_PD_INTERNAL_NCO_PLAN

## 0. 本文件作用

本文件记录新平台 `v-weifang-clean` 的下一阶段实验方案。

主题是：

`PD` 原始信号直接进入 Red Pitaya `IN1`，FPGA 内部生成 `4.6 MHz sin/cos` 参考，完成数字混频和 LPF，最后从 `OUT1` 输出 error-like signal。

本文件只是方案，不是 RTL 实现。当前没有新增 NCO/DDS 代码，也没有修改 Vivado 工程。

## 1. 新实验链路

目标链路：

```text
PD raw signal
  -> Red Pitaya IN1
  -> ADC
  -> optional DC remove
  -> optional digital BPF / gain
  -> mixer with internal 4.6 MHz NCO sin/cos
  -> post-mixer LPF
  -> output scaling / output_protect
  -> OUT1
  -> oscilloscope first
```

内部参考链路：

```text
FPGA adc_clk = 125 MHz
  -> phase accumulator / NCO
  -> 4.6 MHz sin_ref
  -> 4.6 MHz cos_ref
  -> digital mixer reference
```

这和当前 v1d/v1e 的区别很大：

当前已验证链路是：

```text
IN1 = PD path after analog front-end
IN2 = external 4.6 MHz REF
IN1 × IN2 -> mixer_core -> lpf_core -> OUT1
```

新实验目标是：

```text
IN1 = raw PD
IN2 = 不再作为 mixer REF 必需输入
FPGA 内部自己生成 4.6 MHz REF
```

## 2. 为什么不使用模拟 BPF 和模拟放大

不使用模拟 `10 MHz LPF`、`1.8 MHz HPF` 和 `ZFL-500LN+ amplifier` 的目的，是为了验证：

1. Red Pitaya ADC 能否直接采到 PD 中与 MTS 调制相关的成分；
2. FPGA 是否能用数字方式完成原来模拟链路的前级处理；
3. 后续是否可以减少模拟器件数量，让系统更紧凑、更可控；
4. 是否能把 REF 相位、滤波、gain、I/Q 解调都放到 FPGA 中统一调参。

但这不是“模拟前端没用”。相反，当前真实实验已经证明，模拟前级对信噪比和幅度很重要。

因此本方案是探索路线，不是直接替代成功结论。

## 3. 取消模拟前端的风险

取消模拟 BPF 和 RF 放大器后，主要风险有：

1. `PD raw signal` 中的 `4.6 MHz` 调制成分可能很弱；
2. 低频背景、扫描信号、DC offset 和漂移会一起进入 ADC；
3. ADC 前没有模拟带通，宽带噪声会全部进入 FPGA；
4. 如果 ADC 输入幅度太小，数字 gain 只能放大已经量化后的信号和噪声；
5. 如果 ADC 输入太大，会直接削顶，后续 DSP 无法恢复；
6. 没有外部 REF 时，内部 NCO 和真实 EOM 相位关系需要校准；
7. 如果 EOM 的真实调制频率和内部 NCO 频率有偏差，解调结果会漂移或变差。

对 FPGA 小白来说，关键点是：

数字滤波和数字增益只能处理 ADC 已经采到的数据。  
如果 ADC 之前信号已经太弱、太吵、或已经削顶，FPGA 不能凭空恢复真实信息。

## 4. ADC ±1 V 输入限制

Red Pitaya STEMlab 125-14 的模拟输入必须保持在安全范围内。

本项目按保守原则使用：

- `IN1` 进入 ADC 前目标范围在 `±1 V` 内；
- 第一次实验不要满幅；
- 建议先从 `100 mVpp` 到 `500 mVpp` 量级开始；
- 所有进板信号必须先用示波器确认幅度和 offset；
- 禁止把未知幅度的 PD 或放大器输出直接接进板子。

如果 PD 原始输出带有较大 DC offset，必须先评估是否会让 ADC 输入接近饱和。

## 5. PD 原始信号太弱时的风险

如果 `PD raw signal` 太弱，会出现：

1. ADC code 变化只有很少几位；
2. `4.6 MHz` 调制分量埋在量化噪声和模拟噪声中；
3. mixer 后低频输出很小；
4. LPF 后可能看不到清晰 error-like 结构；
5. digital gain 会同时放大信号和噪声；
6. 示波器上 OUT1 可能只有噪声或不稳定背景。

这就是为什么当前真实链路中 `ZFL-500LN+` 放大器很重要：它在 ADC 之前提高目标频带信号幅度。

## 6. FPGA 数字增益不能改善 ADC 前 SNR

数字 gain 的作用是：

```text
ADC 已经采到的 code -> 乘以 gain -> 输出更大
```

它不能做到：

```text
把 ADC 前已经丢失的弱信号重新找回来
```

原因很简单：

ADC 采样之后，FPGA 只知道数字码。如果真实 PD 中的目标成分在 ADC 前已经被噪声淹没，那么数字 gain 会把目标成分和噪声一起放大。

所以本实验必须记录：

1. PD raw signal 的 Vpp；
2. PD raw signal 的 offset；
3. ADC 是否削顶；
4. OUT1 是否只是放大噪声；
5. 是否需要重新加入某种模拟前置放大。

## 7. 内部 NCO 参考和外部 IN2 REF 的区别

### 7.1 外部 IN2 REF

当前已验证方式：

```text
signal generator / EOM same source
  -> attenuated 4.6 MHz REF
  -> Red Pitaya IN2
  -> ADC
  -> ref_i
```

优点：

- 和 EOM 同源；
- 相位关系真实；
- 已经通过 v1c/v1d/v1e 验证；
- 调试直观，示波器能直接看 REF。

缺点：

- 占用 `IN2`；
- 需要外部线缆和衰减；
- ADC 会采到 REF 噪声；
- REF 幅度必须进板前保证安全。

### 7.2 内部 NCO REF

目标方式：

```text
adc_clk
  -> phase accumulator
  -> sin/cos lookup or CORDIC
  -> internal 4.6 MHz reference
```

优点：

- 不占用 `IN2`；
- 幅度、相位、频率可由 FPGA 参数控制；
- 可以自然扩展到 I/Q 解调；
- 后续 AI/自动重锁可以调相位和频率。

风险：

- 必须确认内部 NCO 和真实 EOM 调制同频、同相或可调相；
- 如果 EOM 仍由外部信号发生器驱动，内部 NCO 需要和外部信号发生器同步，否则相位会漂移；
- 如果没有同步机制，长时间 error-like signal 可能出现呼吸、漂移或失真。

因此，如果 EOM 仍由外部信号发生器驱动，内部 NCO 方案要考虑：

1. 继续输入一个同步触发 / reference；
2. 或让 FPGA 也驱动 EOM；
3. 或做相位 / 频率锁定机制。

这三种都不是当前 clean 迁移马上能解决的问题。

## 8. OUT1 应该观察什么

第一阶段 OUT1 只接示波器。

在教学验证中，可以先不用真实 PD：

### 测试 A：信号源代替 PD

```text
IN1 = 4.6 MHz sine, 100-500 mVpp, 0 V offset
internal NCO = 4.6 MHz
OUT1 = mixer + LPF output
```

预期：

- 如果 IN1 和 internal NCO 同频，LPF 后应有 DC / 低频分量；
- 如果频率略有差异，例如 `IN1=4.601 MHz`，应看到约 `1 kHz` 差频；
- 这一步证明内部 NCO + mixer + LPF 的数学链路通了。

### 测试 B：真实 PD raw signal

```text
IN1 = raw PD
internal NCO = 4.6 MHz
OUT1 = error-like signal candidate
```

预期：

- 如果 PD raw 中有足够强的 `4.6 MHz` 调制成分，OUT1 可能出现随 scan / 谱线变化的低频结构；
- 如果没有明显结构，不能马上说代码错，可能是 PD raw 信号太弱或缺少前级滤波/放大。

## 9. OUT2 建议输出什么调试信号

新实验建议充分利用 `OUT2` 做调试，但必须先设计清楚。

建议优先级：

1. `OUT2 = internal NCO sin_ref`
   - 用示波器确认 FPGA 内部确实生成 `4.6 MHz`；
   - 观察频率、幅度、相位是否合理。

2. `OUT2 = raw mixer`
   - 用于和 `OUT1 = LPF output` 对比；
   - 观察 LPF 是否真的压制高频项。

3. `OUT2 = scaled PD input`
   - 用于确认 raw PD 进入 ADC 后是否有足够幅度；
   - 适合早期排查。

注意：

当前旧 v1d top 中 DAC B / OUT2 主要保持官方路径，不应随便改。  
如果新平台要使用 OUT2 调试，必须先写设计说明，再修改 `red_pitaya_top.sv` 的 DAC B mux，不能临时乱接。

## 10. 如果没有误差信号，按什么顺序排查

如果 OUT1 没有可用 error-like signal，按下面顺序排查。

### 10.1 先查输入安全和波形

1. 示波器确认 `IN1` 前的 PD raw 信号；
2. 记录 Vpp、offset、频谱或至少时间波形；
3. 确认没有超过 `±1 V`；
4. 确认没有明显削顶；
5. 如果信号太弱，先不要怪 FPGA。

### 10.2 再查内部 NCO

1. 用 `OUT2` 输出 `sin_ref`；
2. 示波器确认约 `4.6 MHz`；
3. 确认幅度不削顶；
4. 确认 NCO 频率计算来自 `125 MS/s` 采样时钟；
5. 如果 NCO 频率错，mixer 后不会得到正确低频项。

### 10.3 再查 mixer

1. 用信号源给 `IN1` 输入 `4.6 MHz`；
2. internal NCO 设 `4.6 MHz`；
3. 观察 raw mixer 或 LPF 输出；
4. 如果信号源测试都不行，先修 RTL / bitstream；
5. 如果信号源测试可以，真实 PD 不行，问题更可能在 PD 信号幅度、SNR 或实验物理链路。

### 10.4 再查 LPF

1. 确认 `LPF_SHIFT`；
2. `LPF_SHIFT` 太大，输出会很慢；
3. `LPF_SHIFT` 太小，高频会残留；
4. 用差频测试，例如 `4.600 MHz` 和 `4.601 MHz`，看是否出现约 `1 kHz`。

### 10.5 最后查实验物理

1. EOM 是否真的在 `4.6 MHz` 调制；
2. PD 是否看到饱和吸收/MTS相关结构；
3. scan 是否稳定；
4. 内部 NCO 是否和 EOM 同源或同步；
5. 相位是否需要扫描；
6. 是否需要回退到外部 IN2 REF 方式对照。

## 11. 下一阶段如何加入数字 BPF、I/Q 解调和 AI 优化

建议路线：

### 阶段 1：内部 NCO 最小验证

新增：

- `nco_ref_core.sv`
- `tb_nco_ref_core.sv`

目标：

`internal 4.6 MHz sin_ref/cos_ref` 可仿真、可上板观察。

### 阶段 2：NCO mixer + LPF

新增或修改：

- `laser_lock_core` 新增内部参考模式；
- `OUTPUT_MODE=4`：`IN1 × internal sin_ref -> LPF -> OUT1`
- `OUT2` 输出 `internal sin_ref` 或 raw mixer。

目标：

不用 `IN2` 也能完成同频/差频测试。

### 阶段 3：数字 BPF / DC remove

新增：

- `dc_remove_core.sv`
- `bpf_core.sv`

目标：

替代或部分替代真实模拟前级：

```text
10 MHz LPF
1.8 MHz HPF
```

注意：

数字 BPF 系数必须根据：

- `125 MS/s` ADC 采样率；
- `4.6 MHz` 中心频率；
- passband / bandwidth；
- 定点位宽；
- FPGA 资源；

不能直接照搬模拟滤波器参数。

### 阶段 4：I/Q 解调

使用：

```text
I = PD × sin_ref -> LPF
Q = PD × cos_ref -> LPF
```

意义：

- 可以做相位优化；
- 可以判断 REF 相位是否合适；
- 可以构造更稳定的幅度/相位特征；
- 为自动锁定和 AI 判断提供更多数据。

### 阶段 5：AI 优化

AI 不应太早进入 FPGA PL。

优先路线：

1. 先采集数据：
   - scan；
   - PD；
   - I；
   - Q；
   - OUT1；
   - analog reference；
   - lock / unlock 状态。
2. 在 PC / Python 上做峰识别、锁定状态分类；
3. 再决定哪些逻辑适合 FPGA，哪些适合 CPU 或上位机。

## 12. 当前结论

`v-weifang-clean` 已经具备：

- Red Pitaya 顶层参考；
- ADC/DAC 官方路径；
- `mixer_core`;
- `lpf_core`;
- v1c/v1d testbench；
- 当前 v1 实验文档参考。

但它还不具备：

- 内部 NCO/DDS；
- 内部 `sin/cos` 参考；
- 原始 PD 直入专用 BPF/DC remove/gain；
- I/Q 解调；
- AI 优化。

因此，下一步最小动作不是直接上板，而是先设计并确认内部 NCO/DDS 模块方案。
