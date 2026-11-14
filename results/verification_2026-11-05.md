# Independent Verification — 2026-11-05

## Scope and nature of these checks

The three checks below are **user-executed computational checks**, run by the
user outside OpenCode, independently of the agent's inspection script
(`src/inspect_raw_agnews.py`). The user used different code paths than the agent
(pandas, PyArrow directly, Python's `Counter`) so the results are independent
recomputations, not re-runs of the agent's work.

**These checks verify data properties only** (shape, value counts, null/blank/
duplicate counts). **They do not verify the correctness of the topic labels**:
no check confirms that any given text's label matches the topic assigned by the
official annotation process. Assessing label correctness would require separate
verification (e.g., manual review or cross-referencing the original source).

## Results

### Check 1 — Passed
Method: The user loaded the local Parquet file with pandas, without running the
agent's inspection script.
Observed output:
```
Shape: (7600, 2)
Columns: ['text', 'label']
```

### Check 2 — Passed
Method: The user read the label column with PyArrow and counted values using
Python's `Counter`.
Observed output:
```
Counts by label: [(0, 1900), (1, 1900), (2, 1900), (3, 1900)]
Total: 7600
```

### Check 3 — Passed
Method: The user checked PyArrow column null counts, counted whitespace-only or
empty texts, and compared the number of texts with the number of unique texts.
Observed output:
```
Missing values: {'text': 0, 'label': 0}
Blank texts: 0
Duplicate texts beyond first occurrence: 0
```

## Note on class balance

Check 2 shows perfectly balanced classes (1900 rows per label). **Balanced
classes do not establish that classification is easy.** Balance only means each
class is equally represented; classification difficulty depends on how similar
the texts are across classes, the quality of the labels, and the boundary
structure between topics — none of which is measured by these counts.

## Provenance

- Checks 1–3: run by the user on 2026-11-05 (inputs computed figures above; no agent involvement in their execution).
- File inspected: `data/raw/test-00000-of-00001.parquet` (read-only).
- Cross-references: `results/inspect_raw_agnews_summary.txt` (script: `src/inspect_raw_agnews.py`) was produced earlier by the agent; all three checks independently reproduce its counts.
