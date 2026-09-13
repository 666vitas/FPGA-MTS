"""Aligned capture and target-selection ownership for the lock workflow."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..common.lock_models import LockTarget
from ..custom_fpga_backend import CustomFpgaBackendError, resolve_target_transition


class AcquisitionService:
    def __init__(self, backend: Any) -> None:
        self._backend = backend
        self._capture_id = 0
        self._confirmed_target: LockTarget | None = None
        self._validated_target: LockTarget | None = None

    @property
    def capture_id(self) -> int:
        return self._capture_id

    def adopt_capture_id(self, capture_id: int) -> None:
        """Record the ID delivered by the completed GUI capture callback."""
        value = int(capture_id)
        if value <= 0:
            raise CustomFpgaBackendError("capture id must be positive")
        self._capture_id = value
        self._confirmed_target = None
        self._validated_target = None

    def invalidate(self) -> None:
        self._capture_id = 0
        self._confirmed_target = None
        self._validated_target = None

    @property
    def validated_target(self) -> LockTarget | None:
        return self._validated_target

    @property
    def confirmed_target(self) -> LockTarget | None:
        return self._confirmed_target

    def bind_confirmed_target(self, target: LockTarget) -> None:
        self.require_current(target)
        self._confirmed_target = target
        self._validated_target = None

    def require_confirmed(self, target: LockTarget) -> None:
        self.require_current(target)
        if self._confirmed_target is None or target != self._confirmed_target:
            raise CustomFpgaBackendError(
                "target does not match the persistent confirmed capture/configuration"
            )

    def mark_validated(self, target: LockTarget, payload: dict[str, Any]) -> None:
        """Record only a complete, fresh FPGA VALIDATED result for this target."""
        self.require_confirmed(target)
        event = payload.get("acquisition_event")
        before = payload.get("validation_sequence_before")
        failures: list[str] = []
        if not isinstance(event, dict) or not bool(event.get("valid")):
            failures.append("event invalid")
        else:
            if int(event.get("event_type", 0)) != 7:
                failures.append("event is not VALIDATED")
            if before is None or int(event.get("sequence", -1)) == int(before):
                failures.append("event sequence did not advance")
            if int(event.get("config_generation", 0)) != int(target.config_generation):
                failures.append("generation mismatch")
            if int(event.get("scan_direction", -1)) != int(target.scan_direction):
                failures.append("scan direction mismatch")
            if int(event.get("error_crossing_direction", -1)) != int(target.error_crossing_direction):
                failures.append("error crossing direction mismatch")
        if int(payload.get("acquisition_state", -1)) != 1:
            failures.append("FPGA state is not SCAN")
        if int(payload.get("mode", -1)) != 1 or int(payload.get("enable", -1)) != 1:
            failures.append("MODE/ENABLE is not SCAN/1")
        if bool(payload.get("saturated", False)):
            failures.append("saturation is active")
        if failures:
            raise CustomFpgaBackendError("VALIDATE completion rejected: " + "; ".join(failures))
        self._validated_target = target

    def require_validated(self, target: LockTarget) -> None:
        # Legacy direct callers may not bind a GUI confirmation. The operator
        # workflow always binds first, so only that path receives the strict
        # VALIDATE gate.
        self.require_current(target)
        if self._confirmed_target is None:
            return
        if target != self._confirmed_target:
            raise CustomFpgaBackendError(
                "target does not match the persistent confirmed capture/configuration"
            )
        if self._validated_target is None or target != self._validated_target:
            raise CustomFpgaBackendError(
                "ARM BASIC LOCK requires a matching VALIDATED target for this generation"
            )

    def capture(self, *, capture_length: int, capture_decimation: int):
        response = self._backend.capture_waveform(
            capture_length=capture_length,
            capture_decimation=capture_decimation,
        )
        self._capture_id += 1
        self._confirmed_target = None
        return response

    def select_target(
        self,
        *,
        error_counts,
        out2_counts,
        clicked_index: int,
        safe_min_counts: int,
        safe_max_counts: int,
        target_window_counts: int,
        config_generation: int,
    ) -> LockTarget:
        error = np.asarray(error_counts, dtype=float)
        out2 = np.asarray(out2_counts, dtype=float)
        resolved = resolve_target_transition(
            error_counts=error,
            out2_counts=out2,
            clicked_index=int(clicked_index),
            safe_min_counts=int(safe_min_counts),
            safe_max_counts=int(safe_max_counts),
            saturated=False,
        )
        if not resolved.valid:
            raise CustomFpgaBackendError(resolved.reason or "target selection failed")
        slope = float(resolved.slope)
        center = max(1, min(len(out2) - 2, int(round(resolved.index))))
        scan_direction = 1 if out2[center + 1] > out2[center - 1] else 2
        error_crossing_direction = (
            1 if error[center + 1] > error[center - 1] else 2
        )
        return LockTarget(
            capture_id=self._capture_id,
            config_generation=int(config_generation),
            target_out2_counts=int(round(resolved.out2_counts)),
            error_setpoint_counts=int(round(resolved.error_counts)),
            target_window_counts=int(target_window_counts),
            scan_direction=scan_direction,
            error_crossing_direction=error_crossing_direction,
            slope=slope,
            polarity_suggestion=1 if slope > 0 else 0,
            safe_min_counts=int(safe_min_counts),
            safe_max_counts=int(safe_max_counts),
        )

    def require_current(self, target: LockTarget) -> None:
        if int(target.capture_id) != self._capture_id:
            raise CustomFpgaBackendError(
                "selected target is stale for the current aligned capture"
            )
