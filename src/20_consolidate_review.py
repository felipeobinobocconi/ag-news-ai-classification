"""Consolidate and validate the completed qualitative review workbook.

Input:
  results/disagreement_review_completed.xlsx

Validation compares the completed review with the frozen human labels, frozen
AI labels and the raw texts retrieved through the manifest. It checks that the
38 reviewed IDs are exactly the frozen disagreement set, that texts, labels,
confidence and uncertainty reasons are unchanged, and that both review columns
are complete. Assessment counts are checked against the expected 23 / 8 / 7.

Outputs:
  results/qualitative_review_summary.json
  results/qualitative_review_summary.md

No model is called; no frozen input or previous result is modified.

Run:
  uv run --with openpyxl src/20_consolidate_review.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

SEED = 42

PROJECT = Path(__file__).resolve().parents[1]
REVIEW = PROJECT / "results" / "disagreement_review_completed.xlsx"
WORKBOOK = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"
RAW = PROJECT / "data" / "raw" / "test-00000-of-00001.parquet"

OUT_JSON = PROJECT / "results" / "qualitative_review_summary.json"
OUT_MD = PROJECT / "results" / "qualitative_review_summary.md"

COLUMNS = [
    "item_id", "text", "human_label", "ai_label", "human_confidence",
    "uncertainty_reason", "review_explanation", "review_assessment",
]
ASSESSMENTS = {
    "AI label better supported": 23,
    "human label better supported": 8,
    "both defensible": 7,
}
EXPECTED_N = 38


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    print(f"random seed fixed at {SEED} (no stochastic step in this script)")

    manual = pd.read_excel(
        WORKBOOK, sheet_name="evaluation_200",
        usecols=["item_id", "text", "human_label", "human_confidence",
                 "uncertainty_reason"],
        dtype={"item_id": str},
    )
    ai = pd.read_csv(AI_CSV, usecols=["item_id", "label"], dtype={"item_id": str})
    manifest = pd.read_csv(MANIFEST, dtype={"item_id": str})
    raw = pd.read_parquet(RAW, columns=["text"])

    print(f"rows read: manual={len(manual)}, AI={len(ai)}, manifest={len(manifest)}, "
          f"raw={len(raw)}")
    require(len(manual) == len(ai) == len(manifest) == 200,
            "expected 200 rows in each frozen source")
    require(manual["item_id"].is_unique and ai["item_id"].is_unique
            and manifest["item_id"].is_unique, "frozen IDs are not unique")

    frozen = manual.merge(ai, on="item_id", how="inner", validate="one_to_one")
    frozen = frozen.merge(manifest, on="item_id", how="inner", validate="one_to_one")
    print(f"frozen joined rows: {len(frozen)}; dropped: {200 - len(frozen)} "
          "(reason: no unmatched IDs)")
    require(len(frozen) == 200, "frozen join is not 200 rows")
    frozen = frozen[frozen["human_label"] != frozen["label"]].copy()
    frozen = frozen.sort_values("item_id").reset_index(drop=True)
    print(f"frozen disagreements: {len(frozen)} of 200 "
          "(reason: human_label != AI label)")
    require(len(frozen) == EXPECTED_N,
            f"frozen disagreements = {len(frozen)}, expected {EXPECTED_N}")

    wb = load_workbook(REVIEW, data_only=True)
    require(wb.sheetnames == ["disagreements"],
            f"unexpected sheets: {wb.sheetnames}")
    ws = wb["disagreements"]
    require(ws.max_column == len(COLUMNS),
            f"review columns = {ws.max_column}, expected {len(COLUMNS)}")
    header = [ws.cell(1, c).value for c in range(1, len(COLUMNS) + 1)]
    require(header == COLUMNS, f"unexpected header: {header}")

    rows = []
    for r in range(2, ws.max_row + 1):
        rows.append({name: ws.cell(r, c).value
                     for c, name in enumerate(COLUMNS, start=1)})
    wb.close()

    print(f"reviewed rows: {len(rows)} (expected {EXPECTED_N})")
    require(len(rows) == EXPECTED_N,
            f"review rows = {len(rows)}, expected {EXPECTED_N}")

    reviewed_ids = [row["item_id"] for row in rows]
    require(len(set(reviewed_ids)) == len(reviewed_ids),
            "reviewed item_ids are not unique")
    require(set(reviewed_ids) == set(frozen["item_id"]),
            "reviewed IDs are not exactly the frozen disagreement IDs")

    positions = manifest.set_index("item_id")["source_row_position"].astype(int)
    frozen_by_id = frozen.set_index("item_id")
    text_mismatches = 0
    label_mismatches = 0
    confidence_mismatches = 0
    reason_mismatches = 0
    blank_explanations = 0
    blank_assessments = 0
    for row in rows:
        item_id = row["item_id"]
        source = frozen_by_id.loc[item_id]
        raw_text = str(raw["text"].iloc[int(positions.loc[item_id])])
        if row["text"] != raw_text:
            text_mismatches += 1
        if row["human_label"] != int(source["human_label"]):
            label_mismatches += 1
        if row["ai_label"] != int(source["label"]):
            label_mismatches += 1
        if row["human_confidence"] != str(source["human_confidence"]):
            confidence_mismatches += 1
        expected_reason = (None if pd.isna(source["uncertainty_reason"])
                           else str(source["uncertainty_reason"]))
        if row["uncertainty_reason"] != expected_reason:
            reason_mismatches += 1
        if not (isinstance(row["review_explanation"], str)
                and row["review_explanation"].strip()):
            blank_explanations += 1
        if not (isinstance(row["review_assessment"], str)
                and row["review_assessment"].strip()):
            blank_assessments += 1

    print(f"text mismatches versus raw via manifest: {text_mismatches}")
    print(f"label mismatches versus frozen classifications: {label_mismatches}")
    print(f"confidence mismatches: {confidence_mismatches}")
    print(f"uncertainty-reason mismatches: {reason_mismatches}")
    print(f"blank explanations: {blank_explanations}; blank assessments: {blank_assessments}")
    require(text_mismatches == 0, "reviewed texts differ from the raw texts")
    require(label_mismatches == 0, "reviewed labels differ from frozen classifications")
    require(confidence_mismatches == 0, "reviewed confidence differs from frozen labels")
    require(reason_mismatches == 0, "reviewed uncertainty reasons differ from frozen labels")
    require(blank_explanations == 0, "some review explanations are blank")
    require(blank_assessments == 0, "some review assessments are blank")

    counts = Counter(row["review_assessment"] for row in rows)
    print(f"assessment counts: {dict(counts)}")
    require(set(counts) == set(ASSESSMENTS),
            f"unexpected assessment values: {sorted(counts)}")
    for label, expected in ASSESSMENTS.items():
        require(counts[label] == expected,
                f"{label} = {counts[label]}, expected {expected}")

    pair_counts = Counter(
        (int(frozen_by_id.loc[row["item_id"], "human_label"]),
         int(frozen_by_id.loc[row["item_id"], "label"]))
        for row in rows
    )

    # A small, explicit illustrative set; the text is quoted from the workbook.
    example_ids = ["eval_006", "eval_030", "eval_016", "eval_181"]
    examples = []
    rows_by_id = {row["item_id"]: row for row in rows}
    for item_id in example_ids:
        row = rows_by_id[item_id]
        examples.append({
            "item_id": item_id,
            "human_label": int(frozen_by_id.loc[item_id, "human_label"]),
            "ai_label": int(frozen_by_id.loc[item_id, "label"]),
            "assessment": row["review_assessment"],
            "explanation": row["review_explanation"],
        })
    require(len(examples) == len(example_ids), "an example ID is missing")

    names = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
    pair_rows = [
        [f"{h} {names[h]} -> {a} {names[a]}", str(n)]
        for (h, a), n in sorted(pair_counts.items(),
                                key=lambda item: (-item[1], item[0]))
    ]

    summary = {
        "script": "src/20_consolidate_review.py",
        "input": "results/disagreement_review_completed.xlsx",
        "reviewed": len(rows),
        "expected_disagreements": EXPECTED_N,
        "checks": {
            "ids_exactly_match_frozen_disagreements": True,
            "unique_reviewed_ids": len(set(reviewed_ids)),
            "text_mismatches": text_mismatches,
            "label_mismatches": label_mismatches,
            "confidence_mismatches": confidence_mismatches,
            "uncertainty_reason_mismatches": reason_mismatches,
            "blank_explanations": blank_explanations,
            "blank_assessments": blank_assessments,
        },
        "assessment_counts": {label: counts[label] for label in ASSESSMENTS},
        "disagreement_pairs": {
            f"{h}->{a}": n for (h, a), n in sorted(pair_counts.items())
        },
        "examples": examples,
        "attribution": (
            "Retrospective student judgments made after seeing both labels; "
            "not independent adjudication and not a revised accuracy measure."
        ),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    lines = []
    lines.append("# Qualitative review summary")
    lines.append("")
    lines.append("- Script: `src/20_consolidate_review.py`")
    lines.append("- Input: `results/disagreement_review_completed.xlsx`")
    lines.append("- Frozen sources: human labels and uncertainty reasons from "
                 "`data/derived/evaluation_200_labelled.xlsx`; AI labels from "
                 "`results/ai_classification/evaluation_gemini/ai_classifications.csv`; "
                 "texts from the raw `text` column via `data/derived/evaluation_manifest.csv`.")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append(f"- Reviewed rows: {len(rows)}; expected disagreements: {EXPECTED_N}.")
    lines.append(f"- Reviewed IDs exactly match the frozen disagreement set; "
                 f"unique reviewed IDs: {len(set(reviewed_ids))}.")
    lines.append(f"- Text mismatches versus the raw texts: {text_mismatches}.")
    lines.append(f"- Label mismatches versus the frozen classifications: {label_mismatches}.")
    lines.append(f"- Confidence mismatches: {confidence_mismatches}.")
    lines.append(f"- Original uncertainty-reason mismatches: {reason_mismatches}.")
    lines.append(f"- Blank explanations: {blank_explanations}; blank assessments: "
                 f"{blank_assessments}.")
    lines.append("")
    lines.append("## Assessment counts")
    lines.append("")
    lines.append("These are the student's retrospective judgments after seeing both "
                 "labels. They are not independent adjudication, not ground truth, "
                 "and not a revised accuracy measure.")
    lines.append("")
    lines.append("| Assessment | Items |")
    lines.append("| --- | --- |")
    for label in ["AI label better supported", "human label better supported",
                  "both defensible"]:
        lines.append(f"| {label} | {counts[label]} |")
    lines.append("")
    lines.append("## Disagreement pairs")
    lines.append("")
    lines.append("| Frozen pair (human -> AI) | Items |")
    lines.append("| --- | --- |")
    for pair, count in pair_rows:
        lines.append(f"| {pair} | {count} |")
    lines.append("")
    lines.append("## Illustrative examples")
    lines.append("")
    lines.append("The excerpts below are the student's recorded explanations. They "
                 "illustrate the reasoning; they are not presented as established "
                 "facts about the texts.")
    lines.append("")
    for ex in examples:
        lines.append(f"- **`{ex['item_id']}`** (human {ex['human_label']}, AI "
                     f"{ex['ai_label']}; assessment: *{ex['assessment']}*): "
                     f"\"{ex['explanation']}\"")
    lines.append("")
    lines.append("## Reading")
    lines.append("")
    lines.append("Most reviewed disagreements sit on the World/Business and "
                 "Business/Sci-Tech boundaries, where the codebook asks for the "
                 "main focus of the text. The review records the student's "
                 "case-by-case reading of that focus; it does not resolve whether "
                 "the human or AI label is correct in any general sense.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"report written: {OUT_MD.relative_to(PROJECT)}")
    print(f"summary written: {OUT_JSON.relative_to(PROJECT)}")
    print("CHECKS PASSED")


if __name__ == "__main__":
    main()
