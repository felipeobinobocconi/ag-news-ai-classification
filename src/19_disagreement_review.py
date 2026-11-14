"""Build a qualitative review workbook for the classification disagreements.

Inputs (frozen):
  data/derived/evaluation_200_labelled.xlsx       human labels, confidence, reasons
  results/ai_classification/evaluation_gemini/ai_classifications.csv
  data/derived/evaluation_manifest.csv            item_id -> zero-based raw position
  data/raw/test-00000-of-00001.parquet            text column only

The script joins the frozen classifications one-to-one by item_id, selects all
disagreements, retrieves each original text through the manifest and the raw
`text` column, and writes results/disagreement_review.xlsx.

The review columns are intentionally blank. This script does not suggest
explanations, does not decide which classifier is right, does not read the
original dataset labels, and does not call a model.

Run:
  uv run --with openpyxl src/19_disagreement_review.py
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Fixed seed although this script has no stochastic step (AGENTS.md rule 5).
SEED = 42

PROJECT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"
RAW = PROJECT / "data" / "raw" / "test-00000-of-00001.parquet"

MANUAL_FREEZE = PROJECT / "results" / "manual_labels_freeze_note.md"
AI_FREEZE = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "classification_freeze_note.md"

OUT = PROJECT / "results" / "disagreement_review.xlsx"
TMP = PROJECT / "results" / ".disagreement_review.tmp.xlsx"

N_EXPECTED = 200
N_EXPECTED_DISAGREEMENTS = 38
VALID_LABELS = {0, 1, 2, 3}
VALID_CONFIDENCE = {"confident", "uncertain"}

COLUMNS = [
    "item_id",
    "text",
    "human_label",
    "ai_label",
    "human_confidence",
    "uncertainty_reason",
    "review_explanation",
    "review_assessment",
]
WIDTHS = {
    "item_id": 12,
    "text": 90,
    "human_label": 12,
    "ai_label": 10,
    "human_confidence": 18,
    "uncertainty_reason": 55,
    "review_explanation": 40,
    "review_assessment": 30,
}
WRAP_COLUMNS = {"text", "uncertainty_reason", "review_explanation", "review_assessment"}


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    if TMP.exists():
        TMP.unlink()
    sys.exit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def labeled_hash(path: Path, label: str) -> str | None:
    """Return the unique SHA-256 recorded after `label`, else None."""
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        rf"{re.escape(label)}\s*:?\s*`([0-9A-Fa-f]{{64}})`", text, flags=re.S)
    return matches[0].upper() if len(matches) == 1 else None


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    print(f"random seed fixed at {SEED} (no stochastic step in this script)")
    print("")

    if OUT.exists():
        fail(f"output already exists and will not be overwritten: {OUT}")

    # ---------------------------------------------------------------- hashes
    print("STEP 1: recorded hashes where available")
    expected_manual = labeled_hash(MANUAL_FREEZE, "Workbook SHA-256")
    expected_ai = labeled_hash(AI_FREEZE, "SHA-256")
    require(expected_manual is not None,
            "manual labels freeze note has no unique Workbook SHA-256")
    require(expected_ai is not None,
            "AI classification freeze note has no unique SHA-256")

    observed_manual = sha256(WORKBOOK)
    observed_ai = sha256(AI_CSV)
    observed_manifest = sha256(MANIFEST)
    print(f"  manual workbook: recorded {expected_manual}, observed {observed_manual}, "
          f"match={observed_manual == expected_manual}")
    print(f"  AI classifications: recorded {expected_ai}, observed {observed_ai}, "
          f"match={observed_ai == expected_ai}")
    print(f"  manifest: no freeze-note hash recorded; observed {observed_manifest}")
    require(observed_manual == expected_manual,
            "manual workbook SHA-256 does not match its freeze note")
    require(observed_ai == expected_ai,
            "AI classification SHA-256 does not match its freeze note")

    # ----------------------------------------------------------------- joins
    print("")
    print("STEP 2: load frozen classifications and join one-to-one")
    manual = pd.read_excel(
        WORKBOOK, sheet_name="evaluation_200",
        usecols=["item_id", "human_label", "human_confidence", "uncertainty_reason"],
        dtype={"item_id": str},
    )
    ai = pd.read_csv(AI_CSV, usecols=["item_id", "label"], dtype={"item_id": str})
    manifest = pd.read_csv(MANIFEST, dtype={"item_id": str})

    print(f"  rows read: manual={len(manual)}, AI={len(ai)}, manifest={len(manifest)}")
    require(len(manual) == N_EXPECTED, f"manual rows = {len(manual)}, expected {N_EXPECTED}")
    require(len(ai) == N_EXPECTED, f"AI rows = {len(ai)}, expected {N_EXPECTED}")
    require(len(manifest) == N_EXPECTED, f"manifest rows = {len(manifest)}, expected {N_EXPECTED}")

    require(manual["item_id"].is_unique, "manual item_ids are not unique")
    require(ai["item_id"].is_unique, "AI item_ids are not unique")
    require(manifest["item_id"].is_unique, "manifest item_ids are not unique")

    manual_ids = set(manual["item_id"])
    ai_ids = set(ai["item_id"])
    manifest_ids = set(manifest["item_id"])
    require(manual_ids == ai_ids == manifest_ids,
            "item_id sets differ across manual labels, AI labels and manifest")

    merged = manual.merge(ai, on="item_id", how="inner", validate="one_to_one")
    print(f"  joined rows: {len(merged)} one-to-one; rows dropped: "
          f"{len(manual) - len(merged)} (reason: no unmatched IDs)")
    require(len(merged) == N_EXPECTED, f"joined rows = {len(merged)}, expected {N_EXPECTED}")
    require(set(merged["human_label"].unique()) <= VALID_LABELS,
            "human_label has values outside 0-3")
    require(set(merged["label"].unique()) <= VALID_LABELS,
            "AI label has values outside 0-3")
    require(set(merged["human_confidence"].unique()) <= VALID_CONFIDENCE,
            "human_confidence has unexpected values")

    # --------------------------------------------------------- disagreements
    print("")
    print("STEP 3: select disagreements")
    disagreements = merged[merged["human_label"] != merged["label"]].copy()
    disagreements = disagreements.sort_values("item_id").reset_index(drop=True)
    print(f"  disagreements selected: {len(disagreements)} of {len(merged)} "
          f"(expected {N_EXPECTED_DISAGREEMENTS}; reason: human_label != AI label)")
    require(len(disagreements) == N_EXPECTED_DISAGREEMENTS,
            f"disagreements = {len(disagreements)}, expected {N_EXPECTED_DISAGREEMENTS}")

    # ------------------------------------------------------------- raw texts
    print("")
    print("STEP 4: retrieve original texts from the raw text column via manifest")
    raw = pd.read_parquet(RAW, columns=["text"])
    positions = manifest.set_index("item_id")["source_row_position"].astype(int)
    require(positions.isin(range(len(raw))).all(),
            "manifest contains an out-of-range source_row_position")
    require(positions.is_unique, "manifest source positions are not unique")

    texts: dict[str, str] = {}
    for item_id in disagreements["item_id"]:
        position = int(positions.loc[item_id])
        value = raw["text"].iloc[position]
        require(pd.notna(value), f"raw text is missing at position {position}")
        text = str(value)
        require(text.strip() != "", f"raw text is blank at position {position}")
        texts[item_id] = text
    print(f"  texts retrieved: {len(texts)} of {len(disagreements)} rows "
          f"(reason: every disagreement has one manifest position)")

    # --------------------------------------------------------------- output
    print("")
    print("STEP 5: build and verify the review workbook")
    wb = Workbook()
    ws = wb.active
    ws.title = "disagreements"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    for col_index, name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_index, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        ws.column_dimensions[get_column_letter(col_index)].width = WIDTHS[name]
    ws.row_dimensions[1].height = 30

    for row_index, row in enumerate(disagreements.itertuples(index=False), start=2):
        reason = None if pd.isna(row.uncertainty_reason) else str(row.uncertainty_reason)
        values = [
            row.item_id,
            texts[row.item_id],
            int(row.human_label),
            int(row.label),
            str(row.human_confidence),
            reason,
            None,
            None,
        ]
        for col_index, name in enumerate(COLUMNS, start=1):
            cell = ws.cell(row=row_index, column=col_index, value=values[col_index - 1])
            cell.alignment = Alignment(
                vertical="top", wrap_text=name in WRAP_COLUMNS,
                horizontal="center" if name in {"item_id", "human_label", "ai_label"}
                else "left",
            )
            # Keep leading "=" as text rather than letting Excel treat it as a formula.
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"
        ws.row_dimensions[row_index].height = 90

    ws.freeze_panes = "A2"
    wb.save(TMP)
    wb.close()

    # ---------------------------------------------------------- verify file
    check_wb = load_workbook(TMP, data_only=False)
    check_ws = check_wb["disagreements"]
    require(check_ws.max_row == len(disagreements) + 1,
            f"output rows = {check_ws.max_row - 1}, expected {len(disagreements)}")
    require(check_ws.max_column == len(COLUMNS),
            f"output columns = {check_ws.max_column}, expected {len(COLUMNS)}")
    require([check_ws.cell(1, c).value for c in range(1, len(COLUMNS) + 1)] == COLUMNS,
            "output header does not match the required columns")

    output_ids: list[str] = []
    for row_index, row in enumerate(disagreements.itertuples(index=False), start=2):
        output_ids.append(check_ws.cell(row_index, 1).value)
        require(check_ws.cell(row_index, 1).value == row.item_id,
                f"item_id mismatch at output row {row_index}")
        require(check_ws.cell(row_index, 2).value == texts[row.item_id],
                f"text is not preserved exactly for {row.item_id}")
        require(check_ws.cell(row_index, 3).value == int(row.human_label),
                f"human_label mismatch for {row.item_id}")
        require(check_ws.cell(row_index, 4).value == int(row.label),
                f"AI label mismatch for {row.item_id}")
        require(check_ws.cell(row_index, 5).value == str(row.human_confidence),
                f"human_confidence mismatch for {row.item_id}")
        expected_reason = None if pd.isna(row.uncertainty_reason) else str(row.uncertainty_reason)
        require(check_ws.cell(row_index, 6).value == expected_reason,
                f"uncertainty_reason is not preserved exactly for {row.item_id}")
        require(check_ws.cell(row_index, 7).value is None,
                f"review_explanation is not blank for {row.item_id}")
        require(check_ws.cell(row_index, 8).value is None,
                f"review_assessment is not blank for {row.item_id}")

    require(len(set(output_ids)) == len(output_ids), "output item_ids are not unique")
    require(set(output_ids) == set(disagreements["item_id"]),
            "output item_id set differs from the disagreement set")
    require(check_ws.freeze_panes == "A2", "header row is not frozen")
    for col_index, name in enumerate(COLUMNS, start=1):
        require(bool(check_ws.cell(2, col_index).alignment.wrap_text)
                == (name in WRAP_COLUMNS),
                f"wrapping is not set as intended for column {name}")
    check_wb.close()

    TMP.replace(OUT)
    print(f"  verified rows: {len(output_ids)}; unique IDs: {len(set(output_ids))}")
    print(f"  review columns blank: yes; header frozen: yes; text wrapping: yes")
    print("")
    print(f"OUTPUT: {OUT.relative_to(PROJECT)}")
    print("CHECKS PASSED: hashes, one-to-one join, 38 disagreements, "
          "exact texts, exact uncertainty reasons, blank review columns")


if __name__ == "__main__":
    main()
