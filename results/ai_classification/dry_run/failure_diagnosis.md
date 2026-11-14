# Dry Run Failure Diagnosis (addendum)

Written after the dry run completed with checks not all passed. The original
run artifacts (`verification.md`, `stdout_raw.txt`, `stderr_raw.txt`,
`negative_control_stdout.txt`, `parsed_result.json`) are preserved exactly as
produced; this file only documents the diagnosis. Nothing was retried and no
permissions were weakened.

## What failed

**Main dry call — provider quota, not a configuration failure.**

- Structured error from the CLI (`stdout_raw.txt`):
  `"type": "provider.free-limit"`, HTTP status 429, message: "Free usage limit
  reached. Free models work in OpenCode (https://opencode.ai); subscribe to
  OpenCode Go to keep going, or switch models."
- `retryAfterMs: 33149000` ≈ 9 h 12 m. The failing request is timestamped
  2026-11-12T14:47:31Z, so the limit is expected to reset around
  2026-11-13T00:00Z (approximate; server-controlled).
- Session created but no model completion was produced:
  `ses_e2fc5990bffecAboIpUEw40u9m` (from the error event).
- The stderr server log confirms: `AI.Error.QuotaExceeded: Free usage limit
  reached ... SessionStep.attempt ... SessionRunner.drain`.

**Negative control — agent-ID validation (distinct error).**

- `negative_control_stdout.txt`: `"Agent not found: \"definitely_not_an_agent_xyz\""`
  — a configuration validation error, *not* the quota error.
- Interpretation: `--agent` names are validated against the loaded
  configuration, and the request using `--agent classifier` was accepted.
  Together with the `agent.updated` event and the location boot line for the
  scratch directory in `stderr_raw.txt`, this is **configuration-level
  evidence that the dedicated classifier agent exists in the loaded config**.
- It is still not direct proof that the deny-all permission rule was enforced
  during a model call — the model never answered, so tool behavior remains
  unverified.

## What remains unverified (to be checked when the limit allows a retry)

1. Final-answer format and parsing (`label: <0-3>`).
2. Classification correctness on the synthetic example (expected label 1).
3. Tool behavior under the deny-all permissions (zero tool calls observed in
   the failed call, but that is not evidence of enforcement).
4. `--standalone` session-storage isolation (not claimed, not audited).

## No evaluation content was exposed

- The only text sent to the model was the synthetic codebook example.
- No evaluation texts, human annotations, or original dataset labels were
  read or transmitted. The call failed before any completion anyway.

## Options for proceeding (user decisions; no automatic action taken)

- (a) Re-run the dry run (`uv run src/05_dry_run_classifier.py`) after the
  free-tier limit resets (~9.2 h later). The script guards against overwrite;
  the existing `dry_run` directory must be moved/archived first, or the run
  will stop by design.
- (b) Subscribe to OpenCode Go or connect a provider — a cost decision for
  the project owner. Per the project brief, the model would remain
  `opencode/glm-5.3-flash-free`; no model switching is implemented.
- No other remediation is proposed. The script itself behaved correctly and
  logged the failure honestly; the blocker is external (free-tier quota).
