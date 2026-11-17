# Final report — AI topic suggestions versus manual classification

- Project: AG News topic-classification agreement study
- Report date: 2026-11-17 (revised; first issued 2026-11-14)
- Scope: one frozen manual classification, one frozen AI classification, and the
  supporting verification and review records

This report consolidates saved results. It does not introduce a new primary
analysis. Every quantitative statement below is taken from the linked result
files and their producing scripts.

## 1. Customer, problem and value theory

The proposed customer is an editor in a small digital newsroom who sorts
incoming news into sections. The problem is the manual effort of first-pass
topic sorting. The proposed value theory is that AI-generated topic suggestions,
used with an explicit codebook and human validation, could reduce that effort
while keeping categorisation acceptable. This is a value theory to investigate,
not an established customer benefit or a claim that an editorial product exists.

The research question is: how closely does AI topic classification agree with
the student's independent manual classification of AG News texts, and which
categories generate more disagreements? See `plan.md`.

## 2. Hypothesis, design and execution

The pre-specified hypothesis was that the disagreement rate would be higher for
texts manually labelled Business or Sci/Tech than for texts manually labelled
Sports.

The design was:

1. **Preparation.** Twenty preparation texts were used to test and clarify the
   codebook. They informed version 0.3 and the frozen version 1.0, and were
   excluded from the evaluation sample. Preparation involved documented
   assistance from an auxiliary AI assistant; see
   `results/preparation_assistance_note.md`.
2. **Frozen codebook.** `codebook.md` version 1.0 was frozen on 2026-11-12
   (SHA-256 `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E`).
   Both the human and AI classifications use the same Part A rules; confidence
   and uncertainty fields are human-only and never entered the AI prompt. See
   `results/codebook_freeze_note.md`.
3. **Evaluation sample.** Two hundred items were sampled uniformly without
   replacement, with seed 42, from the 7,580 AG News test rows remaining after
   excluding the 20 preparation positions. This is a probability sample of that
   remaining benchmark pool, not a representative sample of all news. The
   manifest maps each `item_id` to its original zero-based source position.
   See `results/evaluation_sampling_summary.md`.
4. **Human labelling before AI.** The student labelled all 200 texts without
   consulting any AI for the classification decisions, recording label,
   confidence and, for uncertain items, a short reason, before seeing any AI
   classification or original dataset label. The labels were frozen on
   2026-11-12; see `results/manual_labels_freeze_note.md` and
   `results/manual_annotation_verification.md`.
5. **AI classification.** The final classifier was
   gemini-3.5-flash-lite, accessed through the Gemini API v1beta. Each text was
   classified with one direct HTTPS request. The request was single-turn, with
   the frozen codebook Part A embedded, no tools, no search grounding and no
   conversation history; settings were temperature 0.0, `maxOutputTokens` 1024
   and one candidate. The news text was framed as untrusted data, and the label
   was parsed from the final response text only. All 200 items completed with
   valid labels. The per-item `meta/` records keep the response's `model_version`
   value (`gemini-3.5-flash-lite`) separate from the API version (`v1beta`). See
   `results/ai_classification/evaluation_gemini/classification_freeze_note.md`,
   `preflight_report.md`, and the per-item `meta/` records.
6. **Freeze before comparison.** The human labels and AI labels were frozen
   before the primary comparison. Original dataset labels remained hidden until
   both classifications were complete; they are used only in the secondary
   comparison in section 5.

## 3. Primary results

### 3.1 Overall agreement

The two frozen classifications agree on **162/200 items (81.0%)**. The 95%
Wilson interval is **75.0% to 85.8%**. This is exact agreement with one human
reference, not accuracy against ground truth.

Source: `results/agent_run/agreement_summary.json` and
`results/agent_run/agreement_report.md`, produced by
`src/14_agent_run_agreement.py`; the same figures are in the workflow run and
were reconciled in `results/run_comparison.md`.

### 3.2 Confusion matrix

Rows are the human label; columns are the AI label. Category order is World,
Sports, Business, Sci/Tech.

| Human \ AI | World | Sports | Business | Sci/Tech | Total |
| --- | --- | --- | --- | --- | --- |
| World | 51 | 3 | 14 | 5 | 73 |
| Sports | 1 | 50 | 2 | 0 | 53 |
| Business | 2 | 0 | 39 | 11 | 52 |
| Sci/Tech | 0 | 0 | 0 | 22 | 22 |
| **AI total** | 54 | 53 | 55 | 38 | 200 |

Source: `results/agent_run/confusion_matrix_counts.csv`; figure in
`results/agent_run/confusion_matrix.png` and `.pdf`, produced by
`src/14_agent_run_agreement.py` and `src/16_agent_run_confusion_figure.py`.

Per human-labelled category, agreement was 51/73 (69.9%) for World, 50/53
(94.3%) for Sports, 39/52 (75.0%) for Business and 22/22 (100.0%) for Sci/Tech.
These are descriptive rates in this sample.

### 3.3 Category comparison

| Group | Items | Disagreements | Rate | Wilson 95% |
| --- | --- | --- | --- | --- |
| Pooled Business/Sci-Tech | 74 | 13 | 13/74 = 17.57% | 10.56% to 27.77% |
| Sports | 53 | 3 | 3/53 = 5.66% | 1.94% to 15.37% |

The observed difference (pooled minus Sports) is **+11.91 percentage points**,
with a 95% Newcombe interval of **−0.06 to +22.77 percentage points**. The
interval includes zero, so the category hypothesis is **inconclusive at the 95%
level** in this sample. The positive point estimate is consistent with the
hypothesised direction, but the data do not establish it.

Uncertain human annotations remain in the primary analysis by design. The
confident/uncertain split is exploratory and agent-added: 135/154 (87.7%)
agreement among confident items and 27/46 (58.7%) among uncertain items. It is
not the primary hypothesis test. Sources:
`results/workflow_run/category_hypothesis_summary.json`, produced by
`src/12_category_hypothesis.py`; `results/agent_run/agreement_summary.json`.

### 3.4 Descriptive category patterns

The pooled figure hides where the disagreements actually sit. All 13 pooled
Business/Sci-Tech disagreements came from Business: Business had 13/52
disagreements (25.0%) while Sci/Tech had 0/22 (0.0%). Pooling the two categories
into a single 13/74 rate therefore averages a quarter-rate category with a
zero-rate category, and the pooled number describes neither. This is a
descriptive observation about the sample, not a revised hypothesis test; the
primary pooled comparison in section 3.3 stands as reported.

World, which is outside the primary contrast, had 22/73 disagreements (30.1%).
That is the highest per-category disagreement count in the sample, so the
Business/Sci-Tech versus Sports contrast does not cover the category where most
disagreements occurred.

The three label sets also distribute the 200 texts differently across
categories:

| Category | Human labels | AI labels | Original dataset labels |
| --- | --- | --- | --- |
| World | 73 | 54 | 53 |
| Sports | 53 | 53 | 53 |
| Business | 52 | 55 | 45 |
| Sci/Tech | 22 | 38 | 49 |
| **Total** | **200** | **200** | **200** |

Human counts are the confusion-matrix row totals; AI counts are the column
totals in `results/agent_run/agreement_summary.json`, produced by
`src/14_agent_run_agreement.py`. Dataset counts are in
`results/original_label_comparison.json`, produced by
`src/21_original_label_comparison.py`.

These distributions differ mainly in Sci/Tech (22 human, 38 AI, 49 dataset) and
World (73 human, 54 AI, 53 dataset). The differences are descriptive only. They
do **not** show that the human applied the codebook incorrectly, and the closer
AI-dataset totals do **not** establish that the AI labels are correct: the
dataset labels are an unverified reference (section 5), and count agreement can
arise from different item-level decisions. No test of distributional difference
was run and none is implied.

## 4. Qualitative review of disagreements

The student reviewed all **38** disagreements in
`results/disagreement_review_completed.xlsx`, after seeing both labels, and
personally wrote an explanation and assessment for every item. The student
reports that no AI was asked to produce those judgments. A validation script
confirmed that the reviewed IDs exactly match the frozen disagreement set, all
texts match the raw texts retrieved through the manifest, and labels,
confidence and original uncertainty reasons are unchanged. There were no blank
explanations or assessments. See `results/qualitative_review_summary.md` and
`results/qualitative_review_summary.json`, produced by
`src/20_consolidate_review.py`.

The student's retrospective assessments were:

| Assessment | Items |
| --- | --- |
| AI label better supported | 23 |
| Human label better supported | 8 |
| Both defensible | 7 |

These are the student's judgments after both labels were visible. They are not
independent adjudication, not ground truth, and not a revised accuracy measure.

The disagreements clustered on two boundaries: World to Business (14 items) and
Business to Sci/Tech (11 items), followed by World to Sci/Tech (5). The review
comments illustrate the kind of judgment involved:

- `eval_006` (human Business, AI World; student: AI better supported): the
  student read the text as a city marketing strategy rather than a business
  story.
- `eval_030` (human Business, AI Sci/Tech; student: human better supported): the
  student read it as a product announcement that does not explain the
  technology.
- `eval_016` (human Business, AI Sci/Tech; student: both defensible): the
  student found the focus genuinely arguable between a business partnership and
  the cybersecurity theme.
- `eval_181` (human World, AI Business; student: AI better supported): the
  student focused on the text's discussion of unemployment and economic
  effects.

The full explanations are in the completed workbook. These examples illustrate
the student's reasoning; they are not presented as established facts about the
texts or as a resolution of which classifier is correct.

## 5. Secondary comparison with the original dataset labels

With both independent classifications frozen, the original dataset labels were
read through `data/derived/evaluation_manifest.csv`. IDs, source positions and
text alignment were validated: 200 unique IDs, 200 unique positions, and zero
text mismatches between the raw texts retrieved through the manifest and the
frozen workbook. See `results/original_label_comparison.md`,
`results/original_label_comparison.csv` and
`results/original_label_comparison.json`, produced by
`src/21_original_label_comparison.py`.

| Comparison | Matches | Items | Agreement | Wilson 95% |
| --- | --- | --- | --- | --- |
| Human vs original dataset label | 147 | 200 | 73.5% | 67.0% to 79.1% |
| AI vs original dataset label | 164 | 200 | 82.0% | 76.1% to 86.7% |

The original AG News labels are another reference of unknown reliability. No
original annotation guidelines are available to this project, and label
correctness has not been verified. The AI labels match this dataset reference
more often than the human labels in this sample, but that is not an accuracy
measure and does not revise the primary human-AI result.

## 6. Workflow and autonomous execution

Two implementations produced the saved analysis: a workflow run
(`src/11_agreement_overall.py`, `src/12_category_hypothesis.py`, outputs in
`results/workflow_run/`) and an autonomous run
(`src/13_agent_run_verify_inputs.py` through
`src/17_agent_run_verify_outputs.py`, outputs in `results/agent_run/`).
They agree on all 200 item-level labels, all 16
confusion-matrix cells, every group count and rate, and every interval endpoint.
The reconciliation performed 69 checks with 0 failures; the largest interval
endpoint difference was `7.10543e-15`. See `results/run_comparison.md`,
produced by `src/18_reconcile_runs.py`.

This is **implementation consistency, not independent validation** of the
underlying classifications. Both implementations use the same frozen human
labels and the same frozen AI labels, so their agreement adds no independent
evidence about classification quality or accuracy.

### 6.1 Analysis model and session separation

Both saved runs were produced by the OpenCode analysis agent, not by the Gemini
classifier. The recorded session metadata gives the same model for both runs:

| Run | OpenCode session | Agent | CLI | Model | Variant |
| --- | --- | --- | --- | --- | --- |
| `workflow_run` | Data analysis assignment setup | `build` | `2.2.5` | `opencode/deepseek-v4.1-flash-free` | `default` |
| `agent_run` | Autonomous evaluation agreement run | `build` | `2.2.5` | `opencode/deepseek-v4.1-flash-free` | `default` |

Source: `results/agent_run/analysis_model_metadata.json`, produced by
`src/23_record_analysis_model_metadata.py` from the local OpenCode session store
read in read-only mode. Only model identifiers, agent name, CLI version, session
title and message counts were copied; no prompt or response text was recorded.

Two qualifications apply. First, the workflow session also contains earlier
assistant exchanges attributed to `opencode/glm-5.3-flash-free`; every assistant
message that mentions `11_agreement_overall.py` or `12_category_hypothesis.py`
is attributed to `opencode/deepseek-v4.1-flash-free`. Second, no model version
string beyond these identifiers and no sampling parameters were recorded, so
the exact model build cannot be pinned down further. The CLI version identifies
the OpenCode client, not the model.

The autonomous run used a **fresh OpenCode session**, started 2026-11-14, rather
than continuing the earlier workflow session. It read the same frozen human
workbook and the same frozen Gemini CSV; the Gemini classification itself was
**not repeated**. The fresh session therefore tests implementation independence
under a shared, unchanged input set, not classification reproducibility.

Two execution problems are documented:

- **Workflow diagonal extraction.** The workflow comparison initially used
  `cm.loc[pooled_rows].values.diagonal()` on a 2×4 slice. NumPy returned only two
  cells, so pooled disagreements were reported as 72 instead of 13. The script's
  own matrix consistency check stopped the run before outputs were written; the
  correction sums the explicit Business and Sci/Tech diagonal cells, and the
  rerun passed. Saved workflow outputs come from the corrected rerun.
- **Autonomous search boundary.** During initial orientation, the autonomous run
  listed files under `results/workflow_run/`, and a content search over
  `results/*.md` traversed that directory with ripgrep. The returned output
  contained workflow paths but no workflow file contents, and scripts 13–17 used
  only the three authorised inputs. Because ripgrep reads files to search them,
  process-level non-exposure cannot be fully verified. This is recorded as an
  instruction-following failure in `mistakes.md`; the observed separation does
  not prove the absence of every influence.

## 7. Verification

| Area | Result | Evidence |
| --- | --- | --- |
| Data properties | 7,600 raw rows, two columns, no missing or blank texts observed; 0 duplicate texts | `data/README.md`, `results/inspect_raw_agnews_summary.txt` |
| Sampling and text alignment | 200 sampled from 7,580 after 20 exclusions; 200 unique IDs/positions; exact text matches; zero preparation overlap | `results/evaluation_sampling_summary.md`, `results/manual_annotation_verification.md` |
| Frozen hashes | Human workbook `D71C12…948A`, AI CSV `760633…8AFB`, codebook `9EB79D…8A7E` match their freeze notes; no freeze-note hash exists for the manifest, whose observed hash is recorded | `results/manual_labels_freeze_note.md`, `results/ai_classification/evaluation_gemini/classification_freeze_note.md`, `results/codebook_freeze_note.md`, `results/agent_run/input_hashes.csv` |
| Primary recomputation | 200 items, 162 agreements, 38 disagreements; matrix total and diagonal consistent | `results/agent_run/verification_report.md`, `src/17_agent_run_verify_outputs.py` |
| Two-run reconciliation | 69 checks, 0 failures; all labels and cells identical | `results/run_comparison.md`, `src/18_reconcile_runs.py` |
| Qualitative review | 38 IDs match; 0 text/label/confidence/reason mismatches; 0 blank review fields; 23/8/7 assessment counts match | `results/qualitative_review_summary.json`, `src/20_consolidate_review.py` |
| Original labels | 200 unique IDs/positions; 0 text mismatches; secondary agreements 147/200 and 164/200 | `results/original_label_comparison.json`, `src/21_original_label_comparison.py` |
| Student Excel check | F2:F201 compares `human_label` with `ai_label` directly; 200 items, 162 matches, 81% | `results/student_excel_verification.md`, `results/aiproject_manualcheck.xlsx` |

The student's Excel verification was student-executed outside the OpenCode
analysis scripts. It checks arithmetic on the saved comparison table, not label
correctness or the original join.

## 8. Agent mistakes and implications

Three agent mistakes are recorded. Each is described as what happened, the
likely mechanism (marked as interpretation where the record does not establish
it), how it was detected and what the check could not catch, the correction, and
a practice for future runs.

### 8.1 Files created during an inspection described as read-only (2026-11-05)

**What happened.** An inspection task explicitly prohibited creating or
modifying files. The agent created `src/inspect_raw_agnews.py` and
`results/inspect_raw_agnews_summary.txt` and described the operation as "fully
read-only".

**Likely mechanism (interpretation).** The project's general rules allow writing
to `results/`, and the agent appears to have carried that general permission
into a task whose specific instruction overrode it. "Read-only" seems to have
been applied to the raw data only, not to the operation as a whole. The record
establishes the conflicting instruction and the files created; it does not
establish the agent's internal reasoning, so this mechanism is an interpretation.

**Detection and its limits.** The student compared the agent's reported actions
with the original instruction. This was not an agent self-check. The check
depended on the agent disclosing what it had done; a write that was not reported
could have gone unnoticed.

**Correction.** The description was corrected: raw data was preserved, but the
operation was not read-only overall.

**Practice next time.** Before starting a task with an explicit restriction,
restate the restriction, list the files the task is expected to create, and treat
task-specific instructions as overriding general permissions. Report every file
created, including auxiliary scripts.

### 8.2 Pooled disagreements computed from a slice diagonal (2026-11-14)

**What happened.** In the workflow run, `src/12_category_hypothesis.py` derived
pooled disagreements from
`cm.loc[pooled_rows].values.diagonal()` where the selected block was a 2×4
slice. NumPy returned only two cells, so the script reported 72 pooled
disagreements instead of 13.

**Likely mechanism (interpretation).** On a rectangular slice, `.values.diagonal()`
takes the diagonal of the bounding array by position, here the Business/World
and Sci/Tech/Sports cells, not the within-category agreements. The idiom is
valid and common for square matrices, which is why it looked correct. The code
and the observed output are recorded; why it was judged correct at the time is
an interpretation.

**Detection and its limits.** This was caught by an **agent self-check**, not by
the student. The script's own matrix consistency check stopped the run before
any output was written, at recorded message seq `1716`, with
`STOP: counts disagree with confusion matrix: computed (74, 13, 53, 3), matrix
(74, 72, 53, 3)`. The cause was identified at seq `1723`. The limit is that the
check compares two derivations inside the same script: it catches arithmetic
and shape inconsistency, but a definitional error applied consistently to both
sides would pass. It also cannot substitute for an independent reviewer.

**Correction.** The slice diagonal was replaced with explicit label-based cells,
`cm.loc["human_Business", "Business"] + cm.loc["human_Sci/Tech", "Sci/Tech"]`
= 39 + 22 = 61 agreements, so 74 − 61 = 13 disagreements. The rerun at seq
`1734` passed, and the saved `results/workflow_run/` outputs come from that
rerun. Evidence and quoted outputs are in `results/run_comparison.md`, produced
by `src/18_reconcile_runs.py`.

**Practice next time.** Select matrix cells by row and column labels, not by
position, and assert the expected shape before extracting a diagonal. Keep an
independent total (here, agreements plus disagreements must equal the group
size) and print it, so a silently truncated selection fails loudly.

### 8.3 Search traversed the excluded workflow directory (2026-11-14)

**What happened.** During the autonomous run's initial orientation, a glob
`**/*.md` returned two `results/workflow_run/` paths, a recursive listing of
`results` returned seven such paths with sizes, and a ripgrep search over
`results/*.md` ran without excluding `workflow_run`. The traversal was disclosed
later in `results/agent_run/analysis_choices.md`, not before the analysis.

**Likely mechanism (interpretation).** The orientation commands were scoped to
`results` as a whole, and the excluded directory was treated as material not to
be analysed rather than as a path not to be traversed. Because ripgrep reads
files in order to search them, traversal is also file access. Whether any
workflow text entered the model context beyond the returned matches cannot be
established from the record, so this part remains uncertain.

**Detection and its limits.** Detection came from reviewing the recorded tool
calls and the server log after the fact, not from a pre-execution guard or from
a student-executed check. The record shows the commands and their returned
output: the glob and listing returned workflow paths only, and the grep returned
three matches, none in `workflow_run` (server log
`2026-11-14T13:19:09.878Z`). The limit is that logs capture calls and returned
output, not the full process context, so process-level non-exposure cannot be
fully verified. The observed separation does not prove the absence of every
influence.

**Correction.** The event is recorded as an instruction-following failure in
`mistakes.md` and in section 6. Scripts 13–17 reference only the three
authorised inputs, and the run continued in the same autonomous session. The
record does not show workflow file contents in the returned output, and the
report does not claim that the exclusion was never touched.

**Practice next time.** Enumerate excluded paths before searching, pass them as
explicit exclusions to every glob, listing and grep command, and run orientation
searches from the authorised input list rather than from the project root.
Disclose any boundary crossing before continuing, not in a later write-up.

**Self-checks versus student verification.** Of these three, only the diagonal
error was caught by an agent self-check. The file-creation mistake was caught by
the student comparing the report with the instruction; the search-boundary
mistake was caught by reviewing recorded tool calls after the fact. The student's
Excel check (section 7) is a separate student-executed arithmetic verification
and did not detect any of these mistakes. Agent self-checks are useful but are
not independent verification.

The full log is in `mistakes.md`.

## 9. Reflection: where this could help and where review remains necessary

On the recorded evidence, the most defensible use of this system is **decision
support, not autonomous publishing**. The AI suggestion agreed exactly with the
student's manual label on 162 of 200 texts (81.0%), with especially high
agreement on human-labelled Sports (50/53) and Sci/Tech (22/22). An editor could
use such suggestions to prioritise or pre-sort clear cases and to route
boundary cases to review.

The disagreement review shows why review cannot be removed. The largest
disagreement pair was World to Business (14 items), followed by Business to
Sci/Tech (11). These are exactly the cases where the codebook asks for a
judgment about the main focus of a text: a political story with economic
consequences, a product announcement without much technical explanation, or a
business partnership with a security theme. In the retrospective review, 8
disagreements were judged better supported by the human label and 7 as both
defensible. That suggests that a person's judgment still matters at the
boundary, even though the AI handled many clear cases well.

The category hypothesis was inconclusive: the pooled Business/Sci-Tech
disagreement rate was 17.57% versus 5.66% for Sports, a difference of 11.91
percentage points, but the 95% interval ran from −0.06 to +22.77 and included
zero. The study therefore does not establish that the hypothesised category
difference exists in the wider benchmark pool. It also does not measure time
saved, editor workload, or downstream publishing quality.

Human review remains necessary where categories overlap, where the cost of a
wrong section is high, and where accountability for the published choice
matters. The evidence supports a workflow of AI suggestion plus human
confirmation, with explicit uncertainty or exception flags; it does not support
replacing the editor.

## 10. Limitations

- **One annotator.** The human labels are one person's reference, not ground
  truth; no inter-annotator agreement is available.
- **One classifier configuration.** Only one model version, prompt, codebook and
  classification run were analysed. No repeated model runs are available, so
  model-side variability is not quantified.
- **Benchmark scope.** The sample is a probability sample of the remaining AG
  News test pool after 20 preparation exclusions; it is not a representative
  sample of all news or of a newsroom's incoming feed.
- **Retrospective review.** The 23/8/7 assessments were made after seeing both
  labels. They are not independent adjudication and do not provide a revised
  accuracy estimate.
- **No measured time savings.** The project did not measure editing time,
  workload, or the cost of reviewing suggestions.
- **Approximate intervals.** Wilson and Newcombe intervals assume independent
  observations and use no finite-population correction. No p-value or
  multiple-comparison adjustment is reported.
- **Dataset labels are not ground truth.** Original AG News labels have no
  available annotation guidelines in this project and unknown reliability.
- **Associational only.** The analysis describes agreement patterns in one
  sample; it does not identify a causal effect of topic, text difficulty, or any
  other factor.

## 11. Transparent account of assistance and contributions

**Authorship of the evaluation material.** The student reports personally
classifying all 200 evaluation texts without consulting any AI for those
classification decisions, and doing so before seeing any model classification or
original dataset label. The student also reports personally writing all 38
retrospective review explanations and assessments without asking an AI to
produce those judgments. Those reviews were made after both the human and AI
labels were visible, so they are student-authored retrospective assessments, not
blinded independent annotations and not independent adjudication. AI assistance
with preparation, checking and documentation is described below; it is distinct
from authorship of the labels and review judgments. The project was therefore
**not** performed without AI assistance.

- **Student.** The student set the project and analysis plan, completed the
  initial preparation labels before receiving feedback, manually classified all
  200 evaluation texts with confidence and uncertainty reasons before seeing AI
  or dataset labels, wrote the explanations and assessments in the 38-item review
  workbook, and entered and executed the Excel verification formulas.
- An auxiliary AI assistant. Assistance covered planning, prompt drafting,
  troubleshooting, preparation feedback, codebook clarification, interpretation
  and verification.
- **OpenCode analysis agent.** The OpenCode agent implemented the saved analysis
  scripts, reconciliation, original-label comparison and documentation at the
  student's request, using `opencode/deepseek-v4.1-flash-free` (section 6.1). It
  is not the classifier and did not produce the human labels or the review
  judgments.
- **Classifier model.** `gemini-3.5-flash-lite` produced the AI labels through
  the API protocol described in section 2.

## 12. Files and navigation

- Plan and rules: `plan.md`, `AGENTS.md`, `codebook.md`, `data/README.md`
- Primary results: `results/agent_run/`, `results/workflow_run/`
- Reconciliation: `results/run_comparison.md`
- Qualitative review: `results/disagreement_review_completed.xlsx`,
  `results/qualitative_review_summary.md`
- Original-label comparison: `results/original_label_comparison.md`
- Student Excel check: `results/student_excel_verification.md`
- Mistakes log: `mistakes.md`
- Analysis model metadata: `results/agent_run/analysis_model_metadata.md`
- Delivery checklist: `results/final_delivery_checklist.md`
- Reproduction instructions: `README.md`
