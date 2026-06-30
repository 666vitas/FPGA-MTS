"""Application entry point."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as exc:
    if exc.name == "yaml":
        print("Missing PyYAML. Please run:", file=sys.stderr)
        print(r".\.venv\Scripts\python.exe -m pip install PyYAML", file=sys.stderr)
        raise SystemExit(1) from exc
    raise
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


DEFAULT_CONFIG = {
    "red_pitaya": {
        "host": "rp-f0cb13.local",
        "scpi_port": 5000,
        "timeout_s": 3.0,
    },
    "scan": {
        "frequency_hz": 50.0,
        "amplitude_v": 0.2,
        "offset_v": 0.0,
    },
    "acquisition": {
        "decimation": 1024,
    },
    "gui": {
        "refresh_ms": 100,
        "sample_count": 2048,
    },
    "preview": {
        "cycles": 2,
        "min_points": 1024,
        "max_points": 5000,
    },
}


def load_config() -> dict:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "config.yaml"
    if not config_path.exists():
        return DEFAULT_CONFIG
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = DEFAULT_CONFIG.copy()
    for section, values in loaded.items():
        if isinstance(values, dict) and section in config:
            config[section] = {**config[section], **values}
        else:
            config[section] = values
    return config


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mock", action="store_true", help="start with Mock Mode enabled")
    return parser.parse_known_args(argv[1:])


def main() -> int:
    args, qt_args = parse_args(sys.argv)
    app = QApplication([sys.argv[0], *qt_args])
    window = MainWindow(load_config(), start_mock=args.mock)
    window.resize(1600, 950)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
