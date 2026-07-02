"""Deprecated legacy Red Pitaya business-level client for the laser lock host.

The V2 GUI uses rp_scpi_client.RedPitayaScpiClient. This module is kept for
compatibility with older scripts and should use the same safe SCPI trigger
sequence when it is called.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock

import numpy as np

from .safety import ScanSettings, validate_scan_settings
from .scpi_client import ScpiClient, ScpiError


@dataclass
class RedPitayaClient:
    scpi: ScpiClient

    def __post_init__(self) -> None:
        self.idn: str = ""
        self.decimation: int = 1024
        self._lock = RLock()

    @property
    def connected(self) -> bool:
        return self.scpi.connected and bool(self.idn)

    def connect(self) -> str:
        with self._lock:
            self.scpi.connect()
            self.idn = self.scpi.query("*IDN?")
            if not self.idn:
                self.scpi.close()
                raise ScpiError("*IDN? returned an empty response")
            return self.idn

    def apply_triangle_scan(
        self,
        frequency_hz: float,
        amplitude_v: float,
        offset_v: float,
        enable: bool = True,
    ) -> ScanSettings:
        with self._lock:
            settings = validate_scan_settings(frequency_hz, amplitude_v, offset_v)
            self.scpi.write("GEN:RST")
            self.scpi.write("SOUR2:FUNC TRIANGLE")
            self.scpi.write(f"SOUR2:FREQ:FIX {settings.frequency_hz:.9g}")
            self.scpi.write(f"SOUR2:VOLT {settings.amplitude_v:.9g}")
            self.scpi.write(f"SOUR2:VOLT:OFFS {settings.offset_v:.9g}")
            self.scpi.write(f"OUTPUT2:STATE {'ON' if enable else 'OFF'}")
            self.scpi.write("SOUR2:TRig:INT")
            return settings

    def stop_scan(self) -> None:
        with self._lock:
            self.scpi.write("OUTPUT2:STATE OFF")
            self.scpi.write("GEN:STOP")

    def configure_acquisition(self, decimation: int) -> None:
        decimation = int(decimation)
        if decimation <= 0:
            raise ScpiError("decimation must be positive")
        with self._lock:
            self.decimation = decimation
            self.scpi.write("ACQ:RST")
            self.scpi.write("ACQ:DATA:FORMAT ASCII")
            self.scpi.write("ACQ:DATA:UNITS VOLTS")
            self.scpi.write(f"ACQ:DEC {decimation}")
            self.scpi.write("ACQ:TRIG:DLY 0")

    def acquire_in1_in2(self) -> tuple[np.ndarray, np.ndarray]:
        with self._lock:
            try:
                self.scpi.write("ACQ:START")
                self.scpi.write("ACQ:TRIG NOW")
                self._wait_for_trigger_fill()
                in1 = self.read_in1()
                in2 = self.read_in2()
                return in1, in2
            finally:
                try:
                    self.scpi.write("ACQ:STOP")
                except ScpiError:
                    pass

    def read_in1(self) -> np.ndarray:
        with self._lock:
            return self.parse_scpi_data(self.scpi.query("ACQ:SOUR1:DATA?"))

    def read_in2(self) -> np.ndarray:
        with self._lock:
            return self.parse_scpi_data(self.scpi.query("ACQ:SOUR2:DATA?"))

    def stop_acquisition(self) -> None:
        with self._lock:
            if self.scpi.connected:
                self.scpi.write("ACQ:STOP")

    def _wait_for_trigger_fill(self, timeout_s: float = 5.0) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            filled = self.scpi.query("ACQ:TRIG:FILL?").strip()
            if filled in {"1", "TD", "true", "TRUE"}:
                return
            time.sleep(0.02)
        raise ScpiError("ACQ:TRIG:FILL? timeout")

    @staticmethod
    def parse_scpi_data(raw: str) -> np.ndarray:
        text = raw.strip().strip("{}")
        if not text:
            return np.array([], dtype=float)
        try:
            return np.fromstring(text, sep=",", dtype=float)
        except ValueError as exc:
            raise ScpiError(f"failed to parse SCPI data: {exc}") from exc

    def safe_shutdown(self) -> None:
        with self._lock:
            try:
                if self.scpi.connected:
                    try:
                        self.scpi.write("ACQ:STOP")
                    except ScpiError:
                        pass
                    self.scpi.write("SOUR2:VOLT 0")
                    time.sleep(0.1)
                    self.scpi.write("OUTPUT2:STATE OFF")
                    self.scpi.write("GEN:STOP")
            finally:
                self.idn = ""
                self.scpi.close()
