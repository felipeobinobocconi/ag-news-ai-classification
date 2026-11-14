# Original-label comparison (secondary)

- Script: `src/21_original_label_comparison.py`
- Inputs: `data/raw/test-00000-of-00001.parquet`, `data/derived/evaluation_manifest.csv`, `data/derived/evaluation_200_labelled.xlsx`, and `results/ai_classification/evaluation_gemini/ai_classifications.csv`.
- Items: 200; unique IDs: 200; unique source positions: 200.
- Text alignment mismatches between the raw texts retrieved through the manifest and the frozen workbook: 0.

## Agreement with the original dataset label

| Comparison | Matches | Items | Agreement | Wilson 95% |
| --- | --- | --- | --- | --- |
| Human vs dataset | 147 | 200 | 73.50% | 66.98% to 79.13% |
| AI vs dataset | 164 | 200 | 82.00% | 76.09% to 86.71% |

For context only, the frozen human-AI comparison reproduces 162/200 = 81.00% exact agreement. This secondary comparison does not change that result.

## Confusion matrices

Rows are the classification being compared; columns are the original dataset label.

### Human labels by dataset label

| Human \ Dataset | World | Sports | Business | Sci/Tech | Total |
| --- | --- | --- | --- | --- | --- |
| World | 48 | 2 | 15 | 8 | 73 |
| Sports | 1 | 51 | 1 | 0 | 53 |
| Business | 1 | 0 | 29 | 22 | 52 |
| Sci/Tech | 3 | 0 | 0 | 19 | 22 |
| **Total** | 53 | 53 | 45 | 49 | 200 |

### AI labels by dataset label

| AI \ Dataset | World | Sports | Business | Sci/Tech | Total |
| --- | --- | --- | --- | --- | --- |
| World | 42 | 1 | 7 | 4 | 54 |
| Sports | 2 | 51 | 0 | 0 | 53 |
| Business | 6 | 1 | 37 | 11 | 55 |
| Sci/Tech | 3 | 0 | 1 | 34 | 38 |
| **Total** | 53 | 53 | 45 | 49 | 200 |

## Interpretation limits

The original AG News labels are another reference of unknown reliability. No original annotation guidelines are available to this project, and label correctness has not been verified. The dataset labels are therefore not treated as unquestionable ground truth, and these comparisons are secondary rather than a replacement for the primary human-AI analysis.
