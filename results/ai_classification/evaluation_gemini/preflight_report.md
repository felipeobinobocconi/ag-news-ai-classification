# Evaluation batch preflight — Gemini API

- Date: 2026-11-14T12:35:58Z
- Model: `gemini-3.5-flash-lite` (v1beta); configuration identical to dry_run_05_gemini

## Checks

- [x] codebook.md SHA-256 matches results/codebook_freeze_note.md
- [x] exactly 200 unique item_ids identical to evaluation_manifest.csv
- [ ] Google project free-tier / no-billing status verified

## Evidence

- codebook.md SHA-256: `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` (freeze-note match: True)
- Billing check: Cannot verify the Google project's billing status programmatically in this environment: the Cloud Billing API requires OAuth2 user/service credentials, not an API key, and gcloud is not installed. No request has been sent.

## Billing gate

Requests are **not** sent until `--confirm-free-tier` is passed after the
operator verifies billing manually. Options to check:

- AI Studio rate-limit page (https://aistudio.google.com/rate-limit): the tier
  badge shows Free vs paid for the project.
- AI Studio projects page (https://aistudio.google.com/projects): project tier.
- Cloud Console billing (https://console.cloud.google.com/billing): the project
  has no billing account / billing disabled.
- With gcloud installed: `gcloud billing projects describe PROJECT_ID` →
  `billingEnabled: false`.

This cannot be checked with only an API key: the Cloud Billing API requires
OAuth2 credentials and the `cloudbilling.projects.getBillingInfo` permission.
