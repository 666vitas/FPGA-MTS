# V1G Digital Gain / Output Scaling 方案

## 2026-06-10 当前定位：digital gain 降级为辅助功能

`digital gain` 只作为 ADC 后幅度匹配和 DAC 输出缩放功能，不作为替代 `ZFL-500LN+` 的手段。

必须明确：

- ADC 前 SNR 不足时，FPGA 内部 `digital gain` 不能恢复已经丢失的信噪比；
- `digital gain` 会同时放大信号和噪声；
- `ZFL-500LN+` 暂时必须保留；
- 当前主线是 `v2 FPGA PI/PID` 替代 `D2-125`，而不是用 `digital gain` 强行替代模拟前级；
- 后续只有在 D2-125 / v2 PI 输入输出幅度匹配确实需要时，才考虑受控 `x2/x4` 缩放。

## 0.1 论文路线下的当前判断

目标报告要求本项目最终形成“FPGA 快速确定性内环 + AI 慢速监督外环”的全自动数字稳频参数优化系统。放在这个大目标下，`v1g digital gain` 只是 error signal 接口优化的一种手段，不是论文主线本身。

new-6.9 已经看到：

```text
FPGA OUT1 -> D2-125 error input
D2-125 后级输出 CH3 约 3.42 Vpp
```

因此当前不能盲目认为“FPGA OUT1 太小，所以必须先加 gain”。更正确的判断是：

1. 如果 D2-125 后级已经不过载、过零清晰、噪声可接受，则优先执行 `v1i` 安全验证；
2. 如果 D2-125 输入响应不足，才考虑 `gain x2 / x4`；
3. 如果 CH3 已经接近饱和，增加 FPGA gain 反而有风险；
4. `v1g` 必须服从 `v1i` 安全接入结果，而不是反过来。

## 0. 2026-06-09 重要更新：v1g 当前是可选优化，不是唯一下一步

new-6.9 实验显示：

- FPGA 直接输出已有约 `160 mVpp`；
- 三通/并联 REF 条件下 FPGA OUT1 可能下降到约 `30-120 mVpp`；
- FPGA OUT1 输入 `D2-125` 后，D2-125 后级已经能输出约 `3.42 Vpp`。

因此，`v1g digital gain / output scaling` 不一定需要立刻作为唯一下一步。

当前判断：

1. 如果 `D2-125` 输入端需要更大 FPGA OUT1，则开发 `gain x2 / x4`；
2. 如果 `D2-125` 对当前 FPGA OUT1 已经有良好响应，则优先进行 `v1i` 安全接入，而不是盲目增加 FPGA 输出增益；
3. 避免过大 gain 导致 `D2-125` 输入饱和；
4. 是否需要 digital gain 不应仅由 CH2/CH4 幅度比决定，而应由 `D2-125` 输入需求、是否饱和、过零点噪声和闭环前安全测试决定。

保留 v1g 的原因：

- 如果后续确认 `D2-125` 需要更高输入幅度，`gain x2 / x4` 仍然有价值；
- 如果 FPGA OUT1 在某些 REF 分配方式下偏小，受控 gain 可以作为补偿；
- 但 gain 会同时放大 error 和噪声，不能替代相位优化和安全接入检查。

## 1. 背景

当前 `v1e-A_real_chain_mixer_replacement` 已经在真实链路下观察到 FPGA mixer+LPF 输出的 error-like signal。

当前对照结果：

```text
FPGA OUT1 ≈ 0.16 Vpp
模拟链路 error ≈ 1.57 Vpp
幅度比例 ≈ 1.57 / 0.16 ≈ 9.8
```

这说明 FPGA 已经能完成真实链路下的 mixer + post-mixer LPF 功能验证，但 OUT1 幅度明显偏小。

当前 FPGA 只替代：

```text
ZFM-3+ mixer
  -> mixer 后低频提取 / LPF
```

当前仍保留：

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
```

因此，本文件只讨论 FPGA 输出端的 digital gain / output scaling，不讨论替代前级 `10 MHz LPF`、`1.8 MHz HPF` 和 `ZFL-500LN+`。

## 2. 目标

把 FPGA OUT1 从约 `0.16 Vpp` 提高到：

- 第一目标：约 `0.6 Vpp`；
- 第二目标：约 `0.8-1.0 Vpp`。

同时保证：

- 不削顶；
- 不饱和；
- 不明显放大噪声到不可用；
- `output_protect` 仍然有效；
- OUT1 仍然先接示波器，不接 D2-125。

对小白来说，digital gain 可以理解为：

```text
FPGA 已经算出来一个形状还不错、但幅度偏小的 error-like signal。
digital gain 的作用是把它按固定倍数放大到更方便观察和后续接口评估的范围。
```

但它不是魔法。它会同时放大信号和噪声，也不能恢复 ADC 前已经丢掉的信噪比。

## 3. 建议实现

建议在 FPGA 中增加：

```text
mixer_core
  -> lpf_core
  -> digital_gain
  -> output_protect
  -> OUT1
```

建议增益档位：

- gain `x1`；
- gain `x2`；
- gain `x4`；
- gain `x8`。

优先上板测试：

- gain `x4`；
- gain `x8`。

如果当前 `0.16 Vpp` 近似按比例放大：

| 增益 | 预期 OUT1 Vpp | 说明 |
|---|---:|---|
| x1 | 0.16 Vpp | 当前基线 |
| x2 | 0.32 Vpp | 观察增益比例是否正确 |
| x4 | 0.64 Vpp | 第一优先测试，接近第一目标 |
| x8 | 1.28 Vpp | 可能偏大，需要特别检查削顶和噪声 |

因此，`x4` 是更稳的第一版目标；`x8` 只作为对照和上限探索。

## 4. 风险

1. digital gain 会同时放大误差信号和噪声。
2. 过大增益会导致 OUT1 削顶。
3. 如果 REF 相位未优化，仅放大不一定改善锁定质量。
4. 如果 offset 偏大，放大后更容易顶到输出范围。
5. D2-125 仍不能直接接入，必须先完成安全评估。
6. 如果 `output_protect` 前后的位宽和 signed 处理不清楚，可能出现 wrap-around 或符号错误。

## 5. 上板前测试标准

在进入 D2-125 前必须完成：

- REF 相位扫描；
- REF 幅度扫描；
- gain `x4` / `x8` 对比；
- CH3 / CH4 形状对比；
- CH4 噪声测量；
- CH4 是否存在稳定过零点；
- OUT1 是否在 `±1 V` 范围内；
- OUT1 是否没有削顶；
- OUT1 offset 是否安全；
- `output_protect` 是否仍然有效。

## 6. 进入代码开发前的门槛

当前可以准备 v1g 方案，但不建议立刻写 RTL。

代码开发前应先补齐：

1. REF 相位扫描记录；
2. REF 幅度扫描记录；
3. CH3 / CH4 峰位置、过零点、极性、斜率对比；
4. CH4 噪声和稳定性记录；
5. 当前 OUT1 是否存在 offset 或削顶风险；
6. 用户和 GPT 对 gain 档位的审查意见。

## 7. 仍然禁止

- 不接 D2-125；
- 不闭环锁定；
- 不做 PID；
- 不做 AI；
- 不声称已经实现高精度锁定；
- 不把 Vpp 当作唯一成功标准。
