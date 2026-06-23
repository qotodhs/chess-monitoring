from __future__ import annotations

import csv
import math
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .config import SourceConfig


class DataSource(ABC):
    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self.options = config.options or {}

    @abstractmethod
    def read(self) -> dict[str, Any]:
        """Read a single payload from a field sensor, meter, gateway, or simulator."""


class SimulatedSource(DataSource):
    """Generate plausible CHESS data for development without field devices."""

    def read(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        minute_of_day = now.hour * 60 + now.minute
        workday_factor = 1.0 if 8 <= now.hour <= 18 else 0.35
        wave = (math.sin(minute_of_day / 1440 * 2 * math.pi) + 1) / 2

        co2 = 420 + workday_factor * (260 + 300 * wave) + random.uniform(-25, 25)
        fan_speed = 55 + workday_factor * (18 + 22 * wave) + random.uniform(-4, 4)
        fan_speed = max(35, min(100, fan_speed))
        fan_hz = 60 * fan_speed / 100
        power_kw = 22.0 * (fan_speed / 100) ** 3 + random.uniform(-0.4, 0.4)

        return {
            "timestamp": now.isoformat(),
            "co2_ppm": round(co2, 1),
            "outdoor_co2_ppm": 420,
            "temperature_c": round(22.0 + random.uniform(-0.3, 0.4), 2),
            "relative_humidity_pct": round(48 + random.uniform(-2, 2), 2),
            "differential_pressure_pa": round(12 + random.uniform(-1.5, 1.5), 2),
            "particle_count": int(1800 + workday_factor * 900 * wave + random.uniform(-100, 100)),
            "damper_position_pct": round(min(100, max(10, (co2 - 400) / 8)), 1),
            "fan_frequency_hz": round(fan_hz, 2),
            "fan_speed_pct": round(fan_speed, 2),
            "power_kw": round(max(0, power_kw), 3),
            "operation_mode": "control",
        }


class HttpSource(DataSource):
    """Read latest sensor data from an HTTP gateway that returns JSON."""

    def read(self) -> dict[str, Any]:
        url = self.options.get("url")
        if not url:
            raise ValueError(f"HTTP source {self.config.name} requires 'url'")
        timeout = float(self.options.get("timeout_seconds", 5))
        response = requests.get(str(url), timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("HTTP source must return a JSON object")
        return _map_fields(payload, self.options.get("field_map") or {})


class CsvReplaySource(DataSource):
    """Read one row at a time from CSV for bench testing and replay."""

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        path = self.options.get("path")
        if not path:
            raise ValueError(f"CSV replay source {config.name} requires 'path'")
        self.path = Path(str(path))
        self._rows = self._load_rows()
        self._idx = 0

    def _load_rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            raise FileNotFoundError(f"CSV replay file not found: {self.path}")
        with self.path.open("r", encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))

    def read(self) -> dict[str, Any]:
        if not self._rows:
            return {}
        row = self._rows[self._idx % len(self._rows)]
        self._idx += 1
        return dict(row)


def create_source(config: SourceConfig) -> DataSource:
    source_type = config.type.lower()
    if source_type == "simulated":
        return SimulatedSource(config)
    if source_type == "http":
        return HttpSource(config)
    if source_type == "csv_replay":
        return CsvReplaySource(config)
    raise ValueError(f"unsupported source type: {config.type}")


def _map_fields(payload: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    if not field_map:
        return payload
    mapped: dict[str, Any] = {}
    for output_field, input_field in field_map.items():
        mapped[output_field] = payload.get(input_field)
    if "timestamp" not in mapped and "timestamp" in payload:
        mapped["timestamp"] = payload["timestamp"]
    return mapped
