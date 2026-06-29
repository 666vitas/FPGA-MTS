"""Mock Red Pitaya client and waveform generator for GUI testing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .safety import ScanSettings, validate_scan_settings


@dataclass
class MockRedPitayaClient:
    idn: str = "MOCK,Red Pitaya STEMlab 125-14,fpga-lock-host,0.1.1"
    settings: ScanSettings = field(default_factory=ScanSettings)
    scan_enabled: bool = False
    _connected: bool = False
    _t0: float = field(default_factory=time.monotonic)

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> str:
        self._connected = True
        self._t0 = time.monotonic()
        return self.idn

    def apply_triangle_scan(
        self,
        frequency_hz: float,
        amplitude_v: float,
        offset_v: float,
        enable: bool = True,
    ) -> ScanSettings:
        self.settings = validate_scan_settings(frequency_hz, amplitude_v, offset_v)
        self.scan_enabled = bool(enable)
        return self.settings

    def stop_scan(self) -> None:
        self.scan_enabled = False

    def safe_shutdown(self) -> None:
        self.scan_enabled = False
        self._connected = False

    def get_waveforms(
        self,
        sample_count: int = 2048,
        decimation: int = 1024,
    ) -> dict[str, np.ndarray]:
        now = time.monotonic() - self._t0
        sample_rate = 125e6 / max(int(decimation), 1)
        span_s = int(sample_count) / sample_rate
        t = np.linspace(now, now + span_s, int(sample_count), endpoint=False)
        ref_frequency = 4.6e6 if sample_rate > 12e6 else 4.6e3
        ref = 0.05 * np.sin(2 * np.pi * ref_frequency * t)
        envelope = np.sin(2 * np.pi * max(self.settings.frequency_hz, 0.1) * t)
        pd = 0.05 * np.sin(2 * np.pi * 1e3 * t)
        pd += 0.01 * envelope
        error_placeholder = np.zeros_like(t)
        return {
            "time_s": t - t[0],
            "in1_v": pd,
            "in2_v": ref,
            "error_internal": error_placeholder,
        }
