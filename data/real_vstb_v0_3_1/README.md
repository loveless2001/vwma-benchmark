# Real-Image VSTB Intake

This directory is reserved for hand-photographed real-image variants of the top
three scenario families:

- `pen_release_real`
- `keys_occlusion_real`
- `mug_moved_real`

Expected target: 10 labeled variants per family, 30 items total.

Place image files under `images/` and create `items.jsonl` using the same schema
as `data/vstb_v0_3_1/items.jsonl`. The validator is:

```bash
python3 scripts/validate_real_image_manifest.py
```

The benchmark scorer can evaluate real-image predictions unchanged once a model
runner emits prediction JSONL with matching `item_id` values.
