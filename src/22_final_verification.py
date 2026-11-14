"""Final verification of the delivery package.

Checks:
  - frozen input hashes against freeze notes and the recorded raw-data hash;
  - key numbers in final_report.md against saved result files;
  - local links in final_report.md and README.md;
  - the student Excel workbook formulas and summary values;
  - repository hygiene markers without reading .env or using Git.

Writes results/final_delivery_checklist.md. Does not modify any frozen input or
analysis result.

Run:
  uv run --with openpyxl src/22_final_verification.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

SEED = 42

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "final_report.md"
README = PROJECT / "README.md"
CHECKLIST = PROJECT / "results" / "final_delivery_checklist.md"

MANUAL_NOTE = PROJECT / "results" / "manual_labels_freeze_note.md"
AI_NOTE = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "classification_freeze_note.md"
CODEBOOK_NOTE = PROJECT / "results" / "codebook_freeze_note.md"
DATA_README = PROJECT / "data" / "README.md"
MANUAL_XLSX = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
CODEBOOK = PROJECT / "codebook.md"
RAW = PROJECT / "data" / "raw" / "test-00000-of-00001.parquet"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"
INPUT_HASHES = PROJECT / "results" / "agent_run" / "input_hashes.csv"
EXCEL_CHECK = PROJECT / "results" / "aiproject_manualcheck.xlsx"

AGREEMENT = PROJECT / "results" / "agent_run" / "agreement_summary.json"
CATEGORY = PROJECT / "results" / "workflow_run" / "category_hypothesis_summary.json"
QUALITATIVE = PROJECT / "results" / "qualitative_review_summary.json"
ORIGINAL = PROJECT / "results" / "original_label_comparison.json"
RECONCILE = PROJECT / "results" / "run_comparison.md"

CHECKS: list[tuple[str, bool, str]] = []


def add(name: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(passed), detail))


def sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def labeled_hash(path: Path, label: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        rf"{re.escape(label)}\s*:?\s*`([0-9A-Fa-f]{{64}})`", text, flags=re.S)
    return matches[0].upper() if len(matches) == 1 else None


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def normalise(text: str) -> str:
    """Collapse whitespace so checks are immune to Markdown line wrapping."""
    return re.sub(r"\s+", " ", text).strip()


def require_text(name: str, text: str, needle: str) -> None:
    add(name, normalise(needle) in normalise(text), f"missing text: {needle}")


def main() -> None:
    print(f"random seed fixed at {SEED} (no stochastic step in this script)")

    # Frozen hashes
    tests = [
        ("manual workbook hash", MANUAL_XLSX, MANUAL_NOTE, "Workbook SHA-256"),
        ("AI classification hash", AI_CSV, AI_NOTE, "SHA-256"),
        ("codebook hash", CODEBOOK, CODEBOOK_NOTE,
         "SHA-256 of the frozen codebook"),
    ]
    for name, path, note, label in tests:
        expected = labeled_hash(note, label)
        observed = sha256(path)
        add(name, expected is not None and observed == expected,
            f"expected {expected}, observed {observed}")

    raw_expected = re.search(
        r"SHA-256:\s*`([0-9A-Fa-f]{64})`",
        DATA_README.read_text(encoding="utf-8"))
    raw_observed = sha256(RAW)
    add("raw data hash", bool(raw_expected)
        and raw_observed == raw_expected.group(1).upper(),
        f"recorded {raw_expected.group(1).upper() if raw_expected else None}, "
        f"observed {raw_observed}")

    manifest_observed = sha256(MANIFEST)
    hashes = pd.read_csv(INPUT_HASHES, dtype=str)
    manifest_rows = hashes[hashes["path"].str.replace("\\", "/", regex=False)
                           .str.endswith("data/derived/evaluation_manifest.csv")]
    recorded_manifest = (manifest_rows["observed_sha256"].iloc[0].upper()
                         if len(manifest_rows) == 1 else None)
    add("manifest hash matches prior recorded observation",
        recorded_manifest is not None and manifest_observed == recorded_manifest,
        f"recorded {recorded_manifest}, observed {manifest_observed}")

    # Key saved values
    agreement = read_json(AGREEMENT)
    category = read_json(CATEGORY)
    qualitative = read_json(QUALITATIVE)
    original = read_json(ORIGINAL)

    add("primary item count", agreement["n_items"] == 200,
        f"n_items={agreement['n_items']}")
    add("primary agreements", agreement["agreements"] == 162,
        f"agreements={agreement['agreements']}")
    add("primary disagreement count", agreement["disagreements"] == 38,
        f"disagreements={agreement['disagreements']}")
    add("primary agreement rate", abs(agreement["agreement_rate"] - 0.81) < 1e-12,
        f"rate={agreement['agreement_rate']}")

    pooled = category["groups"]["pooled_business_scitech"]
    sports = category["groups"]["sports"]
    add("pooled group counts", pooled["items"] == 74
        and pooled["disagreements"] == 13,
        f"items={pooled['items']}, disagreements={pooled['disagreements']}")
    add("sports group counts", sports["items"] == 53
        and sports["disagreements"] == 3,
        f"items={sports['items']}, disagreements={sports['disagreements']}")
    add("category difference",
        abs(category["difference_pp"] - 11.907190209077003) < 1e-12,
        f"difference_pp={category['difference_pp']}")

    add("reviewed disagreements", qualitative["reviewed"] == 38,
        f"reviewed={qualitative['reviewed']}")
    expected_counts = {"AI label better supported": 23,
                      "human label better supported": 8,
                      "both defensible": 7}
    add("qualitative assessment counts",
        qualitative["assessment_counts"] == expected_counts,
        f"counts={qualitative['assessment_counts']}")
    qchecks = qualitative["checks"]
    add("qualitative preservation checks",
        qchecks["text_mismatches"] == 0
        and qchecks["label_mismatches"] == 0
        and qchecks["confidence_mismatches"] == 0
        and qchecks["uncertainty_reason_mismatches"] == 0
        and qchecks["blank_explanations"] == 0
        and qchecks["blank_assessments"] == 0,
        f"checks={qchecks}")

    add("original-label item count", original["checks"]["n"] == 200,
        f"n={original['checks']['n']}")
    add("original-label text alignment",
        original["checks"]["text_mismatches"] == 0,
        f"text_mismatches={original['checks']['text_mismatches']}")
    add("human-dataset matches",
        original["human_vs_dataset"]["matches"] == 147,
        f"matches={original['human_vs_dataset']['matches']}")
    add("ai-dataset matches",
        original["ai_vs_dataset"]["matches"] == 164,
        f"matches={original['ai_vs_dataset']['matches']}")

    reconcile_text = RECONCILE.read_text(encoding="utf-8")
    add("reconciliation 69 checks, 0 failed",
        "Comparisons performed: **69**; failed: **0**." in reconcile_text,
        "expected reconciliation summary line")

    # Student Excel workbook
    wb_f = load_workbook(EXCEL_CHECK, data_only=False, read_only=True)
    wb_v = load_workbook(EXCEL_CHECK, data_only=True, read_only=True)
    ws_f = wb_f["comparison_table"]
    ws_v = wb_v["comparison_table"]
    formulas_ok = all(
        ws_f.cell(r, 6).value == f"=--(B{r}=C{r})"
        for r in range(2, 202)
    )
    values = [ws_v.cell(r, 6).value for r in range(2, 202)]
    add("student Excel 200 direct formulas",
        formulas_ok and len(values) == 200,
        "F2:F201 expected =--(B{r}=C{r})")
    add("student Excel summary values",
        ws_v.cell(2, 8).value == 200
        and ws_v.cell(3, 8).value == 162
        and abs(float(ws_v.cell(4, 8).value) - 0.81) < 1e-12,
        f"H2={ws_v.cell(2, 8).value}, H3={ws_v.cell(3, 8).value}, "
        f"H4={ws_v.cell(4, 8).value}")
    add("student Excel formula results sum to matches",
        sum(int(v) for v in values if v is not None) == 162,
        f"sum(F2:F201)={sum(int(v) for v in values if v is not None)}")
    wb_f.close()
    wb_v.close()

    # Report text against saved values
    report_text = REPORT.read_text(encoding="utf-8")
    require_text("report overall agreement", report_text, "162/200")
    require_text("report overall rate", report_text, "81.0%")
    require_text("report overall interval", report_text, "75.0% to 85.8%")
    require_text("report pooled denominator", report_text, "13/74")
    require_text("report pooled rate", report_text, "17.57%")
    require_text("report sports denominator", report_text, "3/53")
    require_text("report sports rate", report_text, "5.66%")
    require_text("report difference", report_text, "+11.91")
    require_text("report Newcombe interval", report_text, "−0.06 to +22.77")
    require_text("report review counts", report_text,
                 "| AI label better supported | 23 |")
    require_text("report human review count", report_text,
                 "| Human label better supported | 8 |")
    require_text("report both-defensible count", report_text,
                 "| Both defensible | 7 |")
    require_text("report original human match", report_text, "147/200")
    require_text("report original AI match", report_text, "164/200")
    require_text("report implementation caveat", report_text,
                 "implementation consistency, not independent validation")
    require_text("report search-boundary wording", report_text,
                 "instruction-following failure")
    require_text("report Excel provenance", report_text,
                 "not an unaided manual calculation")

    # Documentation corrections of 2026-11-14
    readme_text = README.read_text(encoding="utf-8")
    phrase = "gemini-3.5-flash-lite, accessed through the Gemini API v1beta"
    require_text("report model/API phrase", report_text, phrase)
    require_text("README model/API phrase", readme_text, phrase)
    add("v1beta not presented as model version",
        re.search(r"gemini-3\.5-flash-lite`?\s*\(v1beta\)", report_text) is None
        and re.search(r"gemini-3\.5-flash-lite`?\s*\(v1beta\)", readme_text) is None,
        "found the old 'model (v1beta)' wording")
    add("README reproduction markers",
        all(s in readme_text for s in (
            "### Verify the saved outputs",
            "### Regenerate the analysis in a separate copy",
            "prior_outputs/workflow_run/")),
        "expected verify/regenerate sections and the prior_outputs marker")
    add("README optional .env note",
        "not required to reproduce the saved analysis" in readme_text
        and "that single hygiene check will fail" not in readme_text,
        "README still warns that a missing .env fails verification")
    archive_dir = PROJECT / "archive" / "2026-11-14_documentation_corrections"
    archived = ["final_report.md", "README.md", "ARCHIVE_NOTE.md",
                "results/final_delivery_checklist.md"]
    add("prior document versions archived",
        all((archive_dir / name).is_file() for name in archived),
        f"missing: {[n for n in archived if not (archive_dir / n).is_file()]}")

    # Local links
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    allowed_created = {"results/final_delivery_checklist.md"}
    for doc_name, doc_text in (("final_report.md", report_text),
                               ("README.md", README.read_text(encoding="utf-8"))):
        missing = []
        for target in link_pattern.findall(doc_text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            path = (PROJECT / target).resolve()
            if not path.exists() and target not in allowed_created:
                missing.append(target)
        add(f"{doc_name} local links", not missing,
            f"missing: {missing}" if missing else f"checked links in {doc_name}")

    # Repository hygiene; no Git is available, so no tracked-file check is claimed.
    gitignore = (PROJECT / ".gitignore").read_text(encoding="utf-8")
    ignore_lines = gitignore.splitlines()
    add(".env ignored", ".env" in ignore_lines,
        ".gitignore must contain .env")
    add(".env.* ignored", ".env.*" in ignore_lines,
        ".gitignore must contain .env.*")
    add(".venv ignored", any(line.strip() == ".venv/"
                             for line in ignore_lines),
        ".gitignore must contain .venv/")
    add("no .git directory", not (PROJECT / ".git").exists(),
        "a Git repository would require a tracked-file audit")

    # A local .env is optional: existence is checked, contents are never read.
    env_present = (PROJECT / ".env").exists()
    if env_present:
        env_status = ("Present; contents not read. Credentials must remain "
                      "local; `.env` and `.env.*` are excluded from version "
                      "control.")
        env_ok = ".env" in ignore_lines and ".env.*" in ignore_lines
        env_detail = (env_status if env_ok else
                      "ignore rules for .env and .env.* are missing from "
                      ".gitignore")
    else:
        env_status = "Not present; not required for saved-analysis reproduction."
        env_ok = True
        env_detail = env_status
    add("local .env handling", env_ok, env_detail)
    secret_pattern = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
    combined_docs = report_text + "\n" + README.read_text(encoding="utf-8")
    add("no Google API key pattern in docs",
        secret_pattern.search(combined_docs) is None,
        "scanned final_report.md and README.md")

    # Checklist
    technical_failures = [name for name, passed, _ in CHECKS if not passed]
    status = ("Ready for final review; not published."
              if not technical_failures else
              "NOT READY: technical checks failed; see below.")

    lines = [
        "# Final delivery checklist",
        "",
        f"- Script: `src/22_final_verification.py`",
        f"- Run (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Status: **{status}**",
        "",
        "## Completed checks",
        "",
    ]
    for name, passed, detail in CHECKS:
        mark = "x" if passed else " "
        suffix = "" if passed else f" — {detail}"
        lines.append(f"- [{mark}] {name}{suffix}")
    lines += [
        "",
        "## Documentation corrections",
        "",
        "- Model/API wording: `gemini-3.5-flash-lite, accessed through the Gemini "
        "API v1beta` in `final_report.md` and `README.md`; `v1beta` is kept "
        "separate from the recorded `model_version` metadata.",
        "- Reproduction instructions: exact procedure for a separate copy, only "
        "the guarded `results/workflow_run/` outputs moved aside, and a split "
        "between verification and regeneration commands.",
        "- Pre-correction documents preserved in "
        "`archive/2026-11-14_documentation_corrections/`.",
        "- Local `.env` handling: optional; its absence is reported without "
        "failing verification, and its presence is reported without reading "
        "the file.",
        "",
        "## Local environment",
        "",
        f"- `.env`: {env_status}",
        "",
        "## Publication and repository",
        "",
        "- [ ] GitHub publication — **not done**. No Git client is installed and "
        "no `.git/` directory exists; nothing was staged, committed, pushed or "
        "published.",
        "- [ ] Tracked-file audit — **not possible locally**. Without a Git "
        "repository, there are no tracked files to inspect. `.env` and `.env.*` "
        "are ignored, and `.venv/`, `__pycache__/`, `*.py[cod]` and "
        "`.pytest_cache/` were added to `.gitignore`.",
        "",
    ]
    superseded = sorted(CHECKLIST.parent.glob(
        "final_delivery_checklist_superseded_*.md"))
    if superseded:
        lines += ["## Preserved earlier checklists", ""]
        for path in superseded:
            lines.append(f"- `{path.relative_to(PROJECT).as_posix()}` — an earlier "
                         "run that recorded a different status; kept unchanged.")
        lines.append("")
    lines += [
        "## Final status",
        "",
        status,
        "",
    ]
    if technical_failures:
        lines.append("Failed checks:")
        lines.append("")
        for name in technical_failures:
            lines.append(f"- {name}")
        lines.append("")

    # Never silently replace a checklist that recorded a different status.
    new_content = "\n".join(lines)
    archive: Path | None = None
    if CHECKLIST.exists():
        previous = CHECKLIST.read_text(encoding="utf-8")
        previous_status = next(
            (line for line in previous.splitlines() if line.startswith("- Status:")),
            "")
        new_status = next(
            (line for line in new_content.splitlines() if line.startswith("- Status:")),
            "")
        if previous_status and previous_status != new_status:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            archive = CHECKLIST.with_name(
                f"final_delivery_checklist_superseded_{stamp}.md")
            archive.write_text(previous, encoding="utf-8")
            lines.append("")
            lines.append("## Superseded checklist")
            lines.append("")
            lines.append(f"The previous checklist, which recorded a different "
                         f"status, was preserved as "
                         f"`{archive.relative_to(PROJECT).as_posix()}`.")
            lines.append("")
            new_content = "\n".join(lines)

    CHECKLIST.write_text(new_content, encoding="utf-8")
    print(f"checklist written: {CHECKLIST.relative_to(PROJECT)}")
    print(f"checks: {len(CHECKS)}; failed: {len(technical_failures)}")
    for name, passed, detail in CHECKS:
        print(f"  {'PASS' if passed else 'FAIL'}: {name}"
              + ("" if passed else f" ({detail})"))
    if technical_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
