# Real Open-Weight VLM Modal Results

Date: 2026-05-12

This pass used Modal GPU inference to run two real open-weight VLMs against the
13-item VSTB seed set:

- `HuggingFaceTB/SmolVLM-256M-Instruct`
- `Qwen/Qwen2.5-VL-3B-Instruct`

The models were run as direct image+query baselines. They were not given gold
state labels. The runner rendered the benchmark SVG frame assets to PIL images
inside Modal, prompted each model for compact JSON, normalized raw model output
into the benchmark prediction schema, and scored the predictions with
`scripts/evaluate_predictions.py`.

## Commands

```bash
modal run scripts/modal_vlm_runner.py \
  --model-id HuggingFaceTB/SmolVLM-256M-Instruct \
  --limit 0 \
  --max-new-tokens 220

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_HuggingFaceTB_SmolVLM-256M-Instruct_limit13.jsonl \
  --output runs/real_vlm_HuggingFaceTB_SmolVLM-256M-Instruct_limit13_report.json

modal run scripts/modal_vlm_runner.py \
  --model-id Qwen/Qwen2.5-VL-3B-Instruct \
  --limit 0 \
  --max-new-tokens 420

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_Qwen_Qwen2.5-VL-3B-Instruct_limit13.jsonl \
  --output runs/real_vlm_Qwen_Qwen2.5-VL-3B-Instruct_limit13_report.json
```

## Aggregate Scores

| Runner | Overall | Counterfactual | Support | Relation Delta | Text Claim Resistance |
| --- | ---: | ---: | ---: | ---: | ---: |
| SmolVLM-256M-Instruct | 0.2811 | 0.0000 | 0.0769 | 0.1538 | 1.0000 |
| Qwen2.5-VL-3B-Instruct | 0.2568 | 0.0000 | 0.1538 | 0.1538 | 0.9231 |
| Base prior reference | 0.2600 | 0.0000 | 0.0000 | 0.1538 | 0.9231 |
| Structured-state oracle | 0.9931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Observations

- SmolVLM produced short free-form answers rather than strict JSON, but it did
  answer some visual questions directly. Example: it correctly said the cable
  was not plugged in, but it did not emit typed deltas.
- Qwen2.5-VL-3B followed the JSON format much better, but its semantics still
  collapsed to object appearance and generic priors. It often labeled occluded
  objects as missing and accepted visual-symbol substitutions such as "red
  circle" rather than the benchmark object identity.
- Neither model solved counterfactual state separation, frame-identical history
  pairs, provenance-gated false-claim resistance, or typed explanation
  faithfulness.
- The low scores are expected for a direct VLM baseline on abstract synthetic
  SVG frames. The result still supports the benchmark's purpose: a direct
  image+query VLM is not equivalent to a mutable state model with deltas,
  hypotheses, and gates.

## Artifacts

- `runs/real_vlm_HuggingFaceTB_SmolVLM-256M-Instruct_limit13.jsonl`
- `runs/real_vlm_HuggingFaceTB_SmolVLM-256M-Instruct_limit13_report.json`
- `runs/real_vlm_Qwen_Qwen2.5-VL-3B-Instruct_limit13.jsonl`
- `runs/real_vlm_Qwen_Qwen2.5-VL-3B-Instruct_limit13_report.json`
- Modal runs:
  - `https://modal.com/apps/auroratherapeutics-inc/main/ap-bTuzcPJrVQZNTSs0LLd7sa`
  - `https://modal.com/apps/auroratherapeutics-inc/main/ap-D2GOx5vNILE0emOZqgzWJC`
