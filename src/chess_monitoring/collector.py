from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass
from typing import Any

from .config import CollectorConfig
from .models import MeasurementRecord
from .sources import DataSource, create_source
from .storage import CsvStorage, create_storage

logger = logging.getLogger(__name__)


@dataclass
class Collector:
    config: CollectorConfig
    sources: list[DataSource]
    storage: CsvStorage
    _running: bool = True

    @classmethod
    def from_config(cls, config: CollectorConfig) -> "Collector":
        sources = [create_source(source) for source in config.sources if source.enabled]
        if not sources:
            raise ValueError("at least one enabled data source is required")
        storage = create_storage(config.storage.type, config.storage.path)
        return cls(config=config, sources=sources, storage=storage)

    def read_once(self) -> MeasurementRecord:
        payload: dict[str, Any] = {}
        source_errors: list[str] = []

        for source in self.sources:
            try:
                source_payload = source.read()
                payload.update(source_payload)
            except Exception as exc:  # noqa: BLE001 - collector should keep running
                message = f"{source.config.name}: {exc}"
                logger.exception("source read failed: %s", message)
                source_errors.append(message)

        if source_errors:
            payload["source_status"] = "partial_error"
            payload["alarm_code"] = payload.get("alarm_code") or "SOURCE_READ_ERROR"
        else:
            payload["source_status"] = "ok"

        record = MeasurementRecord.from_payload(
            site_id=self.config.site_id,
            ahu_id=self.config.ahu_id,
            payload=payload,
        )
        if source_errors:
            record.validation_errors.extend(source_errors)
        return record

    def run_once(self) -> MeasurementRecord:
        record = self.read_once()
        self.storage.write(record)
        logger.info(
            "recorded %s %s co2=%s power=%s fan=%s errors=%s",
            record.site_id,
            record.ahu_id,
            record.co2_ppm,
            record.power_kw,
            record.fan_speed_pct,
            len(record.validation_errors),
        )
        return record

    def run_forever(self) -> None:
        self._install_signal_handlers()
        logger.info("collector started with interval=%ss", self.config.interval_seconds)
        while self._running:
            started = time.monotonic()
            self.run_once()
            elapsed = time.monotonic() - started
            sleep_seconds = max(0, self.config.interval_seconds - elapsed)
            time.sleep(sleep_seconds)
        logger.info("collector stopped")

    def stop(self) -> None:
        self._running = False

    def _install_signal_handlers(self) -> None:
        def _handle_signal(signum: int, _frame: Any) -> None:
            logger.info("received signal %s; stopping collector", signum)
            self.stop()

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
