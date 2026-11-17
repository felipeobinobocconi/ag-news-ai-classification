# Data — AG News (test split)

## Dataset identification

- Name: AG News ("AG's news topic classification dataset"), constructed by
  Xiang Zhang et al. from the AG corpus of news articles; used as a text
  classification benchmark in Zhang, Zhao & LeCun, "Character-level
  Convolutional Networks for Text Classification" (NIPS 2015). [Source:
  official dataset card, checked 2026-11-05.]
- Source: https://huggingface.co/datasets/fancyzhx/ag_news
- Split used: **test**. The card documents a test split of 7,600 rows; the
  local file has 7,600 rows (row counts match). [Assumption: the local file
  corresponds to that official split. The counts match, but byte-level
  provenance has not been verified.]

## File location and format

- Exact path: `data/raw/test-00000-of-00001.parquet`
- Format: Apache Parquet. [Established: read successfully by
  `src/inspect_raw_agnews.py` via pandas/pyarrow.]
- Size: 1,234,829 bytes.
- SHA-256: `71DE87EC66BC5737752A2502204DFA6D7FE9856ADE3EA444DC6317789A4F13FB`,
  recorded on 2026-11-05 and identical before and after that inspection.
  [No claim is made that the file has remained unchanged since that date.]
- No official reference hash was checked.

## What one row represents

One news text together with one assigned topic label. [Established: two
columns, `text` and `label`. Assumption, based on the dataset card's preview:
the text combines a title and a description; its exact relation to a single
underlying article has not been verified.]

## Columns

| Column | Meaning | Data type | Allowed values | Units | Missing values |
| ------ | ------- | --------- | -------------- | ----- | -------------- |
| text   | News text. Documented on the dataset card as English; **language was not checked computationally**. Observed locally: 0 null values and 0 blank (empty or whitespace-only) texts. | string (pandas dtype `str`, per the inspection report) | Non-empty text observed locally; the full range of content has not been characterized | Not applicable (plain text) | Source missing-value convention not established; no null values observed in this local file. |
| label  | Topic category code | integer (pandas dtype `int64`, per the inspection report) | Observed values: {0, 1, 2, 3}, confirmed by the full label-frequency count. | Not applicable (categorical code) | Source missing-value convention not established; no null values observed in this local file. |

## Label mapping

| Code | Category name |
| ---- | ------------- |
| 0    | World         |
| 1    | Sports        |
| 2    | Business      |
| 3    | Sci/Tech      |

Source of mapping: the official dataset card's "Data Fields" section
(https://huggingface.co/datasets/fancyzhx/ag_news), checked 2026-11-05. This
mapping is documentation, not a property inferred from the data: the file
itself contains only the numeric codes.

**The correctness of any individual topic label is NOT verified.** The checks
described below verify data properties (shape, counts, nulls, blanks,
duplicates) only. Confirming that a given text's label matches the topic
assigned by the original annotation process would require separate
verification.

## Verified data properties

The core data properties were recomputed in user-executed, AI-assisted checks
outside the agent's inspection script. The verification commands were supplied
by an auxiliary AI assistant. Fully duplicated rows were reported by the
inspection script only.

| Property | Value | Supporting report |
| -------- | ----- | ----------------- |
| Rows | 7,600 | `results/inspect_raw_agnews_summary.txt` (script `src/inspect_raw_agnews.py`); `results/verification_2026-11-05.md` Check 1 |
| Columns | 2 (`text`, `label`) | same two reports |
| Rows per label | 0→1,900; 1→1,900; 2→1,900; 3→1,900 | summary file; verification file Check 2 |
| Missing values | text: 0; label: 0 | summary file; verification file Check 3 |
| Blank texts (empty or whitespace-only) | 0 | summary file; verification file Check 3 |
| Exact duplicate texts (beyond first occurrence) | 0 | summary file; verification file Check 3 |
| Fully duplicated rows (all columns identical) | 0 | summary file only (not recomputed in the verification checks) |

## Documented external metadata

The following statements come from the official dataset card (checked
2026-11-05) and are reported as documented there, not independently verified
by this project:

- Split sizes documented on the card: train 120,000; test 7,600 rows.
- The card lists the license as "unknown".
- The card's sections on the annotation process, annotators, biases, and other
  known limitations all say "More Information Needed"; no reliable information
  on label quality or annotation agreement is available to us from that source.

## Limitations relevant to our study

- **Label correctness is unverified** (see above); the dataset's own labels
  are a reference of unknown reliability for agreement analysis.
- **Balanced classes do not mean classification is easy** (note in
  `results/verification_2026-11-05.md`).
- **Benchmark split, not a probability sample** of all news; results apply to
  this sample and setup.
- **Only the test split is present locally**; the training split (120,000
  rows, documented on the card) is not in this repository.
- No established information about annotation quality or inter-annotator
  agreement (card: "More Information Needed"); license status unknown per the
  card.

## Raw-data rule

`data/raw/` is read-only (AGENTS.md rule 1). Nothing in `data/raw/` may ever be
modified, moved, renamed or deleted; derived data must be written to
`data/derived/`.
