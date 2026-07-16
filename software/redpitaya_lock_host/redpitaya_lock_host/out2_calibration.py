"""Measured STEM125-14 OUT2 voltage calibration."""

from __future__ import annotations


COUNTS_PER_VOLT = 8191.0
OUT2_CENTER_GAIN = 1.13
OUT2_CENTER_OFFSET = 0.009
OUT2_AMPLITUDE_GAIN = 1.18


def _clamp_dac_counts(counts: int) -> int:
    return max(-8191, min(8191, int(counts)))


def out2_voltage_to_counts(volts: float) -> int:
    """Convert a requested absolute OUT2 voltage to a compensated DAC count."""
    nominal_volts = (float(volts) - OUT2_CENTER_OFFSET) / OUT2_CENTER_GAIN
    return _clamp_dac_counts(round(nominal_volts * COUNTS_PER_VOLT))


def out2_amplitude_to_counts(volts: float) -> int:
    """Convert an OUT2 amplitude or correction delta to compensated counts."""
    nominal_volts = abs(float(volts)) / OUT2_AMPLITUDE_GAIN
    return abs(_clamp_dac_counts(round(nominal_volts * COUNTS_PER_VOLT)))


def out2_counts_to_voltage(counts: int | float) -> float:
    """Estimate absolute physical OUT2 voltage from a DAC count."""
    return OUT2_CENTER_GAIN * float(counts) / COUNTS_PER_VOLT + OUT2_CENTER_OFFSET


def out2_delta_counts_to_voltage(counts: int | float) -> float:
    """Estimate a physical OUT2 amplitude/correction delta from DAC counts."""
    return OUT2_AMPLITUDE_GAIN * float(counts) / COUNTS_PER_VOLT
