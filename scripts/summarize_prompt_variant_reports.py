#!/usr/bin/env python3
"""Summarize prompt-variant reports and select the best prompt per model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROMPT_VARIANTS = ("json_schema", "state_strict", "adversarial_strict")


def model_from_report(path: Path) -> tuple[str, str]:
    stem = path.stem
    for variant in PROMPT_VARIANTS:
        marker = f"_{variant}_limit"
        if marker in stem:
            return stem.removeprefix("real_vlm_").split(marker, 1)[0], variant
    return stem.removeprefix("real_vlm_"), "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", default="runs/prompt_variant_summary.json")
    args = parser.parse_args()

    rows = []
    for path in args.reports:
        report = json.loads(path.read_text(encoding="utf-8"))
        model, variant = model_from_report(path)
        aggregate = report["aggregate"]
        rows.append(
            {
                "model": model,
                "prompt_variant": variant,
                "report": str(path),
                "item_count": report["item_count"],
                "overall": aggregate["overall"],
                "counterfactual_accuracy": aggregate["counterfactual_accuracy"],
                "support_state_accuracy": aggregate["support_state_accuracy"],
                "relation_delta_accuracy": aggregate["relation_delta_accuracy"],
                "text_claim_resistance": aggregate["text_claim_resistance"],
            }
        )

    best = {}
    for row in rows:
        current = best.get(row["model"])
        if current is None or row["overall"] > current["overall"]:
            best[row["model"]] = row

    summary = {
        "rows": sorted(rows, key=lambda row: (row["model"], row["prompt_variant"])),
        "best_by_model": dict(sorted(best.items())),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary["best_by_model"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
