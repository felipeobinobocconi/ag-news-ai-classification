"""Final verification of the delivery package.

Checks:
  - frozen input hashes against freeze notes and the recorded raw-data hash;
  - key numbers in final_report.md against saved result files;
  - descriptive category counts and label distributions in final_report.md;
  - recorded analysis-model identifiers and session-separation wording;
  - assistance and authorship wording, and removed-passage checks;
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
import shutil
import struct
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
MODEL_META = PROJECT / "results" / "agent_run" / "analysis_model_metadata.json"
ARCHIVE_NOTE = (PROJECT / "archive" / "2026-11-17_reflection_and_wording"
                / "ARCHIVE_NOTE.md")
AGENTS = PROJECT / "AGENTS.md"
MISTAKES = PROJECT / "mistakes.md"

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


def read_git_index(path: Path) -> list[str] | None:
    """Return tracked paths from a Git index file without a Git client.

    Supports index versions 2 and 3. Version 4 uses path compression and is
    reported as unreadable rather than guessed.
    """
    data = path.read_bytes()
    if data[:4] != b"DIRC":
        return None
    version, count = struct.unpack(">II", data[4:12])
    if version not in (2, 3):
        return None
    offset = 12
    paths: list[str] = []
    for _ in range(count):
        start = offset
        offset += 62
        end = data.index(b"\x00", offset)
        paths.append(data[offset:end].decode("utf-8", "surrogateescape"))
        entry_len = end - start + 1
        offset = end + 1 + ((8 - (entry_len % 8)) % 8)
    return paths


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

    # Descriptive category counts used in section 3.4
    per_category = {row["category"]: row
                    for row in agreement["per_human_category"].values()}
    add("Business category counts",
        per_category["Business"]["n_human"] == 52
        and per_category["Business"]["disagreements"] == 13,
        f"Business={per_category['Business']}")
    add("Sci/Tech category counts",
        per_category["Sci/Tech"]["n_human"] == 22
        and per_category["Sci/Tech"]["disagreements"] == 0,
        f"Sci/Tech={per_category['Sci/Tech']}")
    add("World category counts",
        per_category["World"]["n_human"] == 73
        and per_category["World"]["disagreements"] == 22,
        f"World={per_category['World']}")
    add("human and AI label distributions",
        agreement["confusion_matrix_row_totals"] == [73, 53, 52, 22]
        and agreement["confusion_matrix_col_totals"] == [54, 53, 55, 38],
        f"human={agreement['confusion_matrix_row_totals']}, "
        f"AI={agreement['confusion_matrix_col_totals']}")
    add("dataset label distribution",
        original["checks"]["dataset_label_counts"] == {
            "World": 53, "Sports": 53, "Business": 45, "Sci/Tech": 49},
        f"counts={original['checks']['dataset_label_counts']}")

    # Recorded analysis-model identifiers
    model_meta = read_json(MODEL_META)
    runs = {run["run"]: run for run in model_meta["runs"]}
    add("workflow analysis model recorded",
        runs["workflow_run"]["session_model"]
        == "opencode/deepseek-v4.1-flash-free"
        and runs["workflow_run"]["cli_version"] == "2.2.5",
        f"run={runs['workflow_run']}")
    add("autonomous analysis model recorded",
        runs["agent_run"]["session_model"]
        == "opencode/deepseek-v4.1-flash-free"
        and runs["agent_run"]["cli_version"] == "2.2.5",
        f"run={runs['agent_run']}")
    attribution_ok = all(
        counts and set(counts) == {"opencode/deepseek-v4.1-flash-free"}
        for run in model_meta["runs"]
        for counts in run["scripts"].values()
    )
    add("analysis scripts attributed to the recorded model",
        attribution_ok and all(run["scripts"] for run in model_meta["runs"]),
        "every script mention must map to the recorded model")

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
    readme_text = README.read_text(encoding="utf-8")
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
    add("removed Excel limitation sentence absent",
        "It is not an unaided manual calculation."
        not in normalise(report_text),
        "the removed sentence is still present")

    # Descriptive category interpretations (section 3.4)
    require_text("report Business/Sci-Tech split", report_text, "13/52")
    require_text("report Sci/Tech zero disagreements", report_text, "0/22")
    require_text("report Business rate", report_text, "25.0%")
    require_text("report World split", report_text, "22/73")
    require_text("report World rate", report_text, "30.1%")
    require_text("report pooling caveat", report_text,
                 "hides where the disagreements actually sit")
    require_text("report distribution table header", report_text,
                 "| Category | Human labels | AI labels | Original dataset labels |")
    require_text("report distribution World", report_text,
                 "| World | 73 | 54 | 53 |")
    require_text("report distribution Sports", report_text,
                 "| Sports | 53 | 53 | 53 |")
    require_text("report distribution Business", report_text,
                 "| Business | 52 | 55 | 45 |")
    require_text("report distribution Sci/Tech", report_text,
                 "| Sci/Tech | 22 | 38 | 49 |")
    require_text("report distribution non-inference", report_text,
                 "do **not** establish that the AI labels are correct")

    # Analysis model and fresh-session wording (section 6.1)
    require_text("report analysis model identifier", report_text,
                 "opencode/deepseek-v4.1-flash-free")
    require_text("report OpenCode CLI version", report_text, "`2.2.5`")
    require_text("report fresh session", report_text, "fresh OpenCode session")
    require_text("report classifier not repeated", report_text, "not repeated")
    require_text("report analysis-agent separation", report_text,
                 "not by the Gemini classifier")

    # Assistance and authorship (section 11)
    require_text("report student authorship", report_text,
                 "personally classifying all 200 evaluation texts without "
                 "consulting any AI")
    require_text("report review authorship", report_text,
                 "personally writing all 38 retrospective review explanations")
    require_text("report retrospective limit", report_text,
                 "not blinded independent annotations")
    require_text("report auxiliary assistant wording", report_text,
                 "An auxiliary AI assistant. Assistance covered planning, "
                 "prompt drafting, troubleshooting, preparation feedback, "
                 "codebook clarification, interpretation and verification.")
    require_text("report Excel verification sentence", report_text,
                 "The student's Excel verification was student-executed "
                 "outside the OpenCode analysis scripts.")
    require_text("README assistance paragraph", readme_text,
                 "An auxiliary AI assistant provided documented help with "
                 "planning, prompt drafting, troubleshooting, feedback on the "
                 "preparation annotations, interpretation support and "
                 "verification assistance. The OpenCode analysis agent "
                 "implemented the analysis and documentation scripts, and a "
                 "Gemini model produced the AI classifications.")
    require_text("README assistance section", readme_text,
                 "## Authorship and assistance")

    # Removed editorial passages must stay removed.
    add("report dataset-access paragraph removed",
        "Dataset-access restriction" not in report_text
        and "allowlist" not in normalise(report_text).lower(),
        "the allowlist paragraph is still present in the report")
    add("README allowlist paragraph removed",
        "allowlist" not in normalise(readme_text).lower()
        and "instructor acceptance" not in normalise(readme_text).lower(),
        "the allowlist/instructor paragraph is still present in README")
    add("report historical section removed",
        "## 13." not in report_text
        and "Historical records and exclusions" not in report_text,
        "section 13 is still present in the report")
    add("README historical records section removed",
        "## Historical records" not in readme_text,
        "the historical-records section is still present in README")

    current_docs = [REPORT, README, DATA_README,
                    PROJECT / "results" / "preparation_assistance_note.md",
                    PROJECT / "results" / "student_excel_verification.md"]
    offenders = [path.name for path in current_docs
                 if "ChatGPT" in path.read_text(encoding="utf-8")]
    add("product name absent from current docs", not offenders,
        f"found in {offenders}")

    add("revision archive note present", ARCHIVE_NOTE.is_file(),
        f"missing {ARCHIVE_NOTE.relative_to(PROJECT)}")
    archive_note_text = (ARCHIVE_NOTE.read_text(encoding="utf-8")
                         if ARCHIVE_NOTE.is_file() else "")
    add("revision archive note documents exclusion",
        "excluded from the reader-facing delivery set"
        in normalise(archive_note_text),
        "ARCHIVE_NOTE must state the exclusion policy")

    agents_text = AGENTS.read_text(encoding="utf-8")
    add("AGENTS matrix-label rule",
        "Align matrix labels explicitly" in agents_text,
        "missing rule 11")
    add("AGENTS excluded-search rule",
        "Search with explicit exclusions" in agents_text,
        "missing rule 12")
    add("AGENTS prospective-rule note",
        "prospective" in normalise(agents_text)
        and "did not apply to the earlier runs" in normalise(agents_text),
        "rules 11-12 must be marked prospective")

    mistakes_text = MISTAKES.read_text(encoding="utf-8")
    empty_row = re.compile(r"^\|\s*\|(?:\s*\|)+\s*$", flags=re.M)
    dated_rows = re.findall(r"^\| 20\d\d-\d\d-\d\d \|", mistakes_text, flags=re.M)
    add("mistakes table has no empty row",
        empty_row.search(mistakes_text) is None,
        "found an all-empty table row")
    add("mistakes table has three dated rows", len(dated_rows) == 3,
        f"dated rows={len(dated_rows)}")

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

    # Repository hygiene: ignore rules and, when an index exists, tracked paths.
    gitignore = (PROJECT / ".gitignore").read_text(encoding="utf-8")
    ignore_lines = gitignore.splitlines()
    add(".env ignored", ".env" in ignore_lines,
        ".gitignore must contain .env")
    add(".env.* ignored", ".env.*" in ignore_lines,
        ".gitignore must contain .env.*")
    add(".venv ignored", any(line.strip() == ".venv/"
                             for line in ignore_lines),
        ".gitignore must contain .venv/")

    # Repository state: a .git directory may pre-date this revision. A Git
    # client is not required to read the index and check tracked paths.
    git_dir = PROJECT / ".git"
    index_path = git_dir / "index"
    tracked = read_git_index(index_path) if index_path.is_file() else None
    if tracked is not None:
        add(".env not tracked", ".env" not in tracked,
            ".env appears in the Git index")
        add(".env.* not tracked",
            not any(Path(p).name.startswith(".env.") for p in tracked),
            "a .env.* path appears in the Git index")
    push_reflog = git_dir / "logs" / "refs" / "remotes" / "origin" / "main"
    push_recorded = (push_reflog.is_file()
                     and "update by push" in push_reflog.read_text(
                         encoding="utf-8", errors="replace"))
    git_client = bool(shutil.which("git"))

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
    status = ("Ready for final review; this revision made no publication."
              if not technical_failures else
              "NOT READY: technical checks failed; see below.")

    if git_dir.exists():
        repo_state = "a `.git/` directory is present and pre-dates this revision"
        if tracked is not None:
            repo_state += f"; its index lists {len(tracked)} tracked paths"
        repo_state += (
            ". No Git client is installed, so status, diff and tracked-file "
            "history checks were not possible" if not git_client else
            ". A Git client is available, but this verification did not run "
            "status or diff checks")
        if push_recorded:
            publication_state = ("a remote is configured and its reflog records "
                                 "a push that pre-dates this revision. This "
                                 "revision made no commit, push or publication")
        else:
            publication_state = ("a remote may be configured, but no push is "
                                 "recorded in the reflog. This revision made no "
                                 "commit, push or publication")
    else:
        repo_state = "no `.git/` directory is present"
        publication_state = ("no Git client is installed and no repository is "
                             "present; nothing was staged, committed, pushed or "
                             "published")

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
        "- Reflection revision (2026-11-17): per-mistake narratives, descriptive "
        "category patterns (section 3.4), recorded analysis-model identifiers, "
        "fresh-session clarification, and assistance/authorship wording. "
        "Pre-revision documents preserved in "
        "`archive/2026-11-17_reflection_and_wording/`.",
        "- Analysis-model provenance: `results/agent_run/"
        "analysis_model_metadata.json`, recorded by "
        "`src/23_record_analysis_model_metadata.py` from the local OpenCode "
        "session store.",
        "",
        "## Local environment",
        "",
        f"- `.env`: {env_status}",
        "",
        "## Publication and repository",
        "",
        f"- Repository state — {repo_state}.",
        f"- Publication — {publication_state}.",
        "- Tracked secrets — `.env` and `.env.*` are not in the Git index when "
        "the index is readable; `.venv/`, `__pycache__/`, `*.py[cod]` and "
        "`.pytest_cache/` are ignored.",
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
