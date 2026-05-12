#!/usr/bin/env python3
"""Validate hand-photographed real-image VSTB items."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from vwma_benchmark.schema import validate_item


REAL_FAMILIES = {"pen_release_real", "keys_occlusion_real", "mug_moved_real"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/real_vstb_v0_3_1/items.jsonl")
    parser.add_argument("--root", default="data/real_vstb_v0_3_1")
    parser.add_argument("--strict-count", action="store_true", help="Require exactly 10 items per real-image family.")
    args = parser.parse_args()

    items_path = Path(args.items)
    root = Path(args.root)
    if not items_path.exists():
        print(f"{items_path} does not exist yet; add hand-photographed labels before real-image validation.", file=sys.stderr)
        return 1

    errors: list[str] = []
    items = []
    for line_number, line in enumerate(items_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{items_path}:{line_number}: invalid JSON: {exc}")
            continue
        items.append(row)
        item_id = row.get("item_id", f"line_{line_number}")
        if row.get("scene_family") not in REAL_FAMILIES:
            errors.append(f"{item_id}: scene_family must be one of {sorted(REAL_FAMILIES)}")
        if row.get("split") != "VSTB-test-real":
            errors.append(f"{item_id}: real-photo items must use split VSTB-test-real")
        for error in validate_item(row):
            if "invalid split" not in error:
                errors.append(f"{item_id}: {error}")
        for frame in row.get("frames", []):
            frame_path = root / frame
            if frame_path.suffix.lower() not in IMAGE_SUFFIXES:
                errors.append(f"{item_id}: real frame must be one of {sorted(IMAGE_SUFFIXES)}: {frame}")
            if not frame_path.exists():
                errors.append(f"{item_id}: missing frame {frame}")

    counts = Counter(row.get("scene_family") for row in items)
    if args.strict_count:
        for family in REAL_FAMILIES:
            if counts[family] != 10:
                errors.append(f"{family}: expected 10 items, found {counts[family]}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"real-image manifest validation passed for {len(items)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
