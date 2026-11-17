# Student Excel verification

- Workbook: `results/aiproject_manualcheck.xlsx`
- Sheet: `comparison_table`
- Source table: `results/workflow_run/comparison_table.csv`
- Scope: arithmetic check on the saved comparison table only

## What was done

The student imported `results/workflow_run/comparison_table.csv` into Excel. An auxiliary AI assistant supplied the formulas below; the student entered and executed them in the workbook; this was not an unaided manual calculation.

In column `F` (`my_check`), rows 2 to 201, the student entered a direct comparison of the human and AI labels. The formula in `F2` is `=--(B2=C2)`, and the same pattern continues through `F201` (`=--(B201=C201)`). Column `B` is `human_label`; column `C` is `ai_label`. The comparison does not use the existing `agreement` column in `E`.

The summary cells are:

| Check | Cell | Formula | Saved value |
| --- | --- | --- | --- |
| Items counted | `H2` | `=COUNTA(A2:A201)` | 200 |
| Matches | `H3` | `=SUM(F2:F201)` | 162 |
| Agreement rate | `H4` | `=H3/H2` | 0.81 (81%) |

There are 200 formula cells in `F2:F201`, one per item. Their saved results are 162 ones and 38 zeros.

## Reported inspection

The student reports that an auxiliary AI assistant inspected the uploaded workbook and confirmed all 200 formulas and their saved results.

## What this check supports

This is a student-executed, AI-assisted verification performed outside the OpenCode analysis scripts. It confirms the arithmetic on the saved comparison table: the stored `human_label` and `ai_label` values produce 162 matches out of 200 items, or 81% agreement.

It does not check label correctness, codebook application, the original dataset join, or the correctness of the OpenCode analysis scripts. The formulas compare the labels already saved in the workbook; they do not re-derive those labels from the source data.

## Provenance

This note was written in OpenCode from the saved workbook and the student's account. Reading the workbook for this note did not modify it. No analysis was rerun, no label was changed, and no model call was made while preparing this document.
