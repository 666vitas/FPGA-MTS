"""Low-level SCPI socket client.

This module intentionally knows nothing about laser locking or OUT2 scans.
"""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass


class ScpiError(RuntimeError):
    """Raised for socket or SCPI transport errors."""


@dataclass
class ScpiClient:
    host: str
    port: int = 5000
    timeout_s: float = 3.0

    def __post_init__(self) -> None:
        self._sock: socket.socket | None = None

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def connect(self) -> None:
        if self._sock is not None:
            return
        try:
            self._sock = socket.create_connection(
                (self.host, int(self.port)),
                timeout=float(self.timeout_s),
            )
            self._sock.settimeout(float(self.timeout_s))
        except OSError as exc:
            self._sock = None
            raise ScpiError(f"SCPI connect failed: {exc}") from exc

    def close(self) -> None:
        sock = self._sock
        self._sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def write(self, command: str) -> None:
        sock = self._require_socket()
        data = self._format_command(command)
        try:
            sock.sendall(data)
        except OSError as exc:
            raise ScpiError(f"SCPI write failed for {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        sock = self._require_socket()
        data = self._format_command(command)
        try:
            sock.sendall(data)
            return self._recv_response(sock, float(self.timeout_s))
        except OSError as exc:
            raise ScpiError(f"SCPI query failed for {command!r}: {exc}") from exc

    def _require_socket(self) -> socket.socket:
        if self._sock is None:
            raise ScpiError("SCPI socket is not connected")
        return self._sock

    @staticmethod
    def _format_command(command: str) -> bytes:
        stripped = command.strip()
        if not stripped:
            raise ScpiError("empty SCPI command")
        return f"{stripped}\r\n".encode("ascii")

    @staticmethod
    def _recv_response(sock: socket.socket, timeout_s: float) -> str:
        deadline = time.monotonic() + timeout_s
        chunks: list[bytes] = []
        while True:
            remaining = max(0.05, deadline - time.monotonic())
            sock.settimeout(remaining)
            try:
                chunk = sock.recv(4096)
            except TimeoutError:
                if chunks:
                    break
                raise
            except socket.timeout:
                if chunks:
                    break
                raise
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
            if time.monotonic() >= deadline:
                break
        if not chunks:
            raise ScpiError("SCPI query returned no data")
        return b"".join(chunks).decode("utf-8", errors="replace").strip()
