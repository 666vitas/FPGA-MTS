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

    def invalidate(self) -> None:
        self._capture_id = 0
        self._confirmed_target = None

    def bind_confirmed_target(self, target: LockTarget) -> None:
        self.require_current(target)
        self._confirmed_target = target

    def require_confirmed(self, target: LockTarget) -> None:
        self.require_current(target)
        if self._confirmed_target is None or target != self._confirmed_target:
            raise CustomFpgaBackendError(
                "target does not match the persistent confirmed capture/configuration"
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
