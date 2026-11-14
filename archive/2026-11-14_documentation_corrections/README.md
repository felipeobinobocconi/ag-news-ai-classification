# AG News AI topic-classification study

This project measures how closely one AI classifier agrees with one student's
independent manual topic classification of AG News texts, and which topic
categories generate more disagreements. It also documents a qualitative review
of every disagreement, a secondary comparison with the original AG News labels,
and the verification of both analysis runs.

The project is a study of **agreement with a manual reference**, not a measure
of accuracy against ground truth. It does not measure editorial time savings or
downstream publishing quality.

## Key findings

| Finding | Result | Source |
| --- | --- | --- |
| Overall human-AI agreement | 162/200 = 81.0% (95% Wilson 75.0% to 85.8%) | [`results/agent_run/agreement_report.md`](results/agent_run/agreement_report.md) |
| Category contrast | Pooled Business/Sci-Tech 13/74 (17.57%) vs Sports 3/53 (5.66%); difference +11.91 pp, 95% Newcombe −0.06 to +22.77 pp; inconclusive | [`results/workflow_run/category_hypothesis_report.md`](results/workflow_run/category_hypothesis_report.md) |
| Qualitative review | 38 disagreements reviewed; 23 AI label better supported, 8 human label better supported, 7 both defensible (retrospective student judgments) | [`results/qualitative_review_summary.md`](results/qualitative_review_summary.md) |
| Original-label comparison | Human vs dataset 147/200 (73.5%); AI vs dataset 164/200 (82.0%); secondary only, dataset labels are not ground truth | [`results/original_label_comparison.md`](results/original_label_comparison.md) |
| Two-run reconciliation | 69 checks, 0 failures; implementation consistency, not independent validation | [`results/run_comparison.md`](results/run_comparison.md) |
| Student Excel check | 200 items, 162 matches, 81% agreement from direct `human_label`/`ai_label` formulas | [`results/student_excel_verification.md`](results/student_excel_verification.md) |

The full narrative is in [`final_report.md`](final_report.md).

## Project navigation

- [`plan.md`](plan.md) — research question, hypothesis, analysis plan.
- [`codebook.md`](codebook.md) — frozen v1.0 classification rules.
- [`data/README.md`](data/README.md) — data dictionary and data limitations.
- [`results/workflow_run/`](results/workflow_run/) — first implementation of the
  primary agreement and category comparison (scripts 11–12).
- [`results/agent_run/`](results/agent_run/) — autonomous implementation of the
  primary analysis and its verification (scripts 13–17).
- [`results/run_comparison.md`](results/run_comparison.md) — item-level and
  numerical reconciliation of the two implementations.
- [`results/disagreement_review_completed.xlsx`](results/disagreement_review_completed.xlsx)
  — the student's completed 38-item qualitative review.
- [`results/qualitative_review_summary.md`](results/qualitative_review_summary.md)
  — validated review counts and illustrative examples.
- [`results/original_label_comparison.md`](results/original_label_comparison.md)
  — secondary comparison with the original dataset labels.
- [`results/student_excel_verification.md`](results/student_excel_verification.md)
  — student-executed Excel arithmetic check.
- [`mistakes.md`](mistakes.md) — documented agent mistakes and corrections.
- [`results/final_delivery_checklist.md`](results/final_delivery_checklist.md)
  — final readiness checks and any remaining items.

## Reproducing the analysis without new API calls

### Requirements

- Python 3.13 or newer.
- [`uv`](https://docs.astral.sh/uv/).
- Base dependencies from [`pyproject.toml`](pyproject.toml): pandas, pyarrow,
  statsmodels, matplotlib.
- `openpyxl` is **not** a declared dependency; scripts that read or write Excel
  are run with `uv run --with openpyxl ...`.

No API key is needed to reproduce the saved analyses. The frozen human labels
and the frozen AI classifications are already in the repository. Do **not** run
`src/10_gemini_evaluation_batch.py` unless you intend to make new API calls and
have separately verified the account tier and billing status.

### Saved outputs

All reported outputs are already present under `results/`. The workflow scripts
11–12 refuse to overwrite existing outputs. The agent scripts 13–17 write into
`results/agent_run/` and can overwrite their own previous files. To reproduce
them safely, work in a copy of the repository or preserve the existing
`results/agent_run/` files first.

### Primary analysis

```text
uv sync
uv run --with openpyxl src/11_agreement_overall.py
uv run --with openpyxl src/12_category_hypothesis.py
```

The autonomous implementation (requires `analysis_dataset.csv` from script 13):

```text
uv run --with openpyxl src/13_agent_run_verify_inputs.py
uv run src/14_agent_run_agreement.py
uv run src/15_agent_run_category_comparison.py
uv run src/16_agent_run_confusion_figure.py
uv run src/17_agent_run_verify_outputs.py
```

Reconcile the two implementations:

```text
uv run src/18_reconcile_runs.py
```

### Review and secondary comparison

Script 19 refuses to overwrite an existing `results/disagreement_review.xlsx`.
Script 20 reads the student-completed review workbook; it does not recreate the
student's judgments. Script 21 reads the original dataset labels only for the
secondary comparison.

```text
uv run --with openpyxl src/19_disagreement_review.py
uv run --with openpyxl src/20_consolidate_review.py
uv run --with openpyxl src/21_original_label_comparison.py
uv run --with openpyxl src/22_final_verification.py
```

## Making new API calls

The evaluation classification used `gemini-3.5-flash-lite` (v1beta) through
direct HTTPS requests, with temperature 0.0, one candidate, no tools, no search
grounding and no conversation history. The prompt embedded the frozen codebook
Part A and treated the news text as untrusted data. Each request and response is
recorded under `results/ai_classification/evaluation_gemini/`.

Scripts 05–10 contain dry-run and classification calls from earlier routes and
the final Gemini route. Re-running any of them may consume quota or create new
model outputs; that is a new data-collection step, not a reproduction of the
saved analysis. The API key is read from a local `.env` file for authentication
only and is never written to project outputs. `.env` and `.env.*` are ignored.

## Repository readiness and secrets

- `.env` is present locally and is ignored by [`.gitignore`](.gitignore).
- `.venv/`, `__pycache__/`, compiled Python files and `.pytest_cache/` are
  ignored.
- No secrets are included in this README or in the reports. Do not add API keys,
  credentials or `.env` contents to tracked files.
- This directory is not currently a Git repository (`git` is not installed and
  there is no `.git/` directory here), so there are no tracked-file or staging
  checks to perform locally. GitHub publication has not been done.

## Data and license notes

The AG News dataset card lists the license as unknown. The local raw file is
treated as read-only; see [`data/README.md`](data/README.md). The study used a
200-item probability sample of the AG News test pool remaining after 20
preparation exclusions; it is not a representative sample of all news.
