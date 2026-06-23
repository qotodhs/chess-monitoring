from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .models import MeasurementRecord


CSV_FIELDS = [
    "timestamp",
    "site_id",
    "ahu_id",
    "co2_ppm",
    "outdoor_co2_ppm",
    "temperature_c",
    "relative_humidity_pct",
    "differential_pressure_pa",
    "particle_count",
    "damper_position_pct",
    "fan_frequency_hz",
    "fan_speed_pct",
    "fan_law_power_ratio",
    "power_kw",
    "energy_kwh",
    "operation_mode",
    "alarm_code",
    "source_status",
    "validation_errors",
]


class CsvStorage:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: MeasurementRecord) -> None:
        exists = self.path.exists()
        row = record.to_dict()
        row["validation_errors"] = ";".join(record.validation_errors)

        with self.path.open("a", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerow(row)


def create_storage(storage_type: str, path: str) -> CsvStorage:
    if storage_type.lower() != "csv":
        raise ValueError("only csv storage is currently implemented")
    return CsvStorage(path)
