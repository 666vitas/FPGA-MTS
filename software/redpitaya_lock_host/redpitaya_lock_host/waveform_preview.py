"""Generated OUT1/OUT2 preview waveform helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np


SUPPORTED_WAVEFORMS = {"sine", "square", "triangle", "sawtooth"}


@dataclass(frozen=True)
class PreviewConfig:
    cycles: float = 2.0
    min_points: int = 1024
    max_points: int = 5000

    @classmethod
    def from_mapping(cls, values: Mapping[str, object] | None) -> "PreviewConfig":
        values = values or {}
        cycles = float(values.get("cycles", cls.cycles))
        min_points = int(values.get("min_points", cls.min_points))
        max_points = int(values.get("max_points", cls.max_points))
        return cls(cycles=cycles, min_points=min_points, max_points=max_points).normalized()

    def normalized(self) -> "PreviewConfig":
        cycles = max(float(self.cycles), 1.0)
        min_points = max(int(self.min_points), 16)
        max_points = max(int(self.max_points), min_points)
        return PreviewConfig(cycles=cycles, min_points=min_points, max_points=max_points)


def make_preview_time_axis(
    freq_hz: float,
    cycles: float = 2.0,
    min_points: int = 1024,
    max_points: int = 5000,
) -> np.ndarray:
    """Return an independent preview time axis covering the configured cycles."""
    cfg = PreviewConfig(cycles=cycles, min_points=min_points, max_points=max_points).normalized()
    freq = max(float(freq_hz), 0.001)
    point_count = min(max(cfg.min_points, int(np.ceil(cfg.cycles * 512))), cfg.max_points)
    duration_s = cfg.cycles / freq
    return np.linspace(0.0, duration_s, point_count, endpoint=True, dtype=float)


def generate_waveform(
    t: np.ndarray,
    waveform: str,
    freq_hz: float,
    amplitude_v: float,
    offset_v: float,
    phase_deg: float,
) -> np.ndarray:
    """Generate a software-only waveform over t, not measured ADC data."""
    name = waveform.lower()
    if name not in SUPPORTED_WAVEFORMS:
        raise ValueError(f"unsupported waveform: {waveform}")

    freq = max(float(freq_hz), 0.001)
    phase_cycles = float(phase_deg) / 360.0
    phase_rad = np.deg2rad(float(phase_deg))
    phase = (freq * t + phase_cycles) % 1.0

    if name == "square":
        y_unit = np.where(np.sin(2.0 * np.pi * freq * t + phase_rad) >= 0.0, 1.0, -1.0)
    elif name == "triangle":
        y_unit = 2.0 * np.abs(2.0 * phase - 1.0) - 1.0
    elif name == "sawtooth":
        y_unit = 2.0 * phase - 1.0
    else:
        y_unit = np.sin(2.0 * np.pi * freq * t + phase_rad)

    return float(offset_v) + float(amplitude_v) * y_unit


def generate_waveform_preview(
    waveform: str,
    frequency_hz: float,
    amplitude_v: float,
    offset_v: float,
    phase_deg: float,
    config: PreviewConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate independent-time-axis OUT preview data."""
    cfg = config.normalized()
    t = make_preview_time_axis(
        freq_hz=frequency_hz,
        cycles=cfg.cycles,
        min_points=cfg.min_points,
        max_points=cfg.max_points,
    )
    y = generate_waveform(t, waveform, frequency_hz, amplitude_v, offset_v, phase_deg)
    return t, y
