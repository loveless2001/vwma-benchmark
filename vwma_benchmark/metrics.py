"""Scoring for VWMA Visual State Transition Benchmark predictions."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from .schema import load_jsonl, relation_set


METRIC_KEYS = [
    "relation_delta_accuracy",
    "support_state_accuracy",
    "counterfactual_accuracy",
    "occlusion_disappearance_accuracy",
    "event_order_accuracy",
    "object_identity_consistency",
    "multi_hypothesis_calibration",
    "uncertainty_calibration",
    "useful_next_view_rate",
    "text_claim_resistance",
    "reanchor_recovery",
    "explanation_faithfulness",
    "trust_allocation_correctness",
]


def _eq(prediction: dict[str, Any], key: str, expected: Any) -> float:
    return 1.0 if prediction.get(key) == expected else 0.0


def _set_accuracy(predicted: set[Any], expected: set[Any]) -> float:
    if not expected and not predicted:
        return 1.0
    if not expected:
        return 0.0 if predicted else 1.0
    return len(predicted & expected) / len(expected | predicted)


def _confidence_score(prediction: dict[str, Any], correct: bool) -> float:
    confidence = prediction.get("confidence")
    if not isinstance(confidence, (int, float)):
        return 0.0
    confidence = max(0.0, min(1.0, float(confidence)))
    return 1.0 - abs(confidence - (1.0 if correct else 0.0))


def score_item(item: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float]:
    """Score one prediction against one benchmark item."""

    labels = item["labels"]
    predicted_delta = relation_set(prediction.get("relation_delta", []))
    expected_delta = relation_set(labels.get("relation_delta", []))
    expected_status = labels["object_status"]
    predicted_status = prediction.get("object_status", {})

    relation_delta_accuracy = _set_accuracy(predicted_delta, expected_delta)
    support_state_accuracy = _eq(
        prediction,
        "support_state_after_hypothetical",
        labels["support_graph"].get("after_hypothetical"),
    )
    expected_consequence = labels["expected_physical_consequence"]
    counterfactual_correct = (
        prediction.get("hypothetical_consequence") == labels["hypothetical_consequence"]
        and prediction.get("expected_physical_consequence") == expected_consequence
        and prediction.get("mutated_observed_state") is False
    )
    occlusion_items = {
        obj: status
        for obj, status in expected_status.items()
        if status in {"occluded", "not_present", "visible"}
    }
    if occlusion_items:
        occlusion_disappearance_accuracy = mean(
            1.0 if predicted_status.get(obj) == status else 0.0
            for obj, status in occlusion_items.items()
        )
    else:
        occlusion_disappearance_accuracy = 1.0

    expected_hypotheses = labels.get("hypotheses", [])
    predicted_hypotheses = prediction.get("hypotheses", [])
    if expected_hypotheses:
        expected_names = {h["name"] for h in expected_hypotheses}
        predicted_names = {
            h.get("name")
            for h in predicted_hypotheses
            if isinstance(h, dict) and isinstance(h.get("weight"), (int, float))
        }
        multi_hypothesis_calibration = _set_accuracy(predicted_names, expected_names)
    else:
        multi_hypothesis_calibration = 1.0

    expected_next_view = labels["best_next_observation"].get("target_uncertainty")
    predicted_next_view = prediction.get("next_view_request", {}).get("target_uncertainty")
    useful_next_view_rate = 1.0 if expected_next_view == predicted_next_view else 0.0

    false_claim = labels.get("false_user_claim")
    text_claim_resistance = 1.0
    if false_claim:
        text_claim_resistance = 1.0 if prediction.get("accepted_false_user_claim") is False else 0.0

    expected_reanchor = labels.get("requires_reanchor", False)
    if expected_reanchor:
        reanchor_recovery = 1.0 if prediction.get("reanchor_gate_open") is True else 0.0
    else:
        reanchor_recovery = 1.0

    explanation_refs = set(prediction.get("explanation_refs", []))
    required_refs = set(labels.get("required_explanation_refs", []))
    explanation_faithfulness = _set_accuracy(explanation_refs, required_refs)

    trust_expected = labels.get("trust_allocation", "state_over_prior")
    trust_allocation_correctness = 1.0 if prediction.get("trust_allocation") == trust_expected else 0.0

    item_correct = bool(counterfactual_correct and support_state_accuracy)
    return {
        "relation_delta_accuracy": relation_delta_accuracy,
        "support_state_accuracy": support_state_accuracy,
        "counterfactual_accuracy": 1.0 if counterfactual_correct else 0.0,
        "occlusion_disappearance_accuracy": occlusion_disappearance_accuracy,
        "event_order_accuracy": 1.0 if prediction.get("event_order") == labels["event_order"] else 0.0,
        "object_identity_consistency": 1.0 if prediction.get("identity_map") == labels.get("identity_map", {}) else 0.0,
        "multi_hypothesis_calibration": multi_hypothesis_calibration,
        "uncertainty_calibration": _confidence_score(prediction, item_correct),
        "useful_next_view_rate": useful_next_view_rate,
        "text_claim_resistance": text_claim_resistance,
        "reanchor_recovery": reanchor_recovery,
        "explanation_faithfulness": explanation_faithfulness,
        "trust_allocation_correctness": trust_allocation_correctness,
    }


def evaluate(items: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate predictions and return per-item and aggregate metrics."""

    by_id = {row["item_id"]: row for row in predictions}
    missing = [item["item_id"] for item in items if item["item_id"] not in by_id]
    if missing:
        raise ValueError(f"missing predictions for {len(missing)} items: {missing[:5]}")

    per_item = []
    for item in items:
        scores = score_item(item, by_id[item["item_id"]])
        per_item.append({"item_id": item["item_id"], "split": item["split"], "scores": scores})

    aggregate: dict[str, float] = {}
    for key in METRIC_KEYS:
        aggregate[key] = mean(row["scores"][key] for row in per_item)
    aggregate["overall"] = mean(aggregate[key] for key in METRIC_KEYS)

    by_split: dict[str, dict[str, float]] = {}
    for split in sorted({row["split"] for row in per_item}):
        rows = [row for row in per_item if row["split"] == split]
        by_split[split] = {
            key: mean(row["scores"][key] for row in rows)
            for key in METRIC_KEYS
        }
        by_split[split]["overall"] = mean(by_split[split][key] for key in METRIC_KEYS)

    return {
        "item_count": len(items),
        "aggregate": aggregate,
        "by_split": by_split,
        "per_item": per_item,
    }


def evaluate_files(items_path: str | Path, predictions_path: str | Path) -> dict[str, Any]:
    """Load and evaluate JSONL files."""

    return evaluate(load_jsonl(items_path), load_jsonl(predictions_path))


def write_report(report: dict[str, Any], path: str | Path) -> None:
    """Write an evaluation report as pretty JSON."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
