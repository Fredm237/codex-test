"""CLI du FILON Quality Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .integrity import atomic_write_text
from .readiness import build_readiness_report
from .scorecard import (
    build_scorecard,
    ensure_output_is_distinct,
    quality_input_paths,
    scorecard_input_paths,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Évalue la préparation du FILON Quality Lab")
    parser.add_argument("--manifest", default="../quality/manifest.json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="retourne 1 si le laboratoire est intègre mais pas prêt",
    )
    parser.add_argument(
        "--run",
        type=Path,
        help="valide et score un manifeste de prédictions séparé sur le holdout",
    )
    parser.add_argument("--output", type=Path, help="écrit aussi le rapport JSON")
    args = parser.parse_args()
    if args.output:
        protected = (
            scorecard_input_paths(args.manifest, args.run)
            if args.run
            else quality_input_paths(args.manifest)
        )
        try:
            ensure_output_is_distinct(args.output, protected)
        except ValueError as exc:
            parser.error(str(exc))
    report = (
        build_scorecard(args.manifest, args.run)
        if args.run
        else build_readiness_report(args.manifest)
    )
    payload = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    print(payload)
    if args.output:
        try:
            atomic_write_text(args.output, payload + "\n")
        except (OSError, ValueError) as exc:
            parser.error(f"unable to write output: {exc}")
    if args.run:
        if report["status"] == "pass":
            return 0
        if report["status"] == "fail":
            return 1
        return 2
    if not report.get("integrity_valid", False):
        return 2
    return 1 if args.strict and not report["ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
