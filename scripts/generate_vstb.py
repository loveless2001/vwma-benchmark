#!/usr/bin/env python3
"""Generate the synthetic VSTB v0.3.1 benchmark seed set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vwma_benchmark.schema import dump_jsonl, validate_dataset


def rel(subject: str, predicate: str, object_: str, value: bool = True) -> dict[str, Any]:
    return {"subject": subject, "predicate": predicate, "object": object_, "value": value}


def frame(name: str, title: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
    return {"name": f"frames/{name}.svg", "title": title, "elements": elements}


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
        "support_graph": {
            "current": support_graph or [],
            "after_hypothetical": support_after,
        },
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
    item_id: str,
    split: str,
    scene_family: str,
    query: str,
    frames: list[str],
    captions: list[str],
    history: list[str],
    item_labels: dict[str, Any],
    tags: list[str],
    focus: list[str],
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "split": split,
        "scene_family": scene_family,
        "query": query,
        "frames": frames,
        "frame_captions": captions,
        "history": history,
        "labels": item_labels,
        "adversarial_tags": tags,
        "evaluation_focus": focus,
        "schema_version": "v0.3.1-alpha",
    }


def build_frames() -> list[dict[str, Any]]:
    hand_pen = [
        {"type": "rect", "id": "left_hand", "x": 120, "y": 220, "w": 150, "h": 44, "fill": "#c79a65"},
        {"type": "rect", "id": "right_hand", "x": 530, "y": 220, "w": 150, "h": 44, "fill": "#c79a65"},
        {"type": "rect", "id": "pen", "x": 245, "y": 235, "w": 310, "h": 14, "fill": "#244b9b"},
    ]
    return [
        frame("pen_two_hands_t0", "pen supported by two hands", hand_pen),
        frame("pen_left_released_t1", "left hand released, right hand supports pen", [
            {"type": "rect", "id": "left_hand", "x": 90, "y": 140, "w": 140, "h": 44, "fill": "#c79a65"},
            {"type": "rect", "id": "right_hand", "x": 530, "y": 220, "w": 150, "h": 44, "fill": "#c79a65"},
            {"type": "rect", "id": "pen", "x": 245, "y": 235, "w": 310, "h": 14, "fill": "#244b9b"},
        ]),
        frame("pen_occluded_same_final", "occluded right side, final frame shared by two histories", [
            {"type": "rect", "id": "left_hand", "x": 92, "y": 145, "w": 140, "h": 44, "fill": "#c79a65"},
            {"type": "rect", "id": "pen", "x": 245, "y": 235, "w": 310, "h": 14, "fill": "#244b9b"},
            {"type": "rect", "id": "occluder", "x": 500, "y": 190, "w": 190, "h": 130, "fill": "#4b5563"},
        ]),
        frame("keys_visible_t0", "keys on desk", [
            {"type": "circle", "id": "keyring", "cx": 230, "cy": 260, "r": 28, "fill": "#f2c94c"},
            {"type": "rect", "id": "key", "x": 250, "y": 254, "w": 95, "h": 12, "fill": "#f2c94c"},
        ]),
        frame("keys_under_notebook_t1", "keys covered by notebook", [
            {"type": "circle", "id": "keyring_partial", "cx": 230, "cy": 260, "r": 28, "fill": "#f2c94c"},
            {"type": "rect", "id": "notebook", "x": 205, "y": 220, "w": 230, "h": 145, "fill": "#8cc7a1"},
        ]),
        frame("cup_visible_train_t0", "training cup visible", [
            {"type": "circle", "id": "cup", "cx": 310, "cy": 255, "r": 45, "fill": "#ef476f"},
            {"type": "rect", "id": "paper", "x": 500, "y": 220, "w": 120, "h": 90, "fill": "#f8fafc"},
        ]),
        frame("cup_under_paper_train_t1", "training cup partly covered by paper", [
            {"type": "circle", "id": "cup_partial", "cx": 310, "cy": 255, "r": 45, "fill": "#ef476f"},
            {"type": "rect", "id": "paper", "x": 270, "y": 225, "w": 190, "h": 120, "fill": "#f8fafc"},
        ]),
        frame("mug_desk_t0", "mug on desk", [
            {"type": "rect", "id": "desk", "x": 90, "y": 285, "w": 620, "h": 55, "fill": "#b08968"},
            {"type": "circle", "id": "mug", "cx": 245, "cy": 255, "r": 42, "fill": "#e4572e"},
        ]),
        frame("mug_shelf_t1", "mug moved to shelf", [
            {"type": "rect", "id": "desk", "x": 90, "y": 285, "w": 620, "h": 55, "fill": "#b08968"},
            {"type": "rect", "id": "shelf", "x": 90, "y": 120, "w": 620, "h": 35, "fill": "#6d6875"},
            {"type": "circle", "id": "mug", "cx": 560, "cy": 92, "r": 42, "fill": "#e4572e"},
        ]),
        frame("cable_plugged_t0", "cable plugged in", [
            {"type": "rect", "id": "socket", "x": 550, "y": 210, "w": 70, "h": 70, "fill": "#d9d9d9"},
            {"type": "line", "id": "cable", "x1": 160, "y1": 245, "x2": 552, "y2": 245, "stroke": "#111827", "sw": 10},
        ]),
        frame("cable_unplugged_t1", "cable unplugged", [
            {"type": "rect", "id": "socket", "x": 550, "y": 210, "w": 70, "h": 70, "fill": "#d9d9d9"},
            {"type": "line", "id": "cable", "x1": 160, "y1": 245, "x2": 500, "y2": 310, "stroke": "#111827", "sw": 10},
        ]),
        frame("drawer_closed_t0", "drawer closed", [
            {"type": "rect", "id": "drawer", "x": 210, "y": 150, "w": 370, "h": 160, "fill": "#9c6644"},
            {"type": "circle", "id": "handle", "cx": 395, "cy": 230, "r": 12, "fill": "#f1c453"},
        ]),
        frame("drawer_open_t1", "drawer opened", [
            {"type": "rect", "id": "cabinet", "x": 210, "y": 150, "w": 370, "h": 160, "fill": "#7f5539"},
            {"type": "rect", "id": "drawer", "x": 250, "y": 205, "w": 370, "h": 125, "fill": "#9c6644"},
            {"type": "circle", "id": "handle", "cx": 435, "cy": 268, "r": 12, "fill": "#f1c453"},
        ]),
        frame("string_attached_t0", "object attached by string", [
            {"type": "line", "id": "string", "x1": 400, "y1": 80, "x2": 400, "y2": 230, "stroke": "#111827", "sw": 4},
            {"type": "circle", "id": "weight", "cx": 400, "cy": 270, "r": 42, "fill": "#7c3aed"},
            {"type": "rect", "id": "hand", "x": 280, "y": 242, "w": 100, "h": 42, "fill": "#c79a65"},
        ]),
        frame("similar_blocks_before", "similar objects before swap", [
            {"type": "rect", "id": "red_block_A", "x": 190, "y": 230, "w": 95, "h": 95, "fill": "#d62828"},
            {"type": "rect", "id": "red_block_B", "x": 500, "y": 230, "w": 95, "h": 95, "fill": "#d62828"},
        ]),
        frame("similar_blocks_cross", "similar objects crossing paths", [
            {"type": "rect", "id": "red_block_A", "x": 330, "y": 205, "w": 95, "h": 95, "fill": "#d62828"},
            {"type": "rect", "id": "red_block_B", "x": 370, "y": 255, "w": 95, "h": 95, "fill": "#d62828"},
        ]),
        frame("similar_blocks_after", "similar objects after ambiguous swap", [
            {"type": "rect", "id": "red_block_A_or_B", "x": 190, "y": 230, "w": 95, "h": 95, "fill": "#d62828"},
            {"type": "rect", "id": "red_block_B_or_A", "x": 500, "y": 230, "w": 95, "h": 95, "fill": "#d62828"},
        ]),
        frame("camera_left_t0", "camera view left", [
            {"type": "rect", "id": "mug", "x": 330, "y": 230, "w": 85, "h": 85, "fill": "#e4572e"},
            {"type": "rect", "id": "background_mark", "x": 70, "y": 95, "w": 45, "h": 45, "fill": "#64748b"},
        ]),
        frame("camera_right_t1", "camera moved right, object static", [
            {"type": "rect", "id": "mug", "x": 250, "y": 230, "w": 85, "h": 85, "fill": "#e4572e"},
            {"type": "rect", "id": "background_mark", "x": 10, "y": 95, "w": 45, "h": 45, "fill": "#64748b"},
        ]),
        frame("depth_support_misleading", "2D overlap but depth shows no support", [
            {"type": "rect", "id": "hand_far", "x": 300, "y": 225, "w": 150, "h": 42, "fill": "#c79a65"},
            {"type": "circle", "id": "ball_near", "cx": 390, "cy": 245, "r": 38, "fill": "#06b6d4"},
            {"type": "line", "id": "depth_axis", "x1": 585, "y1": 100, "x2": 650, "y2": 310, "stroke": "#111827", "sw": 3},
        ]),
    ]


def build_items() -> list[dict[str, Any]]:
    return [
        item(
            "vstb_train_cup_occlusion_000",
            "VSTB-train-synth",
            "training_occlusion_state_transition",
            "Is the cup still there?",
            ["frames/cup_visible_train_t0.svg", "frames/cup_under_paper_train_t1.svg"],
            ["A cup is visible on the desk.", "A paper covers the cup area; part of the cup remains visible."],
            ["cup visible", "paper moved over cup"],
            labels(
                objects=["cup", "paper"],
                object_status={"cup": "occluded", "paper": "visible"},
                relation_state=[rel("paper", "covering", "cup")],
                relation_delta=[rel("paper", "covering", "cup", True)],
                event_type=["occlusion"],
                event_order=["cup_visible", "paper_covers_cup"],
                target_uncertainty="cup_exact_position",
                suggested_action="lift the paper to re-ground the cup state",
                required_refs=["B_t", "Delta_B_t", "provenance"],
            ),
            ["train_synth", "occlusion_vs_disappearance"],
            ["occlusion/disappearance accuracy", "relation-delta accuracy"],
        ),
        item(
            "vstb_pen_counterfactual_001",
            "VSTB-dev-synth",
            "pen_held_by_two_hands_one_release",
            "What happens if I release only my left hand?",
            ["frames/pen_two_hands_t0.svg"],
            ["A pen is held by both the left hand and right hand."],
            ["left_hand grasping pen", "right_hand grasping pen"],
            labels(
                objects=["pen", "left_hand", "right_hand"],
                object_status={"pen": "visible", "left_hand": "visible", "right_hand": "visible"},
                relation_state=[rel("left_hand", "grasping", "pen"), rel("right_hand", "grasping", "pen")],
                relation_delta=[rel("left_hand", "grasping", "pen", False)],
                support_graph=[rel("left_hand", "supporting", "pen"), rel("right_hand", "supporting", "pen")],
                support_delta=[rel("left_hand", "supporting", "pen", False)],
                support_after="supported",
                event_type=["counterfactual_release"],
                event_order=["query_counterfactual_release_left_hand"],
                hypothetical_action="release(left_hand, pen)",
                hypothetical_consequence="right_hand_support_remains",
                expected_physical_consequence="stable_or_minor_motion",
                required_refs=["B_t", "B_t_h", "support_graph", "override_gate"],
            ),
            ["counterfactual", "support_graph"],
            ["support-state accuracy", "counterfactual accuracy", "trust-allocation error rate"],
        ),
        item(
            "vstb_keys_occlusion_002",
            "VSTB-test-synth",
            "keys_covered_by_notebook",
            "Are the keys gone?",
            ["frames/keys_visible_t0.svg", "frames/keys_under_notebook_t1.svg"],
            ["Keys are visible on the desk.", "A notebook covers the key area; part of the key ring remains visible."],
            ["keys visible on desk", "notebook moved over keys"],
            labels(
                objects=["keys", "notebook"],
                object_status={"keys": "occluded", "notebook": "visible"},
                relation_state=[rel("notebook", "covering", "keys")],
                relation_delta=[rel("notebook", "covering", "keys", True)],
                event_type=["occlusion"],
                event_order=["keys_visible", "notebook_covers_keys"],
                target_uncertainty="keys_exact_position",
                suggested_action="lift or slide the notebook enough to reveal the key ring",
                required_refs=["B_t", "Delta_B_t", "provenance", "uncertainty"],
            ),
            ["occlusion_vs_disappearance"],
            ["occlusion/disappearance accuracy", "useful next-view rate"],
        ),
        item(
            "vstb_mug_moved_003",
            "VSTB-test-synth",
            "mug_moved_from_desk_to_shelf",
            "What changed since before?",
            ["frames/mug_desk_t0.svg", "frames/mug_shelf_t1.svg"],
            ["The mug is on the desk.", "The same mug is on the shelf."],
            ["mug on desk", "mug moved to shelf"],
            labels(
                objects=["mug", "desk", "shelf"],
                object_status={"mug": "visible", "desk": "visible", "shelf": "visible"},
                relation_state=[rel("mug", "on", "shelf")],
                relation_delta=[rel("mug", "on", "desk", False), rel("mug", "on", "shelf", True)],
                event_type=["move"],
                event_order=["mug_on_desk", "mug_on_shelf"],
                required_refs=["B_t", "Delta_B_t", "identity_map"],
            ),
            ["relation_delta", "identity"],
            ["relation-delta accuracy", "object-identity consistency"],
        ),
        item(
            "vstb_cable_unplugged_004",
            "VSTB-test-synth",
            "cable_plugged_unplugged",
            "Is the cable plugged in?",
            ["frames/cable_plugged_t0.svg", "frames/cable_unplugged_t1.svg"],
            ["The cable connector is inserted into the socket.", "The cable connector is separated from the socket."],
            ["cable plugged into socket", "cable unplugged from socket"],
            labels(
                objects=["cable", "socket"],
                object_status={"cable": "visible", "socket": "visible"},
                relation_state=[rel("cable", "plugged_into", "socket", False)],
                relation_delta=[rel("cable", "plugged_into", "socket", False)],
                event_type=["relation_removed"],
                event_order=["plugged", "unplugged"],
                required_refs=["B_t", "Delta_B_t", "relation_state"],
            ),
            ["fine_relation_change"],
            ["relation-delta accuracy", "event-order accuracy"],
        ),
        item(
            "vstb_drawer_opened_005",
            "VSTB-test-synth",
            "drawer_opened_closed",
            "Is the drawer open now?",
            ["frames/drawer_closed_t0.svg", "frames/drawer_open_t1.svg"],
            ["The drawer is closed.", "The drawer is pulled open."],
            ["drawer closed", "drawer opened"],
            labels(
                objects=["drawer", "cabinet"],
                object_status={"drawer": "visible", "cabinet": "visible"},
                relation_state=[rel("drawer", "state", "open")],
                relation_delta=[rel("drawer", "state", "closed", False), rel("drawer", "state", "open", True)],
                event_type=["open"],
                event_order=["drawer_closed", "drawer_opened"],
                required_refs=["B_t", "Delta_B_t", "event_log"],
            ),
            ["event_state_persistence"],
            ["event-order accuracy", "relation-delta accuracy"],
        ),
        item(
            "vstb_string_attached_006",
            "VSTB-test-synth",
            "object_attached_by_string",
            "What happens if I release the object?",
            ["frames/string_attached_t0.svg"],
            ["The object is held by a hand and also attached to an overhead string."],
            ["weight supported by hand", "weight constrained by string"],
            labels(
                objects=["weight", "hand", "string"],
                object_status={"weight": "visible", "hand": "visible", "string": "visible"},
                relation_state=[rel("hand", "grasping", "weight"), rel("string", "attached_to", "weight")],
                relation_delta=[rel("hand", "grasping", "weight", False)],
                support_graph=[rel("hand", "supporting", "weight"), rel("string", "constraining", "weight")],
                support_delta=[rel("hand", "supporting", "weight", False)],
                support_after="constrained",
                event_type=["counterfactual_release"],
                event_order=["query_counterfactual_release_hand"],
                hypothetical_action="release(hand, weight)",
                hypothetical_consequence="string_constraint_remains",
                expected_physical_consequence="hangs_or_swings_not_free_fall",
                required_refs=["B_t_h", "support_graph", "override_gate"],
            ),
            ["counterfactual", "support_graph"],
            ["support-state accuracy", "counterfactual accuracy"],
        ),
        item(
            "vstb_similar_swap_007",
            "VSTB-test-adversarial",
            "similar_objects_swap_positions",
            "Which red block is on the left now?",
            ["frames/similar_blocks_before.svg", "frames/similar_blocks_cross.svg", "frames/similar_blocks_after.svg"],
            ["Two visually similar red blocks are separated.", "The blocks cross with heavy overlap.", "The final left/right identities are ambiguous."],
            ["red_block_A left", "red_block_B right", "tracks crossed under occlusion"],
            labels(
                objects=["red_block_A", "red_block_B"],
                object_status={"red_block_A": "visible", "red_block_B": "visible"},
                relation_state=[rel("red_block_A", "left_of", "red_block_B")],
                relation_delta=[],
                event_type=["identity_ambiguous_crossing"],
                event_order=["separated", "crossed", "ambiguous_final"],
                target_uncertainty="red_block_identity_after_crossing",
                suggested_action="show a side angle or distinctive mark before assigning identities",
                identity_map={"red_block_A": "hypothesis_left_or_right", "red_block_B": "hypothesis_right_or_left"},
                hypotheses=[
                    {"name": "A_left_B_right", "weight": 0.52},
                    {"name": "A_right_B_left", "weight": 0.48},
                ],
                required_refs=["H_t", "identity_protocol", "uncertainty"],
            ),
            ["identity_swap", "multi_hypothesis"],
            ["object-identity consistency", "multi-hypothesis calibration", "useful next-view rate"],
        ),
        item(
            "vstb_camera_motion_008",
            "VSTB-test-adversarial",
            "camera_moves_object_static",
            "Did the mug move?",
            ["frames/camera_left_t0.svg", "frames/camera_right_t1.svg"],
            ["The mug appears near the center-left of the camera view.", "The camera moved right; the mug appears shifted but stayed in place."],
            ["camera_pose left", "camera_pose right", "mug world position unchanged"],
            labels(
                objects=["mug", "camera"],
                object_status={"mug": "visible", "camera": "not_visible"},
                relation_state=[rel("mug", "world_position", "unchanged")],
                relation_delta=[rel("camera", "pose", "changed", True), rel("mug", "world_position", "unchanged", True)],
                event_type=["camera_motion"],
                event_order=["camera_left_pose", "camera_right_pose"],
                required_refs=["camera_motion", "Delta_B_t", "B_t"],
            ),
            ["camera_motion_compensation"],
            ["relation-delta accuracy", "trust-allocation error rate"],
        ),
        item(
            "vstb_false_claim_009",
            "VSTB-test-adversarial",
            "user_falsely_claims_object_disappeared",
            "I moved the keys to the shelf. Where are they?",
            ["frames/keys_visible_t0.svg", "frames/keys_under_notebook_t1.svg"],
            ["Keys are visible on the desk.", "A notebook covers the keys; no visual shelf movement occurred."],
            ["keys visible on desk", "notebook covers keys", "user claims keys moved to shelf"],
            labels(
                objects=["keys", "notebook", "shelf"],
                object_status={"keys": "occluded", "notebook": "visible", "shelf": "visible"},
                relation_state=[rel("notebook", "covering", "keys")],
                relation_delta=[rel("notebook", "covering", "keys", True)],
                event_type=["unsupported_user_claim"],
                event_order=["keys_visible", "notebook_covers_keys", "unsupported_user_claim"],
                target_uncertainty="keys_under_notebook",
                suggested_action="show under the notebook or the shelf to resolve the claim",
                provenance_validity="text_claim_unsupported_by_visual_evidence",
                false_user_claim="keys moved to shelf",
                required_refs=["provenance", "override_gate", "text_claim_resistance"],
            ),
            ["provenance_corruption", "false_user_claim"],
            ["text-claim resistance", "occlusion/disappearance accuracy"],
        ),
        item(
            "vstb_same_final_history_a_010",
            "VSTB-test-adversarial",
            "same_final_frame_different_history",
            "Will the pen stay up if the left hand lets go?",
            ["frames/pen_two_hands_t0.svg", "frames/pen_occluded_same_final.svg"],
            ["The pen was held by both hands.", "The right side is occluded, but history says right-hand support existed."],
            ["left_hand grasping pen", "right_hand grasping pen", "right side occluded"],
            labels(
                objects=["pen", "left_hand", "right_hand", "occluder"],
                object_status={"pen": "visible", "left_hand": "visible", "right_hand": "occluded", "occluder": "visible"},
                relation_state=[rel("right_hand", "grasping", "pen")],
                relation_delta=[rel("left_hand", "grasping", "pen", False)],
                support_graph=[rel("right_hand", "supporting", "pen")],
                support_delta=[rel("left_hand", "supporting", "pen", False)],
                support_after="supported",
                event_type=["counterfactual_release", "occlusion"],
                event_order=["two_hand_support_seen", "right_side_occluded", "query_release_left"],
                hypothetical_action="release(left_hand, pen)",
                hypothetical_consequence="right_hand_support_remains_probable",
                expected_physical_consequence="stable_or_minor_motion",
                target_uncertainty="right_hand_current_grip",
                suggested_action="show the right side of the pen",
                required_refs=["B_t", "H_t", "B_t_h", "support_graph"],
            ),
            ["frame_identical_pair", "state_use_over_caption"],
            ["state-ablation gap", "counterfactual accuracy"],
        ),
        item(
            "vstb_same_final_history_b_011",
            "VSTB-test-adversarial",
            "same_final_frame_different_history",
            "Will the pen stay up if the left hand lets go?",
            ["frames/pen_left_released_t1.svg", "frames/pen_occluded_same_final.svg"],
            ["The pen was not supported by the right hand in prior state.", "The right side is occluded in the same final frame."],
            ["left_hand grasping pen", "right_hand not grasping pen", "right side occluded"],
            labels(
                objects=["pen", "left_hand", "right_hand", "occluder"],
                object_status={"pen": "visible", "left_hand": "visible", "right_hand": "occluded", "occluder": "visible"},
                relation_state=[rel("right_hand", "grasping", "pen", False)],
                relation_delta=[rel("left_hand", "grasping", "pen", False)],
                support_graph=[],
                support_delta=[rel("left_hand", "supporting", "pen", False)],
                support_after="unsupported",
                event_type=["counterfactual_release", "occlusion"],
                event_order=["right_hand_not_supporting_seen", "right_side_occluded", "query_release_left"],
                hypothetical_action="release(left_hand, pen)",
                hypothetical_consequence="no_known_support_remains",
                expected_physical_consequence="falls_or_swings",
                target_uncertainty="right_hand_current_grip",
                suggested_action="show the right side of the pen",
                required_refs=["B_t", "H_t", "B_t_h", "support_graph"],
            ),
            ["frame_identical_pair", "state_use_over_caption"],
            ["state-ablation gap", "counterfactual accuracy"],
        ),
        item(
            "vstb_depth_support_012",
            "VSTB-test-adversarial",
            "depth_stress_support",
            "Is the hand supporting the ball?",
            ["frames/depth_support_misleading.svg"],
            ["In 2D the hand overlaps the ball, but depth evidence places the hand behind it."],
            ["2D overlap", "depth ordering says hand is behind ball"],
            labels(
                objects=["ball", "hand"],
                object_status={"ball": "visible", "hand": "visible"},
                relation_state=[rel("hand", "supporting", "ball", False), rel("hand", "behind", "ball", True)],
                relation_delta=[],
                support_graph=[rel("hand", "supporting", "ball", False)],
                support_after="unsupported",
                event_type=["depth_stress"],
                event_order=["depth_observed"],
                target_uncertainty="contact_vs_depth_ordering",
                suggested_action="show a side view or depth map confidence for the contact point",
                required_refs=["spatial_evidence", "support_graph", "uncertainty"],
            ),
            ["depth_stress", "support_graph"],
            ["support-state accuracy", "useful next-view rate"],
        ),
    ]


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
                f'width="{element["w"]}" height="{element["h"]}" rx="8" fill="{element["fill"]}"/>'
            )
        elif element["type"] == "circle":
            parts.append(
                f'<circle data-id="{element["id"]}" cx="{element["cx"]}" cy="{element["cy"]}" '
                f'r="{element["r"]}" fill="{element["fill"]}"/>'
            )
        elif element["type"] == "line":
            parts.append(
                f'<line data-id="{element["id"]}" x1="{element["x1"]}" y1="{element["y1"]}" '
                f'x2="{element["x2"]}" y2="{element["y2"]}" stroke="{element["stroke"]}" '
                f'stroke-width="{element["sw"]}" stroke-linecap="round"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    frames = build_frames()
    frame_dir = output_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for spec in frames:
        (output_dir / spec["name"]).write_text(svg_for(spec), encoding="utf-8")

    items = build_items()
    dump_jsonl(output_dir / "items.jsonl", items)
    split_rows = []
    for split in sorted({item["split"] for item in items}):
        split_items = [item["item_id"] for item in items if item["split"] == split]
        split_rows.append({"split": split, "item_count": len(split_items), "item_ids": split_items})
    (output_dir / "splits.json").write_text(
        json.dumps(split_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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
