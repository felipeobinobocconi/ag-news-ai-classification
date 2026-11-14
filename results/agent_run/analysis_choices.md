# Analysis choices — agent run

- Date: 2026-11-14
- Scope: independent agreement analysis of the frozen human labels and the
  frozen Gemini AI classifications for the evaluation sample.
- Status: analysis complete; all verification checks passed (see
  `results/agent_run/verification_report.md`).

This file records the implementation choices made without asking for approval,
the few execution problems detected and corrected, and the boundaries of the
run. It does not restate quantitative results; those are in the files named
below. No study-design element, codebook rule, or label was changed.

## Inputs and boundaries

1. **Authorised inputs only.** The analysis used exactly:
   - `data/derived/evaluation_200_labelled.xlsx`
   - `results/ai_classification/evaluation_gemini/ai_classifications.csv`
   - `data/derived/evaluation_manifest.csv`

   The freeze notes were read only to obtain the recorded SHA-256 values, and
   the codebook was read to confirm category definitions. The pre-existing
   verification documents (`manual_annotation_verification.md`,
   `evaluation_sampling_summary.md`) were read for context. No original
   dataset label, no individual news text, no prior agreement report, and no
   earlier analysis script was consulted. No classification model was called
   and `.env` was not accessed.
2. **Freeze-note hash verification before analysis.** The labelled workbook and
   the AI classification CSV were checked against the hashes recorded in their
   freeze notes. The codebook hash was checked against the codebook freeze note
   as a context check. No freeze note available to this run records a hash for
   `evaluation_manifest.csv`; its observed hash is recorded in
   `results/agent_run/input_hashes.csv` for traceability, and its integrity was
   validated structurally (ID set, uniqueness, position range).
3. **ID validation before analysis.** All three inputs were checked for the
   expected row count, unique `item_id`, the expected sequential ID range,
   identical ID sets, unique manifest positions, valid labels, valid
   confidence values, nonblank uncertainty reasons, AI call status, finish
   reason, and a single model version. The exact checks and outcomes are in
   `results/agent_run/input_verification.md` (script
   `src/13_agent_run_verify_inputs.py`).

## Data handling and primary analysis

4. **One-to-one join by `item_id`.** Human and AI labels were joined with an
   inner merge and `validate="one_to_one"`. No row was filtered or dropped.
   Row counts before and after the join, and the reason for the join, are
   logged in `13_run_log.txt` and `input_verification.md`.
5. **Uncertain human annotations stay in the primary analysis.** All
   evaluation items enter the agreement calculation, confusion matrix, and
   group comparison, including items whose `human_confidence` is `uncertain`.
   The confident/uncertain split is reported only as a secondary descriptive
   table in `agreement_report.md`; it does not replace or modify the primary
   result. This follows codebook Part B and the analysis plan.
6. **Agreement definition.** Overall agreement is the unweighted proportion of
   items with an exact match between the human label and the AI label. It is
   not accuracy, because the human labels are an independent reference of
   unknown correctness. No Cohen's kappa or other chance-corrected statistic
   was added; the plan asks for agreement and a confusion matrix, and adding a
   chance correction would change the estimand without a pre-specified reason.
7. **Confusion matrix orientation and ordering.** Rows are the human (manual)
   label; columns are the AI label. Categories follow the codebook order
   (0 World, 1 Sports, 2 Business, 3 Sci/Tech). Both counts and row-normalised
   percentages are saved. Machine-readable tables are
   `confusion_matrix_counts.csv` and `confusion_matrix_row_pct.csv`, produced by
   `src/14_agent_run_agreement.py`.
8. **Overall agreement interval.** A 95% Wilson score interval, without
   continuity correction, is reported descriptively for overall agreement.
   This interval was not requested explicitly; it was added to keep the
   headline agreement number from being read as exact.

## Group comparison and interval method

9. **Groups are defined by the human label only.** The pooled group is human
   labels 2 (Business) and 3 (Sci/Tech); the comparison group is human label 1
   (Sports). Human-labelled World texts (label 0) are outside the pre-specified
   contrast and are excluded from this comparison; the exclusion and the
   resulting row count are logged in `15_run_log.txt` and stated in
   `category_hypothesis_report.md`.
10. **Denominators are group sizes.** Each disagreement rate is the number of
    items in that human-labelled group whose AI label differs, divided by the
    total number of items in that group. No weighting, pooling of denominators,
    or reweighting to a common class distribution was applied.
11. **Contrast orientation.** The reported difference is
    `pooled Business/Sci-Tech rate − Sports rate`, expressed in percentage
    points. A positive value means higher disagreement in the pooled group.
    This orientation follows the direction of the plan's hypothesis.
12. **Interval method.** The 95% interval for the difference is Newcombe's
    (1998) method 10 hybrid score interval, built from the two Wilson score
    intervals without continuity correction. The standard-normal 95% quantile
    is used. Wilson bounds are truncated to the [0, 1] probability range; the
    Newcombe bounds are not truncated. The exact method constants are recorded
    in `difference_summary.json`.
13. **No hypothesis test or p-value.** The interval is the inferential summary.
    No p-value was computed, no one-sided test was performed, and no
    multiple-comparison adjustment was applied. The per-category rates
    (including World) are descriptive only and are not used for separate
    hypothesis tests.
14. **Neutral interpretation.** The report separates the observed direction
    from statistical uncertainty, states whether the interval includes zero,
    and explicitly distinguishes agreement from accuracy. It makes no causal
    claim and does not generalise beyond this sample and classification setup.
    This follows AGENTS.md rule 6.

## Figure and formatting

15. **Confusion-matrix figure.** The figure has two panels: counts and
    row-normalised percentages. Axes are labelled as human label (rows) and AI
    label (columns), with category names, a colour bar in each panel, and the
    sample size in the title. The figure is saved as PNG and PDF, with a
    separate caption file. It is produced by
    `src/16_agent_run_confusion_figure.py` from the tables written by
    `src/14_agent_run_agreement.py`.
16. **Rounding.** Narrative rates are shown to one decimal place; the
    difference and its interval are shown to two decimal places where the
    near-zero bound matters. Full precision is retained in the CSV and JSON
    outputs. All numbers in the reports are generated by the scripts, not
    typed by hand.
17. **Software execution.** Every Python run used `uv run`. Reading the Excel
    workbook required `openpyxl`, which is not a declared project dependency;
    it was supplied per run with `uv run --with openpyxl` rather than by
    changing `pyproject.toml` or the lockfile. The scripts fix the random seed
    at 42 at the top even though no step is stochastic.
18. **Output location and preservation.** New scripts are numbered 13–17 in
    `src/`. All new analysis outputs are under `results/agent_run/`. No existing
    file was edited, moved, or deleted; `data/raw/` was not accessed.

## Deviations from the plan and scope

19. **Plan step 8 was not performed.** The plan's final step compares the
    independent classifications with the original dataset labels. This run was
    explicitly prohibited from reading original dataset labels, so that
    comparison was not attempted. This is a scope limit of the run, not a
    change to the study design. The codebook, manual labels, and AI labels are
    unchanged.
20. **No qualitative review of individual texts.** The plan's step 8 also
    mentions qualitative examination of disagreements. This run was prohibited
    from reviewing individual news texts, so no such review was performed. The
    disagreement counts and matrix cells are reported without inspecting their
    content.

## Errors detected and corrected during execution

1. **Missing Excel engine during initial inspection.** An early inspection
   command failed with `ModuleNotFoundError: No module named 'openpyxl'`. The
   project environment does not declare `openpyxl`. Correction: all Excel reads
   were run with `uv run --with openpyxl`, matching the approach already used by
   the project's validation script; no dependency file was changed.
2. **Hash parser assumed one hash per freeze note.** The first run of
   `src/13_agent_run_verify_inputs.py` stopped before any analysis because the
   parser expected exactly one backticked SHA-256 in each freeze note, while the
   manual-labels freeze note records both the workbook hash and the codebook
   hash. Correction: the parser now extracts the hash by its explicit label
   (workbook hash, AI-file hash, codebook hash). The rerun passed all hash
   checks. No analysis output was produced by the failed run.
3. **Disclosure about directory traversal.** During initial orientation, a
   recursive file listing displayed the names and sizes of files under
   `results/workflow_run/`, and a content search over `results/*.md` traversed
   that directory. The search returned no lines from those files, and no
   content from `results/workflow_run/` was displayed, consulted, or used. The
   analysis scripts 13–17 do not reference that directory. A recursive listing
   also showed the file names of the earlier analysis scripts without opening
   them. `src/04_validate_freeze_manual_labels.py` was opened only to confirm
   the documented `uv run --with openpyxl` invocation; it is a validation
   script and contains no analysis results. No workflow file contents were
   returned by the recorded search, and the analysis scripts did not use
   workflow outputs as inputs. This documents the observed separation; it does
   not prove the absence of every influence.

## Verification

- `src/17_agent_run_verify_outputs.py` rebuilds the joined dataset from the
  three authorised inputs, recomputes the agreement, confusion matrix, group
  rates, difference, and interval, and compares every result with the saved
  files.
- The Wilson intervals are cross-checked against
  `statsmodels.stats.proportion.proportion_confint(method="wilson")` with no
  continuity correction. The Newcombe interval is rebuilt from those
  independently computed Wilson bounds.
- The figure files are checked for existence, size, and readability.
- All checks pass; the full list is in
  `results/agent_run/verification_report.md`.

## Outputs

| Output | Made by |
| ------ | ------- |
| `analysis_dataset.csv` | `src/13_agent_run_verify_inputs.py` |
| `input_hashes.csv` | `src/13_agent_run_verify_inputs.py` |
| `input_verification.md` | `src/13_agent_run_verify_inputs.py` |
| `13_run_log.txt` | `src/13_agent_run_verify_inputs.py` |
| `confusion_matrix_counts.csv` | `src/14_agent_run_agreement.py` |
| `confusion_matrix_row_pct.csv` | `src/14_agent_run_agreement.py` |
| `agreement_summary.json` | `src/14_agent_run_agreement.py` |
| `agreement_report.md` | `src/14_agent_run_agreement.py` |
| `14_run_log.txt` | `src/14_agent_run_agreement.py` |
| `group_disagreement.csv` | `src/15_agent_run_category_comparison.py` |
| `category_disagreement.csv` | `src/15_agent_run_category_comparison.py` |
| `difference_summary.json` | `src/15_agent_run_category_comparison.py` |
| `category_hypothesis_report.md` | `src/15_agent_run_category_comparison.py` |
| `15_run_log.txt` | `src/15_agent_run_category_comparison.py` |
| `confusion_matrix.png` | `src/16_agent_run_confusion_figure.py` |
| `confusion_matrix.pdf` | `src/16_agent_run_confusion_figure.py` |
| `confusion_matrix_caption.md` | `src/16_agent_run_confusion_figure.py` |
| `16_run_log.txt` | `src/16_agent_run_confusion_figure.py` |
| `verification_report.md` | `src/17_agent_run_verify_outputs.py` |
| `verification_summary.json` | `src/17_agent_run_verify_outputs.py` |
| `17_run_log.txt` | `src/17_agent_run_verify_outputs.py` |

## Limitations

- **The human labels are a reference, not ground truth.** Agreement measures
  consistency with one manual annotator under one frozen codebook; it does not
  measure correctness. No accuracy claim is possible without a trusted
  standard.
- **The sample is a probability sample of the remaining benchmark pool.** The
  200 evaluation items were sampled uniformly without replacement from the
  AG News test split after excluding the 20 preparation items. This is a
  probability sample of that remaining benchmark pool, not a representative
  sample of all news or real newsroom activity. The reported intervals use
  approximate independent-binomial methods without a finite-population
  correction.
- **One classifier configuration.** Only one model version, one prompt
  protocol, one codebook, and one classification run were analysed. No repeated
  model runs are available, so model-side sampling variability is not
  quantified.
- **Intervals are approximate and assume item independence.** The Wilson and
  Newcombe intervals treat items as independent observations; the intervals
  describe sampling uncertainty under that approximation.
- **Pooling can hide heterogeneity.** Business and Sci/Tech are combined for
  the primary contrast, as pre-specified, but the two categories need not
  behave similarly. The descriptive per-category table shows this, and the
  smaller category has a wide interval.
- **Uncertain annotations remain in the primary analysis by design.** The
  secondary confident/uncertain table makes their influence visible but is not
  a substitute for the primary estimate.
- **No original-label comparison.** Because original dataset labels were out of
  scope for this run, the study cannot say here whether either the human or the
  AI labels match the dataset's own labels.
- **Associational only.** The analysis describes disagreement patterns in one
  sample. It does not identify a causal effect of topic, text difficulty, or
  any other factor on disagreement.
