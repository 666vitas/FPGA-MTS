"""Background workers for network, SSH, and SCPI operations."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .connection_probe import ProbeResult, probe_redpitaya, test_port
from .custom_fpga_backend import CustomFpgaBackend, build_acquisition_target_config
from .rp_scpi_client import RedPitayaScpiClient
from .scpi_client import ScpiClient
from .ssh_client import RedPitayaSshClient


class ProbeWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, host: str, parent=None) -> None:
        super().__init__(parent)
        self.host = host

    def run(self) -> None:
        try:
            self.finished_ok.emit(probe_redpitaya(self.host))
        except Exception as exc:
            self.failed.emit(str(exc))


class StartScpiServerWorker(QThread):
    finished_ok = Signal(object, bool, str)
    failed = Signal(str)

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.host = host
        self.username = username
        self.password = password

    def run(self) -> None:
        try:
            ssh = RedPitayaSshClient(self.host, self.username, self.password)
            result = ssh.start_scpi_server()
            port_ok = test_port(self.host, 5000, timeout_s=2.0)
            log = (
                f"exit_code={result.exit_code}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
            self.finished_ok.emit(result, port_ok, log)
        except Exception as exc:
            self.failed.emit(str(exc))


class ConnectScpiWorker(QThread):
    finished_ok = Signal(object, str)
    failed = Signal(str)

    def __init__(
        self,
        host: str,
        port: int,
        timeout_s: float,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.host = host
        self.port = int(port)
        self.timeout_s = float(timeout_s)

    def run(self) -> None:
        try:
            client = RedPitayaScpiClient(ScpiClient(self.host, self.port, self.timeout_s))
            idn = client.connect_idn()
            self.finished_ok.emit(client, idn)
        except Exception as exc:
            self.failed.emit(str(exc))


class DisconnectWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, client, parent=None) -> None:
        super().__init__(parent)
        self.client = client

    def run(self) -> None:
        try:
            if hasattr(self.client, "safe_shutdown_outputs"):
                self.client.safe_shutdown_outputs()
            elif hasattr(self.client, "safe_shutdown"):
                self.client.safe_shutdown()
            self.finished_ok.emit("Disconnected; outputs safe shutdown complete")
        except Exception as exc:
            self.failed.emit(str(exc))


class CustomFpgaRegisterWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        operation: str,
        host: str,
        username: str,
        password: str,
        base_addr: int,
        params: dict | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.operation = operation
        self.host = host
        self.username = username
        self.password = password
        self.base_addr = int(base_addr)
        self.params = params or {}

    def run(self) -> None:
        try:
            backend = CustomFpgaBackend(
                self.host,
                self.username,
                self.password,
                base_addr=self.base_addr,
            )
            if self.operation == "probe":
                response = backend.probe_registers()
            elif self.operation == "status":
                response = backend.read_status()
            elif self.operation == "capture-bias":
                response = backend.capture_bias()
            elif self.operation == "safe":
                response = backend.set_mode_safe()
            elif self.operation == "scan":
                response = backend.set_mode_scan(
                    offset_v=float(self.params["offset_v"]),
                    amp_v=float(self.params["amp_v"]),
                    freq_hz=float(self.params["freq_hz"]),
                    step_counts=int(self.params["step_counts"]),
                    limit_counts=int(self.params["limit_counts"]),
                )
            elif self.operation == "hold":
                response = backend.set_mode_hold(
                    hold_v=float(self.params["hold_v"]),
                )
            elif self.operation == "hold-selected-count":
                response = backend.set_mode_hold_counts(
                    hold_counts=int(self.params["hold_counts"]),
                )
            elif self.operation == "p-lock":
                response = backend.set_mode_p_lock(
                    kp=int(self.params["kp"]),
                    polarity=int(self.params["polarity"]),
                    lock_bias_v=float(self.params["lock_bias_v"]),
                    lock_limit_counts=int(self.params["lock_limit_counts"]),
                    correction_limit_counts=int(self.params.get("correction_limit_counts", 128)),
                )
            elif self.operation == "update-p-lock":
                response = backend.update_p_lock(
                    kp=int(self.params["kp"]),
                    polarity=int(self.params["polarity"]),
                    config_generation=int(self.params.get("config_generation", 0)),
                )
            elif self.operation == "lock":
                target = build_acquisition_target_config(
                    target_out2_counts=int(self.params["target_out2_counts"]),
                    target_error_setpoint_counts=int(self.params["target_error_setpoint_counts"]),
                    target_window_counts=int(self.params.get("target_window_counts", 64)),
                    required_scan_direction=int(self.params["required_scan_direction"]),
                    required_error_crossing_direction=int(
                        self.params["required_error_crossing_direction"]
                    ),
                    initial_polarity_suggestion=int(
                        self.params.get("initial_polarity_suggestion", 0)
                    ),
                    correction_limit_counts=int(
                        self.params.get("correction_limit_counts", 128)
                    ),
                    absolute_limit_counts=int(self.params["absolute_limit_counts"]),
                    safe_min_counts=int(self.params.get("safe_min_counts", -8191)),
                    safe_max_counts=int(self.params.get("safe_max_counts", 8191)),
                    config_generation=int(self.params["config_generation"]),
                )
                response = backend.arm_lock_target(target)
            elif self.operation == "abort-acquisition":
                response = backend.abort_acquisition()
            elif self.operation == "clear-acquisition-event":
                response = backend.clear_acquisition_event()
            elif self.operation == "pi-lock":
                response = backend.set_mode_pi_lock(
                    kp=int(self.params["kp"]),
                    ki=int(self.params["ki"]),
                    polarity=int(self.params["polarity"]),
                    lock_bias_v=float(self.params["lock_bias_v"]),
                    lock_limit_counts=int(self.params["lock_limit_counts"]),
                    correction_limit_counts=int(self.params.get("correction_limit_counts", 128)),
                )
            elif self.operation == "capture":
                response = backend.capture_waveform(
                    capture_length=int(self.params["capture_length"]),
                    capture_decimation=int(self.params["capture_decimation"]),
                )
            else:
                raise ValueError(f"Unknown Custom FPGA operation: {self.operation}")
            self.finished_ok.emit(response.as_dict())
        except Exception as exc:
            self.failed.emit(str(exc))
