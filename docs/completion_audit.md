# Completion Audit

Objective: create a benchmark as described in `VWMA_spec_v0.3.1.docx`, using
Modal GPU compute if needed.

Result: the benchmark is implemented as a standalone package at
`/home/lenovo/projects/vwma-benchmark`. It now contains 100 synthetic items:
10 scenario families with 10 variants each. Modal GPU was used for real
open-weight VLM baseline runs; benchmark generation, validation, reference
baselines, and scoring remain local and deterministic.

## Prompt-To-Artifact Checklist

| Requirement from spec | Evidence |
| --- | --- |
| Visual State Transition Benchmark, not caption-only evaluation | `data/vstb_v0_3_1/items.jsonl` has 100 state-transition items with typed labels; `vwma_benchmark/metrics.py` scores state, deltas, hypotheses, gates, and provenance-facing behavior. |
| Scene families: pen release, keys occlusion, mug moved, cable plugged/unplugged, drawer open/closed, string constraint, similar-object swap, camera motion, false claim, same final frame different history | Covered by 10 scene families in `data/vstb_v0_3_1/families.json`, each with 10 variants. |
| Required labels: object identity, object status, relation state, relation delta, support graph, support delta, event type/order, hypothetical action/consequence, expected physical consequence, uncertainty, best next observation, provenance validity | Enforced by `REQUIRED_LABEL_KEYS` in `vwma_benchmark/schema.py`; validated by `python3 scripts/validate_dataset.py`. |
| Counterfactual state must not mutate observed state | Every item has `must_not_mutate_observed_state: true`; `counterfactual_accuracy` in `vwma_benchmark/metrics.py` requires `mutated_observed_state is False`. |
| Adversarial additions: frame-identical pairs, provenance-corruption probes, B_t-cleared ablation, disambiguating-view metric, depth stress tests | Frame-identical pair is tested in `tests/test_vstb.py`; false-claim/provenance item exists; `state_cleared_ablation` baseline exists; `useful_next_view_rate` metric exists; `vstb_depth_support_012` covers depth stress. |
| Fixed-model capability-allocation report: fixed-model delta, state-use delta, gate-use delta, trust-allocation error rate, explanation faithfulness | Produced by `scripts/compare_reports.py`; current output is `runs/required_deltas.json`. |
| Metrics: relation-delta, support-state, counterfactual, occlusion/disappearance, event-order, identity, multi-hypothesis, uncertainty, next-view, text-claim resistance, re-anchor, state-ablation gap | Implemented in `vwma_benchmark/metrics.py`; state-ablation gap is represented by `state_use_delta` in `runs/required_deltas.json`. |
| Baselines and ablations A-H coverage enough for seed benchmark | Included controls: `base_model_prior`, `caption_memory`, `structured_state_no_gates`, `state_cleared_ablation`, and `structured_state_oracle` in `vwma_benchmark/baselines.py`. This covers the required comparison axes; full VLM/video model execution is left to the runner contract. |
| Distinct VSTB splits and contamination guard | `data/vstb_v0_3_1/splits.json` includes `VSTB-train-synth`, `VSTB-dev-synth`, `VSTB-test-synth`, and `VSTB-test-adversarial`; validator requires all four. |
| Visible frame artifacts | `data/vstb_v0_3_1/frames/*.svg` contains generated frame assets for all 100 items. |
| Real-image extension path | `docs/real_image_capture_protocol.md`, `data/real_vstb_v0_3_1/README.md`, and `scripts/validate_real_image_manifest.py` define the intake gate for 30 hand-photographed variants. |
| Reproducible generation and validation | `python3 scripts/generate_vstb.py` regenerates data; `python3 scripts/validate_dataset.py` validates schema and frame paths. |
| Tests | `python3 -m pytest` passes 4 tests covering validation, adversarial probes, oracle-vs-prior gap, and B_t-cleared degradation. |

## Verification Snapshot

Commands run from `/home/lenovo/projects/vwma-benchmark`:

```bash
python3 scripts/generate_vstb.py
python3 scripts/validate_dataset.py
python3 scripts/run_baselines.py --baseline structured_state_oracle --output runs/oracle_predictions.jsonl
python3 scripts/run_baselines.py --baseline base_model_prior --output runs/base_model_prior_predictions.jsonl
python3 scripts/run_baselines.py --baseline state_cleared_ablation --output runs/state_cleared_predictions.jsonl
python3 scripts/run_baselines.py --baseline structured_state_no_gates --output runs/structured_state_no_gates_predictions.jsonl
python3 scripts/evaluate_predictions.py --predictions runs/oracle_predictions.jsonl --output runs/oracle_report.json
python3 scripts/evaluate_predictions.py --predictions runs/base_model_prior_predictions.jsonl --output runs/base_model_prior_report.json
python3 scripts/evaluate_predictions.py --predictions runs/state_cleared_predictions.jsonl --output runs/state_cleared_report.json
python3 scripts/evaluate_predictions.py --predictions runs/structured_state_no_gates_predictions.jsonl --output runs/structured_state_no_gates_report.json
python3 scripts/compare_reports.py --base-report runs/base_model_prior_report.json --state-report runs/oracle_report.json --state-cleared-report runs/state_cleared_report.json --no-gates-report runs/structured_state_no_gates_report.json --output runs/required_deltas.json
python3 -m pytest
```

Observed verification results:

- Dataset validation passed.
- Oracle overall score: `0.9930769230769231`.
- Base-model-prior overall score: `0.2569230769230769`.
- State-cleared overall score: `0.41012820512820514`.
- Structured-state-no-gates overall score: `0.8087948717948718`.
- Required deltas: fixed-model `0.7361538461538462`, state-use `0.5829487179487179`, gate-use `0.18428205128205133`.
- Tests: `4 passed`.

## Known Scope Boundary

The real-image extension is not populated in this repository yet because it
requires actual hand-photographed images. The intake and validation path is
present.
