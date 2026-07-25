"""In-process API used by the GUI instead of direct register/SSH ownership."""

from __future__ import annotations

from ..common.lock_models import BasicLockRequest
from ..core.lock_service import LockService


class LocalClient:
    def __init__(self, lock_service: LockService) -> None:
        self.lock_service = lock_service

    def safe(self):
        return self.lock_service.safe()

    def start_scan(self, **kwargs):
        return self.lock_service.start_scan(**kwargs)

    def capture(self, *, capture_length: int, capture_decimation: int):
        return self.lock_service.capture(
            capture_length=capture_length,
            capture_decimation=capture_decimation,
        )

    def arm_basic_lock(self, request: BasicLockRequest):
        return self.lock_service.request_lock(request)

    def apply_p(self, *, kp: int, polarity: int, config_generation: int):
        return self.lock_service.apply_p(
            kp=kp,
            polarity=polarity,
            config_generation=config_generation,
        )
