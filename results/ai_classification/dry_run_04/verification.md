# Dry Run Verification — attempt 04 (DeepSeek)

- Script: `src/08_dry_run_classifier_deepseek_attempt04.py`
- Date: 2026-11-14
- Model call: ONE synthetic test call (example from the codebook). No
  evaluation text was sent. All earlier attempts (../dry_run/,
  ../dry_run_02/, ../dry_run_03_deepseek/) and their scratch locations were
  preserved untouched. plan.md was not modified.
- Model: `opencode/deepseek-v4.1-flash-free` (exact ID re-verified in the installed catalog before the
  call); CLI `opencode v2.2.5`; no model switching; no retries.

## Evidence log

- CLI path: `C:\Users\felip\AppData\Roaming\ai.opencode.desktop\cli\2.2.5-x64\opencode-cli.exe`; version output: `opencode v2.2.5`
- OPENCODE_* environment variables removed from the subprocess environment: ['OPENCODE', 'OPENCODE_CLIENT', 'OPENCODE_DISABLE_EMBEDDED_WEB_UI', 'OPENCODE_EXPERIMENTAL_FILEWATCHER', 'OPENCODE_EXPERIMENTAL_ICON_DISCOVERY', 'OPENCODE_SESSION_ID', 'OPENCODE_TERMINAL']
- codebook.md SHA-256: `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` (freeze-note match: True)
- Global config entries (C:\Users\felip\.config\opencode): ['service.json']
- Exact-ID catalog check: 'opencode/deepseek-v4.1-flash-free' listed = True (no substitution; catalog saved to models_raw.txt)
- Classifier agent written to `C:\Users\felip\AppData\Local\Temp\opencode\agnews_dry_run_04\.opencode\agents\classifier.md` (deny-all permissions; model opencode/deepseek-v4.1-flash-free); SHA-256 `E0DB1547A47B8E92103B60CF630B3F13471764D07A559D67FE00690039382FA2`
- Ancestor-chain audit findings: none (full listing: audit_files.txt)
- Exact prompt saved to prompt.txt (Part A extracted by section headings; prompt SHA-256 `14161D532CD5C9A19E2ED4F701344E18774E28A7D0CDD9AE95953CBC475071A0`)
- Scratch listing before: 3 entries; after: 3; new: none
- Session-storage isolation with --standalone is NOT claimed as verified; the observation above is descriptive only.
- Occurrences of 'classifier'/'denied' in raw stderr logs: none found
- QUOTA BLOCKED: error type provider.free-limit; retry_after_ms 41710000 (~11.6 h). Logged and stopped; no retries performed.

## Checks

- [x] CLI exists and reports a version ('opencode v2.2.5')
- [x] codebook.md SHA-256 matches results/codebook_freeze_note.md
- [x] global OpenCode config contains only service.json
- [x] exact model ID 'opencode/deepseek-v4.1-flash-free' appears in the CLI model catalog
- [x] no AGENTS.md / opencode.json(c) / .opencode directories in the ancestor chain

## Verdict

BLOCKED: free-usage quota still exhausted (DeepSeek attempt 04)

## Verified configuration vs observed behavior

- **Verified configuration (static evidence):** exact model ID present in the
  installed catalog; deny-all classifier agent definition written in the
  loaded scratch location; codebook hash matches the freeze note; global
  config contains only `service.json`; no ancestor configuration or
  instructions. Attempt-01 additionally showed the CLI validates agent IDs
  (`Agent not found`) — referenced, not re-tested here.
- **Observed behavior (runtime evidence):** the structured output of the
  single synthetic call, including the final answer (parsed from structured
  text fields when available; raw-stdout fallback is explicitly flagged in
  `parsed_result.json`), session ID, and tool-related structures. Observing no
  tool calls is NOT proof of enforcement; enforcement itself was not
  independently tested.
- **Not verified:** `--standalone` session-storage isolation; the model's
  internal version ("not available"); whether the agent's `model:` field (vs a
  default) served the request (the two are indistinguishable here).
