"""Agent run, step 1: verify frozen inputs, validate IDs, build analysis dataset.

Inputs (only the three files authorised for this run):
  data/derived/evaluation_200_labelled.xlsx
  results/ai_classification/evaluation_gemini/ai_classifications.csv
  data/derived/evaluation_manifest.csv

Freeze notes are read only to compare SHA-256 values. No news text is
reviewed, no original dataset label is read, no classification model is
called, no .env file is accessed, and no previous analysis result or earlier
analysis script is consulted.

Outputs (results/agent_run/):
  input_hashes.csv
  input_verification.md
  analysis_dataset.csv
  13_run_log.txt

Run:
  uv run --with openpyxl src/13_agent_run_verify_inputs.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Fixed seed although this script has no stochastic step (AGENTS.md rule 5).
SEED = 42
np.random.seed(SEED)

PROJECT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"

MANUAL_FREEZE = PROJECT / "results" / "manual_labels_freeze_note.md"
AI_FREEZE = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "classification_freeze_note.md"
CODEBOOK_FREEZE = PROJECT / "results" / "codebook_freeze_note.md"
CODEBOOK = PROJECT / "codebook.md"

OUTDIR = PROJECT / "results" / "agent_run"
HASH_CSV = OUTDIR / "input_hashes.csv"
REPORT = OUTDIR / "input_verification.md"
DATASET = OUTDIR / "analysis_dataset.csv"
RUN_LOG = OUTDIR / "13_run_log.txt"

N_EXPECTED = 200
VALID_LABELS = {0, 1, 2, 3}
VALID_CONF = {"confident", "uncertain"}
CATEGORY = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str = "") -> None:
        print(message)
        self.lines.append(str(message))

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


log = Log()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def labeled_hash(path: Path, label: str) -> str | None:
    """Return the SHA-256 on the line introduced by `label`, else None.

    A freeze note can contain more than one hash (e.g. the manual-labels note
    records both the workbook hash and the codebook hash), so the label is
    matched explicitly instead of taking the only backticked hash.
    """
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        rf"{re.escape(label)}\s*:?\s*`([0-9A-Fa-f]{{64}})`", text, flags=re.S)
    return matches[0].upper() if len(matches) == 1 else None


def fail(message: str) -> None:
    log(f"CHECK FAILED: {message}")
    log.save(RUN_LOG)
    sys.exit(1)


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    log("AGENT RUN STEP 13 — input verification and ID validation")
    log(f"run_utc: {datetime.now(timezone.utc).isoformat()}")
    log(f"random seed fixed at {SEED} (no stochastic step in this script)")
    log("")
    log("AUTHORISED INPUTS ONLY:")
    for p in (WORKBOOK, AI_CSV, MANIFEST):
        log(f"  - {p.relative_to(PROJECT)}")
    log("NOT read: results/workflow_run/, src/11*, src/12*, data/raw/, .env")
    log("")

    # ---------------------------------------------------------------- hashes
    log("STEP 1 — SHA-256 verification against freeze notes")
    expected_workbook = labeled_hash(MANUAL_FREEZE, "Workbook SHA-256")
    expected_ai = labeled_hash(AI_FREEZE, "SHA-256")
    expected_codebook = labeled_hash(
        CODEBOOK_FREEZE, "SHA-256 of the frozen codebook")

    if expected_workbook is None:
        fail("manual labels freeze note does not contain a unique workbook SHA-256")
    if expected_ai is None:
        fail("AI classification freeze note does not contain a unique SHA-256")
    if expected_codebook is None:
        fail("codebook freeze note does not contain a unique codebook SHA-256")

    observed_workbook = sha256(WORKBOOK)
    observed_ai = sha256(AI_CSV)
    observed_manifest = sha256(MANIFEST)
    observed_codebook = sha256(CODEBOOK)

    hash_rows = [
        {
            "path": str(WORKBOOK.relative_to(PROJECT)),
            "recorded_sha256": expected_workbook,
            "observed_sha256": observed_workbook,
            "match": observed_workbook == expected_workbook,
            "recorded_in": str(MANUAL_FREEZE.relative_to(PROJECT)),
        },
        {
            "path": str(AI_CSV.relative_to(PROJECT)),
            "recorded_sha256": expected_ai,
            "observed_sha256": observed_ai,
            "match": observed_ai == expected_ai,
            "recorded_in": str(AI_FREEZE.relative_to(PROJECT)),
        },
        {
            "path": str(MANIFEST.relative_to(PROJECT)),
            "recorded_sha256": "",
            "observed_sha256": observed_manifest,
            "match": "",
            "recorded_in": "no freeze note available to this run records a manifest hash",
        },
        {
            "path": str(CODEBOOK.relative_to(PROJECT)),
            "recorded_sha256": expected_codebook,
            "observed_sha256": observed_codebook,
            "match": observed_codebook == expected_codebook,
            "recorded_in": str(CODEBOOK_FREEZE.relative_to(PROJECT)),
        },
    ]
    hash_df = pd.DataFrame(hash_rows)
    hash_df.to_csv(HASH_CSV, index=False, encoding="utf-8")

    checks: list[tuple[str, bool]] = []
    checks.append(("labelled workbook SHA-256 matches manual labels freeze note",
                   observed_workbook == expected_workbook))
    checks.append(("AI classification CSV SHA-256 matches AI freeze note",
                   observed_ai == expected_ai))
    checks.append(("codebook SHA-256 matches codebook freeze note (context check)",
                   observed_codebook == expected_codebook))
    checks.append(("manifest SHA-256 recorded for traceability "
                   "(no freeze-note hash exists for it)",
                   bool(observed_manifest)))

    for name, ok in checks:
        log(f"  CHECK {'PASS' if ok else 'FAIL'}: {name}")
    log(f"  workbook observed: {observed_workbook}")
    log(f"  AI CSV observed:   {observed_ai}")
    log(f"  manifest observed: {observed_manifest} (no recorded reference hash)")
    log("")

    if not (observed_workbook == expected_workbook and observed_ai == expected_ai
            and observed_codebook == expected_codebook):
        fail("a recorded frozen-input hash does not match; stopping before analysis")

    # ----------------------------------------------------------- read inputs
    log("STEP 2 — read inputs (no text is displayed or reviewed)")
    labelled = pd.read_excel(WORKBOOK, sheet_name=0, dtype=str, keep_default_na=False)
    ai = pd.read_csv(AI_CSV, encoding="utf-8-sig")
    manifest = pd.read_csv(MANIFEST, encoding="utf-8-sig")
    log(f"  row counts before any step: workbook={len(labelled)}, "
        f"AI={len(ai)}, manifest={len(manifest)}")

    required_workbook = {"item_id", "text", "human_label", "human_confidence",
                         "uncertainty_reason"}
    required_ai = {"item_id", "label", "status", "attempts", "finish_reason",
                   "model_version"}
    required_manifest = {"item_id", "source_row_position"}
    checks.append(("labelled workbook has required columns",
                   required_workbook.issubset(labelled.columns)))
    checks.append(("AI CSV has required columns", required_ai.issubset(ai.columns)))
    checks.append(("manifest has required columns",
                   required_manifest.issubset(manifest.columns)))
    for name, ok in checks[-3:]:
        log(f"  CHECK {'PASS' if ok else 'FAIL'}: {name}")
    if not all(ok for _, ok in checks[-3:]):
        fail("one or more inputs lack required columns")

    # Normalise identifiers only; labels are validated before conversion.
    labelled["item_id"] = labelled["item_id"].astype(str).str.strip()
    ai["item_id"] = ai["item_id"].astype(str).str.strip()
    manifest["item_id"] = manifest["item_id"].astype(str).str.strip()
    manifest["source_row_position"] = pd.to_numeric(
        manifest["source_row_position"], errors="raise").astype(int)

    # ----------------------------------------------------------- ID checks
    log("")
    log("STEP 3 — ID and domain validation")
    expected_ids = [f"eval_{i:03d}" for i in range(1, N_EXPECTED + 1)]
    id_checks = [
        ("workbook has exactly 200 rows", len(labelled) == N_EXPECTED),
        ("AI CSV has exactly 200 rows", len(ai) == N_EXPECTED),
        ("manifest has exactly 200 rows", len(manifest) == N_EXPECTED),
        ("workbook item_id is unique", labelled["item_id"].is_unique),
        ("AI item_id is unique", ai["item_id"].is_unique),
        ("manifest item_id is unique", manifest["item_id"].is_unique),
        ("manifest source_row_position is unique",
         manifest["source_row_position"].is_unique),
        ("workbook IDs are exactly eval_001..eval_200",
         sorted(labelled["item_id"]) == expected_ids),
        ("AI IDs are exactly eval_001..eval_200",
         sorted(ai["item_id"]) == expected_ids),
        ("manifest IDs are exactly eval_001..eval_200",
         sorted(manifest["item_id"]) == expected_ids),
        ("workbook, AI and manifest ID sets are identical",
         set(labelled["item_id"]) == set(ai["item_id"]) == set(manifest["item_id"])),
        ("manifest positions lie within documented source range 0..7599",
         bool(manifest["source_row_position"].between(0, 7599).all())),
        ("workbook has no blank text values",
         bool(labelled["text"].astype(str).str.strip().ne("").all())),
    ]
    for name, ok in id_checks:
        log(f"  CHECK {'PASS' if ok else 'FAIL'}: {name}")
    checks.extend(id_checks)
    if not all(ok for _, ok in id_checks):
        fail("ID or manifest validation failed; stopping before analysis")

    # ------------------------------------------------------ label validation
    human_label = pd.to_numeric(labelled["human_label"].str.strip(), errors="coerce")
    ai_label = pd.to_numeric(ai["label"], errors="coerce")
    confidence = labelled["human_confidence"].str.strip().str.lower()
    reason = labelled["uncertainty_reason"].str.strip()
    status = ai["status"].astype(str).str.strip().str.lower()
    finish = ai["finish_reason"].astype(str).str.strip().str.upper()
    model_versions = sorted(ai["model_version"].astype(str).str.strip().unique())

    label_checks = [
        ("all human_label values are valid 0-3",
         bool(human_label.notna().all() and human_label.isin(VALID_LABELS).all())),
        ("all AI label values are valid 0-3",
         bool(ai_label.notna().all() and ai_label.isin(VALID_LABELS).all())),
        ("all human_confidence values are confident/uncertain",
         bool(set(confidence) <= VALID_CONF)),
        ("every uncertain item has a nonblank uncertainty_reason",
         bool(reason[confidence == "uncertain"].ne("").all())),
        ("all AI calls have status ok", bool((status == "ok").all())),
        ("all AI calls have finish_reason STOP", bool((finish == "STOP").all())),
        ("all AI calls report one model version", len(model_versions) == 1),
        ("all AI attempt counts are positive integers",
         bool(pd.to_numeric(ai["attempts"], errors="coerce").ge(1).all())),
    ]
    for name, ok in label_checks:
        log(f"  CHECK {'PASS' if ok else 'FAIL'}: {name}")
    checks.extend(label_checks)
    if not all(ok for _, ok in label_checks):
        fail("label/domain validation failed; stopping before analysis")

    # ---------------------------------------------------------------- join
    log("")
    log("STEP 4 — one-to-one join on item_id")
    human = labelled[["item_id", "human_label", "human_confidence"]].copy()
    human["human_label"] = human_label.astype(int)
    human["human_confidence"] = confidence

    machine = ai[["item_id", "label"]].copy()
    machine["ai_label"] = ai_label.astype(int)

    joined = human.merge(machine[["item_id", "ai_label"]], on="item_id",
                         how="inner", validate="one_to_one", indicator=True)
    log(f"  row counts: human={len(human)}, AI={len(machine)}, "
        f"after inner one-to-one join={len(joined)}")
    log("  reason: join adds AI labels to human rows by exact item_id; "
        "no filter or drop is applied")
    n_left_only = int((joined["_merge"] == "left_only").sum())
    n_right_only = int((joined["_merge"] == "right_only").sum())
    n_both = int((joined["_merge"] == "both").sum())
    log(f"  matched={n_both}, human-only={n_left_only}, AI-only={n_right_only}")
    join_checks = [
        ("join retains exactly 200 rows", len(joined) == N_EXPECTED),
        ("join matches both sides for every row", n_both == N_EXPECTED),
        ("join drops no human row", n_left_only == 0),
        ("join drops no AI row", n_right_only == 0),
    ]
    for name, ok in join_checks:
        log(f"  CHECK {'PASS' if ok else 'FAIL'}: {name}")
    checks.extend(join_checks)
    if not all(ok for _, ok in join_checks):
        fail("join validation failed")

    joined = joined.drop(columns=["_merge"])
    joined["human_category"] = joined["human_label"].map(CATEGORY)
    joined["ai_category"] = joined["ai_label"].map(CATEGORY)
    joined["disagreement"] = (joined["human_label"] != joined["ai_label"]).astype(int)
    joined["human_group"] = np.where(
        joined["human_label"] == 1,
        "Sports",
        np.where(joined["human_label"].isin([2, 3]),
                 "Business/Sci-Tech pooled", "World (not in comparison)"),
    )
    joined = joined.sort_values("item_id").reset_index(drop=True)
    joined = joined[["item_id", "human_label", "human_category", "human_confidence",
                     "ai_label", "ai_category", "human_group", "disagreement"]]
    joined.to_csv(DATASET, index=False, encoding="utf-8")
    log(f"  analysis dataset written: {DATASET.relative_to(PROJECT)} "
        f"({len(joined)} rows, no text column)")

    # ------------------------------------------------------------- report
    n_confident = int((joined["human_confidence"] == "confident").sum())
    n_uncertain = int((joined["human_confidence"] == "uncertain").sum())
    human_counts = joined["human_label"].value_counts().sort_index()
    n_agree = int((joined["disagreement"] == 0).sum())
    n_disagree = int(joined["disagreement"].sum())

    log("")
    log("STEP 5 — descriptive counts (full primary sample)")
    log(f"  rows={len(joined)}; agreements={n_agree}; disagreements={n_disagree}")
    log(f"  human_confidence: confident={n_confident}, uncertain={n_uncertain}")
    log("  human_label counts: " + ", ".join(
        f"{k} ({CATEGORY[k]})={int(v)}" for k, v in human_counts.items()))

    lines = [
        "# Input verification — agent run",
        "",
        f"- Script: `src/13_agent_run_verify_inputs.py`",
        f"- Run (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Random seed: {SEED} (fixed; no stochastic step)",
        "- Authorised inputs only: labelled workbook, Gemini AI classifications,",
        "  and evaluation manifest. No original dataset labels, news-text review,",
        "  model calls, `.env` access, `results/workflow_run/` or earlier",
        "  analysis scripts were used.",
        "",
        "## SHA-256 verification",
        "",
        "| File | Recorded | Observed | Match | Recorded in |",
        "| ---- | -------- | -------- | ----- | ----------- |",
    ]
    for row in hash_rows:
        match = row["match"] if isinstance(row["match"], bool) else "n/a"
        lines.append(
            f"| `{row['path']}` | `{row['recorded_sha256'] or 'none'}` | "
            f"`{row['observed_sha256']}` | {match} | {row['recorded_in']} |"
        )
    lines += [
        "",
        "The manifest has no recorded hash in any freeze note available to this",
        "run; its observed hash is recorded for traceability and its integrity is",
        "validated structurally (exact ID set, unique positions, range check).",
        "",
        "## Row counts",
        "",
        "| Step | Rows | Reason |",
        "| ---- | ---- | ------ |",
        f"| Labelled workbook | {len(labelled)} | frozen human reference |",
        f"| AI classifications | {len(ai)} | frozen Gemini reference |",
        f"| Manifest | {len(manifest)} | sampling frame for ID validation |",
        f"| After one-to-one inner join | {len(joined)} | exact `item_id` match; "
        "no row dropped |",
        "",
        "## Validation checks",
        "",
    ]
    lines += [f"- [{'x' if ok else ' '}] {name}" for name, ok in checks]
    lines += [
        "",
        "## Summary counts",
        "",
        f"- Items: {len(joined)}",
        f"- Agreements: {n_agree}; disagreements: {n_disagree}",
        f"- `human_confidence`: confident = {n_confident}, uncertain = {n_uncertain}",
        f"- `human_label` counts: " + ", ".join(
            f"{k} ({CATEGORY[k]}) = {int(v)}" for k, v in human_counts.items()),
        f"- Model version(s) in AI file: {', '.join(model_versions)}",
        "",
        "All checks passed. The analysis dataset contains no news text.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    log("")
    log(f"files written: {HASH_CSV.relative_to(PROJECT)}; "
        f"{REPORT.relative_to(PROJECT)}; {DATASET.relative_to(PROJECT)}; "
        f"{RUN_LOG.relative_to(PROJECT)}")
    log.save(RUN_LOG)


if __name__ == "__main__":
    main()
