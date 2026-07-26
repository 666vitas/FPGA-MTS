"""Transport-independent models for the basic scan-to-P-lock workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LockState(str, Enum):
    SAFE = "SAFE"
    SCANNING = "SCANNING"
    TARGET_SELECTED = "TARGET_SELECTED"
    VALIDATING = "VALIDATING"
    ARMED = "ARMED"
    ACQUIRING = "ACQUIRING"
    P_LOCKED = "P_LOCKED"
    FAILED = "FAILED"
    FAULT = "FAULT"


class AcquisitionCapability(str, Enum):
    NONE = "NONE"
    SIMPLE = "SIMPLE"
    L1_ERROR_CROSSING = "L1_ERROR_CROSSING"
    D1 = "D1"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LockTarget:
    capture_id: int
    config_generation: int
    target_out2_counts: int
    error_setpoint_counts: int
    target_window_counts: int
    scan_direction: int
    error_crossing_direction: int
    slope: float
    polarity_suggestion: int
    safe_min_counts: int
    safe_max_counts: int

    @property
    def guard_center_counts(self) -> int:
        """Historical OUT2 estimate used only to reject adjacent crossings."""
        return self.target_out2_counts

    @property
    def guard_half_width_counts(self) -> int:
        return self.target_window_counts


@dataclass(frozen=True)
class BasicLockRequest:
    target: LockTarget
    kp: int
    polarity: int
    correction_limit_counts: int
    absolute_limit_counts: int
    validate_only: bool = False
    crossing_hysteresis_counts: int = 4
    crossing_consecutive_samples: int = 3
    kp_ramp_step: int = 1
    kp_ramp_div: int = 1
    acquire_timeout_cycles: int = 12_500_000
    servo_update_div: int = 125
    out2_slew_limit_counts: int = 1
    observe_shift: int = 8
    lock_confirm_windows: int = 4
    divergence_windows: int = 4
    error_mean_limit_counts: int = 16
    error_abs_limit_counts: int = 32


def capability_from_version(
    version: int | str, l1_capability: int | str = 0
) -> AcquisitionCapability:
    value = int(version, 0) if isinstance(version, str) else int(version)
    feature = (
        int(l1_capability, 0)
        if isinstance(l1_capability, str)
        else int(l1_capability)
    )
    if value == 0x00030200 and feature == 0x4C310001:
        return AcquisitionCapability.L1_ERROR_CROSSING
    if value == 0x00030200:
        return AcquisitionCapability.SIMPLE
    if value == 0x00030100:
        return AcquisitionCapability.D1
    if value == 0x00030000:
        return AcquisitionCapability.NONE
    return AcquisitionCapability.UNKNOWN
