# Public-Corpus Source Notes

The public-corpus split is a real-frame supplement, not a replacement for the
canonical synthetic benchmark. Its purpose is to test whether SVG failures also
appear on redistributable real video frames while keeping source provenance
auditable.

## Active Seed

Perception Test is currently used because its repository documents
redistributable materials under CC-BY-4.0, provides direct sample-video and
sample-annotation downloads, and includes action/object annotations that can be
mapped into VSTB-style frame-pair items.

Generated artifacts:

- `data/public_corpus_vstb_v0_3_1/items.jsonl`
- `data/public_corpus_vstb_v0_3_1/images/*.jpg`
- split: `VSTB-test-real-public`
- family: `object_moved_public`

Raw downloads and extracted MP4 files are cache-only under
`data/public_corpus_vstb_v0_3_1/cache/` and are ignored by git.

## Candidate Sources

BridgeData V2 is the next best source for tabletop manipulation and
pick/place-style real frames. It is listed as CC-BY-4.0 by the project page, but
it needs a separate loader for trajectory format.

Ego4D is conceptually strong for episodic memory, object location, and
hand-object state changes. It is license-gated, so extracted frames should not
be committed until redistribution under the signed license is reviewed.

## Discipline

Every public-corpus item must include:

- `source_provenance.dataset`
- `source_provenance.dataset_url`
- `source_provenance.source_split`
- `source_provenance.source_video_id`
- `source_provenance.source_frames`
- `source_provenance.license`
- `source_provenance.redistribution`

Public-corpus examples must stay in `VSTB-test-real-public` so they are not
mixed with hand-photographed real images or synthetic adversarial pairs.
