"""CSV and PNG export helpers."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

import pandas as pd
from PySide6.QtWidgets import QWidget


def timestamped_name(prefix: str, suffix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{suffix}"


def save_waveforms_csv(
    path: str | Path,
    waveforms: dict,
    notes: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    path = Path(path)
    data = {
        "time_s": waveforms.get("time_s", []),
        "in1_pd_v": waveforms.get("in1_v", []),
        "in2_ref_v": waveforms.get("in2_v", []),
        "error_internal_placeholder": waveforms.get("error_internal", []),
    }
    frame = pd.DataFrame(data)
    metadata = metadata or {}
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# Red Pitaya Laser Lock Host V1.1 CSV\n")
        handle.write(f"# saved_at={datetime.now().isoformat(timespec='seconds')}\n")
        handle.write(f"# notes={notes.strip().replace(chr(10), ' ')}\n")
        for key in sorted(metadata):
            handle.write(f"# {key}={metadata[key]}\n")
        frame.to_csv(handle, index=False)


def save_plot_png(path: str | Path, widget: QWidget) -> None:
    path = Path(path)
    if not widget.grab().save(str(path), "PNG"):
        raise OSError(f"failed to save PNG: {path}")
