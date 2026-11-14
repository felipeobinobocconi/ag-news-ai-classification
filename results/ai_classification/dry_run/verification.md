# Dry Run Verification — dedicated classifier agent

- Script: `src/05_dry_run_classifier.py`
- Date: 2026-11-12
- Purpose: gate check before the 200-item evaluation batch. The model call
  used a SYNTHETIC example from the codebook; no evaluation text was sent.
- Model: `opencode/glm-5.3-flash-free` (requested; no model switching implemented)
- Working directory for the model call: `C:\Users\felip\AppData\Local\Temp\opencode\agnews_dry_run` (scratch location; not the project)

## Evidence log

- CLI path: `C:\Users\felip\AppData\Roaming\ai.opencode.desktop\cli\2.2.5-x64\opencode-cli.exe`
- CLI version output: `opencode v2.2.5`
- OPENCODE_* environment variables removed from the subprocess environment: ['OPENCODE', 'OPENCODE_CLIENT', 'OPENCODE_DISABLE_EMBEDDED_WEB_UI', 'OPENCODE_EXPERIMENTAL_FILEWATCHER', 'OPENCODE_EXPERIMENTAL_ICON_DISCOVERY', 'OPENCODE_SESSION_ID', 'OPENCODE_TERMINAL']
- codebook.md SHA-256: `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` (freeze-note match: True)
- Global config entries (C:\Users\felip\.config\opencode): ['service.json']
- Classifier agent written to `C:\Users\felip\AppData\Local\Temp\opencode\agnews_dry_run\.opencode\agents\classifier.md` (deny-all permissions; model opencode/glm-5.3-flash-free); copy saved with SHA-256 `16ACC4705F1E8C9858812596FE12A4C3F7036324CCE0D6F646B6FC7B58017CD6`
- Ancestor-chain audit findings: none (full listing: results/ai_classification/dry_run/audit_files.txt)
- CLI catalog check: model listed = True (raw output saved to models_raw.txt)
- Negative control (nonexistent agent id): exit code 1; error-style evidence in output: True. Interpretation depends on CLI behavior; see verification.md caveats.
- Exact prompt saved to results/ai_classification/dry_run/prompt.txt (Part A extracted by section headings; SHA-256 of prompt file `14161D532CD5C9A19E2ED4F701344E18774E28A7D0CDD9AE95953CBC475071A0`)
- Scratch-location listing before call: 3 entries; after call: 3 entries; new: none
- Session-storage isolation with --standalone is NOT claimed as verified; the new-files observation above is descriptive only, and the standalone server's storage location was not audited.
- Session ID(s) observed in output: ['ses_e2fc5990bffecAboIpUEw40u9m', 'ses_e2fc5990bffecAboIpUEw40u9m', 'ses_e2fc5990bffecAboIpUEw40u9m']
- Model values observed in structured output: none found (requested opencode/glm-5.3-flash-free; internal model version: not available)
- Tool-related keys observed in structured output: none; non-empty tool structures: 0
- IMPORTANT: observing zero tool calls is NOT proof that permissions were denied. Config-level evidence is the deny-all permission rule in the classifier agent definition (results/ai_classification/dry_run/agent_classifier.md); whether OpenCode enforced it in this call could not be independently verified in the dry run.
- Occurrences of 'classifier'/'denied' in raw stderr logs: none found (see stderr_raw.txt)

## Checks

- [x] CLI exists and reports a version ('opencode v2.2.5')
- [x] codebook.md SHA-256 matches results/codebook_freeze_note.md
- [x] global OpenCode config contains only service.json (no global agents/plugins/instructions)
- [x] no AGENTS.md / opencode.json(c) / .opencode directories in the ancestor chain of the scratch location
- [x] model 'opencode/glm-5.3-flash-free' appears in the CLI model catalog
- [x] nonexistent agent id rejected by the CLI (supports that --agent names are validated)
- [ ] main dry call completed (timed out: False; exit code: 1)
- [ ] final answer parsed as a single allowed label line
- [ ] synthetic example classified as expected (expected label 1; got None)

## Verdict

CHECKS NOT ALL PASSED (see caveats; no permissions were weakened)

## Known limitations and uncertainties

- Zero tool calls observed in the structured output is weak evidence; it does
  not prove the deny-all permission rule was enforced. No independent
  enforcement test was performed (none was authorized).
- `--standalone` session-storage isolation was NOT verified; only descriptive
  file listings of the scratch location were recorded.
- Whether the agent's `model:` field (rather than a default) served the
  request could not be directly verified; the model id requested equals the
  id configured in the agent file, so the two are indistinguishable here.
- The negative control result calibrates how much weight `--agent classifier`
  acceptance carries as evidence that the dedicated agent was loaded.
- No evaluation texts, human annotations, or original dataset labels were
  read or sent to the model.
