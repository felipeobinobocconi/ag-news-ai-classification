# Input verification — agent run

- Script: `src/13_agent_run_verify_inputs.py`
- Run (UTC): 2026-11-14T13:24:11.020924+00:00
- Random seed: 42 (fixed; no stochastic step)
- Authorised inputs only: labelled workbook, Gemini AI classifications,
  and evaluation manifest. No original dataset labels, news-text review,
  model calls, `.env` access, `results/workflow_run/` or earlier
  analysis scripts were used.

## SHA-256 verification

| File | Recorded | Observed | Match | Recorded in |
| ---- | -------- | -------- | ----- | ----------- |
| `data\derived\evaluation_200_labelled.xlsx` | `D71C12E8FBD7E070698413FCB341F162665CB0101A5539A454D25CB49203948A` | `D71C12E8FBD7E070698413FCB341F162665CB0101A5539A454D25CB49203948A` | True | results\manual_labels_freeze_note.md |
| `results\ai_classification\evaluation_gemini\ai_classifications.csv` | `760633BD862E1902772A93B02DEE3CFF1492295451BAED3A794F215C3FC78AFB` | `760633BD862E1902772A93B02DEE3CFF1492295451BAED3A794F215C3FC78AFB` | True | results\ai_classification\evaluation_gemini\classification_freeze_note.md |
| `data\derived\evaluation_manifest.csv` | `none` | `1F0417686F17DF69766BB5ACED25557B04890FDE99A40018098DCC5FF8D048CD` | n/a | no freeze note available to this run records a manifest hash |
| `codebook.md` | `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` | `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` | True | results\codebook_freeze_note.md |

The manifest has no recorded hash in any freeze note available to this
run; its observed hash is recorded for traceability and its integrity is
validated structurally (exact ID set, unique positions, range check).

## Row counts

| Step | Rows | Reason |
| ---- | ---- | ------ |
| Labelled workbook | 200 | frozen human reference |
| AI classifications | 200 | frozen Gemini reference |
| Manifest | 200 | sampling frame for ID validation |
| After one-to-one inner join | 200 | exact `item_id` match; no row dropped |

## Validation checks

- [x] labelled workbook SHA-256 matches manual labels freeze note
- [x] AI classification CSV SHA-256 matches AI freeze note
- [x] codebook SHA-256 matches codebook freeze note (context check)
- [x] manifest SHA-256 recorded for traceability (no freeze-note hash exists for it)
- [x] labelled workbook has required columns
- [x] AI CSV has required columns
- [x] manifest has required columns
- [x] workbook has exactly 200 rows
- [x] AI CSV has exactly 200 rows
- [x] manifest has exactly 200 rows
- [x] workbook item_id is unique
- [x] AI item_id is unique
- [x] manifest item_id is unique
- [x] manifest source_row_position is unique
- [x] workbook IDs are exactly eval_001..eval_200
- [x] AI IDs are exactly eval_001..eval_200
- [x] manifest IDs are exactly eval_001..eval_200
- [x] workbook, AI and manifest ID sets are identical
- [x] manifest positions lie within documented source range 0..7599
- [x] workbook has no blank text values
- [x] all human_label values are valid 0-3
- [x] all AI label values are valid 0-3
- [x] all human_confidence values are confident/uncertain
- [x] every uncertain item has a nonblank uncertainty_reason
- [x] all AI calls have status ok
- [x] all AI calls have finish_reason STOP
- [x] all AI calls report one model version
- [x] all AI attempt counts are positive integers
- [x] join retains exactly 200 rows
- [x] join matches both sides for every row
- [x] join drops no human row
- [x] join drops no AI row

## Summary counts

- Items: 200
- Agreements: 162; disagreements: 38
- `human_confidence`: confident = 154, uncertain = 46
- `human_label` counts: 0 (World) = 73, 1 (Sports) = 53, 2 (Business) = 52, 3 (Sci/Tech) = 22
- Model version(s) in AI file: gemini-3.5-flash-lite

All checks passed. The analysis dataset contains no news text.
