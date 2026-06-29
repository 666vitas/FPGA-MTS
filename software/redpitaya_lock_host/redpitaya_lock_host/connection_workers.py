"""Background workers for network, SSH, and SCPI operations."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .connection_probe import ProbeResult, probe_redpitaya, test_port
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
