from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .collector import Collector
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CHESS monitoring data collector")
    parser.add_argument(
        "--config",
        default="config.example.yaml",
        help="Path to YAML config file. Default: config.example.yaml",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Collect only one record and exit.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print collected records as JSON to stdout.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    config = load_config(Path(args.config))
    collector = Collector.from_config(config)

    if args.once:
        record = collector.run_once()
        if args.print_json:
            print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))
        return

    collector.run_forever()


if __name__ == "__main__":
    main()
