# Exit-code note (addendum, written after the run)

The original attempt-02 artifacts are preserved exactly as produced. This file
documents one unexplained observation; nothing was re-run and no permissions
were changed.

## Observation

- The script's quota-blocked branch is coded to end the process with exit
  status 2 (`sys.exit(2)` in `src/06_dry_run_classifier_attempt02.py`).
- Both VERDICT lines of that branch were printed to stdout, so the branch
  executed.
- The process nonetheless exited with status 1 (as reported by the shell
  harness).
- The bundled CLI's own exit code for the model call was 1 (captured reliably
  by `subprocess.run` and recorded in `parsed_result.json` as
  `"returncode": 1`); that is the CLI process, not this script.

## What was tested (small probe scripts in the temp directory, no project files)

1. `print` of the same em-dash line + `sys.exit(2)` → exit status 2.
2. Same, plus a `subprocess.run` call and file writes first → exit status 2.
3. Same, invoked as `uv run <script.py>` (script mode, as the real script was)
   → exit status 2.

The discrepancy could not be reproduced or explained from these probes. The
verdict does not depend on it: the quota block is established by the saved
artifacts (`parsed_result.json`: `"error_type": "provider.free-limit"`,
`stdout_raw.txt` structured error event, `stderr_raw.txt` server log with
`AI.Error.QuotaExceeded`), not by the process exit code.

## Quota timing (from saved artifacts)

- Error timestamp: 2026-11-13T14:15:59Z; `retryAfterMs` 35,041,000 ≈ 9 h 44 m
  → expected reset ≈ 2026-11-14T00:00Z (server-controlled, approximate).
- Attempt 01's error (2026-11-12T14:47:31Z, retry-after ≈ 9 h 12 m) pointed to
  a reset at ≈ 2026-11-13T00:00Z, consistent with a daily 00:00 UTC reset.
- Observation for planning: by 14:16Z on Nov 13 the free allowance was
  exhausted again. The interactive analysis session itself runs on the same
  free model/allowance and consumes quota with each turn, so the daily free
  allowance may be small relative to a 200-call batch. This is a hypothesis
  from timing, not a verified quota-accounting fact.
