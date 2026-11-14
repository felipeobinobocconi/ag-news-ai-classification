# Text Restoration Verification — preparation workbook

- Script: `src/02_restore_preparation_texts.py`
- Run date: 2026-11-12
- **Deviation from the original authorization (documented):** texts were
  restored from the raw Parquet via `preparation_manifest.csv` instead of
  from `preparation_20.csv`, because the CSV was found corrupted after
  creation (re-saved as semicolon-delimited, unquoted data at 12:23:34 on
  2026-11-12, after the labelled workbook was saved). This recovery path was
  authorized by the user. The corrupted CSV was not modified.
- Inputs (read-only, not modified):
  - `data\raw\test-00000-of-00001.parquet` (text column only; original dataset labels never read)
  - `data\derived\preparation_manifest.csv` (item_id -> source_row_position; unchanged since creation)
  - `data\derived\preparation_20_labelled.xlsx` (human annotations; some texts truncated at semicolons during Excel import)
- Output: `data\derived\preparation_20_labelled_restored.xlsx` (texts restored from the raw source; annotations preserved as entered)
- Matching: strictly by `item_id`; source positions validated as unique,
  zero-based indices within range before any change.
- Items whose text differed between workbook and raw source (text restored):
  **prep_001, prep_003, prep_005, prep_011, prep_015, prep_016, prep_017** (7 of 20; 13 items already matched exactly)
- Annotation columns preserved verbatim: human_label, human_confidence,
  uncertainty_reason (compared before and after for every item).
- News texts and annotation values are not displayed in this report, by
  design.

## Checks (all must pass)

- [x] manifest has exactly 20 rows
- [x] manifest item_ids unique
- [x] all source positions are valid zero-based indices in range
- [x] manifest source positions unique
- [x] workbook has exactly 20 rows
- [x] workbook item_ids unique
- [x] identical item_id sets in manifest and workbook
- [x] restored workbook has exactly 20 rows
- [x] 20 unique item IDs
- [x] item_id set unchanged after restore
- [x] all 20 texts exactly match the raw source texts
- [x] human annotations unchanged for every item
- [x] changed items' annotation values identical before/after

## Integrity notes

- No original dataset labels were read at any point.
- No classification model was called; no evaluation texts were selected.
- The codebook status is unchanged (DRAFT).
- Script 01 was not rerun; the damaged CSV was left as found.
