# Dry Run Verification — attempt 02

- Script: `src/06_dry_run_classifier_attempt02.py`
- Date: 2026-11-13
- Model call: ONE synthetic test call (example from the codebook). No
  evaluation text was sent. Attempt-01 logs (`../dry_run/`) and the attempt-01
  scratch location were preserved untouched.
- Model: `opencode/glm-5.3-flash-free`; CLI `opencode v2.2.5`; no model switching; no
  retries.

## Evidence log

- CLI path: `C:\Users\felip\AppData\Roaming\ai.opencode.desktop\cli\2.2.5-x64\opencode-cli.exe`; version output: `opencode v2.2.5`
- OPENCODE_* environment variables removed from the subprocess environment: ['OPENCODE', 'OPENCODE_CLIENT', 'OPENCODE_DISABLE_EMBEDDED_WEB_UI', 'OPENCODE_EXPERIMENTAL_FILEWATCHER', 'OPENCODE_EXPERIMENTAL_ICON_DISCOVERY', 'OPENCODE_SESSION_ID', 'OPENCODE_TERMINAL']
- codebook.md SHA-256: `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` (freeze-note match: True)
- Global config entries (C:\Users\felip\.config\opencode): ['service.json']
- Classifier agent written to `C:\Users\felip\AppData\Local\Temp\opencode\agnews_dry_run_02\.opencode\agents\classifier.md` (deny-all permissions; model opencode/glm-5.3-flash-free); SHA-256 `16ACC4705F1E8C9858812596FE12A4C3F7036324CCE0D6F646B6FC7B58017CD6`
- Ancestor-chain audit findings: none (full listing: audit_files.txt)
- CLI catalog check: model listed = True
- Exact prompt saved to prompt.txt (Part A extracted by section headings; prompt SHA-256 `14161D532CD5C9A19E2ED4F701344E18774E28A7D0CDD9AE95953CBC475071A0`)
- Scratch listing before: 3 entries; after: 3; new: none
- Session-storage isolation with --standalone is NOT claimed as verified; the observation above is descriptive only.
- Occurrences of 'classifier'/'denied' in raw stderr logs: none found
- QUOTA BLOCKED: error type provider.free-limit; retry_after_ms 35041000 (~9.7 h). Logged and stopped; no retries performed.

## Checks

- [x] CLI exists and reports a version ('opencode v2.2.5')
- [x] codebook.md SHA-256 matches results/codebook_freeze_note.md
- [x] global OpenCode config contains only service.json
- [x] no AGENTS.md / opencode.json(c) / .opencode directories in the ancestor chain
- [x] model 'opencode/glm-5.3-flash-free' appears in the CLI model catalog

## Verdict

BLOCKED: free-usage quota still exhausted

## Verified configuration vs observed behavior

- **Verified configuration (static evidence):** deny-all classifier agent
  definition written in the loaded scratch location; codebook hash matches the
  freeze note; global config contains only `service.json`; no ancestor
  configuration or instructions; model present in the CLI catalog. Attempt-01
  additionally showed the CLI validates agent IDs (`Agent not found` for a
  nonexistent ID) — referenced, not re-tested here.
- **Observed behavior (runtime evidence):** the structured output of the
  single synthetic call, including the final answer, session ID, and
  tool-related structures. Observing no tool calls is NOT proof of
  enforcement; enforcement itself was not independently tested.
- **Not verified:** `--standalone` session-storage isolation; the model's
  internal version ("not available"); whether the agent's `model:` field (vs a
  default) served the request (the two are indistinguishable here).
