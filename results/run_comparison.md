# Reconciliation of workflow_run and agent_run analyses

- Script: `src/18_reconcile_runs.py`
- Run (UTC): 2026-11-14T13:38:19.161377+00:00
- Workflow sources: `results/workflow_run/*`
- Agent sources: `results/agent_run/*`
- Numerical tolerance: absolute `1e-09` on unrounded values
  (proportions for Wilson endpoints; percentage points for the Newcombe endpoints).
- No frozen label, codebook, study-design element or analysis result was changed; no model was called; no original dataset label was read.

## Overall counts and agreement

| Quantity | Workflow | Agent | Agent - workflow | Check |
| --- | --- | --- | --- | --- |
| items | 200 | 200 | 0 | PASS |
| agreements | 162 | 162 | 0 | PASS |
| disagreements (derived) | 38 | 38 | 0 | PASS |
| overall agreement rate | 0.81000000000000005 | 0.81000000000000005 | 0 | PASS |
| items recomputed from item table | 200 | 200 | 0 | PASS |
| agreements recomputed from item table | 162 | 162 | 0 | PASS |
| disagreements recomputed from item table | 38 | 38 | 0 | PASS |
| workflow matrix total | 200 | 200 | 0 | PASS |
| agent matrix total | 200 | 200 | 0 | PASS |
| workflow matrix diagonal | 162 | 162 | 0 | PASS |
| agent matrix diagonal | 162 | 162 | 0 | PASS |

Both runs recompute the same item-level counts from their saved classification tables. The workflow summary's matrix total and diagonal are also checked against the workflow matrix itself.

## Confusion matrix after category alignment

Category alignment: World = 0, Sports = 1, Business = 2, Sci/Tech = 3. Workflow row names `human_*` and column names `ai_*` were mapped to the same codes as the agent's numeric columns. Rows are human labels; columns are AI labels.

### Workflow counts

| Human \ AI | World | Sports | Business | Sci/Tech | Total |
| --- | --- | --- | --- | --- | --- |
| 0 World | 51 | 3 | 14 | 5 | 73 |
| 1 Sports | 1 | 50 | 2 | 0 | 53 |
| 2 Business | 2 | 0 | 39 | 11 | 52 |
| 3 Sci/Tech | 0 | 0 | 0 | 22 | 22 |
| **AI total** | 54 | 53 | 55 | 38 | 200 |

### Agent counts

| Human \ AI | World | Sports | Business | Sci/Tech | Total |
| --- | --- | --- | --- | --- | --- |
| 0 World | 51 | 3 | 14 | 5 | 73 |
| 1 Sports | 1 | 50 | 2 | 0 | 53 |
| 2 Business | 2 | 0 | 39 | 11 | 52 |
| 3 Sci/Tech | 0 | 0 | 0 | 22 | 22 |
| **AI total** | 54 | 53 | 55 | 38 | 200 |

### Cell-by-cell comparison

| Cell (human -> AI) | Workflow | Agent | Agent - workflow | Check |
| --- | --- | --- | --- | --- |
| 0 World -> 0 World | 51 | 51 | 0 | PASS |
| 0 World -> 1 Sports | 3 | 3 | 0 | PASS |
| 0 World -> 2 Business | 14 | 14 | 0 | PASS |
| 0 World -> 3 Sci/Tech | 5 | 5 | 0 | PASS |
| 1 Sports -> 0 World | 1 | 1 | 0 | PASS |
| 1 Sports -> 1 Sports | 50 | 50 | 0 | PASS |
| 1 Sports -> 2 Business | 2 | 2 | 0 | PASS |
| 1 Sports -> 3 Sci/Tech | 0 | 0 | 0 | PASS |
| 2 Business -> 0 World | 2 | 2 | 0 | PASS |
| 2 Business -> 1 Sports | 0 | 0 | 0 | PASS |
| 2 Business -> 2 Business | 39 | 39 | 0 | PASS |
| 2 Business -> 3 Sci/Tech | 11 | 11 | 0 | PASS |
| 3 Sci/Tech -> 0 World | 0 | 0 | 0 | PASS |
| 3 Sci/Tech -> 1 Sports | 0 | 0 | 0 | PASS |
| 3 Sci/Tech -> 2 Business | 0 | 0 | 0 | PASS |
| 3 Sci/Tech -> 3 Sci/Tech | 22 | 22 | 0 | PASS |

All 16 cells were compared. Maximum absolute difference: `0`. Row totals and column totals also match.

## Group comparison

| Quantity | Workflow | Agent | Agent - workflow | Check |
| --- | --- | --- | --- | --- |
| pooled denominator | 74 | 74 | 0 | PASS |
| sports denominator | 53 | 53 | 0 | PASS |
| pooled disagreements | 13 | 13 | 0 | PASS |
| sports disagreements | 3 | 3 | 0 | PASS |
| pooled rate | 0.17567567567567569 | 0.17567567567567569 | 0 | PASS |
| sports rate | 0.056603773584905662 | 0.056603773584905662 | 0 | PASS |
| difference (percentage points) | 11.907190209077003 | 11.907190209077003 | 0 | PASS |
| workflow table pooled rate vs summary | 0.17567567567567569 | 0.17567567567567569 | 0 | PASS |
| workflow table sports rate vs summary | 0.056603773584905662 | 0.056603773584905662 | 0 | PASS |
| agent table pooled rate vs summary | 0.17567567567567569 | 0.17567567567567569 | 0 | PASS |
| agent table sports rate vs summary | 0.056603773584905662 | 0.056603773584905662 | 0 | PASS |

The group contrast is pooled Business/Sci-Tech minus Sports, with each group's own item count as denominator.

## Interval endpoints (unrounded)

| Endpoint | Workflow | Agent | Absolute difference | Check |
| --- | --- | --- | --- | --- |
| pooled Wilson lower | 0.10564208536683117 | 0.10564208536683116 | 1.3877787807814457e-17 | PASS |
| pooled Wilson upper | 0.27771993370109499 | 0.27771993370109493 | 5.5511151231257827e-17 | PASS |
| Sports Wilson lower | 0.019436661484935766 | 0.019436661484935766 | 0 | PASS |
| Sports Wilson upper | 0.15370208310180888 | 0.15370208310180888 | 0 | PASS |
| Newcombe lower (pp) | -0.064770984723877545 | -0.064770984723878933 | 1.3877787807814457e-15 | PASS |
| Newcombe upper (pp) | 22.767404211485097 | 22.76740421148509 | 7.1054273576010019e-15 | PASS |

All interval comparisons use absolute tolerance `1e-09`. Maximum absolute endpoint difference: `7.10543e-15`. Wilson endpoints are proportions; Newcombe endpoints are percentage points.

## Item-level comparison

| Item-level check | Workflow | Agent | Check |
| --- | --- | --- | --- |
| ID sets identical | True | True | PASS |
| workflow rows / unique IDs | 200 | 200 | PASS |
| agent rows / unique IDs | 200 | 200 | PASS |
| one-to-one merged rows | 200 | 200 | PASS |

| Field compared by item_id | Items compared | Mismatches | Check |
| --- | --- | --- | --- |
| human_label | 200 | 0 | PASS |
| ai_label | 200 | 0 | PASS |
| human_confidence | 200 | 0 | PASS |
| agreement = 1 - disagreement | 200 | 0 | PASS |

The item-level merge is one-to-one on `item_id`; no missing or extra IDs were found. The workflow `agreement` indicator equals one minus the agent `disagreement` indicator for every item.

## Internal consistency and the workflow diagonal incident

Both saved matrices sum to the same total, and both diagonals equal the corresponding agreement count. Pooled and Sports disagreement counts recomputed from the matrix slices match the group tables in both runs.

The recorded workflow session contains the earlier failed matrix check and its correction:

- Failure (message seq `1716`):

```
LOAD: 200 rows from comparison_table.csv
GROUPS: pooled Business/Sci-Tech = 74 items; Sports = 53 items
KEPT: uncertain human annotations -> pooled 26, Sports 4
STOP: counts disagree with confusion matrix: computed (74, 13, 53, 3), matrix (74, 72, 53, 3)
SCRIPT_EXIT=1
```

- Cause identified (seq `1723`): Bug in matrix disagreement computation: cm.loc[pooled_rows].values.diagonal() — the pooled rows matrix values is 2x4 (rows Business, S/T; cols World,Sports,Business,SciTech). numpy diagonal of a non-square array returns min(2,4)=2 elements: positions (0,0)=2 and (1,1)=0 → 2, not 39+22. Need explicit: agreements = cm.loc["human_Business","Business"] + cm.loc["human_Sci/Tech","Sci/Tech"] = 39+22=61; disagreements = 74-61=13.  Fix:  cm_pooled_total = int(cm.loc[pooled_rows].values.sum()) cm_pooled_dis = cm_pooled_total - int(cm.loc["human_Business","Business"] + cm.loc["human_Sci/Tech","Sci/Tech"])  Similarly sports: diag = cm.loc["human_Sports","Sports"]=50; dis=3. Current: cm.loc["human_Sports"].sum() - cm.loc["human_Sports","Sports"] = 53-50=3 correct.  Edit script and rerun. No outputs were written (stop before writes).

- Correction (seq `1723`): replaced the slice diagonal with explicit diagonal cells.

```
old: cm_pooled_total = int(cm.loc[pooled_rows].values.sum())
    cm_pooled_dis = int(cm.loc[pooled_rows].values.sum() - cm.loc[pooled_rows].values.diagonal().sum())
new: cm_pooled_total = int(cm.loc[pooled_rows].values.sum())
    cm_pooled_agree = int(cm.loc["human_Business", "Business"] + cm.loc["human_Sci/Tech", "Sci/Tech"])
    cm_pooled_dis = cm_pooled_total - cm_pooled_agree
```

- Successful rerun (seq `1734`):

```
LOAD: 200 rows from comparison_table.csv
GROUPS: pooled Business/Sci-Tech = 74 items; Sports = 53 items
KEPT: uncertain human annotations -> pooled 26, Sports 4
CHECK PASS: group counts match the saved confusion matrix (pooled 74/13, Sports 53/3)

TABLE:
                                         group  items  disagreements  rate_pct
Business/Sci-Tech (pooled, human_label 2 or 3)     74             13 17.567568
                        Sports (human_label 1)     53              3  5.660377
DIFFERENCE: 11.91 pp; 95% Newcombe: [-0.06, 22.77] pp
OUTPUTS: C:\Users\felip\my-analysis\results\workflow_run
VERDICT: STEP 7 COMPLETE
SCRIPT_EXIT=0
```

In the failed check, `diagonal()` on the 2x4 pooled row slice returned only the (Business, World) and (Sci/Tech, Sports) cells, so pooled disagreements were reported as 72 instead of 13. The explicit fix sums the Business and Sci/Tech diagonal cells (39 + 22 = 61 agreements; 74 - 61 = 13 disagreements). The failure stopped the script before outputs were written; the saved workflow outputs come from the successful rerun.

## Confident/uncertain split (agent-added exploratory analysis)

**This split was added by the autonomous agent. It is an exploratory, descriptive analysis, not the primary hypothesis test.** It is not used in the group contrast or the Newcombe interval, and it must not be read as a substitute for the pre-specified analysis.

| Human confidence | Items | Agreements | Agreement rate |
| --- | --- | --- | --- |
| confident | 154 | 135 | 87.66% |
| uncertain | 46 | 27 | 58.70% |

The workflow reported only the number of uncertain annotations kept per comparison group; the agent additionally reported the overall confidence split. The per-group uncertain counts match between the runs, but the split itself remains exploratory.

## Recorded tool-call review: initial autonomous search

- Session: `ses_e25ca40cfffeBwMwykmm0E7pxD` — "Autonomous evaluation agreement run"
- Recorded in: `C:\Users\felip\.local\share\opencode\opencode.db` (read-only)

| Message seq | Tool | Recorded input | Observed returned output |
| --- | --- | --- | --- |
| 29 | glob | glob `**/*.md` | 2 workflow_run path lines among 2,108 chars; paths only, no file contents |
| 67 | shell | recursive `Get-ChildItem -Recurse -File results` | 7 workflow_run path lines among 51,372 chars; sizes, no file contents |
| 78 | grep | grep `evaluation_manifest|manifest.*SHA|SHA-256.*manifest` in `C:\Users\felip\my-analysis\results` with `include=*.md` | 0 workflow_run lines in returned output; 3 matches total, all outside workflow_run |

Server log for the grep invocation:

```
timestamp=2026-11-14T13:19:09.878Z level=INFO run=238ac6af message="spawning process" command="C:\\Users\\felip\\.cache\\opencode\\bin\\rg.exe" args="[\"--no-config\",\"--json\",\"--hidden\",\"--no-messages\",\"--glob=*.md\",\"--glob=!**/.git/**\",\"--\",\"evaluation_manifest|manifest.*SHA|SHA-256.*manifest\",\".\"]" cwd="C:\\Users\\felip\\my-analysis\\results" role=server
```

**Observed actions.** The glob call returned 2 workflow_run paths among the `.md` paths it matched (2,108 characters of output). The recursive listing returned 7 workflow_run paths with sizes (51,372 characters of output). Both returned path strings only, never file contents. The grep returned 3 matching lines, all from files outside workflow_run, and 0 workflow_run lines.

**Recorded disclosure.** The autonomous run's own `results/agent_run/analysis_choices.md` states that the listing displayed names and sizes under `results/workflow_run/` and that the content search traversed that directory without returning lines from it.

**Uncertain context exposure.** The server log shows that the grep was executed with ripgrep over `results` using `--glob=*.md` and no workflow_run exclusion. Ripgrep reads file contents to search them, so the search process had file-level access to the workflow_run markdown files. The recorded tool output, however, contains no workflow_run content. Whether any such bytes entered the model context beyond the returned output cannot be established from the record. Strict process-level independence therefore cannot be fully verified; the analysis is independent at the level of returned content and of the scripts' input paths, but this is not a claim of verified non-exposure.

## Verdict

- Comparisons performed: **69**; failed: **0**.
- All numerical comparisons passed: **YES**.
- The two saved analyses are numerically identical at the reported precision and at the item level.
- **This is implementation consistency, not independent validation of the underlying classifications.** Both runs use the same frozen human labels and the same frozen AI labels; agreement between the runs does not add independent evidence about classification quality or accuracy.
- No frozen label, codebook, study-design element or analysis result was changed. `results/workflow_run/` and `results/agent_run/` were read only.

