# VWMA Visual State Transition Benchmark

This repository is a benchmark package for the Visual World-Model Adapter
(VWMA) spec v0.3.1-alpha. It tests whether a fixed frozen LLM/VLM improves when
current-world belief is moved into an external mutable world state with typed
deltas, counterfactual state, hypotheses, provenance, and gates.

The current synthetic benchmark is deterministic: 10 scenario families with 10
variants each, for 100 items total. It is meant to validate the benchmark
contract and runner before expanding into hand-photographed real-image variants.
The harness accepts predictions from any model or agent as JSONL, so Modal GPU
runs can be attached later without changing the scoring format.

## Artifacts

- `data/vstb_v0_3_1/items.jsonl`: benchmark items and gold labels.
- `data/vstb_v0_3_1/frames/*.svg`: simple visual frame assets.
- `data/vstb_v0_3_1/splits.json`: split manifest.
- `data/vstb_v0_3_1/families.json`: 10-family manifest.
- `data/real_vstb_v0_3_1/`: real-image intake directory.
- `scripts/generate_vstb.py`: deterministic dataset generator.
- `scripts/validate_dataset.py`: schema and frame-asset validator.
- `scripts/run_baselines.py`: reference baselines and oracle controls.
- `scripts/evaluate_predictions.py`: metric runner for JSONL predictions.
- `docs/completion_audit.md`: spec-to-artifact completion audit.
- `scripts/modal_vlm_runner.py`: Modal GPU runner for open-weight VLM baselines.
- `docs/real_vlm_modal_results.md`: scored real-VLM baseline results.
- `docs/real_image_capture_protocol.md`: capture and labeling protocol for real photos.

## Run

```bash
python3 scripts/generate_vstb.py
python3 scripts/validate_dataset.py
python3 scripts/run_baselines.py --baseline structured_state_oracle --output runs/oracle_predictions.jsonl
python3 scripts/evaluate_predictions.py --predictions runs/oracle_predictions.jsonl --output runs/oracle_report.json
python3 scripts/compare_reports.py \
  --base-report runs/base_model_prior_report.json \
  --state-report runs/oracle_report.json \
  --state-cleared-report runs/state_cleared_report.json \
  --no-gates-report runs/structured_state_no_gates_report.json \
  --output runs/required_deltas.json
python3 -m pytest
```

After hand-photographed real-image labels are added, validate them with:

```bash
python3 scripts/validate_real_image_manifest.py --strict-count
```

## Prediction Format

Each prediction row must include `item_id` and may include:

- `relation_delta`
- `support_state_after_hypothetical`
- `hypothetical_consequence`
- `expected_physical_consequence`
- `mutated_observed_state`
- `object_status`
- `event_order`
- `identity_map`
- `hypotheses`
- `confidence`
- `next_view_request`
- `accepted_false_user_claim`
- `reanchor_gate_open`
- `explanation_refs`
- `trust_allocation`

The structured-state oracle in `vwma_benchmark/baselines.py` is the reference
for the complete shape.

## Metrics

The evaluator reports the spec-required quantities that can be scored from the
seed set:

- relation-delta accuracy
- support-state accuracy
- counterfactual accuracy without mutating observed state
- occlusion/disappearance accuracy
- event-order accuracy
- object-identity consistency
- multi-hypothesis calibration
- uncertainty calibration
- useful next-view rate
- text-claim resistance
- re-anchor recovery
- explanation faithfulness
- trust-allocation correctness

State-use delta, gate-use delta, and fixed-model delta are produced by comparing
reports from different prediction files. The included `state_cleared_ablation`
and `caption_memory` baselines are controls for that comparison.
