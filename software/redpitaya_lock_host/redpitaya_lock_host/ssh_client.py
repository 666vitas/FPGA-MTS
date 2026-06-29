"""Paramiko SSH helpers for Red Pitaya service management."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SshCommandResult:
    stdout: str
    stderr: str
    exit_code: int


class SshClientError(RuntimeError):
    """Raised for SSH connection or command failures."""


class RedPitayaSshClient:
    def __init__(
        self,
        host: str,
        username: str = "root",
        password: str = "",
        timeout_s: float = 8.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.timeout_s = timeout_s

    def run(self, command: str, timeout_s: float = 10.0) -> SshCommandResult:
        try:
            import paramiko
        except ImportError as exc:
            raise SshClientError(
                "paramiko is not installed; run pip install -r requirements.txt"
            ) from exc
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password or None,
                timeout=self.timeout_s,
                banner_timeout=self.timeout_s,
                auth_timeout=self.timeout_s,
                look_for_keys=False,
                allow_agent=False,
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout_s)
            del stdin
            channel = stdout.channel
            deadline = time.monotonic() + float(timeout_s)
            while not channel.exit_status_ready():
                if time.monotonic() > deadline:
                    channel.close()
                    raise SshClientError(f"SSH command timed out after {timeout_s:g} s")
                time.sleep(0.05)
            exit_code = channel.recv_exit_status()
            return SshCommandResult(
                stdout=stdout.read().decode("utf-8", errors="replace"),
                stderr=stderr.read().decode("utf-8", errors="replace"),
                exit_code=exit_code,
            )
        except Exception as exc:
            raise SshClientError(f"SSH command failed: {exc}") from exc
        finally:
            client.close()

    def start_scpi_server(self) -> SshCommandResult:
        command = (
            "systemctl stop redpitaya_nginx || true\n"
            "systemctl start redpitaya_scpi\n"
            "systemctl is-active redpitaya_scpi\n"
            "ss -lntp | grep 5000 || true"
        )
        return self.run(command, timeout_s=10.0)

    def check_scpi_listener(self) -> SshCommandResult:
        return self.run("ss -lntp | grep 5000", timeout_s=10.0)
