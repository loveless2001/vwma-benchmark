# Real-Image Extension Status

Target real-photo extension:

- `pen_release_real`: 10 items
- `keys_occlusion_real`: 10 items
- `mug_moved_real`: 10 items
- split: `VSTB-test-real`

The repository contains the capture protocol and validator, but the 30
hand-photographed items are not populated yet because no actual local photo
captures were available in this workspace. Do not substitute generated images
or public-corpus frames for this split; those belong in separate splits.

Current real-image-adjacent artifacts:

- `data/real_vstb_v0_3_1/README.md`
- `docs/real_image_capture_protocol.md`
- `scripts/validate_real_image_manifest.py`
- `data/public_corpus_vstb_v0_3_1/` for the separate public-corpus real-frame
  seed split

Once photos are captured, place image files under
`data/real_vstb_v0_3_1/images/`, add `data/real_vstb_v0_3_1/items.jsonl`, then
run:

```bash
python3 scripts/validate_real_image_manifest.py --strict-count
```
