"""Transport-independent models for the basic scan-to-P-lock workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LockState(str, Enum):
    SAFE = "SAFE"
    SCANNING = "SCANNING"
    TARGET_SELECTED = "TARGET_SELECTED"
    ARMED = "ARMED"
    P_LOCK_KP0 = "P_LOCK_KP0"
    P_LOCK_ACTIVE = "P_LOCK_ACTIVE"
    FAILED = "FAILED"


class AcquisitionCapability(str, Enum):
    NONE = "NONE"
    SIMPLE = "SIMPLE"
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


@dataclass(frozen=True)
class BasicLockRequest:
    target: LockTarget
    kp: int
    polarity: int
    correction_limit_counts: int
    absolute_limit_counts: int


def capability_from_version(version: int | str) -> AcquisitionCapability:
    value = int(version, 0) if isinstance(version, str) else int(version)
    if value == 0x00030200:
        return AcquisitionCapability.SIMPLE
    if value == 0x00030100:
        return AcquisitionCapability.D1
    if value == 0x00030000:
        return AcquisitionCapability.NONE
    return AcquisitionCapability.UNKNOWN
