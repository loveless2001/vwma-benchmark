"""Reference baselines and oracle-style controls for VSTB."""

from __future__ import annotations

from typing import Any


def _blank_prediction(item: dict[str, Any], name: str) -> dict[str, Any]:
    return {
        "item_id": item["item_id"],
        "baseline": name,
        "relation_delta": [],
        "support_state_after_hypothetical": "unknown",
        "hypothetical_consequence": "unknown",
        "expected_physical_consequence": "unknown",
        "mutated_observed_state": False,
        "object_status": {},
        "event_order": [],
        "identity_map": {},
        "hypotheses": [],
        "confidence": 0.5,
        "next_view_request": {"target_uncertainty": "unknown"},
        "accepted_false_user_claim": False,
        "reanchor_gate_open": False,
        "explanation_refs": [],
        "trust_allocation": "prior_over_state",
    }


def base_model_prior(item: dict[str, Any]) -> dict[str, Any]:
    """A frozen-language-prior baseline with no persistent world state."""

    pred = _blank_prediction(item, "A_base_model_prior")
    query = item["query"].lower()
    if "release" in query or "drop" in query:
        pred["support_state_after_hypothetical"] = "unsupported"
        pred["hypothetical_consequence"] = "falls_or_swings"
        pred["expected_physical_consequence"] = "falls_or_swings"
    if "where" in query or "still there" in query:
        pred["object_status"] = {obj: "not_present" for obj in item["labels"]["objects"]}
    if item["labels"].get("false_user_claim"):
        pred["accepted_false_user_claim"] = True
    pred["confidence"] = 0.62
    return pred


def caption_memory(item: dict[str, Any]) -> dict[str, Any]:
    """A current-caption/history-text baseline without typed deltas or gates."""

    pred = _blank_prediction(item, "C_caption_memory")
    labels = item["labels"]
    caption_text = " ".join(item.get("frame_captions", [])).lower()
    if "occluded" in caption_text or "covered" in caption_text:
        pred["object_status"] = {
            obj: ("occluded" if obj in caption_text else "visible")
            for obj in labels["objects"]
        }
    else:
        pred["object_status"] = {
            obj: labels["object_status"].get(obj, "visible")
            for obj in labels["objects"]
            if labels["object_status"].get(obj) == "visible"
        }
    if "right hand" in caption_text and "pen" in caption_text:
        pred["support_state_after_hypothetical"] = "supported"
        pred["expected_physical_consequence"] = "stable_or_minor_motion"
        pred["hypothetical_consequence"] = labels["hypothetical_consequence"]
    else:
        pred["support_state_after_hypothetical"] = "unknown"
        pred["expected_physical_consequence"] = "unknown"
    pred["event_order"] = labels["event_order"][-1:]
    pred["identity_map"] = labels.get("identity_map", {})
    pred["confidence"] = 0.55
    pred["explanation_refs"] = ["frame_caption"]
    pred["trust_allocation"] = "caption_over_state"
    return pred


def structured_state_oracle(item: dict[str, Any]) -> dict[str, Any]:
    """An upper-bound VWMA-style prediction from gold state labels."""

    labels = item["labels"]
    return {
        "item_id": item["item_id"],
        "baseline": "H_structured_state_oracle",
        "relation_delta": labels["relation_delta"],
        "support_state_after_hypothetical": labels["support_graph"]["after_hypothetical"],
        "hypothetical_consequence": labels["hypothetical_consequence"],
        "expected_physical_consequence": labels["expected_physical_consequence"],
        "mutated_observed_state": False,
        "object_status": labels["object_status"],
        "event_order": labels["event_order"],
        "identity_map": labels.get("identity_map", {}),
        "hypotheses": labels.get("hypotheses", []),
        "confidence": 0.91,
        "next_view_request": {
            "target_uncertainty": labels["best_next_observation"]["target_uncertainty"]
        },
        "accepted_false_user_claim": False,
        "reanchor_gate_open": bool(labels.get("requires_reanchor", False)),
        "explanation_refs": labels.get("required_explanation_refs", []),
        "trust_allocation": labels.get("trust_allocation", "state_over_prior"),
    }


def structured_state_no_gates(item: dict[str, Any]) -> dict[str, Any]:
    """Structured memory without read/override/provenance gate authority."""

    pred = structured_state_oracle(item)
    pred["baseline"] = "D_structured_state_no_gates"
    pred["trust_allocation"] = "prior_over_state"
    pred["explanation_refs"] = ["B_t"]
    if item["labels"].get("false_user_claim"):
        pred["accepted_false_user_claim"] = True
    if "release" in item["query"].lower():
        pred["support_state_after_hypothetical"] = "unsupported"
        pred["expected_physical_consequence"] = "falls_or_swings"
        pred["hypothetical_consequence"] = "generic_release_prior"
    return pred


def state_cleared_ablation(item: dict[str, Any]) -> dict[str, Any]:
    """Ablation: current observation only, B_t history cleared."""

    pred = caption_memory(item)
    pred["baseline"] = "ablation_B_t_cleared"
    pred["relation_delta"] = []
    pred["event_order"] = []
    pred["hypotheses"] = []
    pred["next_view_request"] = {"target_uncertainty": "history_state"}
    return pred


BASELINES = {
    "base_model_prior": base_model_prior,
    "caption_memory": caption_memory,
    "structured_state_no_gates": structured_state_no_gates,
    "structured_state_oracle": structured_state_oracle,
    "state_cleared_ablation": state_cleared_ablation,
}
