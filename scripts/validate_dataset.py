#!/usr/bin/env python3
"""Validate a generated VSTB dataset."""

from __future__ import annotations

import argparse
import sys

from vwma_benchmark.schema import load_jsonl, validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/vstb_v0_3_1/items.jsonl")
    parser.add_argument("--frame-root", default="data/vstb_v0_3_1")
    args = parser.parse_args()

    errors = validate_dataset(load_jsonl(args.items), args.frame_root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("dataset validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
