# Category-hypothesis comparison (plan.md step 7)

- Script: `src/12_category_hypothesis.py`
- Input: `results/workflow_run/comparison_table.csv`
- Groups defined exclusively by `human_label`; uncertain annotations kept.

## Group rates

| Group | Items | Disagreements | Rate | Wilson 95% |
| --- | --- | --- | --- | --- |
| Business/Sci-Tech (2 or 3) | 74 | 13 | 0.1757 (17.57%) | 10.56% – 27.77% |
| Sports (1) | 53 | 3 | 0.0566 (5.66%) | 1.94% – 15.37% |

**Difference (pooled minus Sports): 11.91 percentage points.**
**95% Newcombe interval: [-0.06, 22.77] percentage points.**

## Method and assumptions

95% Newcombe (1998) method-10 interval for the difference of two
independent proportions, built from Wilson score intervals (z = 1.959964).
Assumptions: the groups are independent (disjoint items); within-group
disagreement indicators are treated as binomial draws; the interval is
approximate and may be asymmetric; no continuity correction and no
multiple-comparison adjustment. Uncertain human annotations are kept.

## Interpretation

Observed direction: the pooled Business/Sci-Tech disagreement rate is
11.91 pp higher than the Sports rate in this sample. The 95%
interval [-0.06, 22.77] pp includes 0, so the data do not establish the direction of the difference; sampling uncertainty is substantial.

This describes agreement with one human reference in this sample and setup;
it is not accuracy against unquestionable ground truth, not a causal claim,
and does not generalize beyond this sample.
