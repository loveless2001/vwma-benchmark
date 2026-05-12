#!/usr/bin/env python3
"""Validate public-corpus real-frame VSTB items and provenance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vwma_benchmark.schema import validate_item


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
REQUIRED_PROVENANCE_KEYS = {
    "dataset",
    "dataset_url",
    "source_split",
    "source_video_id",
    "source_frames",
    "license",
    "redistribution",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/public_corpus_vstb_v0_3_1/items.jsonl")
    parser.add_argument("--root", default="data/public_corpus_vstb_v0_3_1")
    args = parser.parse_args()

    items_path = Path(args.items)
    root = Path(args.root)
    if not items_path.exists():
        print(f"{items_path} does not exist; run scripts/prepare_public_corpus_vstb.py first.", file=sys.stderr)
        return 1

    errors: list[str] = []
    item_count = 0
    for line_number, line in enumerate(items_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item_count += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{items_path}:{line_number}: invalid JSON: {exc}")
            continue
        item_id = row.get("item_id", f"line_{line_number}")
        if row.get("split") != "VSTB-test-real-public":
            errors.append(f"{item_id}: public-corpus items must use split VSTB-test-real-public")
        if not str(row.get("scene_family", "")).endswith("_public"):
            errors.append(f"{item_id}: public-corpus scene_family must end with _public")
        for error in validate_item(row):
            errors.append(f"{item_id}: {error}")
        provenance = row.get("source_provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{item_id}: missing source_provenance object")
        else:
            missing = REQUIRED_PROVENANCE_KEYS - set(provenance)
            if missing:
                errors.append(f"{item_id}: missing provenance keys: {sorted(missing)}")
            frames = provenance.get("source_frames")
            if not isinstance(frames, list) or len(frames) < 2:
                errors.append(f"{item_id}: source_frames must contain at least two frame ids")
        for frame in row.get("frames", []):
            frame_path = root / frame
            if frame_path.suffix.lower() not in IMAGE_SUFFIXES:
                errors.append(f"{item_id}: public-corpus frame must be an image: {frame}")
            if not frame_path.exists():
                errors.append(f"{item_id}: missing frame {frame}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"public-corpus manifest validation passed for {item_count} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
