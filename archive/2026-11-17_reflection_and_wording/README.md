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
- [`archive/2026-11-14_documentation_corrections/`](archive/2026-11-14_documentation_corrections/)
  — pre-correction versions of `final_report.md`, `README.md` and the checklist.

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

### Verify the saved outputs

These commands re-check the delivered files. They do not rebuild the analysis,
but each rewrites its own verification report, so run them in a copy if the
delivered `results/` must stay untouched.

```text
uv sync
uv run --with openpyxl src/17_agent_run_verify_outputs.py
uv run src/18_reconcile_runs.py
uv run --with openpyxl src/22_final_verification.py
```

- `src/17_agent_run_verify_outputs.py` re-checks the saved files in
  `results/agent_run/` and rewrites `verification_report.md` and
  `verification_summary.json` there.
- `src/18_reconcile_runs.py` compares the two saved implementations and rewrites
  `results/run_comparison.md`. Its tool-call evidence section needs the recorded
  OpenCode session database at `~/.local/share/opencode/opencode.db`; without it
  the numeric comparison is still written but that section is omitted.
- `src/22_final_verification.py` re-checks frozen hashes, report numbers, links,
  Excel formulas and repository hygiene, and rewrites
  `results/final_delivery_checklist.md`. A local `.env` is optional and is
  not required to reproduce the saved analysis; the verifier reports whether it
  is present without reading it.

### Regenerate the analysis in a separate copy

Scripts `src/11` and `src/12` stop if their outputs already exist, and `src/19`
stops if its workbook already exists. In a copy of the project, move those
generated outputs aside — do not delete them — then run the pipeline. Scripts
`src/13`–`src/18`, `src/20` and `src/21` overwrite their own outputs without
asking.

1. Copy the project to a new folder, excluding `.venv/`. Do not copy `.env` to a
   shared or public location; no API key is used below.
2. In the copy, create `prior_outputs/workflow_run/` and move these seven files
   there. They are the only generated outputs that must be moved aside for the
   pipeline to start:

   ```text
   results/workflow_run/comparison_table.csv
   results/workflow_run/confusion_matrix.csv
   results/workflow_run/agreement_summary.json
   results/workflow_run/agreement_report.md
   results/workflow_run/category_hypothesis_table.csv
   results/workflow_run/category_hypothesis_summary.json
   results/workflow_run/category_hypothesis_report.md
   ```

   If you also want to rebuild the blank review template with `src/19`, move
   `results/disagreement_review.xlsx` aside as well. The student-completed
   `results/disagreement_review_completed.xlsx` is an input and must stay.
3. Run, in this order:

   ```text
   uv sync
   uv run --with openpyxl src/11_agreement_overall.py
   uv run --with openpyxl src/12_category_hypothesis.py
   uv run --with openpyxl src/13_agent_run_verify_inputs.py
   uv run src/14_agent_run_agreement.py
   uv run src/15_agent_run_category_comparison.py
   uv run src/16_agent_run_confusion_figure.py
   uv run --with openpyxl src/17_agent_run_verify_outputs.py
   uv run src/18_reconcile_runs.py
   uv run --with openpyxl src/20_consolidate_review.py
   uv run --with openpyxl src/21_original_label_comparison.py
   ```

   `src/12` reads the comparison table and matrix written by `src/11`;
   `src/14`–`src/17` read `results/agent_run/analysis_dataset.csv` written by
   `src/13`; `src/18` reads the outputs of both runs. `src/20` reads the
   preserved `results/disagreement_review_completed.xlsx`, and `src/21` reads
   the original dataset labels only for the secondary comparison.

### What must not be moved or regenerated

Preserve `data/raw/`, `data/derived/` (including `evaluation_manifest.csv` and
`evaluation_200_labelled.xlsx`), all freeze notes in `results/`,
`results/ai_classification/evaluation_gemini/` (including
`ai_classifications.csv`), `results/disagreement_review_completed.xlsx` and
`results/aiproject_manualcheck.xlsx`. Do not rerun `src/01`–`src/10`: they
rebuild sampling, freeze or API outputs, and `src/04` additionally refuses to
run when its freeze-note targets already exist.

### Reproduction limitation

These instructions were derived from the scripts' own output guards and input
checks. The full regeneration sequence was **not executed end-to-end** for this
delivery, so it has not been validated by a clean run. The numeric results
reported in the project remain the saved ones.

## Making new API calls

The evaluation classification used
gemini-3.5-flash-lite, accessed through the Gemini API v1beta, with direct HTTPS
requests, temperature 0.0, one candidate, no tools, no search grounding and no
conversation history. The prompt embedded the frozen codebook Part A and treated
the news text as untrusted data. Each request and response is recorded under
`results/ai_classification/evaluation_gemini/`; the per-item `meta/` records
store `model_version` separately from the API version.

Scripts 05–10 contain dry-run and classification calls from earlier routes and
the final Gemini route. Re-running any of them may consume quota or create new
model outputs; that is a new data-collection step, not a reproduction of the
saved analysis. The API key is read from a local `.env` file for authentication
only and is never written to project outputs. `.env` and `.env.*` are ignored.

## Repository readiness and secrets

- A local `.env` is optional and is ignored by [`.gitignore`](.gitignore) when
  present; it is not needed for the saved analysis.
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
