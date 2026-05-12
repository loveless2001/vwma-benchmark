from pathlib import Path
from collections import Counter, defaultdict

from vwma_benchmark.baselines import (
    base_model_prior,
    state_cleared_ablation,
    structured_state_oracle,
)
from vwma_benchmark.metrics import evaluate
from vwma_benchmark.schema import load_jsonl, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "data" / "vstb_v0_3_1" / "items.jsonl"
FRAMES = ROOT / "data" / "vstb_v0_3_1"
PUBLIC_ITEMS = ROOT / "data" / "public_corpus_vstb_v0_3_1" / "items.jsonl"
PUBLIC_FRAMES = ROOT / "data" / "public_corpus_vstb_v0_3_1"


def test_dataset_validates_and_covers_required_splits():
    items = load_jsonl(ITEMS)
    assert len(items) == 100
    assert validate_dataset(items, FRAMES) == []
    splits = {item["split"] for item in items}
    assert "VSTB-train-synth" in splits
    assert "VSTB-dev-synth" in splits
    assert "VSTB-test-synth" in splits
    assert "VSTB-test-adversarial" in splits
    by_family = {}
    for item in items:
        by_family.setdefault(item["scene_family"], []).append(item)
    assert len(by_family) == 10
    assert {len(rows) for rows in by_family.values()} == {10}


def test_family_and_split_balance_are_stable():
    items = load_jsonl(ITEMS)
    assert Counter(item["split"] for item in items) == {
        "VSTB-train-synth": 10,
        "VSTB-dev-synth": 10,
        "VSTB-test-synth": 48,
        "VSTB-test-adversarial": 32,
    }
    for family in {item["scene_family"] for item in items}:
        rows = [item for item in items if item["scene_family"] == family]
        counts = Counter(item["split"] for item in rows)
        assert counts["VSTB-train-synth"] == 1
        assert counts["VSTB-dev-synth"] == 1
        assert counts["VSTB-test-synth"] in {0, 8}
        assert counts["VSTB-test-adversarial"] in {0, 8}


def test_no_frame_leakage_from_train_or_dev_to_test_splits():
    items = load_jsonl(ITEMS)
    by_frame = defaultdict(list)
    for item in items:
        for frame in item["frames"]:
            by_frame[frame].append(item)

    train_dev = {"VSTB-train-synth", "VSTB-dev-synth"}
    test = {"VSTB-test-synth", "VSTB-test-adversarial"}
    for frame, rows in by_frame.items():
        splits = {row["split"] for row in rows}
        assert not (splits & train_dev and splits & test), frame


def test_no_gold_consequence_string_is_leaked_in_query_or_captions():
    items = load_jsonl(ITEMS)
    for item in items:
        visible_text = " ".join(
            [item["query"], *item.get("frame_captions", []), *item.get("history", [])]
        ).lower()
        for key in ("expected_physical_consequence", "hypothetical_consequence"):
            value = str(item["labels"][key]).lower()
            if value not in {"not_applicable", "unknown"}:
                assert value not in visible_text, (item["item_id"], key, value)


def test_benchmark_contains_required_adversarial_probes():
    items = load_jsonl(ITEMS)
    tags = {tag for item in items for tag in item["adversarial_tags"]}
    assert "frame_identical_pair" in tags
    assert "provenance_corruption" in tags
    assert "false_user_claim" in tags
    assert "identity_swap" in tags
    pair = [item for item in items if "frame_identical_pair" in item["adversarial_tags"]]
    assert len(pair) == 10
    by_final = {}
    for item in pair:
        by_final.setdefault(item["frames"][-1], []).append(item)
    assert len(by_final) == 5
    for rows in by_final.values():
        assert len(rows) == 2
        assert rows[0]["labels"]["expected_physical_consequence"] != rows[1]["labels"]["expected_physical_consequence"]


def test_oracle_scores_above_prior_baseline():
    items = load_jsonl(ITEMS)
    oracle_report = evaluate(items, [structured_state_oracle(item) for item in items])
    prior_report = evaluate(items, [base_model_prior(item) for item in items])
    assert oracle_report["aggregate"]["overall"] > 0.95
    assert prior_report["aggregate"]["overall"] < oracle_report["aggregate"]["overall"]
    assert (
        oracle_report["aggregate"]["counterfactual_accuracy"]
        > prior_report["aggregate"]["counterfactual_accuracy"]
    )


def test_state_cleared_ablation_loses_adversarial_state_use():
    items = load_jsonl(ITEMS)
    oracle_report = evaluate(items, [structured_state_oracle(item) for item in items])
    cleared_report = evaluate(items, [state_cleared_ablation(item) for item in items])
    assert (
        oracle_report["by_split"]["VSTB-test-adversarial"]["overall"]
        > cleared_report["by_split"]["VSTB-test-adversarial"]["overall"]
    )


def test_public_corpus_seed_split_has_provenance_and_frames():
    items = load_jsonl(PUBLIC_ITEMS)
    assert len(items) == 8
    assert validate_dataset(items, PUBLIC_FRAMES) == []
    assert {item["split"] for item in items} == {"VSTB-test-real-public"}
    assert {item["scene_family"] for item in items} == {"object_moved_public"}
    for item in items:
        provenance = item["source_provenance"]
        assert provenance["dataset"] == "Perception Test"
        assert provenance["license"].startswith("CC-BY-4.0")
        assert len(provenance["source_frames"]) == 2
        assert all(frame.endswith(".jpg") for frame in item["frames"])
