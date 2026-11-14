# Verification report — agent run

- Script: `src/17_agent_run_verify_outputs.py`
- Run (UTC): 2026-11-14T13:26:19.052800+00:00
- Method: rebuild the joined dataset from the three authorised inputs,
  recompute all headline quantities from scratch, and compare with the
  saved files. Wilson intervals are additionally cross-checked against
  `statsmodels.stats.proportion.proportion_confint(method="wilson")`
  (no continuity correction).

## Headline quantities recomputed

- Items: 200
- Exact agreements: 162; disagreements: 38
- Overall agreement: 81.00% (95% Wilson 75.00% to 85.83%)
- Pooled Business/Sci-Tech: 13/74 = 17.57% (95% Wilson 10.56% to 27.77%)
- Sports: 3/53 = 5.66% (95% Wilson 1.94% to 15.37%)
- Difference (pooled minus Sports): +11.91 pp (95% Newcombe -0.06 to +22.77 pp)

## Checks

- [x] workbook hash still matches freeze note
- [x] AI CSV hash still matches freeze note
- [x] rebuilt dataset equals saved analysis dataset
- [x] analysis dataset has 200 unique rows
- [x] analysis dataset contains no news-text column
- [x] all manifest IDs used exactly once
- [x] saved agreement count matches recomputation
- [x] saved agreement rate matches recomputation
- [x] saved agreement Wilson interval matches recomputation
- [x] confusion-matrix counts match recomputation
- [x] confusion-matrix counts sum to 200
- [x] confusion-matrix row totals match human-label counts
- [x] row-percentage table matches recomputation
- [x] saved group denominators match recomputation
- [x] saved group disagreement counts match recomputation
- [x] saved group rates match recomputation
- [x] saved Wilson intervals match recomputation
- [x] saved difference matches recomputation
- [x] saved Newcombe interval matches recomputation
- [x] Wilson intervals match statsmodels (group 1)
- [x] Wilson intervals match statsmodels (group 2)
- [x] Wilson interval matches statsmodels (overall agreement)
- [x] Newcombe interval matches statsmodels-based rebuild
- [x] per-category descriptive rates match recomputation
- [x] all expected output files exist
- [x] figure PNG is a readable image larger than 10 KB
- [x] figure PDF is larger than 10 KB
- [x] reports are non-empty

All checks passed: **YES**.

## Scope and limits

- Verification covers data handling, arithmetic and file integrity only.
- The human labels were not judged for correctness; agreement is exact
  label match, not accuracy.
- No original dataset label, news text, classification model, `.env`
  file, `results/workflow_run/` file or earlier analysis script was used.
