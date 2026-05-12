# Real-Image Capture Protocol

The SVG benchmark is intentionally abstract and reproducible. The next real-data
extension should hand-photograph 10 variants each for the three highest-value
families: pen release, keys occlusion, and mug moved.

## Families

### Pen Release

Capture before-state photos where a pen is supported by one or both hands.
Variants should include:

- both hands clearly gripping the pen
- only right hand load-bearing
- right hand partially occluded
- both hands touching but only one supporting
- different pen colors and desk backgrounds

Label the counterfactual release of the left hand. The key fields are
`support_graph`, `support_delta`, `hypothetical_action`,
`hypothetical_consequence`, and `expected_physical_consequence`.

### Keys Occlusion

Capture two-frame sequences: keys visible, then keys covered by a notebook,
paper, folder, or tablet. Variants should include partial visibility and full
occlusion. Label the keys as `occluded`, not `not_present`, when visual history
supports occlusion.

### Mug Moved

Capture two-frame sequences where the same mug moves from one support surface to
another. Vary the source and destination: desk, shelf, tray, mat, box. Label the
identity-preserving relation delta, for example `mug on desk = false` and
`mug on shelf = true`.

## File Layout

```text
data/real_vstb_v0_3_1/
  images/
    pen_release_real_000_t0.jpg
    keys_occlusion_real_000_t0.jpg
    keys_occlusion_real_000_t1.jpg
    mug_moved_real_000_t0.jpg
    mug_moved_real_000_t1.jpg
  items.jsonl
```

## Labeling Rules

- Keep object IDs stable across frames.
- Use `VSTB-test-real` for real-photo evaluation items.
- Do not train gates or prompt adapters on `VSTB-test-real`.
- Preserve provenance in labels: the answer should cite visual history, not user
  claim or generic prior.
- Include `best_next_observation` whenever the current view leaves a
  load-bearing ambiguity.

## Minimum Acceptance Gate

Before running model baselines:

```bash
python3 scripts/validate_real_image_manifest.py
```

The real-image extension is not populated in this commit because it requires
actual hand-photographed images.
