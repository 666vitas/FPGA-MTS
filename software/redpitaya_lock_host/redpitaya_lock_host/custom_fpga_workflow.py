"""Custom FPGA observation calculations for lab workflow decisions."""

from __future__ import annotations

from dataclasses import dataclass


OUT2_ABS_DANGER_V = 0.8
OUT2_VPP_DANGER_V = 1.6
OUT1_SMALL_VPP_WARNING = 0.005


@dataclass(frozen=True)
class CustomFpgaMeasurements:
    out1_error_vpp: float = 0.0
    out1_error_min: float = 0.0
    out1_error_max: float = 0.0
    out2_control_vpp: float = 0.0
    out2_control_min: float = 0.0
    out2_control_max: float = 0.0
    pd_absorption_vpp: float = 0.0
    ref_amplitude: float = 0.0
    notes: str = ""


@dataclass(frozen=True)
class CustomFpgaAnalysis:
    out2_out1_ratio: float | None
    level: str
    messages: tuple[str, ...]
    next_step: str


def analyze_custom_fpga_measurements(values: CustomFpgaMeasurements) -> CustomFpgaAnalysis:
    """Evaluate manual oscilloscope readings without pretending to read FPGA data."""
    messages: list[str] = []
    level = "OK"
    ratio: float | None = None

    if abs(values.out1_error_vpp) > 0:
        ratio = values.out2_control_vpp / values.out1_error_vpp

    out2_abs_peak = max(abs(values.out2_control_min), abs(values.out2_control_max))
    if out2_abs_peak >= OUT2_ABS_DANGER_V:
        level = "DANGER"
        messages.append("OUT2 min/max is close to +/-1 V; stop the experiment.")
    if values.out2_control_vpp >= OUT2_VPP_DANGER_V:
        level = "DANGER"
        messages.append("OUT2 Vpp is too large; stop the experiment.")

    if values.out1_error_vpp <= OUT1_SMALL_VPP_WARNING:
        if level != "DANGER":
            level = "WARNING"
        messages.append("OUT1 laser_error is nearly zero; check input signal, mixer, phase, and LPF path.")

    if not messages:
        messages.append("Manual readings are within the current observe-mode limits.")

    if level == "DANGER":
        next_step = "Stop output/experiment and inspect wiring, limits, and oscilloscope scaling."
    elif level == "WARNING":
        next_step = "Fix the error-signal path before gain or lock tests."
    else:
        next_step = "Continue oscilloscope-only observation; do not connect OUT2 to the laser yet."

    return CustomFpgaAnalysis(
        out2_out1_ratio=ratio,
        level=level,
        messages=tuple(messages),
        next_step=next_step,
    )
