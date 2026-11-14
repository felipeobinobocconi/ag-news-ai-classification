# Final delivery checklist

- Script: `src/22_final_verification.py`
- Run (UTC): 2026-11-14T20:42:29.810980+00:00
- Status: **NOT READY: technical checks failed; see below.**

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
- [x] report Excel provenance
- [x] report model/API phrase
- [x] README model/API phrase
- [x] v1beta not presented as model version
- [x] README reproduction markers
- [ ] README optional .env note — README still warns that a missing .env fails verification
- [x] prior document versions archived
- [x] final_report.md local links
- [x] README.md local links
- [x] .env ignored
- [x] .env.* ignored
- [x] .venv ignored
- [x] no .git directory
- [x] local .env handling
- [x] no Google API key pattern in docs

## Documentation corrections

- Model/API wording: `gemini-3.5-flash-lite, accessed through the Gemini API v1beta` in `final_report.md` and `README.md`; `v1beta` is kept separate from the recorded `model_version` metadata.
- Reproduction instructions: exact procedure for a separate copy, only the guarded `results/workflow_run/` outputs moved aside, and a split between verification and regeneration commands.
- Pre-correction documents preserved in `archive/2026-11-14_documentation_corrections/`.
- Local `.env` handling: optional; its absence is reported without failing verification, and its presence is reported without reading the file.

## Local environment

- `.env`: Not present; not required for saved-analysis reproduction.

## Publication and repository

- [ ] GitHub publication — **not done**. No Git client is installed and no `.git/` directory exists; nothing was staged, committed, pushed or published.
- [ ] Tracked-file audit — **not possible locally**. Without a Git repository, there are no tracked files to inspect. `.env` and `.env.*` are ignored, and `.venv/`, `__pycache__/`, `*.py[cod]` and `.pytest_cache/` were added to `.gitignore`.

## Preserved earlier checklists

- `results/final_delivery_checklist_superseded_20261114T201636Z.md` — an earlier run that recorded a different status; kept unchanged.

## Final status

NOT READY: technical checks failed; see below.

Failed checks:

- README optional .env note


## Superseded checklist

The previous checklist, which recorded a different status, was preserved as `results/final_delivery_checklist_superseded_20261114T204229Z.md`.
