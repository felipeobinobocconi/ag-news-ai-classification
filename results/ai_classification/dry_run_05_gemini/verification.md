# Dry Run Verification — attempt 05 (Gemini API, gemini-3.5-flash-lite)

- Script: `src/09_gemini_dry_run.py`
- Date: 2026-11-14
- Model: `gemini-3.5-flash-lite` (official Gemini API, v1beta endpoint)
- Exactly ONE synthetic request (codebook example); no evaluation texts.

## Evidence log

- codebook.md SHA-256: `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` (freeze-note match: True)
- Exact prompt saved to prompt.txt (Part A extracted by section headings; SHA-256 `14161D532CD5C9A19E2ED4F701344E18774E28A7D0CDD9AE95953CBC475071A0`)
- Request: POST `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent`; single-turn contents; no tools, no google_search/grounding, no system instruction, no conversation history; temperature 0.0, maxOutputTokens 1024, candidateCount 1; timeout 120 s
- Authentication: `x-goog-api-key` header from local .env (key not logged, not in URL)

## Checks

- [x] codebook.md SHA-256 matches results/codebook_freeze_note.md
- [x] API request returned HTTP 200 with a JSON body
- [x] response body parses as JSON
- [x] exact model served (response modelVersion: gemini-3.5-flash-lite)
- [x] final answer parsed as a single allowed label line
- [x] synthetic example classified as expected (expected 1; got 1)

## Parsed result

- Parsed label: `1`
- Served model version: `gemini-3.5-flash-lite`
- Finish reason: `STOP`
- Usage: `{"promptTokenCount": 2280, "candidatesTokenCount": 4, "totalTokenCount": 2284, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 2280}], "serviceTier": "standard"}`

## Verdict

pass

## Notes

- The API key was loaded locally from `.env` for authentication only and is
  replaced by [REDACTED] in every saved file.
- No tools, search grounding, or conversation history were enabled.
- Temperature is fixed at 0 as recorded in the request body.
