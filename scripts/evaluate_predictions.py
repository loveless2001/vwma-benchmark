#!/usr/bin/env python3
"""Evaluate VSTB predictions."""

from __future__ import annotations

import argparse
import json
import sys

from vwma_benchmark.metrics import evaluate_files, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/vstb_v0_3_1/items.jsonl")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = evaluate_files(args.items, args.predictions)
    write_report(report, args.output)
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
