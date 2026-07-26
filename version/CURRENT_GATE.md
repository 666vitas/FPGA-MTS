Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: USER
Last-Updated: 2026-07-26
Supersedes: LOCK-MVP-L0
Superseded-By: NONE

# CURRENT GATE — LOCK-MVP-L1

本 Gate 的唯一目标是验证 `FPGA Real-Time ERROR-Crossing P-Only Lock`：

```text
SAFE -> SCAN -> ARM_VALIDATE / ARM_ACTIVE
-> OUT2 guard
-> FPGA realtime ERROR crossing
-> actual selected_out2 bias capture
-> ACQUIRING with FPGA Kp soft-start
-> P_LOCKED or FAILED/FAULT -> SAFE
```

## 已完成的本地证据

- `[IMPLEMENTED]` H/N crossing detector、VALIDATE/ACTIVE、原子实际 OUT2 bias、FPGA Kp ramp、servo divider、OUT2 slew limit 与 P-only supervisor。
- `[RTL SIMULATED]` crossing、SIMPLE L1、plant、OUT2 controller、D1 register-bank legacy 与 ramp 回归通过。
- `[UNIT TESTED]` Host backend/service/workflow/GUI diagnostics 分文件测试通过。
- `[NOT VERIFIED]` 新 RTL synthesis、implementation timing、bitstream、板卡加载和真实激光/PZT 锁定。

## 当前 blocker

用户尚未对本轮 RTL 重新运行 Vivado synthesis/implementation。旧 timing 结果不能证明本轮新增 crossing、supervisor、servo divider/slew 路径收敛。

## 禁止范围

- 不自动运行 Vivado、生成 bitstream、烧录或连接板卡。
- 不进入 Ki/PI、自动重锁、ML、IQ、PSD、双执行器或网络实时 servo。
- legacy `CAPTURE_LOCK_POINT`、Linux `lock-here`、manual `APPLY P` 只保留诊断源码，不得作为正常 L1 获取路径。
- 不改变 `MAGIC=0x4D545330`、`VERSION=0x00030200`、旧 CSR 地址或 signed14 编码。

## Gate 验收顺序

1. 用户 Reset `synth_1/impl_1` 并重新运行 Synthesis/Implementation。
2. 检查 WNS/TNS/WHS、unconstrained paths、high-fanout 与新增路径。
3. timing 通过后才生成测试 bitstream。
4. 用户按更新后的硬件 SOP 先执行 `ARM VALIDATE`；只有 ERROR crossing 事件与方向/代次正确，才进入受控 `ARM ACTIVE` 硬件 Gate。

当前唯一下一动作：用户重新运行 Vivado Synthesis 和 Implementation，并提供新的 timing summary 与 failing path 报告。
