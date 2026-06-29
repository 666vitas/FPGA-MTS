"""Red Pitaya SCPI business client for V2."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock

import numpy as np

from .safety import OutputSettings, validate_output_settings
from .scpi_client import ScpiClient, ScpiError


SCPI_WAVEFORMS = {
    "sine": "SINE",
    "square": "SQUARE",
    "triangle": "TRIANGLE",
    "sawtooth": "SAWU",
}


@dataclass(frozen=True)
class ScpiApplyResult:
    settings: OutputSettings
    commands: list[str]
    readback: dict[str, str]


@dataclass
class RedPitayaScpiClient:
    scpi: ScpiClient

    def __post_init__(self) -> None:
        self.idn: str = ""
        self.decimation: int = 1024
        self._lock = RLock()

    @property
    def connected(self) -> bool:
        return self.scpi.connected and bool(self.idn)

    def connect_idn(self) -> str:
        with self._lock:
            self.scpi.connect()
            self.idn = self.scpi.query("*IDN?")
            if not self.idn:
                self.scpi.close()
                raise ScpiError("*IDN? returned an empty response")
            return self.idn

    def close(self) -> None:
        with self._lock:
            self.idn = ""
            self.scpi.close()

    def apply_output(
        self,
        channel: int,
        waveform: str,
        freq: float,
        amp: float,
        offset: float,
        enable: bool,
        phase_deg: float = 0.0,
        output_range_v: float = 1.0,
    ) -> ScpiApplyResult:
        settings = validate_output_settings(
            channel,
            waveform,
            freq,
            amp,
            offset,
            phase_deg,
            output_range_v,
        )
        ch = settings.channel
        func = SCPI_WAVEFORMS[settings.waveform]
        commands = [
            f"SOUR{ch}:FUNC {func}",
            f"SOUR{ch}:FREQ:FIX {settings.frequency_hz:.9g}",
            f"SOUR{ch}:VOLT {settings.amplitude_v:.9g}",
            f"SOUR{ch}:VOLT:OFFS {settings.offset_v:.9g}",
            f"OUTPUT{ch}:STATE {'ON' if enable else 'OFF'}",
            f"SOUR{ch}:TRig:INT",
        ]
        with self._lock:
            for command in commands:
                self.scpi.write(command)
            readback = self.read_output_state(ch)
        return ScpiApplyResult(settings=settings, commands=commands, readback=readback)

    def set_output(
        self,
        channel: int,
        waveform: str,
        freq: float,
        amp: float,
        offset: float,
        phase_deg: float = 0.0,
        output_range_v: float = 1.0,
    ) -> OutputSettings:
        return self.apply_output(
            channel,
            waveform,
            freq,
            amp,
            offset,
            enable=False,
            phase_deg=phase_deg,
            output_range_v=output_range_v,
        ).settings

    def enable_output(self, channel: int) -> None:
        with self._lock:
            self.scpi.write(f"OUTPUT{int(channel)}:STATE ON")

    def disable_output(self, channel: int) -> None:
        with self._lock:
            ch = int(channel)
            self.scpi.write(f"SOUR{ch}:VOLT 0")
            self.scpi.write(f"OUTPUT{ch}:STATE OFF")
            self.scpi.write("GEN:STOP")

    def disable_output_with_log(self, channel: int) -> list[str]:
        ch = int(channel)
        commands = [
            f"SOUR{ch}:VOLT 0",
            f"OUTPUT{ch}:STATE OFF",
            "GEN:STOP",
        ]
        with self._lock:
            for command in commands:
                self.scpi.write(command)
        return commands

    def read_output_state(self, channel: int) -> dict[str, str]:
        ch = int(channel)
        queries = [
            f"SOUR{ch}:FUNC?",
            f"SOUR{ch}:FREQ:FIX?",
            f"SOUR{ch}:VOLT?",
            f"SOUR{ch}:VOLT:OFFS?",
            f"OUTPUT{ch}:STATE?",
        ]
        return {query: self.scpi.query(query) for query in queries}

    def safe_shutdown_outputs(self) -> None:
        with self._lock:
            try:
                if self.scpi.connected:
                    try:
                        self.scpi.write("ACQ:STOP")
                    except ScpiError:
                        pass
                    self.scpi.write("SOUR1:VOLT 0")
                    self.scpi.write("SOUR2:VOLT 0")
                    time.sleep(0.1)
                    self.scpi.write("OUTPUT1:STATE OFF")
                    self.scpi.write("OUTPUT2:STATE OFF")
                    self.scpi.write("GEN:STOP")
            finally:
                self.close()

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
                return self.read_in1(), self.read_in2()
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
            response = self.scpi.query("ACQ:TRIG:FILL?").strip()
            if response in {"1", "TD", "true", "TRUE"}:
                return
            time.sleep(0.02)
        raise ScpiError("ACQ:TRIG:FILL? timeout")

    @staticmethod
    def parse_scpi_data(raw: str) -> np.ndarray:
        text = raw.strip().strip("{}")
        if not text:
            return np.array([], dtype=float)
        return np.fromstring(text, sep=",", dtype=float)
