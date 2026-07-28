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
    CustomFpgaCommandError,
    CustomFpgaStateError,
    CustomFpgaTransportError,
    CustomFpgaValidationError,
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
        self.capability = capability_from_version(
            payload.get("version", 0), payload.get("l1_capability", 0)
        )
        return payload

    def safe(self):
        try:
            response = self._backend.set_mode_safe()
        except CustomFpgaTransportError:
            self.state = LockState.FAILED
            raise
        except CustomFpgaCommandError as exc:
            self.state = LockState.FAILED
            raise CustomFpgaStateError(
                "SAFE COMMAND FAILED / MANUAL HARDWARE CHECK REQUIRED: "
                f"{exc}",
                payload=exc.payload,
                safe_confirmed=False,
            ) from exc
        payload = response.payload
        mode = int(payload.get("mode", -1))
        enable = int(payload.get("enable", -1))
        acquisition_state = int(payload.get("acquisition_state", -1))
        if (mode, enable, acquisition_state) != (0, 0, 0):
            self.state = LockState.FAILED
            raise CustomFpgaStateError(
                "SAFE COMMAND FAILED / MANUAL HARDWARE CHECK REQUIRED: "
                f"mode={mode}, enable={enable}, acquisition_state={acquisition_state}",
                payload=payload,
                safe_confirmed=False,
            )
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
        acquisition_state = int(payload.get("acquisition_state", -1))
        acquisition_name = str(
            payload.get(
                "acquisition_state_name",
                {
                    0: "SAFE",
                    1: "SCAN",
                    2: "VALIDATING",
                    3: "ARMED",
                    4: "ACQUIRING",
                    5: "P_LOCKED",
                    6: "FAILED",
                    7: "FAULT",
                }.get(acquisition_state, "UNKNOWN"),
            )
        )
        if acquisition_state in (2, 3, 4, 5):
            return self._fail_safe(
                f"FPGA acquisition is already active: {acquisition_name}. "
                "Execute SAFE or ABORT and verify state=SAFE before arming again."
            )
        if acquisition_state in (6, 7):
            return self._fail_safe(
                f"FPGA acquisition is in {acquisition_name}. "
                "SAFE recovery is required before a new scan or ARM."
            )
        if acquisition_state != 1:
            return self._fail_safe(
                f"ARM requires FPGA acquisition state=SCAN, got {acquisition_name}"
            )
        if self.capability is not AcquisitionCapability.L1_ERROR_CROSSING:
            return self._fail_safe(
                "loaded FPGA build does not advertise LOCK-MVP-L1 realtime crossing capability",
                error_type=CustomFpgaValidationError,
            )

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
            crossing_hysteresis_counts=request.crossing_hysteresis_counts,
            crossing_consecutive_samples=request.crossing_consecutive_samples,
            kp_ramp_step=request.kp_ramp_step,
            kp_ramp_div=request.kp_ramp_div,
            acquire_timeout_cycles=request.acquire_timeout_cycles,
            servo_update_div=request.servo_update_div,
            out2_slew_limit_counts=request.out2_slew_limit_counts,
            observe_shift=request.observe_shift,
            lock_confirm_windows=request.lock_confirm_windows,
            divergence_windows=request.divergence_windows,
            error_mean_limit_counts=request.error_mean_limit_counts,
            error_abs_limit_counts=request.error_abs_limit_counts,
        )
        try:
            response = (
                self._backend.validate_lock_target(config)
                if request.validate_only
                else self._backend.arm_lock_target(config)
            )
        except CustomFpgaCommandError as exc:
            return self._fail_safe(
                str(exc),
                error_type=type(exc),
                payload=exc.payload,
            )
        readback = response.payload
        acq_state = int(readback.get("acquisition_state", -1))
        mode = int(readback.get("mode", -1))
        enable = int(readback.get("enable", 0))
        expected_states = (2,) if request.validate_only else (3, 4, 5)
        if acq_state not in expected_states:
            return self._fail_safe("ARM readback does not match requested VALIDATE/ACTIVE intent")
        if request.validate_only and (mode != 1 or enable != 1):
            return self._fail_safe("VALIDATE readback must preserve MODE=SCAN and ENABLE=1")
        if not request.validate_only and acq_state in (4, 5) and (mode != 3 or enable != 1):
            return self._fail_safe("ACTIVE readback does not match MODE/ENABLE")

        self.target = target
        self.state = {
            2: LockState.VALIDATING,
            3: LockState.ARMED,
            4: LockState.ACQUIRING,
            5: LockState.P_LOCKED,
        }[acq_state]
        return response

    def apply_p(self, *, kp: int, polarity: int, config_generation: int):
        response = self._backend.update_p_lock(
            kp=kp,
            polarity=polarity,
            config_generation=config_generation,
        )
        # Legacy engineer diagnostic only; normal L1 acquisition ramps Kp in FPGA.
        self.state = LockState.ACQUIRING if int(kp) == 0 else LockState.P_LOCKED
        return response

    def _fail_safe(
        self,
        reason: str,
        *,
        error_type: type[CustomFpgaCommandError] = CustomFpgaStateError,
        payload: dict | None = None,
    ):
        try:
            response = self.safe()
        except CustomFpgaTransportError:
            self.state = LockState.FAILED
            raise
        except CustomFpgaStateError as safe_error:
            self.state = LockState.FAILED
            raise CustomFpgaStateError(
                f"{reason}; {safe_error}",
                payload=safe_error.payload,
                safe_confirmed=False,
            ) from safe_error
        self.state = LockState.FAILED
        diagnostic = dict(payload or {})
        diagnostic["safe_readback"] = dict(response.payload)
        raise error_type(
            f"{reason}; SAFE CONFIRMED",
            payload=diagnostic,
            safe_confirmed=True,
        )
