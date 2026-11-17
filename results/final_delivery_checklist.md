# Final delivery checklist

- Script: `src/22_final_verification.py`
- Run (UTC): 2026-11-17T15:47:47.507405+00:00
- Status: **Ready for final review; this revision made no publication.**

## Completed checks

- [x] manual workbook hash
- [x] AI classification hash
- [x] codebook hash
- [x] raw data hash
- [x] manifest hash matches prior recorded observation
- [x] primary item count
- [x] primary agreements
- [x] primary disagreement count
- [x] primary agreement rate
- [x] pooled group counts
- [x] sports group counts
- [x] category difference
- [x] reviewed disagreements
- [x] qualitative assessment counts
- [x] qualitative preservation checks
- [x] original-label item count
- [x] original-label text alignment
- [x] human-dataset matches
- [x] ai-dataset matches
- [x] Business category counts
- [x] Sci/Tech category counts
- [x] World category counts
- [x] human and AI label distributions
- [x] dataset label distribution
- [x] workflow analysis model recorded
- [x] autonomous analysis model recorded
- [x] analysis scripts attributed to the recorded model
- [x] reconciliation 69 checks, 0 failed
- [x] student Excel 200 direct formulas
- [x] student Excel summary values
- [x] student Excel formula results sum to matches
- [x] report overall agreement
- [x] report overall rate
- [x] report overall interval
- [x] report pooled denominator
- [x] report pooled rate
- [x] report sports denominator
- [x] report sports rate
- [x] report difference
- [x] report Newcombe interval
- [x] report review counts
- [x] report human review count
- [x] report both-defensible count
- [x] report original human match
- [x] report original AI match
- [x] report implementation caveat
- [x] report search-boundary wording
- [x] removed Excel limitation sentence absent
- [x] report Business/Sci-Tech split
- [x] report Sci/Tech zero disagreements
- [x] report Business rate
- [x] report World split
- [x] report World rate
- [x] report pooling caveat
- [x] report distribution table header
- [x] report distribution World
- [x] report distribution Sports
- [x] report distribution Business
- [x] report distribution Sci/Tech
- [x] report distribution non-inference
- [x] report analysis model identifier
- [x] report OpenCode CLI version
- [x] report fresh session
- [x] report classifier not repeated
- [x] report analysis-agent separation
- [x] report student authorship
- [x] report review authorship
- [x] report retrospective limit
- [x] report auxiliary assistant wording
- [x] report Excel verification sentence
- [x] README assistance paragraph
- [x] README assistance section
- [x] report dataset-access paragraph removed
- [x] README allowlist paragraph removed
- [x] report historical section removed
- [x] README historical records section removed
- [x] product name absent from current docs
- [x] revision archive note present
- [x] revision archive note documents exclusion
- [x] AGENTS matrix-label rule
- [x] AGENTS excluded-search rule
- [x] AGENTS prospective-rule note
- [x] mistakes table has no empty row
- [x] mistakes table has three dated rows
- [x] report model/API phrase
- [x] README model/API phrase
- [x] v1beta not presented as model version
- [x] README reproduction markers
- [x] README optional .env note
- [x] prior document versions archived
- [x] final_report.md local links
- [x] README.md local links
- [x] .env ignored
- [x] .env.* ignored
- [x] .venv ignored
- [x] .env not tracked
- [x] .env.* not tracked
- [x] local .env handling
- [x] no Google API key pattern in docs

## Documentation corrections

- Model/API wording: `gemini-3.5-flash-lite, accessed through the Gemini API v1beta` in `final_report.md` and `README.md`; `v1beta` is kept separate from the recorded `model_version` metadata.
- Reproduction instructions: exact procedure for a separate copy, only the guarded `results/workflow_run/` outputs moved aside, and a split between verification and regeneration commands.
- Pre-correction documents preserved in `archive/2026-11-14_documentation_corrections/`.
- Local `.env` handling: optional; its absence is reported without failing verification, and its presence is reported without reading the file.
- Reflection revision (2026-11-17): per-mistake narratives, descriptive category patterns (section 3.4), recorded analysis-model identifiers, fresh-session clarification, and assistance/authorship wording. Pre-revision documents preserved in `archive/2026-11-17_reflection_and_wording/`.
- Analysis-model provenance: `results/agent_run/analysis_model_metadata.json`, recorded by `src/23_record_analysis_model_metadata.py` from the local OpenCode session store.

## Local environment

- `.env`: Not present; not required for saved-analysis reproduction.

## Publication and repository

- Repository state — a `.git/` directory is present and pre-dates this revision; its index lists 949 tracked paths. No Git client is installed, so status, diff and tracked-file history checks were not possible.
- Publication — a remote is configured and its reflog records a push that pre-dates this revision. This revision made no commit, push or publication.
- Tracked secrets — `.env` and `.env.*` are not in the Git index when the index is readable; `.venv/`, `__pycache__/`, `*.py[cod]` and `.pytest_cache/` are ignored.

## Preserved earlier checklists

- `results/final_delivery_checklist_superseded_20261114T201636Z.md` — an earlier run that recorded a different status; kept unchanged.
- `results/final_delivery_checklist_superseded_20261114T204229Z.md` — an earlier run that recorded a different status; kept unchanged.
- `results/final_delivery_checklist_superseded_20261114T204250Z.md` — an earlier run that recorded a different status; kept unchanged.
- `results/final_delivery_checklist_superseded_20261117T144141Z.md` — an earlier run that recorded a different status; kept unchanged.
- `results/final_delivery_checklist_superseded_20261117T144940Z.md` — an earlier run that recorded a different status; kept unchanged.

## Final status

Ready for final review; this revision made no publication.
