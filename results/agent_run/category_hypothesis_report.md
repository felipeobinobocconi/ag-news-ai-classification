# Category disagreement comparison — agent run

- Script: `src/15_agent_run_category_comparison.py`
- Run (UTC): 2026-11-14T13:26:12.361883+00:00
- Input: `results\agent_run\analysis_dataset.csv` (produced by `src/13_agent_run_verify_inputs.py`)
- Contrast: pooled human-labelled Business/Sci-Tech disagreement rate minus human-labelled Sports disagreement rate.
- Denominator for each group: the group's number of texts.
- Uncertain human annotations remain in the primary analysis.

## Group construction

- Starting rows: 200
- Excluded from this comparison: 73 World-labelled texts (outside the pre-specified contrast).
- Comparison rows: 127; all retained rows belong to exactly one comparison group.

## Disagreement rates

| Human-labelled group | Labels | n | Disagreements | Disagreement rate | 95% Wilson interval |
| -------------------- | ------ | - | ------------- | ----------------- | ------------------- |
| Business/Sci-Tech pooled | 2, 3 | 74 | 13 | 17.6% | 10.6% to 27.8% |
| Sports | 1 | 53 | 3 | 5.7% | 1.9% to 15.4% |

Wilson intervals use the score method without continuity correction.

## Difference and 95% Newcombe interval

- Observed difference (pooled minus Sports): **+11.91 pp**
- 95% Newcombe interval: **-0.06 pp to +22.77 pp**
- Method: Newcombe (1998) method 10, combining the two Wilson score intervals (z = 1.959964); no continuity correction.
- No p-value or hypothesis test is reported; the interval is the inferential summary.

## Interpretation

- **Observed direction.** The observed pooled Business/Sci-Tech disagreement rate was higher than the Sports rate.
- **Statistical uncertainty.** The 95% interval includes zero, so the data are compatible with both a higher and a lower pooled Business/Sci-Tech disagreement rate; the observed direction is not statistically resolved by this sample.
- **Pre-specified disproof rule.** The plan's disproof condition (pooled rate equal to or lower than the Sports rate), applied to the observed point estimates, is not met: the point estimate is in the hypothesised direction.
- **Agreement is not accuracy.** These rates measure exact label match between the AI and one human reference. The human labels are an independent reference of unknown correctness, not ground truth, and no original dataset labels were consulted.
- **Scope.** This is one sample of 200 texts under one frozen codebook and one classifier configuration. The analysis is associational; it does not identify a causal effect of topic on disagreement, and it does not generalise beyond this sample and setup without further evidence.

## Descriptive per-category rates

| Human category | In comparison | n | Disagreements | Disagreement rate | 95% Wilson interval |
| -------------- | ------------- | - | ------------- | ----------------- | ------------------- |
| 0 — World | no (descriptive) | 73 | 22 | 30.1% | 20.8% to 41.4% |
| 1 — Sports | yes | 53 | 3 | 5.7% | 1.9% to 15.4% |
| 2 — Business | yes | 52 | 13 | 25.0% | 15.2% to 38.2% |
| 3 — Sci/Tech | yes | 22 | 0 | 0.0% | 0.0% to 14.9% |

The per-category rows are descriptive and are not used to test separate
hypotheses; splitting the data reduces the precision of each estimate.
