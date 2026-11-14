# Preparation Sampling Summary

- Script: `src/01_select_preparation_sample.py`
- Run date: 2026-11-12
- Source: `data\raw\test-00000-of-00001.parquet`
- Source SHA-256: `71DE87EC66BC5737752A2502204DFA6D7FE9856ADE3EA444DC6317789A4F13FB` (recorded at sampling time)
- Sampling method: `pandas.DataFrame.sample(n=20, random_state=42)` on the
  text column only; uniform, without replacement; no stratification, no
  filtering by topic, no inspection of original labels.
- Seed: 42 (fixed)
- pandas version: 3.1.1
- Source rows read: 7600 (text column only)
- Rows sampled: 20; distinct source rows: 20; unique item IDs: 20
- Original row count preserved: no rows dropped from the source file; the
  sample is a selection, not a reduction of the source.
- Outputs:
  - `data\derived\preparation_20.csv` (item_id, text, human_label, human_confidence, uncertainty_reason; annotation fields empty)
  - `data\derived\preparation_manifest.csv` (item_id, source_row_position)
- Item IDs: prep_001..prep_020, assigned in ascending source-row order
  (analysis choice, documented here).
- Sampled source positions (for excluding these rows from the future
  evaluation sample): [408, 457, 773, 1017, 1452, 1467, 2110, 2168, 2221, 2402, 2836, 2850, 2941, 4661, 4999, 6256, 6281, 6770, 7094, 7303]
- Verification: all checks passed (20 distinct rows, 20 unique IDs, exact text
  match to source rows, blank annotation fields, no label column in outputs).
