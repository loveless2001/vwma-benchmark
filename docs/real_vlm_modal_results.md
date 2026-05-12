# Real Open-Weight VLM Modal Results

Date: 2026-05-12

This pass used Modal GPU inference on the 100-item synthetic VSTB set. The
models were run as direct image+query baselines. They were not given gold state
labels. The runner rendered SVG frame assets to PIL images inside Modal, prompted
each model for compact JSON, normalized raw model output into the benchmark
prediction schema, and scored the predictions with
`scripts/evaluate_predictions.py`.

## Completed 100-Item Runs

| Runner | Overall | Counterfactual | Support | Relation Delta | Text Claim Resistance |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Qwen/Qwen2.5-VL-7B-Instruct` | 0.2912 | 0.1200 | 0.0600 | 0.1000 | 0.9800 |
| `llava-hf/llava-onevision-qwen2-7b-ov-hf` | 0.2635 | 0.0100 | 0.1700 | 0.1000 | 0.9600 |
| `OpenGVLab/InternVL2_5-8B` | 0.2781 | 0.0000 | 0.1200 | 0.1000 | 0.9700 |
| Base prior reference | 0.2569 | 0.0000 | 0.0600 | 0.1000 | 0.9000 |
| Structured-state oracle | 0.9931 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Commands

```bash
modal run scripts/modal_vlm_runner.py \
  --model-id Qwen/Qwen2.5-VL-7B-Instruct \
  --limit 0 \
  --max-new-tokens 320

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_limit100.jsonl \
  --output runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_limit100_report.json

modal run scripts/modal_vlm_runner.py \
  --model-id llava-hf/llava-onevision-qwen2-7b-ov-hf \
  --limit 0 \
  --max-new-tokens 320

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_limit100.jsonl \
  --output runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_limit100_report.json

modal run scripts/modal_vlm_runner.py \
  --model-id OpenGVLab/InternVL2_5-8B \
  --limit 0 \
  --max-new-tokens 220

python3 scripts/evaluate_predictions.py \
  --predictions runs/real_vlm_OpenGVLab_InternVL2_5-8B_limit100.jsonl \
  --output runs/real_vlm_OpenGVLab_InternVL2_5-8B_limit100_report.json
```

## Runner Notes

- Qwen2.5-VL and LLaVA-OneVision use the generic
  `AutoModelForImageTextToText` path.
- InternVL2.5-8B requires its custom `AutoModel` + `model.chat` path. The Modal
  image pins `transformers==4.49.0` and includes `einops` and `timm` for the
  remote-code loader.
- `Qwen/Qwen2.5-VL-72B-Instruct` remains a separate heavier run. A practical
  path should use a quantized 72B checkpoint, such as
  `Qwen/Qwen2.5-VL-72B-Instruct-AWQ`, on larger GPU hardware rather than the
  current L4/H100 single-model BF16 path.

## Observations

- All direct VLM baselines remain close to the base-prior reference on the
  scaled synthetic benchmark.
- None of the completed real VLMs solved the key VWMA properties: reliable
  counterfactual state separation, typed relation deltas, frame-identical
  history use, provenance-gated false-claim resistance, or explanation
  faithfulness.
- The 7B/8B results currently support the "direct VLMs fail similarly" version
  of the scaling claim on this synthetic set. A 72B quantized run is still needed
  before making a strong all-size claim.

## Artifacts

- `runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_limit100.jsonl`
- `runs/real_vlm_Qwen_Qwen2.5-VL-7B-Instruct_limit100_report.json`
- `runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_limit100.jsonl`
- `runs/real_vlm_llava-hf_llava-onevision-qwen2-7b-ov-hf_limit100_report.json`
- `runs/real_vlm_OpenGVLab_InternVL2_5-8B_limit100.jsonl`
- `runs/real_vlm_OpenGVLab_InternVL2_5-8B_limit100_report.json`

Historical seed-13 runs remain in `runs/` for comparison with the earlier
prototype but should not be mixed with the 100-item results.
