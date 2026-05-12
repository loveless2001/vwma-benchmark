#!/usr/bin/env python3
"""Build a small provenance-preserving public-corpus VSTB seed split.

The default target uses the public Perception Test sample split. Raw downloads
stay under the cache directory; the committed benchmark artifacts are the
derived still frames plus JSONL labels with source provenance.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from vwma_benchmark.schema import dump_jsonl


PERCEPTION_SAMPLE_ANNOTATIONS_URL = (
    "https://storage.googleapis.com/dm-perception-test/zip_data/sample_annotations.zip"
)
PERCEPTION_SAMPLE_VIDEOS_URL = (
    "https://storage.googleapis.com/dm-perception-test/zip_data/sample_videos.zip"
)

ROOT = Path("data/public_corpus_vstb_v0_3_1")
CACHE = ROOT / "cache"
IMAGES = ROOT / "images"
ITEMS = ROOT / "items.jsonl"

ACTION_PRIORITY = (
    "Moving object(s) around",
    "Shuffling objects",
    "Lifting something and placing it back down",
    "Putting something into something",
)
OBJECT_PRIORITY = ("mug", "cup", "glass", "spoon", "bowl", "kettle", "box")


def download(url: str, path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, path.open("wb") as handle:
        handle.write(response.read())


def read_sample_annotations(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read("sample.json"))


def extract_video(zip_path: Path, video_id: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    member = f"videos/{video_id}.mp4"
    output_path = output_dir / f"{video_id}.mp4"
    if output_path.exists():
        return output_path
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as source, output_path.open("wb") as target:
            target.write(source.read())
    return output_path


def select_action(video: dict[str, Any]) -> dict[str, Any] | None:
    actions = video.get("action_localisation", [])
    for label in ACTION_PRIORITY:
        for action in actions:
            if action.get("label") == label and len(action.get("frame_ids", [])) == 2:
                return action
    return None


def sanitize_label(label: str) -> str:
    cleaned = label.strip().replace("--", "_").replace("-", "_").replace(" ", "_")
    return cleaned or "tracked_object"


def select_object(video: dict[str, Any], action: dict[str, Any]) -> str:
    by_id = {obj.get("id"): str(obj.get("label", "")) for obj in video.get("object_tracking", [])}
    parent_labels = [
        sanitize_label(by_id[obj_id])
        for obj_id in action.get("parent_objects", [])
        if by_id.get(obj_id) and by_id[obj_id].lower() not in {"person", "table", "table-cloth", "table-cover"}
    ]
    if parent_labels:
        return "_plus_".join(parent_labels[:4])

    labels = [str(obj.get("label", "")).replace("--", " ") for obj in video.get("object_tracking", [])]
    lowered = [(label.lower(), label) for label in labels]
    for needle in OBJECT_PRIORITY:
        for low, label in lowered:
            if needle in low:
                return sanitize_label(label)
    for label in labels:
        if label and label.lower() != "person":
            return sanitize_label(label)
    return "tracked_object"


def frame_time(frame_id: int, frame_rate: float) -> float:
    return max(frame_id / frame_rate, 0.0)


def extract_frame(video_path: Path, output_path: Path, timestamp: float) -> None:
    if output_path.exists():
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-vf",
        "scale=640:-2",
        str(output_path),
    ]
    subprocess.run(command, check=True)


def make_labels(target: str, action_label: str) -> dict[str, Any]:
    target = target or "tracked_object"
    return {
        "objects": [target, "workspace"],
        "object_status": {target: "visible", "workspace": "visible"},
        "relation_state": [
            {"subject": target, "predicate": "located_in", "object": "workspace", "value": "before"}
        ],
        "relation_delta": [
            {"subject": target, "predicate": "location_changed", "object": "workspace", "value": True}
        ],
        "support_graph": {
            "current": [
                {"subject": "workspace", "predicate": "supporting", "object": target, "value": True}
            ],
            "after_hypothetical": "unchanged",
        },
        "support_delta": [],
        "event_type": ["public_corpus_object_motion"],
        "event_order": ["source_frame_before", action_label, "source_frame_after"],
        "hypothetical_action": "none",
        "hypothetical_consequence": "not_applicable",
        "expected_physical_consequence": "object_relocated_or_rearranged",
        "uncertainty": {"level": "medium", "load_bearing": ["public_corpus_action_label"]},
        "best_next_observation": {
            "suggested_action": "inspect original video clip",
            "target_uncertainty": "object trajectory",
            "expected_information_gain": 0.3,
            "cost": 0.2,
            "risk": 0.05,
        },
        "provenance_validity": "valid_public_corpus",
        "must_not_mutate_observed_state": True,
        "identity_map": {target: target},
        "hypotheses": [
            {
                "claim": f"{target} changed location during the annotated action",
                "probability": 0.8,
            }
        ],
        "requires_reanchor": False,
        "required_explanation_refs": ["public_corpus_provenance", "frame_pair", "action_annotation"],
        "trust_allocation": "source_annotation_over_prior",
    }


def build_items(args: argparse.Namespace) -> list[dict[str, Any]]:
    annotation_zip = CACHE / "perception_sample_annotations.zip"
    video_zip = CACHE / "perception_sample_videos.zip"
    download(PERCEPTION_SAMPLE_ANNOTATIONS_URL, annotation_zip, args.force_download)
    download(PERCEPTION_SAMPLE_VIDEOS_URL, video_zip, args.force_download)

    annotations = read_sample_annotations(annotation_zip)
    video_cache = CACHE / "perception_sample_videos"
    items: list[dict[str, Any]] = []
    for video_id in sorted(annotations):
        video = annotations[video_id]
        action = select_action(video)
        if action is None:
            continue
        metadata = video["metadata"]
        start_frame, end_frame = action["frame_ids"]
        if end_frame <= start_frame:
            continue
        target = select_object(video, action)
        video_path = extract_video(video_zip, video_id, video_cache)
        stem = f"perception_test_sample_{video_id}"
        before_rel = f"images/{stem}_before.jpg"
        after_rel = f"images/{stem}_after.jpg"
        extract_frame(video_path, ROOT / before_rel, frame_time(start_frame, metadata["frame_rate"]))
        extract_frame(video_path, ROOT / after_rel, frame_time(end_frame, metadata["frame_rate"]))
        item = {
            "schema_version": "v0.3.1-alpha",
            "item_id": f"vstb_public_perception_{video_id}",
            "split": "VSTB-test-real-public",
            "scene_family": "object_moved_public",
            "variant_id": len(items),
            "query": f"Did the tracked tabletop object ({target}) change location between these observations?",
            "frames": [before_rel, after_rel],
            "frame_captions": [
                f"Perception Test sample frame before action '{action['label']}'.",
                f"Perception Test sample frame after action '{action['label']}'.",
            ],
            "history": [
                "Derived from Perception Test sample video annotations.",
                f"Source video {video_id}; frames {start_frame} to {end_frame}.",
            ],
            "labels": make_labels(target, action["label"]),
            "adversarial_tags": ["public_corpus", "real_video_frame_pair", "provenance_required"],
            "evaluation_focus": [
                "relation-delta accuracy",
                "event-order accuracy",
                "explanation faithfulness",
            ],
            "source_provenance": {
                "dataset": "Perception Test",
                "dataset_url": "https://github.com/google-deepmind/perception_test",
                "source_split": "sample",
                "source_video_id": video_id,
                "source_frames": [start_frame, end_frame],
                "source_action_label": action["label"],
                "license": "CC-BY-4.0 for materials; Apache-2.0 for code",
                "redistribution": "derived still frames retained with attribution",
                "download_urls": {
                    "annotations": PERCEPTION_SAMPLE_ANNOTATIONS_URL,
                    "videos": PERCEPTION_SAMPLE_VIDEOS_URL,
                },
            },
        }
        items.append(item)
        if args.limit and len(items) >= args.limit:
            break
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ITEMS))
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("ffmpeg is required to extract public-corpus frame pairs", file=sys.stderr)
        return 1
    items = build_items(args)
    if not items:
        print("no public-corpus candidates were generated", file=sys.stderr)
        return 1
    dump_jsonl(args.output, items)
    print(f"wrote {len(items)} public-corpus items to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
