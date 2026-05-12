# Real Open-Weight VLM Modal Results

Date: 2026-05-12

This pass used Modal GPU inference on the 100-item synthetic VSTB set. The
models were run as direct image+query baselines. They were not given gold state
labels. The runner rendered SVG frame assets to PIL images inside Modal, prompted
each model for compact JSON, normalized raw model output into the benchmark
prediction schema, and scored the predictions with
`scripts/evaluate_predictions.py`.

## Best Prompt Per Model

Each model was run with three prompt variants (`json_schema`,
`state_strict`, `adversarial_strict`). The table reports the best prompt by
overall score.

| Runner | Best Prompt | Overall | Counterfactual | Support | Relation Delta | Text Claim Resistance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `Qwen/Qwen2.5-VL-7B-Instruct` | `json_schema` | 0.2938 | 0.1200 | 0.0600 | 0.1000 | 0.9800 |
| `Qwen/Qwen2.5-VL-72B-Instruct-AWQ` | `adversarial_strict` | 0.2931 | 0.0000 | 0.3700 | 0.1000 | 0.9800 |
| `llava-hf/llava-onevision-qwen2-7b-ov-hf` | `state_strict` | 0.2827 | 0.0000 | 0.0600 | 0.1000 | 1.0000 |
| `OpenGVLab/InternVL2_5-8B` | `adversarial_strict` | 0.2821 | 0.0000 | 0.1300 | 0.1000 | 0.9600 |
| Base prior reference | n/a | 0.2569 | 0.0000 | 0.0600 | 0.1000 | 0.9000 |
| Structured-state oracle | n/a | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Full prompt-variant rows are in `runs/prompt_variant_summary.json`.

## Commands

```bash
modal run scripts/modal_vlm_runner.py \
  --model-id Qwen/Qwen2.5-VL-7B-Instruct \
  --limit 0 \
  --prompt-variant json_schema

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_json_schema_limit100.jsonl \
  --output runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_json_schema_limit100_report.json

modal run scripts/modal_vlm_runner.py \
  --model-id Qwen/Qwen2.5-VL-72B-Instruct-AWQ \
  --limit 0 \
  --gpu-tier H100 \
  --prompt-variant adversarial_strict

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ_adversarial_strict_limit100.jsonl \
  --output runs/real_vlm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ_adversarial_strict_limit100_report.json

python3 scripts/summarize_prompt_variant_reports.py runs/*_limit100_report.json \
  --output runs/prompt_variant_summary.json
```

## Runner Notes

- Qwen2.5-VL and LLaVA-OneVision use the generic
  `AutoModelForImageTextToText` path.
- InternVL2.5-8B requires its custom `AutoModel` + `model.chat` path. The Modal
  image pins `transformers==4.49.0` and includes `einops` and `timm` for the
  remote-code loader.
- `Qwen/Qwen2.5-VL-72B-Instruct-AWQ` runs on the H100 path. The Modal image
  uses `autoawq==0.2.7`; `autoawq>=0.2.9` failed with the pinned Transformers
  stack because it imports Qwen3 modules unavailable in `transformers==4.49.0`.

## Observations

- All direct VLM baselines remain close to the base-prior reference on the
  scaled synthetic benchmark after prompt selection.
- None of the completed real VLMs solved the key VWMA properties: reliable
  counterfactual state separation, typed relation deltas, frame-identical
  history use, provenance-gated false-claim resistance, or explanation
  faithfulness.
- The 72B AWQ result does not jump toward 0.50+. It remains in the same overall
  band as the 7B/8B models, strengthening the "scale alone does not solve this
  benchmark" claim for the current synthetic set.

## Artifacts

- `runs/prompt_variant_summary.json`
- `runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_*_limit100.jsonl`
- `runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_*_limit100_report.json`
- `runs/real_vlm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ_*_limit100.jsonl`
- `runs/real_vlm_Qwen_Qwen2.5-VL-72B-Instruct-AWQ_*_limit100_report.json`
- `runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_*_limit100.jsonl`
- `runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_*_limit100_report.json`
- `runs/real_vlm_OpenGVLab_InternVL2_5-8B_*_limit100.jsonl`
- `runs/real_vlm_OpenGVLab_InternVL2_5-8B_*_limit100_report.json`

Historical seed-13 runs remain in `runs/` for comparison with the earlier
prototype but should not be mixed with the 100-item results.
