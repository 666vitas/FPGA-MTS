"""Background acquisition worker for real Red Pitaya SCPI reads."""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import QThread, Signal

from .scpi_client import ScpiError


class AcquisitionWorker(QThread):
    data_ready = Signal(object, object, float)
    status = Signal(str)
    error = Signal(str)
    stopped = Signal()

    def __init__(
        self,
        client,
        decimation: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.client = client
        self.decimation = int(decimation)
        self.sample_rate = 125e6 / self.decimation
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True
        self.requestInterruption()

    def run(self) -> None:
        self._stop_requested = False
        try:
            self.client.configure_acquisition(self.decimation)
            self.status.emit("acquiring")
            while not self._stop_requested and not self.isInterruptionRequested():
                started = time.monotonic()
                in1, in2 = self.client.acquire_in1_in2()
                self.data_ready.emit(in1, in2, self.sample_rate)
                elapsed = time.monotonic() - started
                if elapsed < 0.05:
                    self.msleep(int((0.05 - elapsed) * 1000))
        except ScpiError as exc:
            self.error.emit(str(exc))
        except Exception as exc:
            self.error.emit(f"acquisition failed: {exc}")
        finally:
            try:
                self.client.stop_acquisition()
            except Exception:
                pass
            self.status.emit("stopped")
            self.stopped.emit()
