"""Schema and validation helpers for VSTB items and predictions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_LABEL_KEYS = {
    "objects",
    "object_status",
    "relation_state",
    "relation_delta",
    "support_graph",
    "support_delta",
    "event_type",
    "event_order",
    "hypothetical_action",
    "hypothetical_consequence",
    "expected_physical_consequence",
    "uncertainty",
    "best_next_observation",
    "provenance_validity",
    "must_not_mutate_observed_state",
}

REQUIRED_ITEM_KEYS = {
    "item_id",
    "split",
    "scene_family",
    "query",
    "frames",
    "frame_captions",
    "history",
    "labels",
    "adversarial_tags",
    "evaluation_focus",
}

VALID_SPLITS = {
    "VSTB-train-synth",
    "VSTB-dev-synth",
    "VSTB-test-synth",
    "VSTB-test-adversarial",
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""

    items: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            items.append(value)
    return items


def dump_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Write rows as stable JSONL."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def relation_key(relation: Any) -> tuple[str, str, str, str] | None:
    """Normalize a relation-like value into a comparable key."""

    if isinstance(relation, dict):
        subject = relation.get("subject")
        predicate = relation.get("predicate")
        object_ = relation.get("object")
        value = relation.get("value", True)
    elif isinstance(relation, (list, tuple)) and len(relation) >= 3:
        subject, predicate, object_ = relation[:3]
        value = relation[3] if len(relation) >= 4 else True
    else:
        return None
    if subject is None or predicate is None or object_ is None:
        return None
    return (str(subject), str(predicate), str(object_), str(value).lower())


def relation_set(relations: Any) -> set[tuple[str, str, str, str]]:
    """Normalize a relation list into a set of keys."""

    if not isinstance(relations, list):
        return set()
    out = set()
    for relation in relations:
        key = relation_key(relation)
        if key:
            out.add(key)
    return out


def validate_item(item: dict[str, Any]) -> list[str]:
    """Return validation errors for one benchmark item."""

    errors: list[str] = []
    missing = REQUIRED_ITEM_KEYS - set(item)
    if missing:
        errors.append(f"missing item keys: {sorted(missing)}")
    split = item.get("split")
    if split not in VALID_SPLITS:
        errors.append(f"invalid split: {split!r}")
    frames = item.get("frames")
    captions = item.get("frame_captions")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty list")
    if not isinstance(captions, list) or not captions:
        errors.append("frame_captions must be a non-empty list")
    if isinstance(frames, list) and isinstance(captions, list) and len(frames) != len(captions):
        errors.append("frames and frame_captions length mismatch")
    labels = item.get("labels")
    if not isinstance(labels, dict):
        errors.append("labels must be an object")
    else:
        missing_labels = REQUIRED_LABEL_KEYS - set(labels)
        if missing_labels:
            errors.append(f"missing label keys: {sorted(missing_labels)}")
        if labels.get("must_not_mutate_observed_state") is not True:
            errors.append("must_not_mutate_observed_state must be true")
    if not isinstance(item.get("evaluation_focus"), list) or not item.get("evaluation_focus"):
        errors.append("evaluation_focus must be a non-empty list")
    return errors


def validate_dataset(items: list[dict[str, Any]], frame_root: str | Path | None = None) -> list[str]:
    """Validate a list of items and optionally ensure frame files exist."""

    errors: list[str] = []
    seen: set[str] = set()
    splits: set[str] = set()
    for index, item in enumerate(items):
        item_id = item.get("item_id", f"index_{index}")
        if item_id in seen:
            errors.append(f"{item_id}: duplicate item_id")
        seen.add(str(item_id))
        splits.add(str(item.get("split")))
        for error in validate_item(item):
            errors.append(f"{item_id}: {error}")
        if frame_root is not None:
            root = Path(frame_root)
            for frame in item.get("frames", []):
                if not (root / frame).exists():
                    errors.append(f"{item_id}: missing frame {frame}")
    missing_splits = VALID_SPLITS - splits
    if missing_splits:
        errors.append(f"missing required evaluation splits: {sorted(missing_splits)}")
    return errors
