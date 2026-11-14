"""Agreement analysis, step 1 (plan.md steps 6-7 groundwork) — overall agreement.

Reads the frozen human reference (evaluation_200_labelled.xlsx) and the frozen
AI classifications (evaluation_gemini/ai_classifications.csv), verifies all
relevant hashes against the freeze notes, joins one-to-one by item_id, and
computes overall agreement plus a 4x4 confusion matrix.

Describes agreement with ONE human reference, not accuracy against ground
truth. Does not review individual disagreements, run the category-hypothesis
comparison, or read original dataset labels.

Outputs: results/workflow_run/ (never overwritten)

Run: uv run --with openpyxl src/11_agreement_overall.py
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path.cwd()
OUT_DIR = PROJECT / "results" / "workflow_run"

HUMAN_XLSX = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
CODEBOOK = PROJECT / "codebook.md"

HUMAN_NOTE = PROJECT / "results" / "manual_labels_freeze_note.md"
AI_NOTE = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "classification_freeze_note.md"
CODEBOOK_NOTE = PROJECT / "results" / "codebook_freeze_note.md"

LABELS = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
EXPECTED_N = 200


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def note_hash(path: Path, pattern: str | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    if pattern:
        hits = re.findall(pattern, text)
        if len(hits) != 1:
            raise SystemExit(f"STOP: expected exactly one matching SHA-256 in {path.name}; found {len(hits)}")
        return hits[0].upper()
    hashes = re.findall(r"`([0-9A-Fa-f]{64})`", text)
    if len(hashes) != 1:
        raise SystemExit(f"STOP: expected exactly one SHA-256 in {path.name}; found {len(hashes)}")
    return hashes[0].upper()


def verify(label: str, file: Path, note: Path, checks: list, pattern: str | None = None):
    expected = note_hash(note, pattern)
    actual = sha256_file(file)
    ok = actual == expected
    checks.append({"file": str(file.relative_to(PROJECT)), "note": str(note.relative_to(PROJECT)),
                   "expected": expected, "actual": actual, "match": ok})
    print(f"HASH {'PASS' if ok else 'FAIL'}: {file.name} == {expected[:12]}... (note {note.name})")
    if not ok:
        raise SystemExit(f"STOP: hash mismatch for {file}; not repairing or overwriting anything.")


def main() -> None:
    for name in ("comparison_table.csv", "confusion_matrix.csv", "agreement_summary.json", "agreement_report.md"):
        if (OUT_DIR / name).exists():
            raise SystemExit(f"STOP: output already exists, refusing to overwrite: {OUT_DIR / name}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    checks = []
    verify("codebook", CODEBOOK, CODEBOOK_NOTE, checks,
           pattern=r"SHA-256 of the frozen codebook:\s*`([0-9A-Fa-f]{64})`")
    verify("human labels", HUMAN_XLSX, HUMAN_NOTE, checks,
           pattern=r"Workbook SHA-256:\s*`([0-9A-Fa-f]{64})`")
    verify("AI classifications", AI_CSV, AI_NOTE, checks)

    # --- Load: human reference (no text column needed) ---
    human = pd.read_excel(HUMAN_XLSX, usecols=["item_id", "human_label", "human_confidence"])
    print(f"\nLOAD: {len(human)} human rows (item_id, human_label, human_confidence)")

    ai = pd.read_csv(AI_CSV)
    print(f"LOAD: {len(ai)} AI rows")

    # --- Verify before joining ---
    human["item_id"] = human["item_id"].astype(str)
    ai["item_id"] = ai["item_id"].astype(str)

    assert human["item_id"].is_unique, "human item_ids not unique"
    assert ai["item_id"].is_unique, "AI item_ids not unique"
    assert len(human) == EXPECTED_N, f"human rows {len(human)} != {EXPECTED_N}"
    assert len(ai) == EXPECTED_N, f"AI rows {len(ai)} != {EXPECTED_N}"
    assert set(human["item_id"]) == set(ai["item_id"]), "ID sets differ"
    assert human["human_label"].between(0, 3).all(), "invalid human labels"
    assert ai["label"].between(0, 3).all(), "invalid AI labels"
    assert (ai["status"] == "ok").all(), "AI classifications include non-ok items"
    print("CHECK PASS: 200 unique IDs in each file; identical sets; labels in 0-3; all AI status=ok")

    human_n = len(human)
    ai_n = len(ai)
    merged = human.merge(ai[["item_id", "label"]], on="item_id", how="inner", validate="one_to_one")
    print(f"JOIN: {human_n} human + {ai_n} AI -> {len(merged)} rows (one-to-one on item_id; inner join)")
    assert len(merged) == EXPECTED_N, "join lost rows"

    table = merged.rename(columns={"label": "ai_label"}).copy()
    table["agreement"] = (table["human_label"] == table["ai_label"]).astype(int)
    table = table[["item_id", "human_label", "ai_label", "human_confidence", "agreement"]]
    table = table.sort_values("item_id").reset_index(drop=True)

    n_total = len(table)
    n_agree = int(table["agreement"].sum())
    overall = n_agree / n_total
    print(f"AGREEMENT: {n_agree}/{n_total} = {overall:.4f}")

    # --- Confusion matrix: rows human, cols AI, order World/Sports/Business/Sci-Tech ---
    cm = pd.crosstab(table["human_label"], table["ai_label"], dropna=False)
    cm = cm.reindex(index=[0, 1, 2, 3], columns=[0, 1, 2, 3], fill_value=0).fillna(0).astype(int)
    cm.index = [f"human_{LABELS[i]}" for i in cm.index]
    cm.columns = [f"ai_{LABELS[i]}" for i in cm.columns]
    diag = int(sum(cm.iloc[i, i] for i in range(4)))
    total = int(cm.values.sum())
    print(f"MATRIX: total={total} (expected {EXPECTED_N}); diagonal={diag} (expected {n_agree})")
    assert total == EXPECTED_N, "matrix does not sum to 200"
    assert diag == n_agree, "diagonal does not equal agreement count"

    table.to_csv(OUT_DIR / "comparison_table.csv", index=False)
    cm.to_csv(OUT_DIR / "confusion_matrix.csv")
    summary = {
        "script": "src/11_agreement_overall.py",
        "inputs": {
            "human": str(HUMAN_XLSX.relative_to(PROJECT)),
            "ai": str(AI_CSV.relative_to(PROJECT)),
        },
        "hash_checks": checks,
        "items": n_total,
        "agree": n_agree,
        "overall_agreement": overall,
        "matrix_total": total,
        "matrix_diagonal": diag,
        "label_order": ["World", "Sports", "Business", "Sci/Tech"],
        "note": "Agreement with one human reference, not accuracy against unquestionable ground truth.",
    }
    (OUT_DIR / "agreement_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    report = [
        "# Agreement analysis — step 1 (overall agreement)",
        "",
        "- Script: `src/11_agreement_overall.py`",
        "- Inputs: frozen `evaluation_200_labelled.xlsx` and `ai_classifications.csv`",
        f"- Items: {n_total} (all kept, including uncertain human annotations)",
        f"- Overall agreement: {n_agree}/{n_total} = {overall:.4f}",
        "",
        "## Confusion matrix (rows = human, columns = AI; order World, Sports, Business, Sci/Tech)",
        "",
        "```",
        cm.to_string(),
        "```",
        "",
        f"- Matrix total: {total}; diagonal: {diag} (equals agreement count).",
        "",
        "Interpretation: this is agreement with one human reference, not accuracy",
        "against unquestionable ground truth.",
    ]
    (OUT_DIR / "agreement_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"\nOUTPUTS: {OUT_DIR}")
    print("VERDICT: STEP 1 COMPLETE")


if __name__ == "__main__":
    main()
