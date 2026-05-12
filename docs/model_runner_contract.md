# Model Runner Contract

The benchmark intentionally separates dataset generation and scoring from model
inference. A GPU runner only has to emit prediction JSONL in the format accepted
by `scripts/evaluate_predictions.py`.

## Fixed-Model Rule

For VWMA evaluation, use the same frozen base model across responsibility
allocations:

- base model only
- base model plus visual context
- base model plus caption memory
- base model plus structured state memory
- base model plus structured state memory and gates

Do not update base model weights on VSTB evaluation splits.

## Expected Runner Inputs

A runner should read `data/vstb_v0_3_1/items.jsonl`, load the referenced frame
assets, and produce one JSON object per item with the `item_id` copied exactly.

If the runner cannot consume SVG directly, convert frames to PNG before
inference. The benchmark labels and metrics are independent of the image format
as long as the frame references in the prediction metadata point back to the
original item.

## Optional Modal GPU Shape

A Modal runner should mount this repository, run inference into a file under
`runs/`, then execute:

```bash
python3 scripts/evaluate_predictions.py \
  --predictions runs/<runner>.jsonl \
  --output runs/<runner>_report.json
```

GPU compute is not required for the seed benchmark generator, validator,
reference baselines, or scorer.
