# Qualitative review summary

- Script: `src/20_consolidate_review.py`
- Input: `results/disagreement_review_completed.xlsx`
- Frozen sources: human labels and uncertainty reasons from `data/derived/evaluation_200_labelled.xlsx`; AI labels from `results/ai_classification/evaluation_gemini/ai_classifications.csv`; texts from the raw `text` column via `data/derived/evaluation_manifest.csv`.

## Validation

- Reviewed rows: 38; expected disagreements: 38.
- Reviewed IDs exactly match the frozen disagreement set; unique reviewed IDs: 38.
- Text mismatches versus the raw texts: 0.
- Label mismatches versus the frozen classifications: 0.
- Confidence mismatches: 0.
- Original uncertainty-reason mismatches: 0.
- Blank explanations: 0; blank assessments: 0.

## Assessment counts

These are the student's retrospective judgments after seeing both labels. They are not independent adjudication, not ground truth, and not a revised accuracy measure.

| Assessment | Items |
| --- | --- |
| AI label better supported | 23 |
| human label better supported | 8 |
| both defensible | 7 |

## Disagreement pairs

| Frozen pair (human -> AI) | Items |
| --- | --- |
| 0 World -> 2 Business | 14 |
| 2 Business -> 3 Sci/Tech | 11 |
| 0 World -> 3 Sci/Tech | 5 |
| 0 World -> 1 Sports | 3 |
| 1 Sports -> 2 Business | 2 |
| 2 Business -> 0 World | 2 |
| 1 Sports -> 0 World | 1 |

## Illustrative examples

The excerpts below are the student's recorded explanations. They illustrate the reasoning; they are not presented as established facts about the texts.

- **`eval_006`** (human 2, AI 0; assessment: *AI label better supported*): "Actually the news is not very business related, it's about a marketing strategy that used irony to promote the city of Houston. Should be world because it's related to a city marketing strategy"
- **`eval_030`** (human 2, AI 3; assessment: *human label better supported*): "The focus of the news is a company introducing a new product, it doesn't focus much on explaining the technology behind it"
- **`eval_016`** (human 2, AI 3; assessment: *both defensible*): "It's arguable which is the focus of the news: highlight a new business partnership to improve cybersecurity, or the cybersecurity theme itself"
- **`eval_181`** (human 0, AI 2; assessment: *AI label better supported*): "The news focus on the economic impacts unemployment"

## Reading

Most reviewed disagreements sit on the World/Business and Business/Sci-Tech boundaries, where the codebook asks for the main focus of the text. The review records the student's case-by-case reading of that focus; it does not resolve whether the human or AI label is correct in any general sense.
