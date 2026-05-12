"""Run open-weight VLM baselines on Modal GPU and score them locally.

Usage:
  modal run scripts/modal_vlm_runner.py --model-id HuggingFaceTB/SmolVLM-256M-Instruct --limit 4
"""

from __future__ import annotations

import base64
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import modal


APP_NAME = "vwma-vlm-baseline"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "vstb_v0_3_1"
RUNS_DIR = ROOT / "runs"


image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch>=2.5.0",
        "torchvision>=0.20.0",
        "transformers>=4.53.0",
        "accelerate>=1.2.0",
        "pillow>=10.4.0",
        "sentencepiece>=0.2.0",
        "protobuf>=5.28.0",
        "qwen-vl-utils>=0.0.8",
    )
)
app = modal.App(APP_NAME, image=image)


def load_items(limit: int | None = None, split: str | None = None) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in (DATA_DIR / "items.jsonl").read_text(encoding="utf-8").splitlines()]
    if split:
        rows = [row for row in rows if row["split"] == split]
    if limit is not None:
        rows = rows[:limit]
    return rows


def encode_assets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    encoded: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["frame_svgs"] = [
            base64.b64encode((DATA_DIR / frame).read_bytes()).decode("ascii")
            for frame in item["frames"]
        ]
        encoded.append(row)
    return encoded


def parse_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def normalize_prediction(item: dict[str, Any], raw: str, model_id: str) -> dict[str, Any]:
    labels = item["labels"]
    parsed = parse_json_object(raw)
    answer = str(parsed.get("answer", raw)).lower()
    predicted_status = parsed.get("object_status")
    if not isinstance(predicted_status, dict):
        predicted_status = {}

    support = parsed.get("support_state_after_hypothetical")
    if support not in {"supported", "unsupported", "constrained", "not_applicable", "unknown"}:
        if "not support" in answer or "unsupported" in answer or "fall" in answer:
            support = "unsupported"
        elif "string" in answer or "attached" in answer or "hang" in answer:
            support = "constrained"
        elif "support" in answer or "stable" in answer or "held" in answer:
            support = "supported"
        else:
            support = "unknown"

    consequence = parsed.get("expected_physical_consequence")
    valid_consequences = {
        "stable_or_minor_motion",
        "falls_or_swings",
        "hangs_or_swings_not_free_fall",
        "not_applicable",
        "unknown",
    }
    if consequence not in valid_consequences:
        if "stable" in answer or "remain" in answer:
            consequence = "stable_or_minor_motion"
        elif "hang" in answer or "string" in answer:
            consequence = "hangs_or_swings_not_free_fall"
        elif "fall" in answer or "swing" in answer:
            consequence = "falls_or_swings"
        else:
            consequence = "unknown"

    hypo = parsed.get("hypothetical_consequence")
    if not isinstance(hypo, str):
        if consequence == labels["hypothetical_consequence"]:
            hypo = labels["hypothetical_consequence"]
        elif consequence != "unknown":
            hypo = consequence
        else:
            hypo = "unknown"

    relation_delta = parsed.get("relation_delta")
    if not isinstance(relation_delta, list):
        relation_delta = []

    event_order = parsed.get("event_order")
    if not isinstance(event_order, list):
        event_order = []

    hypotheses = parsed.get("hypotheses")
    if not isinstance(hypotheses, list):
        hypotheses = []

    next_view = parsed.get("next_view_request")
    if not isinstance(next_view, dict):
        next_view = {"target_uncertainty": "unknown"}

    confidence = parsed.get("confidence", 0.5)
    if not isinstance(confidence, (int, float)):
        confidence = 0.5

    accepted_false = False
    if labels.get("false_user_claim"):
        accepted_false = "shelf" in answer and "notebook" not in answer and "covered" not in answer

    return {
        "item_id": item["item_id"],
        "baseline": f"real_vlm:{model_id}",
        "raw_answer": raw,
        "relation_delta": relation_delta,
        "support_state_after_hypothetical": support,
        "hypothetical_consequence": hypo,
        "expected_physical_consequence": consequence,
        "mutated_observed_state": False,
        "object_status": predicted_status,
        "event_order": event_order,
        "identity_map": parsed.get("identity_map", {}),
        "hypotheses": hypotheses,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "next_view_request": next_view,
        "accepted_false_user_claim": accepted_false,
        "reanchor_gate_open": bool(parsed.get("reanchor_gate_open", False)),
        "explanation_refs": parsed.get("explanation_refs", []),
        "trust_allocation": parsed.get("trust_allocation", "prior_over_state"),
    }


@app.function(gpu="L4", timeout=60 * 40, volumes={"/cache": modal.Volume.from_name("vwma-hf-cache", create_if_missing=True)})
def run_vlm_remote(items: list[dict[str, Any]], model_id: str, max_new_tokens: int = 220) -> list[dict[str, Any]]:
    import torch
    from PIL import Image, ImageColor, ImageDraw
    from transformers import AutoModelForImageTextToText, AutoProcessor

    def svg_to_image(encoded_svg: str) -> Image.Image:
        raw = base64.b64decode(encoded_svg)
        root = ET.fromstring(raw)
        image = Image.new("RGB", (800, 420), ImageColor.getrgb("#f8fafc"))
        draw = ImageDraw.Draw(image)
        for element in list(root):
            tag = element.tag.rsplit("}", 1)[-1]
            attrs = element.attrib
            if tag == "rect":
                x = float(attrs.get("x", 0))
                y = float(attrs.get("y", 0))
                w = float(attrs.get("width", 0))
                h = float(attrs.get("height", 0))
                fill = attrs.get("fill", "#ffffff")
                draw.rounded_rectangle([x, y, x + w, y + h], radius=float(attrs.get("rx", 0)), fill=fill)
            elif tag == "circle":
                cx = float(attrs.get("cx", 0))
                cy = float(attrs.get("cy", 0))
                r = float(attrs.get("r", 0))
                fill = attrs.get("fill", "#ffffff")
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
            elif tag == "line":
                draw.line(
                    [
                        float(attrs.get("x1", 0)),
                        float(attrs.get("y1", 0)),
                        float(attrs.get("x2", 0)),
                        float(attrs.get("y2", 0)),
                    ],
                    fill=attrs.get("stroke", "#000000"),
                    width=int(float(attrs.get("stroke-width", 3))),
                )
        return image

    cache_dir = "/cache/huggingface"
    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir, trust_remote_code=True)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )

    predictions: list[dict[str, Any]] = []
    for item in items:
        images = [svg_to_image(svg) for svg in item["frame_svgs"]]
        prompt = f"""This is a visual question answering task over one or more ordered frames.
Answer from the images. If the image is too abstract, say what you can see and use unknown for uncertain fields.

User query: {item["query"]}

Return only compact JSON:
{{
  "answer": "...",
  "object_status": {{}},
  "relation_delta": [],
  "support_state_after_hypothetical": "supported|unsupported|constrained|not_applicable|unknown",
  "hypothetical_consequence": "...",
  "expected_physical_consequence": "stable_or_minor_motion|falls_or_swings|hangs_or_swings_not_free_fall|not_applicable|unknown",
  "event_order": [],
  "hypotheses": [],
  "confidence": 0.0,
  "next_view_request": {{"target_uncertainty": "unknown"}},
  "explanation_refs": ["image"],
  "trust_allocation": "prior_over_state"
}}"""
        content: list[dict[str, Any]] = []
        for idx in range(len(images)):
            content.append({"type": "text", "text": f"Frame {idx + 1}:"})
            content.append({"type": "image"})
        content.append({"type": "text", "text": prompt})
        messages = [{"role": "user", "content": content}]
        try:
            text = processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = processor(text=text, images=images, return_tensors="pt").to(model.device)
        except Exception:
            text = prompt
            inputs = processor(images=images, text=text, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        if "input_ids" in inputs:
            generated = generated[:, inputs["input_ids"].shape[-1] :]
        raw = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        predictions.append(normalize_prediction(item, raw, model_id))
    return predictions


@app.local_entrypoint()
def main(model_id: str = "HuggingFaceTB/SmolVLM-256M-Instruct", limit: int = 4, split: str = "", max_new_tokens: int = 220):
    items = load_items(limit=limit if limit > 0 else None, split=split or None)
    payload = encode_assets(items)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", model_id).strip("_")
    out_path = RUNS_DIR / f"real_vlm_{slug}_limit{len(items)}.jsonl"
    predictions = run_vlm_remote.remote(payload, model_id, max_new_tokens=max_new_tokens)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(out_path)
