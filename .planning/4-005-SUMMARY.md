# 4-005 Summary: ILC Detector

## What Was Done

Created `forge_agent/core/ilc_detector.py` with:

- `ILCCandidate` dataclass: `note_a_path`, `note_b_path`, `shared_terms`, `link_type`, `confidence`
- `ILCDetector` class:
  - `_QUANTITY_RE`: regex matching physical quantities with SI units (MPa, K, m/s, etc.)
  - `_PHENOMENON_RE`: regex matching named engineering phenomena (von Mises stress, Reynolds number, etc.)
  - `detect_candidates(notes, min_shared_terms=2)`: nested loop over note pairs; filters by
    `min_shared_terms`; classifies as cross-domain/reinforcing; Jaccard confidence score
  - `write_candidates(candidates)`: serialises each to YAML-frontmatter markdown under `ilc/links/`
    via `vault_manager.upsert_note(path, markdown, frontmatter)` — P1 signature verified
- `_classify()`: cross-domain when notes have different non-unknown `domain` frontmatter keys
- `_score()`: Jaccard-like `shared / (union)` clamped to `[0.0, 1.0]`

## Files Changed

| Action | File |
|---|---|
| CREATE | `forge_agent/core/ilc_detector.py` |
| CREATE | `forge_agent/tests/test_ilc_detector.py` |

## Gate Results

```
pytest forge_agent/tests/test_ilc_detector.py -v: 8 passed
pytest --tb=short -q (full suite): 425 passed
ruff check forge_agent/core/ilc_detector.py --ignore E501: 0 errors
```

## Gaps

None.
