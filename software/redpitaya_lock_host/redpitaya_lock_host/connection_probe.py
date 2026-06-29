"""Network probe helpers for Red Pitaya connection diagnosis."""

from __future__ import annotations

import platform
import socket
import subprocess
from dataclasses import dataclass, field


@dataclass
class ProbeResult:
    host: str
    resolved_ips: list[str] = field(default_factory=list)
    ping_ok: bool = False
    port_22: bool = False
    port_80: bool = False
    port_5000: bool = False
    warning: str = ""
    error: str = ""


def resolve_host(host: str) -> list[str]:
    infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    ips: list[str] = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


def test_port(host: str, port: int, timeout_s: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_s):
            return True
    except OSError:
        return False


def ping_host(host: str, timeout_ms: int = 1000) -> bool:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), host]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=max(2.0, timeout_ms / 1000 + 1.0),
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def probe_redpitaya(host: str) -> ProbeResult:
    result = ProbeResult(host=host)
    try:
        result.resolved_ips = resolve_host(host)
    except OSError as exc:
        result.error = f"resolve failed: {exc}"
    target = result.resolved_ips[0] if result.resolved_ips else host
    result.ping_ok = ping_host(target)
    result.port_22 = test_port(target, 22)
    result.port_80 = test_port(target, 80)
    result.port_5000 = test_port(target, 5000)
    if len(result.resolved_ips) > 1:
        result.warning = "host resolved to multiple IP addresses; choose the active IP"
    return result
