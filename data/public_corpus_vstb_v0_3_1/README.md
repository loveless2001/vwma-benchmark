# Public-Corpus Real-Frame VSTB

This directory contains real-frame variants derived from public corpora with
explicit provenance. The split is intentionally separate from the synthetic
benchmark and from hand-photographed real images:

- split: `VSTB-test-real-public`
- seed family: `object_moved_public`
- generator: `scripts/prepare_public_corpus_vstb.py`
- validator: `scripts/validate_public_corpus_manifest.py`

The current seed uses the Perception Test sample videos because the dataset
materials are released under CC-BY-4.0 and the source includes action and
tracking annotations. Raw downloaded archives and extracted videos are kept in
`cache/`, which is ignored by git. The committed artifacts are derived still
frames, labels, and source provenance.

Run:

```bash
python3 scripts/prepare_public_corpus_vstb.py
python3 scripts/validate_public_corpus_manifest.py
```

Every item must include a `source_provenance` object with the source dataset,
license, source video ID, source frame IDs, and redistribution note. This keeps
public-corpus examples auditable and prevents mixing them with hand-captured
photos.
