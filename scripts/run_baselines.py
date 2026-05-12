#!/usr/bin/env python3
"""Run reference VSTB baselines."""

from __future__ import annotations

import argparse
import sys

from vwma_benchmark.baselines import BASELINES
from vwma_benchmark.schema import dump_jsonl, load_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/vstb_v0_3_1/items.jsonl")
    parser.add_argument("--baseline", choices=sorted(BASELINES), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    items = load_jsonl(args.items)
    predictions = [BASELINES[args.baseline](item) for item in items]
    dump_jsonl(args.output, predictions)
    print(f"wrote {len(predictions)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
