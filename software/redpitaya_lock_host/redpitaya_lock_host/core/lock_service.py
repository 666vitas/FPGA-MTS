"""Single owner of the host-side basic lock state machine."""

from __future__ import annotations

from typing import Any

from ..common.lock_models import (
    AcquisitionCapability,
    BasicLockRequest,
    LockState,
    LockTarget,
    capability_from_version,
)
from ..custom_fpga_backend import (
    CustomFpgaBackendError,
    build_acquisition_target_config,
)
from .acquisition_service import AcquisitionService


class LockService:
    def __init__(self, backend: Any, acquisition: AcquisitionService | None = None) -> None:
        self._backend = backend
        self.acquisition = acquisition or AcquisitionService(backend)
        self.state = LockState.SAFE
        self.target: LockTarget | None = None
        self.capability = AcquisitionCapability.UNKNOWN

    def _status_payload(self) -> dict:
        response = self._backend.read_status()
        payload = response.payload
        self.capability = capability_from_version(payload.get("version", 0))
        return payload

    def safe(self):
        response = self._backend.set_mode_safe()
        self.state = LockState.SAFE
        self.target = None
        return response

    def start_scan(self, **kwargs):
        response = self._backend.set_mode_scan(**kwargs)
        self.state = LockState.SCANNING
        return response

    def capture(self, *, capture_length: int, capture_decimation: int):
        return self.acquisition.capture(
            capture_length=capture_length,
            capture_decimation=capture_decimation,
        )

    def confirm_target(self, target: LockTarget) -> LockTarget:
        self.acquisition.require_current(target)
        if self.state not in (LockState.SCANNING, LockState.TARGET_SELECTED):
            raise CustomFpgaBackendError("target confirmation requires SCANNING")
        self.target = target
        self.state = LockState.TARGET_SELECTED
        return target

    def request_lock(self, request: BasicLockRequest):
        self.acquisition.require_current(request.target)
        if request.kp not in (0, 4):
            raise CustomFpgaBackendError("basic lock Kp must be an explicit user choice of 0 or 4")
        payload = self._status_payload()
        if int(payload.get("mode", -1)) != 1 or int(payload.get("enable", 0)) != 1:
            return self._fail_safe("ARM requires MODE=SCAN and ENABLE=1")
        if bool(payload.get("saturated", False)):
            return self._fail_safe("ARM refused because saturation is active")
        if int(payload.get("acquisition_state", 1)) == 2:
            raise CustomFpgaBackendError(
                "target configuration writes are forbidden while acquisition is ARMED"
            )
        if self.capability is AcquisitionCapability.D1 and request.kp != 0:
            raise CustomFpgaBackendError("D1 preserves the Kp=0 trigger contract")
        if self.capability not in (AcquisitionCapability.SIMPLE, AcquisitionCapability.D1):
            return self._fail_safe("loaded FPGA build has no supported acquisition capability")

        target = request.target
        config = build_acquisition_target_config(
            target_out2_counts=target.target_out2_counts,
            target_error_setpoint_counts=target.error_setpoint_counts,
            target_window_counts=target.target_window_counts,
            required_scan_direction=target.scan_direction,
            required_error_crossing_direction=target.error_crossing_direction,
            initial_polarity_suggestion=target.polarity_suggestion,
            correction_limit_counts=request.correction_limit_counts,
            absolute_limit_counts=request.absolute_limit_counts,
            config_generation=target.config_generation,
            safe_min_counts=target.safe_min_counts,
            safe_max_counts=target.safe_max_counts,
            preloaded_kp=request.kp,
            preloaded_polarity=request.polarity,
        )
        response = self._backend.arm_lock_target(config)
        readback = response.payload
        acq_state = int(readback.get("acquisition_state", -1))
        mode = int(readback.get("mode", -1))
        enable = int(readback.get("enable", 0))
        if acq_state not in (2, 3, 4, 5):
            return self._fail_safe("ARM readback did not report ARMED or P_LOCK")
        if acq_state in (4, 5) and (mode != 3 or enable != 1):
            return self._fail_safe("P_LOCK readback does not match MODE/ENABLE")

        self.target = target
        self.state = {
            2: LockState.ARMED,
            3: LockState.ARMED,
            4: LockState.P_LOCK_KP0,
            5: LockState.P_LOCK_ACTIVE,
        }[acq_state]
        return response

    def apply_p(self, *, kp: int, polarity: int, config_generation: int):
        response = self._backend.update_p_lock(
            kp=kp,
            polarity=polarity,
            config_generation=config_generation,
        )
        self.state = LockState.P_LOCK_KP0 if int(kp) == 0 else LockState.P_LOCK_ACTIVE
        return response

    def _fail_safe(self, reason: str):
        try:
            self._backend.set_mode_safe()
        finally:
            self.state = LockState.FAILED
        raise CustomFpgaBackendError(f"{reason}; SAFE requested")
