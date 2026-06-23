from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MeasurementRecord:
    """One timestamped CHESS monitoring record.

    The schema is aligned with docs/chess-integration.md so that data can be
    used for before/after verification, Fan Law validation, and cleanroom
    safety checks.
    """

    timestamp: str
    site_id: str
    ahu_id: str
    co2_ppm: float | None = None
    outdoor_co2_ppm: float | None = None
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    differential_pressure_pa: float | None = None
    particle_count: float | None = None
    damper_position_pct: float | None = None
    fan_frequency_hz: float | None = None
    fan_speed_pct: float | None = None
    power_kw: float | None = None
    energy_kwh: float | None = None
    operation_mode: str = "control"
    alarm_code: str | None = None
    source_status: str = "ok"
    validation_errors: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, site_id: str, ahu_id: str, payload: dict[str, Any]) -> "MeasurementRecord":
        timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        record = cls(
            timestamp=str(timestamp),
            site_id=site_id,
            ahu_id=ahu_id,
            co2_ppm=_to_float(payload.get("co2_ppm")),
            outdoor_co2_ppm=_to_float(payload.get("outdoor_co2_ppm")),
            temperature_c=_to_float(payload.get("temperature_c")),
            relative_humidity_pct=_to_float(payload.get("relative_humidity_pct")),
            differential_pressure_pa=_to_float(payload.get("differential_pressure_pa")),
            particle_count=_to_float(payload.get("particle_count")),
            damper_position_pct=_to_float(payload.get("damper_position_pct")),
            fan_frequency_hz=_to_float(payload.get("fan_frequency_hz")),
            fan_speed_pct=_to_float(payload.get("fan_speed_pct")),
            power_kw=_to_float(payload.get("power_kw")),
            energy_kwh=_to_float(payload.get("energy_kwh")),
            operation_mode=str(payload.get("operation_mode") or "control"),
            alarm_code=payload.get("alarm_code"),
            source_status=str(payload.get("source_status") or "ok"),
        )
        record.validation_errors = validate_record(record)
        return record

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fan_law_power_ratio"] = fan_law_power_ratio(self.fan_speed_pct)
        return data


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fan_law_power_ratio(fan_speed_pct: float | None) -> float | None:
    """Return theoretical fan power ratio P2/P1 = (Q2/Q1)^3.

    fan_speed_pct is treated as the flow/speed ratio in percent.
    70% speed -> 0.343 remaining power -> 65.7% theoretical saving.
    """
    if fan_speed_pct is None:
        return None
    ratio = fan_speed_pct / 100.0
    if ratio < 0:
        return None
    return round(ratio**3, 6)


def validate_record(record: MeasurementRecord) -> list[str]:
    errors: list[str] = []

    ranges = {
        "co2_ppm": (300, 5000),
        "outdoor_co2_ppm": (300, 1000),
        "temperature_c": (-20, 60),
        "relative_humidity_pct": (0, 100),
        "differential_pressure_pa": (-100, 200),
        "particle_count": (0, 1_000_000_000),
        "damper_position_pct": (0, 100),
        "fan_frequency_hz": (0, 120),
        "fan_speed_pct": (0, 100),
        "power_kw": (0, 10_000),
        "energy_kwh": (0, 1_000_000_000),
    }

    for field_name, (low, high) in ranges.items():
        value = getattr(record, field_name)
        if value is None:
            continue
        if value < low or value > high:
            errors.append(f"{field_name} out of expected range: {value}")

    if record.fan_speed_pct is None and record.fan_frequency_hz is not None:
        errors.append("fan_speed_pct is missing; Fan Law validation will be unavailable")

    return errors
