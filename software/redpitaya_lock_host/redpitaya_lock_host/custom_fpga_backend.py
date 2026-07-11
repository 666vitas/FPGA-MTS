"""Custom FPGA register backend over SSH and /dev/mem."""

from __future__ import annotations

import base64
import importlib.util
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .ssh_client import RedPitayaSshClient, SshCommandResult


EXPECTED_MAGIC = 0x4D545330
EXPECTED_VERSION = 0x00030001
DEFAULT_BASE_ADDR = 0x4060_0000
DEFAULT_CLK_HZ = 125_000_000.0
COUNTS_PER_VOLT = 8191.0


class CustomFpgaBackendError(RuntimeError):
    """Raised when the Custom FPGA register operation fails."""


@dataclass(frozen=True)
class ScanConfig:
    offset_counts: int
    amp_counts: int
    step_counts: int
    update_div: int
    limit_counts: int


@dataclass(frozen=True)
class HoldConfig:
    hold_counts: int


@dataclass(frozen=True)
class LockConfig:
    kp: int
    ki: int
    polarity: int
    lock_bias_counts: int
    lock_limit_counts: int
    correction_limit_counts: int


@dataclass(frozen=True)
class CaptureConfig:
    capture_length: int
    capture_decimation: int


@dataclass(frozen=True)
class LockHereConfig:
    polarity: int
    lock_limit_counts: int
    correction_limit_counts: int
    settle_s: float
    target_out2_counts: int | None = None
    target_window_counts: int = 64
    target_timeout_s: float = 5.0
    target_poll_s: float = 0.005


@dataclass(frozen=True)
class CustomFpgaResponse:
    operation: str
    payload: dict[str, Any]
    stdout: str
    stderr: str
    exit_code: int
    remote_command: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "payload": self.payload,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "remote_command": self.remote_command,
        }


def volts_to_counts(volts: float) -> int:
    counts = int(round(float(volts) * COUNTS_PER_VOLT))
    return max(-8191, min(8191, counts))


def counts_to_volts(counts: int) -> float:
    return float(int(counts)) / COUNTS_PER_VOLT


def build_scan_config(
    *,
    offset_v: float,
    amp_v: float,
    freq_hz: float,
    step_counts: int,
    limit_counts: int,
    clk_hz: float = DEFAULT_CLK_HZ,
) -> ScanConfig:
    amp_counts = abs(volts_to_counts(amp_v))
    if amp_counts < 1:
        raise CustomFpgaBackendError("scan amplitude must be at least one DAC count")
    if freq_hz <= 0:
        raise CustomFpgaBackendError("scan frequency must be positive")
    step = max(1, int(step_counts))
    update_rate = float(freq_hz) * 4.0 * amp_counts / step
    update_div = max(1, int(round(float(clk_hz) / update_rate)))
    return ScanConfig(
        offset_counts=volts_to_counts(offset_v),
        amp_counts=amp_counts,
        step_counts=step,
        update_div=update_div,
        limit_counts=max(0, min(8191, int(limit_counts))),
    )


def build_hold_config(*, hold_v: float) -> HoldConfig:
    return HoldConfig(hold_counts=volts_to_counts(hold_v))


def build_lock_config(
    *,
    kp: int,
    ki: int,
    polarity: int,
    lock_bias_v: float,
    lock_limit_counts: int,
    correction_limit_counts: int = 128,
) -> LockConfig:
    return LockConfig(
        kp=max(0, min(8191, int(kp))),
        ki=max(0, min(8191, int(ki))),
        polarity=1 if int(polarity) else 0,
        lock_bias_counts=volts_to_counts(lock_bias_v),
        lock_limit_counts=max(0, min(8191, int(lock_limit_counts))),
        correction_limit_counts=max(0, min(8191, int(correction_limit_counts))),
    )


def build_lock_config_from_counts(
    *,
    kp: int,
    ki: int,
    polarity: int,
    lock_bias_counts: int,
    lock_limit_counts: int,
    correction_limit_counts: int = 128,
) -> LockConfig:
    return LockConfig(
        kp=max(0, min(8191, int(kp))),
        ki=max(0, min(8191, int(ki))),
        polarity=1 if int(polarity) else 0,
        lock_bias_counts=max(-8191, min(8191, int(lock_bias_counts))),
        lock_limit_counts=max(0, min(8191, int(lock_limit_counts))),
        correction_limit_counts=max(0, min(8191, int(correction_limit_counts))),
    )


def missing_magic_guidance(magic_text: str) -> str:
    if magic_text.upper() != "0X00000000":
        return (
            "MAGIC mismatch. SAFE/SCAN are blocked until MAGIC is 0x4D545330. "
            "Probe registers and check the loaded bitstream or base address."
        )
    return (
        "MAGIC is 0x00000000: no custom_register_bank was read. Possible causes: "
        "the device was not programmed, an old bit file is loaded, the base address "
        "is wrong, or the timing-pass bitstream must be reloaded. Probe registers "
        "before SAFE/SCAN."
    )


def status_payload_has_expected_magic(payload: dict[str, Any]) -> bool:
    magic = str(payload.get("magic", "")).strip()
    return magic.upper() == f"0X{EXPECTED_MAGIC:08X}"


def _load_scan_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "custom_fpga_scan_control.py"
    spec = importlib.util.spec_from_file_location("_custom_fpga_scan_control", script_path)
    if spec is None or spec.loader is None:
        raise CustomFpgaBackendError(f"Cannot load helper script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _remote_python_command(
    base_addr: int,
    operation: str,
    config: ScanConfig | HoldConfig | LockConfig | CaptureConfig | LockHereConfig | None,
) -> str:
    helper = _load_scan_script_module().REMOTE_HELPER
    helper_b64 = base64.b64encode(helper.encode("utf-8")).decode("ascii")
    remote_args = ["--base-addr", f"0x{int(base_addr):X}", "--op", operation]
    if isinstance(config, ScanConfig):
        remote_args += [
            "--offset-counts",
            str(config.offset_counts),
            "--amp-counts",
            str(config.amp_counts),
            "--step-counts",
            str(config.step_counts),
            "--update-div",
            str(config.update_div),
            "--limit-counts",
            str(config.limit_counts),
        ]
    elif isinstance(config, HoldConfig):
        remote_args += [
            "--hold-counts",
            str(config.hold_counts),
        ]
    elif isinstance(config, LockConfig):
        remote_args += [
            "--kp",
            str(config.kp),
            "--ki",
            str(config.ki),
            "--polarity",
            str(config.polarity),
            "--lock-bias-counts",
            str(config.lock_bias_counts),
            "--lock-limit-counts",
            str(config.lock_limit_counts),
            "--correction-limit-counts",
            str(config.correction_limit_counts),
        ]
    elif isinstance(config, CaptureConfig):
        remote_args += [
            "--capture-length",
            str(config.capture_length),
            "--capture-decimation",
            str(config.capture_decimation),
        ]
    elif isinstance(config, LockHereConfig):
        remote_args += [
            "--polarity",
            str(config.polarity),
            "--lock-limit-counts",
            str(config.lock_limit_counts),
            "--correction-limit-counts",
            str(config.correction_limit_counts),
            "--settle-s",
            str(config.settle_s),
            "--target-window-counts",
            str(config.target_window_counts),
            "--target-timeout-s",
            str(config.target_timeout_s),
            "--target-poll-s",
            str(config.target_poll_s),
        ]
        if config.target_out2_counts is not None:
            remote_args += ["--target-out2-counts", str(config.target_out2_counts)]
    remote_python = (
        "import base64, sys; "
        f"code=base64.b64decode('{helper_b64}').decode('utf-8'); "
        "sys.argv=['rp_custom_fpga_regs.py']+"
        f"{remote_args!r}; "
        "exec(compile(code, 'rp_custom_fpga_regs.py', 'exec'))"
    )
    return "python3 -c " + shlex.quote(remote_python)


def _parse_json_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    start = text.find("{")
    if start < 0:
        raise CustomFpgaBackendError(f"Remote command did not return JSON: {text}")
    return json.loads(text[start:])


class CustomFpgaBackend:
    def __init__(
        self,
        host: str,
        username: str = "root",
        password: str = "",
        base_addr: int = DEFAULT_BASE_ADDR,
        timeout_s: float = 12.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.base_addr = int(base_addr)
        self.timeout_s = float(timeout_s)

    def probe_registers(self) -> CustomFpgaResponse:
        return self._run("probe", None, allow_nonzero=False)

    def read_status(self) -> CustomFpgaResponse:
        return self._run("status", None, allow_nonzero=False)

    def set_mode_safe(self) -> CustomFpgaResponse:
        return self._run("safe", None, allow_nonzero=False)

    def set_mode_scan(
        self,
        *,
        offset_v: float,
        amp_v: float,
        freq_hz: float,
        step_counts: int,
        limit_counts: int,
    ) -> CustomFpgaResponse:
        config = build_scan_config(
            offset_v=offset_v,
            amp_v=amp_v,
            freq_hz=freq_hz,
            step_counts=step_counts,
            limit_counts=limit_counts,
        )
        return self._run("scan", config, allow_nonzero=False)

    def set_mode_hold(self, *, hold_v: float) -> CustomFpgaResponse:
        config = build_hold_config(hold_v=hold_v)
        return self._run("hold", config, allow_nonzero=False)

    def set_mode_p_lock(
        self,
        *,
        kp: int,
        polarity: int,
        lock_bias_v: float,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
    ) -> CustomFpgaResponse:
        config = build_lock_config(
            kp=kp,
            ki=0,
            polarity=polarity,
            lock_bias_v=lock_bias_v,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
        )
        return self._run("p-lock", config, allow_nonzero=False)

    def set_mode_pi_lock(
        self,
        *,
        kp: int,
        ki: int,
        polarity: int,
        lock_bias_v: float,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
    ) -> CustomFpgaResponse:
        config = build_lock_config(
            kp=kp,
            ki=ki,
            polarity=polarity,
            lock_bias_v=lock_bias_v,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
        )
        return self._run("pi-lock", config, allow_nonzero=False)

    def capture_bias(self) -> CustomFpgaResponse:
        response = self.read_status()
        if not status_payload_has_expected_magic(response.payload):
            raise CustomFpgaBackendError(missing_magic_guidance(str(response.payload.get("magic", "--"))))
        payload = dict(response.payload)
        out2_counts = int(payload.get("out2_counts", 0))
        payload["captured_lock_bias_counts"] = out2_counts
        payload["captured_lock_bias_volts_ideal"] = counts_to_volts(out2_counts)
        return CustomFpgaResponse(
            operation="capture-bias",
            payload=payload,
            stdout=response.stdout,
            stderr=response.stderr,
            exit_code=response.exit_code,
            remote_command=response.remote_command,
        )

    def lock_here(
        self,
        *,
        polarity: int,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
        settle_s: float = 0.5,
        target_out2_counts: int | None = None,
        target_window_counts: int = 64,
        target_timeout_s: float = 5.0,
    ) -> CustomFpgaResponse:
        config = LockHereConfig(
            polarity=polarity,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
            settle_s=settle_s,
            target_out2_counts=None if target_out2_counts is None else int(target_out2_counts),
            target_window_counts=max(0, int(target_window_counts)),
            target_timeout_s=max(0.1, float(target_timeout_s)),
        )
        return self._run("lock-here", config, allow_nonzero=False)

    def capture_waveform(self, *, capture_length: int, capture_decimation: int) -> CustomFpgaResponse:
        config = CaptureConfig(
            capture_length=max(1, min(4096, int(capture_length))),
            capture_decimation=max(1, int(capture_decimation)),
        )
        return self._run("capture", config, allow_nonzero=False)

    def read_error_snapshot(self) -> CustomFpgaResponse:
        return self.read_status()

    def read_control_snapshot(self) -> CustomFpgaResponse:
        return self.read_status()

    def set_pid_params(self, *args, **kwargs) -> None:
        del args, kwargs
        raise NotImplementedError("Custom FPGA PID parameter writes are not implemented in v1 GUI control")

    def set_output_limit(self, *args, **kwargs) -> None:
        del args, kwargs
        raise NotImplementedError("Use SCAN limit-counts in v1 GUI control")

    def _run(
        self,
        operation: str,
        config: ScanConfig | HoldConfig | LockConfig | CaptureConfig | LockHereConfig | None,
        *,
        allow_nonzero: bool,
    ) -> CustomFpgaResponse:
        command = _remote_python_command(self.base_addr, operation, config)
        ssh = RedPitayaSshClient(self.host, self.username, self.password, timeout_s=self.timeout_s)
        result: SshCommandResult = ssh.run(command, timeout_s=max(self.timeout_s, 20.0))
        payload = _parse_json_stdout(result.stdout) if result.stdout.strip() else {}
        response = CustomFpgaResponse(
            operation=operation,
            payload=payload,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            remote_command=command,
        )
        if result.exit_code != 0 and not allow_nonzero:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit_code={result.exit_code}"
            raise CustomFpgaBackendError(detail)
        return response


def build_scan_config_from_namespace(args: SimpleNamespace) -> ScanConfig:
    return build_scan_config(
        offset_v=args.offset_v,
        amp_v=args.amp_v,
        freq_hz=args.freq_hz,
        step_counts=args.step_counts,
        limit_counts=args.limit_counts,
        clk_hz=getattr(args, "clk_hz", DEFAULT_CLK_HZ),
    )
