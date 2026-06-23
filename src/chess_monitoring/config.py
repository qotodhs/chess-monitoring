from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class StorageConfig:
    type: str = "csv"
    path: str = "data/chess_measurements.csv"


@dataclass(frozen=True)
class SourceConfig:
    name: str
    type: str
    enabled: bool = True
    options: dict[str, Any] | None = None


@dataclass(frozen=True)
class CollectorConfig:
    site_id: str
    ahu_id: str
    interval_seconds: int
    storage: StorageConfig
    sources: list[SourceConfig]


def load_config(path: str | Path) -> CollectorConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as fp:
        raw = yaml.safe_load(fp) or {}

    storage_raw = raw.get("storage", {}) or {}
    storage = StorageConfig(
        type=str(storage_raw.get("type", "csv")),
        path=str(storage_raw.get("path", "data/chess_measurements.csv")),
    )

    sources: list[SourceConfig] = []
    for item in raw.get("sources", []) or []:
        if not item:
            continue
        name = str(item.get("name") or item.get("type") or "source")
        source_type = str(item.get("type") or "simulated")
        enabled = bool(item.get("enabled", True))
        options = {k: v for k, v in item.items() if k not in {"name", "type", "enabled"}}
        sources.append(SourceConfig(name=name, type=source_type, enabled=enabled, options=options))

    if not sources:
        sources.append(SourceConfig(name="simulator", type="simulated", enabled=True, options={}))

    return CollectorConfig(
        site_id=str(raw.get("site_id") or "SITE-A"),
        ahu_id=str(raw.get("ahu_id") or "AHU-01"),
        interval_seconds=int(raw.get("interval_seconds") or 60),
        storage=storage,
        sources=sources,
    )
