# Evaluation Sampling Summary

- Script: `src/03_select_evaluation_sample.py`
- Run date: 2026-11-12
- Source: `data\raw\test-00000-of-00001.parquet`
- Source SHA-256: `71DE87EC66BC5737752A2502204DFA6D7FE9856ADE3EA444DC6317789A4F13FB` (recorded at sampling time)
- Exclusion input: `data\derived\preparation_manifest.csv` (20 preparation positions; the damaged
  `preparation_20.csv` was not used as an input)
- Sampling method: original zero-based positions preserved; the 20 preparation
  positions excluded (reason: plan.md step 2 keeps preparation and evaluation
  texts separate); `DataFrame.sample(n=200, random_state=42)` on the
  remaining pool of 7580 rows; uniform, without replacement;
  no stratification; original dataset labels never read.
- Seed: 42 (fixed)
- pandas version: 3.1.1
- Row counts: source 7600; excluded 20; pool
  7580; sampled 200.
- Outputs:
  - `data\derived\evaluation_200.xlsx` (item_id, text, human_label, human_confidence,
    uncertainty_reason; annotation fields blank; wrapped text, readable
    column widths, frozen header row)
  - `data\derived\evaluation_manifest.csv` (item_id, source_row_position)
- Item IDs: eval_001..eval_200, assigned in ascending source-row order
  (same convention as the preparation sample; documented).
- Codebook status: FROZEN v1.0 (see `results/codebook_freeze_note.md`).
- Verification: all checks passed (200 unique IDs/positions; exact text match
  to source rows; blank annotation fields; zero overlap with preparation; no
  label column in outputs).
- Original dataset labels and any AI classification remain hidden until both
  independent classifications are complete (plan.md steps 5 and 8).
