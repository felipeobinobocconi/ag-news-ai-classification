# Analysis Plan

## Proposed value proposition

For editors in small digital newsrooms, we offer reduced effort in first-pass
news categorization using AI-generated topic suggestions, a clear classification
codebook, and human review.

This is a proposed value theory to investigate, not an established customer
benefit or a claim that an editorial product has already been built.

| Element | Proposed definition |
| ------- | ------------------- |
| Customers | Editors in small digital newsrooms who organize incoming news into sections. |
| Benefits | Less manual sorting effort while maintaining acceptable categorization quality. |
| Features | AI suggestions across four topics, explicit category definitions and tie-breaking rules, and human validation of suggestions. |

## Research question

How closely does AI topic classification agree with my independent manual
classification of AG News texts, and which categories generate more
disagreements?

## Theory

Business and science/technology news can overlap in subject matter, while
sports news may have more distinctive topic cues.

Hypothesis: the disagreement rate will be higher for texts I manually classify
as Business or Sci/Tech than for texts I classify as Sports.

This is an expectation to test, not an established finding.

## Dataset

Use the existing AG News test Parquet file in `data/raw/`.
Source: https://huggingface.co/datasets/fancyzhx/ag_news

Categories:

| Code | Category name |
| ---- | ------------- |
| 0    | World         |
| 1    | Sports        |
| 2    | Business      |
| 3    | Sci/Tech      |

Keep raw data unchanged. Initial data-property checks are documented in
`results/verification_2026-11-05.md`.

## Analysis plan

1. Develop category definitions and tie-breaking rules using 20 preparation
   texts.
2. Select 200 other texts at random, without replacement, using seed 42. Keep
   preparation and evaluation texts separate.
3. Classify the evaluation texts manually before seeing any model
   classifications or original dataset labels. Record uncertainty separately.
4. Freeze the manual labels and classification instructions before evaluating
   the AI.
5. Give the AI only the text and classification instructions, without manual
   labels or original dataset labels.
6. Compute overall agreement and a confusion matrix against my manual
   classifications.
7. Compare the pooled disagreement rate for manually labelled
   Business/Sci/Tech texts with the disagreement rate for manually labelled
   Sports texts. Use each group's number of texts as its denominator.
8. Examine disagreements qualitatively. Compare with original dataset labels
   only after the independent classifications are complete.

## What result would disprove the theory

The hypothesis would not be supported in this sample if the pooled
Business/Sci/Tech disagreement rate is equal to or lower than the Sports
disagreement rate.

## Verification checks

- Recalculate headline agreement from the saved classification table.
- Check that records align correctly and preparation/evaluation samples do not
  overlap.
- Treat my manual labels as an independent human reference, not unquestionable
  truth.
- Report sampling uncertainty and ambiguous cases.
- Results apply to this sample and classification setup.
- Record the exact classifier model, available version information, prompt and
  settings before classification. Confirm the execution method before any
  model calls.

## Classifier model and execution method

Proposed classifier: `opencode/deepseek-v4.1-flash-free` (a free model permitted
by the project brief). Its exact ID was verified present in the installed CLI
catalog (`opencode v2.2.5`) on 2026-11-13. This choice is subject to the
mandatory synthetic dry run before any evaluation classification.

The previously proposed classifier `opencode/glm-5.3-flash-free` produced no
evaluation classifications: both of its synthetic dry-run attempts were
blocked by the free-usage quota (attempt 01 on 2026-11-12 and attempt 02 on
2026-11-13; artifacts preserved in `results/ai_classification/dry_run/` and
`results/ai_classification/dry_run_02/`).

Execution method (unchanged): one fresh CLI session per item; a dedicated
`classifier` agent with deny-all permissions; frozen Part A of the codebook
embedded verbatim, extracted by section headings; the news text framed as
untrusted data; CLI event/status output separated from the final answer;
strict parsing of the final answer only; per-call timeouts; strictly
sequential calls; resumable progress; full raw logs per call. The frozen
references (codebook v1.0 and manual labels) remain unchanged.

The DeepSeek free-model route produced no evaluation classifications either:
its synthetic dry-run attempts (03 and 04) were quota-blocked (pending the
synthetic dry run of the officially documented Gemini API route below).

Proposed classifier for the Gemini API route: `gemini-3.5-flash-lite` (stable
model; the official pricing page lists free-of-charge input and output on the
Free tier; checked 2026-11-14). Execution method: one direct HTTPS request per
text to the Gemini API (`v1beta/models/gemini-3.5-flash-lite:generateContent`),
single-turn conversation with no tools, search grounding, or history; the same
prompt protocol (frozen Part A verbatim, news text framed as untrusted data);
label parsed from the final response text only; temperature 0; sequential
requests; per-request timeout; full request/response logs saved. The API key
is loaded locally from `.env` for authentication only and is never logged,
displayed, or sent as model input. Subject to the mandatory synthetic dry run
before any evaluation classification.
