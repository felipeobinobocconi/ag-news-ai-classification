# Overall agreement and confusion matrix — agent run

- Script: `src/14_agent_run_agreement.py`
- Run (UTC): 2026-11-14T13:24:14.813657+00:00
- Input: `results\agent_run\analysis_dataset.csv` (produced by `src/13_agent_run_verify_inputs.py`)
- Items: 200
- Primary analysis keeps all items, including uncertain human annotations.

## Overall agreement

- Agreements: 162 of 200
- Disagreements: 38 of 200
- Exact agreement: 81.00% (95% Wilson interval 75.00% to 85.83%; no continuity correction)

Agreement here means exact label match between the human reference and
the AI output. It is not accuracy: the human labels are an independent
reference of unknown correctness, not ground truth.

## Confusion matrix (counts)

Rows are the human label; columns are the AI label.

| Human \ AI | World | Sports | Business | Sci/Tech | Total | Disagreements |
| ---------- | --- | --- | --- | --- | --- | --- |
| 0 — World | 51 | 3 | 14 | 5 | 73 | 22 |
| 1 — Sports | 1 | 50 | 2 | 0 | 53 | 3 |
| 2 — Business | 2 | 0 | 39 | 11 | 52 | 13 |
| 3 — Sci/Tech | 0 | 0 | 0 | 22 | 22 | 0 |
| **AI total** | 54 | 53 | 55 | 38 | **200** | **38** |

Cell values are counts. The full machine-readable matrix, including
row-normalised percentages, is in `results/agent_run/confusion_matrix_counts.csv`
and `results/agent_run/confusion_matrix_row_pct.csv`.

## Row-normalised confusion matrix (row percentages)

| Human \ AI | World | Sports | Business | Sci/Tech | Row total |
| ---------- | --- | --- | --- | --- | --- |
| 0 — World | 69.9% | 4.1% | 19.2% | 6.8% | 73 |
| 1 — Sports | 1.9% | 94.3% | 3.8% | 0.0% | 53 |
| 2 — Business | 3.8% | 0.0% | 75.0% | 21.2% | 52 |
| 3 — Sci/Tech | 0.0% | 0.0% | 0.0% | 100.0% | 22 |

## Descriptive agreement by human category

| Human category | n | Agreements | Disagreements | Agreement rate |
| -------------- | - | ---------- | ------------- | -------------- |
| 0 — World | 73 | 51 | 22 | 69.9% |
| 1 — Sports | 53 | 50 | 3 | 94.3% |
| 2 — Business | 52 | 39 | 13 | 75.0% |
| 3 — Sci/Tech | 22 | 22 | 0 | 100.0% |

## Uncertainty subset (secondary, descriptive)

| Human confidence | n | Agreements | Disagreements | Agreement rate |
| ---------------- | - | ---------- | ------------- | -------------- |
| confident | 154 | 135 | 19 | 87.7% |
| uncertain | 46 | 27 | 19 | 58.7% |

The uncertain subset is shown only to make its influence visible. It does
not replace the primary analysis, which includes all items as required by
the frozen codebook (Part B) and the analysis plan.
