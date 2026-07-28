from types import SimpleNamespace

import numpy as np
import pytest

from redpitaya_lock_host.common.lock_models import (
    BasicLockRequest,
    LockState,
    LockTarget,
)
from redpitaya_lock_host.core.acquisition_service import AcquisitionService
from redpitaya_lock_host.core.lock_service import LockService
from redpitaya_lock_host.custom_fpga_backend import (
    CustomFpgaBackendError,
    CustomFpgaStateError,
)


class FakeBackend:
    def __init__(
        self,
        *,
        arm_state: int = 3,
        current_state: int = 1,
        l1_capability: str = "0x4C310001",
        safe_state: int = 0,
    ) -> None:
        self.arm_state = arm_state
        self.current_state = current_state
        self.safe_calls = 0
        self.arm_configs = []
        self.validate_configs = []
        self.l1_capability = l1_capability
        self.safe_state = safe_state

    def read_status(self):
        return SimpleNamespace(
            payload={
                "version": "0x00030200",
                "l1_capability": self.l1_capability,
                "mode": 1,
                "enable": 1,
                "saturated": False,
                "acquisition_state": self.current_state,
            }
        )

    def arm_lock_target(self, config):
        self.arm_configs.append(config)
        mode = 3 if self.arm_state in (4, 5) else 1
        return SimpleNamespace(
            payload={
                "version": "0x00030200",
                "mode": mode,
                "enable": 1,
                "saturated": False,
                "acquisition_state": self.arm_state,
            }
        )

    def validate_lock_target(self, config):
        self.validate_configs.append(config)
        return SimpleNamespace(
            payload={
                "version": "0x00030200",
                "l1_capability": self.l1_capability,
                "mode": 1,
                "enable": 1,
                "saturated": False,
                "acquisition_state": 2,
            }
        )

    def set_mode_safe(self):
        self.safe_calls += 1
        return SimpleNamespace(
            payload={
                "mode": 0,
                "enable": 0,
                "acquisition_state": self.safe_state,
            }
        )


def make_target(*, capture_id: int = 7, slope: float = 0.5) -> LockTarget:
    return LockTarget(
        capture_id=capture_id,
        config_generation=11,
        target_out2_counts=100,
        error_setpoint_counts=0,
        target_window_counts=8,
        scan_direction=1,
        error_crossing_direction=1,
        slope=slope,
        polarity_suggestion=1 if slope > 0 else 0,
        safe_min_counts=-300,
        safe_max_counts=300,
    )


def test_target_slope_produces_polarity_suggestion_only() -> None:
    service = AcquisitionService(FakeBackend())
    service.adopt_capture_id(1)
    x = np.linspace(-1.0, 1.0, 512)
    out2 = np.linspace(-200.0, 200.0, 512)
    positive = 260.0 * x * np.exp(-(x * 3.5) ** 2)

    positive_target = service.select_target(
        error_counts=positive,
        out2_counts=out2,
        clicked_index=255,
        safe_min_counts=-300,
        safe_max_counts=300,
        target_window_counts=8,
        config_generation=1,
    )
    negative_target = service.select_target(
        error_counts=-positive,
        out2_counts=out2,
        clicked_index=255,
        safe_min_counts=-300,
        safe_max_counts=300,
        target_window_counts=8,
        config_generation=2,
    )

    assert positive_target.slope > 0
    assert positive_target.polarity_suggestion == 1
    assert negative_target.slope < 0
    assert negative_target.polarity_suggestion == 0


def test_stale_capture_is_rejected_before_arm() -> None:
    backend = FakeBackend()
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    with pytest.raises(CustomFpgaBackendError, match="stale"):
        service.request_lock(
            BasicLockRequest(
                target=make_target(capture_id=6),
                kp=0,
                polarity=0,
                correction_limit_counts=12,
                absolute_limit_counts=300,
            )
        )

    assert backend.arm_configs == []
    assert backend.safe_calls == 0


def test_l1_active_request_preloads_fpga_kp_target_and_polarity() -> None:
    backend = FakeBackend()
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    service.request_lock(
        BasicLockRequest(
            target=make_target(),
            kp=4,
            polarity=1,
            correction_limit_counts=12,
            absolute_limit_counts=300,
        )
    )

    assert service.state is LockState.ARMED
    assert backend.arm_configs[0].preloaded_kp == 4
    assert backend.arm_configs[0].preloaded_polarity == 1


def test_l1_validate_is_distinct_and_preserves_scanning_state() -> None:
    backend = FakeBackend()
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    service.request_lock(
        BasicLockRequest(
            target=make_target(),
            kp=4,
            polarity=1,
            correction_limit_counts=12,
            absolute_limit_counts=300,
            validate_only=True,
        )
    )

    assert service.state is LockState.VALIDATING
    assert len(backend.validate_configs) == 1
    assert backend.arm_configs == []


def test_same_version_without_l1_capability_is_safed_before_arm() -> None:
    backend = FakeBackend(l1_capability="0x00000000")
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    with pytest.raises(CustomFpgaBackendError, match="SAFE CONFIRMED"):
        service.request_lock(
            BasicLockRequest(
                target=make_target(),
                kp=4,
                polarity=1,
                correction_limit_counts=12,
                absolute_limit_counts=300,
            )
        )
    assert backend.safe_calls == 1
    assert backend.arm_configs == []


def test_arm_readback_mismatch_requests_safe_and_enters_failed() -> None:
    backend = FakeBackend(arm_state=1)
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    with pytest.raises(CustomFpgaBackendError, match="SAFE CONFIRMED"):
        service.request_lock(
            BasicLockRequest(
                target=make_target(),
                kp=0,
                polarity=0,
                correction_limit_counts=12,
                absolute_limit_counts=300,
            )
        )

    assert backend.safe_calls == 1
    assert service.state is LockState.FAILED


@pytest.mark.parametrize(
    ("state", "name"),
    (
        (2, "VALIDATING"),
        (3, "ARMED"),
        (4, "ACQUIRING"),
        (5, "P_LOCKED"),
    ),
)
def test_repeated_arm_is_rejected_before_shadow_write_and_safed(
    state: int, name: str
) -> None:
    backend = FakeBackend(current_state=state)
    acquisition = AcquisitionService(backend)
    acquisition.adopt_capture_id(7)
    service = LockService(backend, acquisition)

    with pytest.raises(
        CustomFpgaStateError,
        match=rf"already active: {name}.*SAFE CONFIRMED",
    ):
        service.request_lock(
            BasicLockRequest(
                target=make_target(),
                kp=0,
                polarity=0,
                correction_limit_counts=12,
                absolute_limit_counts=300,
            )
        )

    assert backend.arm_configs == []
    assert backend.validate_configs == []
    assert backend.safe_calls == 1


def test_safe_requires_authoritative_acquisition_safe_readback() -> None:
    backend = FakeBackend(safe_state=1)
    service = LockService(backend)

    with pytest.raises(
        CustomFpgaStateError,
        match="SAFE COMMAND FAILED / MANUAL HARDWARE CHECK REQUIRED",
    ) as raised:
        service.safe()

    assert raised.value.safe_confirmed is False
    assert service.state is LockState.FAILED


def test_safe_command_exception_is_not_retried_or_reported_confirmed() -> None:
    backend = FakeBackend()

    def fail_safe():
        raise CustomFpgaStateError(
            "SAFE COMMAND FAILED: acquisition_state=FAULT",
            payload={"acquisition_state": 7},
        )

    backend.set_mode_safe = fail_safe
    service = LockService(backend)

    with pytest.raises(CustomFpgaStateError) as raised:
        service.safe()

    assert raised.value.safe_confirmed is False
    assert "MANUAL HARDWARE CHECK REQUIRED" in str(raised.value)
    assert service.state is LockState.FAILED
