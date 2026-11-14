# Final delivery checklist

- Script: `src/22_final_verification.py`
- Run (UTC): 2026-11-14T20:14:55.734670+00:00
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
- [ ] report overall agreement — missing text: 162/200
- [x] report overall rate
- [x] report overall interval
- [ ] report pooled denominator — missing text: 13/74
- [x] report pooled rate
- [ ] report sports denominator — missing text: 3/53
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
- [ ] report Excel provenance — missing text: not an unaided manual calculation
- [x] final_report.md local links
- [x] README.md local links
- [x] .env ignored
- [x] .venv ignored
- [x] no .git directory
- [x] .env present but not read
- [x] no Google API key pattern in docs

## Publication and repository

- [ ] GitHub publication — **not done**. No Git client is installed and no `.git/` directory exists; nothing was staged, committed, pushed or published.
- [ ] Tracked-file audit — **not possible locally**. Without a Git repository, there are no tracked files to inspect. `.env` and `.env.*` are ignored, and `.venv/`, `__pycache__/`, `*.py[cod]` and `.pytest_cache/` were added to `.gitignore`.

## Final status

NOT READY: technical checks failed; see below.

Failed checks:

- report overall agreement
- report pooled denominator
- report sports denominator
- report Excel provenance
