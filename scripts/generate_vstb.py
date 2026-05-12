#!/usr/bin/env python3
"""Generate the synthetic VSTB v0.3.1 benchmark.

The generator intentionally keeps the family structure explicit:
10 scenario families x 10 variants = 100 synthetic items.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vwma_benchmark.schema import dump_jsonl, validate_dataset


FAMILY_VARIANTS = 10


def rel(subject: str, predicate: str, object_: str, value: bool = True) -> dict[str, Any]:
    return {"subject": subject, "predicate": predicate, "object": object_, "value": value}


def rect(id_: str, x: float, y: float, w: float, h: float, fill: str, rx: float = 8) -> dict[str, Any]:
    return {"type": "rect", "id": id_, "x": x, "y": y, "w": w, "h": h, "fill": fill, "rx": rx}


def circle(id_: str, cx: float, cy: float, r: float, fill: str) -> dict[str, Any]:
    return {"type": "circle", "id": id_, "cx": cx, "cy": cy, "r": r, "fill": fill}


def line(id_: str, x1: float, y1: float, x2: float, y2: float, stroke: str, sw: float = 6) -> dict[str, Any]:
    return {"type": "line", "id": id_, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke, "sw": sw}


def frame(name: str, title: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    return {"name": f"frames/{name}.svg", "title": title, "elements": elements}


def split_for(family: str, variant: int, adversarial: bool = False) -> str:
    if variant == 0:
        return "VSTB-train-synth"
    if variant == 1:
        return "VSTB-dev-synth"
    if adversarial:
        return "VSTB-test-adversarial"
    return "VSTB-test-synth"


def labels(
    *,
    objects: list[str],
    object_status: dict[str, str],
    relation_state: list[dict[str, Any]],
    relation_delta: list[dict[str, Any]],
    support_after: str = "not_applicable",
    support_graph: list[dict[str, Any]] | None = None,
    support_delta: list[dict[str, Any]] | None = None,
    event_type: list[str] | None = None,
    event_order: list[str] | None = None,
    hypothetical_action: str = "none",
    hypothetical_consequence: str = "not_applicable",
    expected_physical_consequence: str = "not_applicable",
    target_uncertainty: str = "none",
    suggested_action: str = "no extra observation needed",
    provenance_validity: str = "valid",
    required_refs: list[str] | None = None,
    identity_map: dict[str, str] | None = None,
    hypotheses: list[dict[str, Any]] | None = None,
    false_user_claim: str | None = None,
    requires_reanchor: bool = False,
    trust_allocation: str = "state_over_prior",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "objects": objects,
        "object_status": object_status,
        "relation_state": relation_state,
        "relation_delta": relation_delta,
        "support_graph": {"current": support_graph or [], "after_hypothetical": support_after},
        "support_delta": support_delta or [],
        "event_type": event_type or [],
        "event_order": event_order or [],
        "hypothetical_action": hypothetical_action,
        "hypothetical_consequence": hypothetical_consequence,
        "expected_physical_consequence": expected_physical_consequence,
        "uncertainty": {
            "level": "medium" if target_uncertainty != "none" else "low",
            "load_bearing": [] if target_uncertainty == "none" else [target_uncertainty],
        },
        "best_next_observation": {
            "target_uncertainty": target_uncertainty,
            "suggested_action": suggested_action,
            "expected_information_gain": 0.74 if target_uncertainty != "none" else 0.0,
            "cost": 0.2 if target_uncertainty != "none" else 0.0,
            "risk": 0.03,
        },
        "provenance_validity": provenance_validity,
        "must_not_mutate_observed_state": True,
        "required_explanation_refs": required_refs or ["B_t", "Delta_B_t"],
        "identity_map": identity_map or {obj: obj for obj in objects},
        "hypotheses": hypotheses or [],
        "requires_reanchor": requires_reanchor,
        "trust_allocation": trust_allocation,
    }
    if false_user_claim:
        out["false_user_claim"] = false_user_claim
    return out


def item(
    family: str,
    variant: int,
    split: str,
    query: str,
    frames: list[str],
    captions: list[str],
    history: list[str],
    item_labels: dict[str, Any],
    tags: list[str],
    focus: list[str],
) -> dict[str, Any]:
    return {
        "item_id": f"vstb_{family}_{variant:03d}",
        "split": split,
        "scene_family": family,
        "variant_id": variant,
        "query": query,
        "frames": frames,
        "frame_captions": captions,
        "history": history,
        "labels": item_labels,
        "adversarial_tags": tags,
        "evaluation_focus": focus,
        "schema_version": "v0.3.1-alpha",
    }


def pen_release(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    y = 210 + (v % 3) * 12
    left_supports = v not in {3, 7}
    right_supports = v not in {4, 8}
    release_both = v in {3, 4, 8}
    color = ["#244b9b", "#0f766e", "#7c3aed", "#be123c"][v % 4]
    frames = [
        frame(
            f"pen_release_{v:03d}_t0",
            "pen support before release",
            [
                rect("left_hand", 100, y - 12, 145, 42, "#c79a65"),
                rect("right_hand", 530, y - 12, 145, 42, "#c79a65"),
                rect("pen", 230, y + 6, 340, 14, color, 4),
            ],
        )
    ]
    support_edges = []
    relations = []
    if left_supports:
        support_edges.append(rel("left_hand", "supporting", "pen"))
        relations.append(rel("left_hand", "grasping", "pen"))
    if right_supports:
        support_edges.append(rel("right_hand", "supporting", "pen"))
        relations.append(rel("right_hand", "grasping", "pen"))
    support_after = "unsupported" if release_both or not right_supports else "supported"
    consequence = "falls_or_swings" if support_after == "unsupported" else "stable_or_minor_motion"
    hypo = "no_known_support_remains" if support_after == "unsupported" else "right_hand_support_remains"
    data = item(
        "pen_release",
        v,
        split_for("pen_release", v),
        "What happens if I release only my left hand?" if not release_both else "What happens if both hands release the pen?",
        [frames[0]["name"]],
        ["A pen is held near one or two visible hands."],
        ["visible grip state recorded before the release query"],
        labels(
            objects=["pen", "left_hand", "right_hand"],
            object_status={"pen": "visible", "left_hand": "visible", "right_hand": "visible"},
            relation_state=relations,
            relation_delta=[rel("left_hand", "grasping", "pen", False)],
            support_graph=support_edges,
            support_delta=[rel("left_hand", "supporting", "pen", False)],
            support_after=support_after,
            event_type=["counterfactual_release"],
            event_order=["support_state_seen", "query_counterfactual_release"],
            hypothetical_action="release(left_hand, pen)" if not release_both else "release_both_hands(pen)",
            hypothetical_consequence=hypo,
            expected_physical_consequence=consequence,
            required_refs=["B_t", "B_t_h", "support_graph", "override_gate"],
        ),
        ["counterfactual", "support_graph"],
        ["support-state accuracy", "counterfactual accuracy", "trust-allocation error rate"],
    )
    return frames, data


def keys_occlusion(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cover = ["notebook", "paper", "folder", "tablet"][v % 4]
    x = 170 + (v % 5) * 55
    y = 230 + (v % 2) * 22
    frames = [
        frame(f"keys_occlusion_{v:03d}_t0", "keys visible", [circle("keyring", x, y, 24, "#f2c94c"), rect("key", x + 18, y - 5, 85, 10, "#f2c94c", 3)]),
        frame(f"keys_occlusion_{v:03d}_t1", "keys covered", [circle("keyring_partial", x, y, 24, "#f2c94c"), rect(cover, x - 28, y - 42, 215, 126, "#8cc7a1")]),
    ]
    data = item(
        "keys_occlusion",
        v,
        split_for("keys_occlusion", v),
        "Are the keys gone?",
        [f["name"] for f in frames],
        ["Keys are visible on the desk.", f"A {cover} covers the key area; part of the key ring may remain visible."],
        ["keys visible on desk", f"{cover} moved over keys"],
        labels(
            objects=["keys", cover],
            object_status={"keys": "occluded", cover: "visible"},
            relation_state=[rel(cover, "covering", "keys")],
            relation_delta=[rel(cover, "covering", "keys", True)],
            event_type=["occlusion"],
            event_order=["keys_visible", f"{cover}_covers_keys"],
            target_uncertainty="keys_exact_position",
            suggested_action=f"lift or slide the {cover} enough to reveal the key ring",
            required_refs=["B_t", "Delta_B_t", "provenance", "uncertainty"],
        ),
        ["occlusion_vs_disappearance"],
        ["occlusion/disappearance accuracy", "useful next-view rate"],
    )
    return frames, data


def mug_moved(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    destinations = ["shelf", "tray", "mat", "box"]
    dest = destinations[v % len(destinations)]
    start_x = 160 + (v % 4) * 75
    end_x = 520 - (v % 3) * 55
    mug_color = ["#e4572e", "#ef476f", "#06b6d4", "#7c3aed"][v % 4]
    frames = [
        frame(f"mug_moved_{v:03d}_t0", "mug on desk", [rect("desk", 80, 290, 640, 52, "#b08968"), circle("mug", start_x, 252, 40, mug_color)]),
        frame(f"mug_moved_{v:03d}_t1", f"mug on {dest}", [rect("desk", 80, 290, 640, 52, "#b08968"), rect(dest, 105, 120, 590, 35, "#6d6875"), circle("mug", end_x, 92, 40, mug_color)]),
    ]
    data = item(
        "mug_moved",
        v,
        split_for("mug_moved", v),
        "What changed since before?",
        [f["name"] for f in frames],
        ["The mug is on the desk.", f"The same mug is on the {dest}."],
        ["mug on desk", f"mug moved to {dest}"],
        labels(
            objects=["mug", "desk", dest],
            object_status={"mug": "visible", "desk": "visible", dest: "visible"},
            relation_state=[rel("mug", "on", dest)],
            relation_delta=[rel("mug", "on", "desk", False), rel("mug", "on", dest, True)],
            event_type=["move"],
            event_order=["mug_on_desk", f"mug_on_{dest}"],
            required_refs=["B_t", "Delta_B_t", "identity_map"],
        ),
        ["relation_delta", "identity"],
        ["relation-delta accuracy", "object-identity consistency"],
    )
    return frames, data


def cable_relation(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    unplug = v % 2 == 0
    query = "Is the cable plugged in?"
    y = 210 + (v % 5) * 18
    frames = [
        frame(f"cable_relation_{v:03d}_t0", "cable start", [rect("socket", 555, y - 35, 70, 70, "#d9d9d9"), line("cable", 150, y, 555, y, "#111827", 10)]),
        frame(
            f"cable_relation_{v:03d}_t1",
            "cable relation changed",
            [rect("socket", 555, y - 35, 70, 70, "#d9d9d9"), line("cable", 150, y, 505 if unplug else 555, y + (62 if unplug else 0), "#111827", 10)],
        ),
    ]
    final_value = not unplug
    data = item(
        "cable_relation",
        v,
        split_for("cable_relation", v),
        query,
        [f["name"] for f in frames],
        ["The cable connector starts inserted into the socket.", "The cable connector final relation is visible."],
        ["cable plugged into socket", "relation changed" if unplug else "relation preserved"],
        labels(
            objects=["cable", "socket"],
            object_status={"cable": "visible", "socket": "visible"},
            relation_state=[rel("cable", "plugged_into", "socket", final_value)],
            relation_delta=[rel("cable", "plugged_into", "socket", final_value)],
            event_type=["relation_removed" if unplug else "relation_preserved"],
            event_order=["plugged_start", "unplugged_final" if unplug else "plugged_final"],
            required_refs=["B_t", "Delta_B_t", "relation_state"],
        ),
        ["fine_relation_change"],
        ["relation-delta accuracy", "event-order accuracy"],
    )
    return frames, data


def drawer_state(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    final_open = v % 3 != 0
    frames = [
        frame(f"drawer_state_{v:03d}_t0", "drawer closed", [rect("drawer", 210, 150, 370, 160, "#9c6644"), circle("handle", 395, 230, 12, "#f1c453")]),
        frame(
            f"drawer_state_{v:03d}_t1",
            "drawer final state",
            [rect("cabinet", 210, 150, 370, 160, "#7f5539"), rect("drawer", 250 if final_open else 210, 205 if final_open else 150, 370, 125 if final_open else 160, "#9c6644"), circle("handle", 435 if final_open else 395, 268 if final_open else 230, 12, "#f1c453")],
        ),
    ]
    state = "open" if final_open else "closed"
    data = item(
        "drawer_state",
        v,
        split_for("drawer_state", v),
        "Is the drawer open now?",
        [f["name"] for f in frames],
        ["The drawer starts closed.", f"The drawer final state is {state}."],
        ["drawer closed", f"drawer {state}"],
        labels(
            objects=["drawer", "cabinet"],
            object_status={"drawer": "visible", "cabinet": "visible"},
            relation_state=[rel("drawer", "state", state)],
            relation_delta=[rel("drawer", "state", "open" if final_open else "closed", final_open)],
            event_type=["open" if final_open else "no_open_event"],
            event_order=["drawer_closed_start", f"drawer_{state}_final"],
            required_refs=["B_t", "Delta_B_t", "event_log"],
        ),
        ["event_state_persistence"],
        ["event-order accuracy", "relation-delta accuracy"],
    )
    return frames, data


def string_attached(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    attached = v % 4 != 0
    color = ["#7c3aed", "#0f766e", "#be123c"][v % 3]
    frames = [
        frame(
            f"string_attached_{v:03d}_t0",
            "object with possible string",
            ([line("string", 400, 80, 400, 230, "#111827", 4)] if attached else [])
            + [circle("weight", 400, 270, 42, color), rect("hand", 280, 242, 100, 42, "#c79a65")],
        )
    ]
    support_after = "constrained" if attached else "unsupported"
    consequence = "hangs_or_swings_not_free_fall" if attached else "falls_or_swings"
    hypo = "string_constraint_remains" if attached else "no_known_support_remains"
    data = item(
        "string_attached",
        v,
        split_for("string_attached", v),
        "What happens if I release the object?",
        [frames[0]["name"]],
        ["The object is held by a hand and may be attached to an overhead string."],
        ["weight support state recorded", "counterfactual release queried"],
        labels(
            objects=["weight", "hand", "string"],
            object_status={"weight": "visible", "hand": "visible", "string": "visible" if attached else "not_present"},
            relation_state=[rel("hand", "grasping", "weight")] + ([rel("string", "attached_to", "weight")] if attached else []),
            relation_delta=[rel("hand", "grasping", "weight", False)],
            support_graph=[rel("hand", "supporting", "weight")] + ([rel("string", "constraining", "weight")] if attached else []),
            support_delta=[rel("hand", "supporting", "weight", False)],
            support_after=support_after,
            event_type=["counterfactual_release"],
            event_order=["support_state_seen", "query_counterfactual_release"],
            hypothetical_action="release(hand, weight)",
            hypothetical_consequence=hypo,
            expected_physical_consequence=consequence,
            required_refs=["B_t_h", "support_graph", "override_gate"],
        ),
        ["counterfactual", "support_graph"],
        ["support-state accuracy", "counterfactual accuracy"],
    )
    return frames, data


def similar_swap(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    color = ["#d62828", "#2563eb", "#0f766e"][v % 3]
    frames = [
        frame(f"similar_swap_{v:03d}_t0", "similar objects before crossing", [rect("block_A", 170, 230, 90, 90, color), rect("block_B", 520, 230, 90, 90, color)]),
        frame(f"similar_swap_{v:03d}_t1", "similar objects crossing", [rect("block_A", 325, 205, 90, 90, color), rect("block_B", 370, 255, 90, 90, color)]),
        frame(f"similar_swap_{v:03d}_t2", "similar objects after ambiguous crossing", [rect("block_A_or_B", 180, 230, 90, 90, color), rect("block_B_or_A", 510, 230, 90, 90, color)]),
    ]
    data = item(
        "similar_swap",
        v,
        split_for("similar_swap", v, adversarial=True),
        "Which block is on the left now?",
        [f["name"] for f in frames],
        ["Two visually similar blocks are separated.", "The blocks cross with heavy overlap.", "The final left/right identities are ambiguous."],
        ["block_A left", "block_B right", "tracks crossed under occlusion"],
        labels(
            objects=["block_A", "block_B"],
            object_status={"block_A": "visible", "block_B": "visible"},
            relation_state=[rel("block_A", "left_of", "block_B")],
            relation_delta=[],
            event_type=["identity_ambiguous_crossing"],
            event_order=["separated", "crossed", "ambiguous_final"],
            target_uncertainty="block_identity_after_crossing",
            suggested_action="show a distinctive mark or side angle before assigning identities",
            identity_map={"block_A": "hypothesis_left_or_right", "block_B": "hypothesis_right_or_left"},
            hypotheses=[{"name": "A_left_B_right", "weight": 0.52}, {"name": "A_right_B_left", "weight": 0.48}],
            required_refs=["H_t", "identity_protocol", "uncertainty"],
        ),
        ["identity_swap", "multi_hypothesis"],
        ["object-identity consistency", "multi-hypothesis calibration", "useful next-view rate"],
    )
    return frames, data


def camera_motion(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dx = 45 + (v % 5) * 18
    obj = ["mug", "phone", "cup"][v % 3]
    frames = [
        frame(f"camera_motion_{v:03d}_t0", "camera view before pan", [rect(obj, 330, 230, 82, 82, "#e4572e"), rect("background_mark", 70, 95, 45, 45, "#64748b")]),
        frame(f"camera_motion_{v:03d}_t1", "camera view after pan", [rect(obj, 330 - dx, 230, 82, 82, "#e4572e"), rect("background_mark", 70 - dx, 95, 45, 45, "#64748b")]),
    ]
    data = item(
        "camera_motion",
        v,
        split_for("camera_motion", v, adversarial=True),
        f"Did the {obj} move?",
        [f["name"] for f in frames],
        [f"The {obj} appears in the camera view.", f"The camera moved; the {obj} appears shifted but stayed in world position."],
        ["camera_pose_before", "camera_pose_after", f"{obj} world position unchanged"],
        labels(
            objects=[obj, "camera"],
            object_status={obj: "visible", "camera": "not_visible"},
            relation_state=[rel(obj, "world_position", "unchanged")],
            relation_delta=[rel("camera", "pose", "changed", True), rel(obj, "world_position", "unchanged", True)],
            event_type=["camera_motion"],
            event_order=["camera_pose_before", "camera_pose_after"],
            required_refs=["camera_motion", "Delta_B_t", "B_t"],
        ),
        ["camera_motion_compensation"],
        ["relation-delta accuracy", "trust-allocation error rate"],
    )
    return frames, data


def false_claim(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obj = ["keys", "wallet", "glasses", "phone"][v % 4]
    cover = ["notebook", "folder", "paper"][v % 3]
    dest = ["shelf", "drawer", "box"][v % 3]
    x = 180 + (v % 4) * 60
    frames = [
        frame(f"false_claim_{v:03d}_t0", "object visible", [circle(obj, x, 260, 28, "#f2c94c")]),
        frame(f"false_claim_{v:03d}_t1", "object covered", [circle(f"{obj}_partial", x, 260, 28, "#f2c94c"), rect(cover, x - 30, 220, 210, 130, "#8cc7a1")]),
    ]
    data = item(
        "false_claim",
        v,
        split_for("false_claim", v, adversarial=True),
        f"I moved the {obj} to the {dest}. Where are they?",
        [f["name"] for f in frames],
        [f"The {obj} is visible on the desk.", f"A {cover} covers the {obj}; no visual {dest} movement occurred."],
        [f"{obj} visible", f"{cover} covers {obj}", f"user claims {obj} moved to {dest}"],
        labels(
            objects=[obj, cover, dest],
            object_status={obj: "occluded", cover: "visible", dest: "visible"},
            relation_state=[rel(cover, "covering", obj)],
            relation_delta=[rel(cover, "covering", obj, True)],
            event_type=["unsupported_user_claim"],
            event_order=[f"{obj}_visible", f"{cover}_covers_{obj}", "unsupported_user_claim"],
            target_uncertainty=f"{obj}_under_{cover}",
            suggested_action=f"show under the {cover} or the {dest} to resolve the claim",
            provenance_validity="text_claim_unsupported_by_visual_evidence",
            false_user_claim=f"{obj} moved to {dest}",
            required_refs=["provenance", "override_gate", "text_claim_resistance"],
        ),
        ["provenance_corruption", "false_user_claim"],
        ["text-claim resistance", "occlusion/disappearance accuracy"],
    )
    return frames, data


def frame_identical_history(v: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pair = v // 2
    supported_history = v % 2 == 0
    final_name = f"frame_identical_history_pair_{pair:03d}_final"
    prior_name = f"frame_identical_history_{v:03d}_prior"
    frames = [
        frame(
            prior_name,
            "history prior state",
            [rect("left_hand", 110, 205, 135, 42, "#c79a65"), rect("pen", 240, 226, 320, 14, "#244b9b", 4)]
            + ([rect("right_hand", 530, 205, 135, 42, "#c79a65")] if supported_history else []),
        ),
        frame(
            final_name,
            "shared final frame with occluded right side",
            [rect("left_hand", 92, 145, 140, 44, "#c79a65"), rect("pen", 245, 235, 310, 14, "#244b9b", 4), rect("occluder", 500, 190, 190, 130, "#4b5563")],
        ),
    ]
    support_after = "supported" if supported_history else "unsupported"
    consequence = "stable_or_minor_motion" if supported_history else "falls_or_swings"
    hypo = "right_hand_support_remains_probable" if supported_history else "no_known_support_remains"
    relation_state = [rel("right_hand", "grasping", "pen", supported_history)]
    data = item(
        "frame_identical_history",
        v,
        split_for("frame_identical_history", v, adversarial=True),
        "Will the pen stay up if the left hand lets go?",
        [f["name"] for f in frames],
        ["Prior history records whether right-hand support existed.", "The final frame is shared across the pair and occludes the right side."],
        ["right_hand support observed" if supported_history else "right_hand not supporting observed", "right side occluded", "query release left"],
        labels(
            objects=["pen", "left_hand", "right_hand", "occluder"],
            object_status={"pen": "visible", "left_hand": "visible", "right_hand": "occluded", "occluder": "visible"},
            relation_state=relation_state,
            relation_delta=[rel("left_hand", "grasping", "pen", False)],
            support_graph=[rel("right_hand", "supporting", "pen")] if supported_history else [],
            support_delta=[rel("left_hand", "supporting", "pen", False)],
            support_after=support_after,
            event_type=["counterfactual_release", "occlusion"],
            event_order=["prior_support_state_seen", "right_side_occluded", "query_release_left"],
            hypothetical_action="release(left_hand, pen)",
            hypothetical_consequence=hypo,
            expected_physical_consequence=consequence,
            target_uncertainty="right_hand_current_grip",
            suggested_action="show the right side of the pen",
            required_refs=["B_t", "H_t", "B_t_h", "support_graph"],
        ),
        ["frame_identical_pair", "state_use_over_caption"],
        ["state-ablation gap", "counterfactual accuracy"],
    )
    return frames, data


FAMILY_BUILDERS = [
    pen_release,
    keys_occlusion,
    mug_moved,
    cable_relation,
    drawer_state,
    string_attached,
    similar_swap,
    camera_motion,
    false_claim,
    frame_identical_history,
]


def build_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frames: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for builder in FAMILY_BUILDERS:
        for variant in range(FAMILY_VARIANTS):
            frame_specs, row = builder(variant)
            frames.extend(frame_specs)
            items.append(row)
    return frames, items


def svg_for(spec: dict[str, Any]) -> str:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420">',
        '<rect width="800" height="420" fill="#f8fafc"/>',
        '<rect x="60" y="350" width="680" height="30" fill="#475569" opacity="0.2"/>',
        f'<title>{spec["title"]}</title>',
    ]
    for element in spec["elements"]:
        if element["type"] == "rect":
            parts.append(
                f'<rect data-id="{element["id"]}" x="{element["x"]}" y="{element["y"]}" '
                f'width="{element["w"]}" height="{element["h"]}" rx="{element.get("rx", 8)}" fill="{element["fill"]}"/>'
            )
        elif element["type"] == "circle":
            parts.append(f'<circle data-id="{element["id"]}" cx="{element["cx"]}" cy="{element["cy"]}" r="{element["r"]}" fill="{element["fill"]}"/>')
        elif element["type"] == "line":
            parts.append(
                f'<line data-id="{element["id"]}" x1="{element["x1"]}" y1="{element["y1"]}" '
                f'x2="{element["x2"]}" y2="{element["y2"]}" stroke="{element["stroke"]}" '
                f'stroke-width="{element["sw"]}" stroke-linecap="round"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    frames, items = build_dataset()
    frame_dir = output_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("*.svg"):
        old_frame.unlink()
    for spec in frames:
        (output_dir / spec["name"]).write_text(svg_for(spec), encoding="utf-8")

    dump_jsonl(output_dir / "items.jsonl", items)
    split_rows = []
    for split in sorted({row["split"] for row in items}):
        split_items = [row["item_id"] for row in items if row["split"] == split]
        split_rows.append({"split": split, "item_count": len(split_items), "item_ids": split_items})
    family_rows = []
    for family in sorted({row["scene_family"] for row in items}):
        family_items = [row["item_id"] for row in items if row["scene_family"] == family]
        family_rows.append({"scene_family": family, "item_count": len(family_items), "item_ids": family_items})
    (output_dir / "splits.json").write_text(json.dumps(split_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "families.json").write_text(json.dumps(family_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data/vstb_v0_3_1")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    items = write_artifacts(output_dir)
    errors = validate_dataset(items, output_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"wrote {len(items)} VSTB items to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
