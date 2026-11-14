# Manual Annotation Verification — evaluation workbook

- Script: `src/04_validate_freeze_manual_labels.py`
- Run date: 2026-11-12
- Labelled workbook: `data\derived\evaluation_200_labelled.xlsx` (validated only; no annotation changed)
- Original dataset labels: never read. The student's categories were not
  judged; only validity and consistency of the annotations were checked.

## Counts

- Items: 200
- human_confidence: confident = 154, uncertain = 46
- human_label values (counts only, no judgment): 0 -> 73, 1 -> 53, 2 -> 52, 3 -> 22
- Invalid labels: 0
- Invalid confidence values: 0
- Uncertain items without a nonblank reason: 0
- Items whose text matched `evaluation_200.xlsx` exactly: 200
- Items whose text matched the raw source text column exactly: 200
- Source-row overlap with preparation: 0

## Checks

- [x] labelled workbook has exactly 200 rows
- [x] 200 unique item IDs in labelled workbook
- [x] labelled item_id set matches evaluation_manifest.csv exactly
- [x] all 200 human_label values valid (0-3)
- [x] all 200 human_confidence values valid (confident/uncertain)
- [x] every uncertain item has a nonblank uncertainty_reason
- [x] texts match evaluation_200.xlsx by item_id for all 200 items
- [x] texts match the raw source text column via the manifest for all 200 items
- [x] zero source-row overlap with preparation_manifest.csv
- [x] exactly one SHA-256 recorded in the codebook freeze note
- [x] current codebook.md hash matches the freeze note

## Outcome

- All checks passed: YES.
- Manual reference frozen; see `results/manual_labels_freeze_note.md`.
