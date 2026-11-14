"""Secondary comparison of human and AI labels with the original AG News labels.

The original dataset labels are read only now, after both independent
classifications were completed and frozen. They are treated as another
reference of unknown reliability, not as unquestionable ground truth.

Inputs:
  data/raw/test-00000-of-00001.parquet            text and original label
  data/derived/evaluation_manifest.csv            item_id -> zero-based position
  data/derived/evaluation_200_labelled.xlsx       frozen human labels
  results/ai_classification/evaluation_gemini/ai_classifications.csv

Outputs:
  results/original_label_comparison.csv
  results/original_label_comparison.json
  results/original_label_comparison.md

No frozen label is changed and the primary human-AI analysis is not recomputed
as a new result; the primary count is only reproduced as context.

Run:
  uv run --with openpyxl src/21_original_label_comparison.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import NormalDist

import pandas as pd

SEED = 42

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw" / "test-00000-of-00001.parquet"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"
WORKBOOK = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"

OUT_CSV = PROJECT / "results" / "original_label_comparison.csv"
OUT_JSON = PROJECT / "results" / "original_label_comparison.json"
OUT_MD = PROJECT / "results" / "original_label_comparison.md"

N_EXPECTED = 200
VALID_LABELS = {0, 1, 2, 3}
NAMES = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
Z95 = NormalDist().inv_cdf(0.975)


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def wilson(successes: int, n: int) -> tuple[float, float]:
    p = successes / n
    denominator = 1 + Z95 * Z95 / n
    centre = (p + Z95 * Z95 / (2 * n)) / denominator
    half = (Z95 * ((p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) ** 0.5)
            / denominator)
    return max(0.0, centre - half), min(1.0, centre + half)


def matrix(frame: pd.DataFrame, row_col: str, col_col: str) -> list[list[int]]:
    out = [[0] * 4 for _ in range(4)]
    for row in frame.itertuples(index=False):
        out[int(getattr(row, row_col))][int(getattr(row, col_col))] += 1
    return out


def matrix_table(values: list[list[int]], row_name: str, col_name: str) -> list[str]:
    lines = [f"| {row_name} \\ {col_name} | " + " | ".join(NAMES[i] for i in range(4))
             + " | Total |",
             "| --- | --- | --- | --- | --- | --- |"]
    for i in range(4):
        row = [str(v) for v in values[i]]
        lines.append(f"| {NAMES[i]} | " + " | ".join(row) + f" | {sum(values[i])} |")
    totals = [sum(values[i][j] for i in range(4)) for j in range(4)]
    lines.append("| **Total** | " + " | ".join(str(v) for v in totals)
                 + f" | {sum(totals)} |")
    return lines


def main() -> None:
    print(f"random seed fixed at {SEED} (no stochastic step in this script)")

    raw = pd.read_parquet(RAW, columns=["text", "label"])
    manifest = pd.read_csv(MANIFEST, dtype={"item_id": str})
    manual = pd.read_excel(
        WORKBOOK, sheet_name="evaluation_200",
        usecols=["item_id", "text", "human_label"],
        dtype={"item_id": str},
    )
    ai = pd.read_csv(AI_CSV, usecols=["item_id", "label"], dtype={"item_id": str})

    print(f"rows read: raw={len(raw)}, manifest={len(manifest)}, "
          f"manual={len(manual)}, AI={len(ai)}")
    require(len(raw) == 7600, f"raw rows = {len(raw)}, expected 7600")
    require(len(manifest) == len(manual) == len(ai) == N_EXPECTED,
            "expected 200 rows in manifest, manual labels and AI labels")
    require(manifest["item_id"].is_unique and manual["item_id"].is_unique
            and ai["item_id"].is_unique, "input IDs are not unique")
    require(set(manifest["item_id"]) == set(manual["item_id"]) == set(ai["item_id"]),
            "item_id sets differ across inputs")

    positions = manifest.set_index("item_id")["source_row_position"].astype(int)
    require(positions.isin(range(len(raw))).all(),
            "manifest has an out-of-range source_row_position")
    require(positions.is_unique, "manifest source positions are not unique")

    joined = manual.merge(ai, on="item_id", how="inner", validate="one_to_one")
    joined = joined.merge(manifest, on="item_id", how="inner", validate="one_to_one")
    print(f"joined rows: {len(joined)}; dropped: {N_EXPECTED - len(joined)} "
          "(reason: no unmatched IDs)")
    require(len(joined) == N_EXPECTED, "joined table is not 200 rows")

    dataset_labels = []
    text_mismatches = 0
    for row in joined.itertuples(index=False):
        position = int(positions.loc[row.item_id])
        raw_row = raw.iloc[position]
        dataset_labels.append(int(raw_row["label"]))
        if str(raw_row["text"]) != str(row.text):
            text_mismatches += 1
    joined["dataset_label"] = dataset_labels

    print(f"source positions valid: {len(joined)} of {len(joined)}")
    print(f"text mismatches versus frozen workbook: {text_mismatches}")
    require(text_mismatches == 0,
            "raw text retrieved through the manifest differs from the frozen workbook")
    require(set(joined["dataset_label"]) <= VALID_LABELS,
            "dataset labels outside 0-3")
    require(set(joined["human_label"]) <= VALID_LABELS, "human labels outside 0-3")
    require(set(joined["label"]) <= VALID_LABELS, "AI labels outside 0-3")

    human_matches = int((joined["human_label"] == joined["dataset_label"]).sum())
    ai_matches = int((joined["label"] == joined["dataset_label"]).sum())
    human_ai_matches = int((joined["human_label"] == joined["label"]).sum())
    human_rate = human_matches / len(joined)
    ai_rate = ai_matches / len(joined)
    human_ci = wilson(human_matches, len(joined))
    ai_ci = wilson(ai_matches, len(joined))

    print(f"human-dataset matches: {human_matches}/{len(joined)} = {human_rate:.4f}")
    print(f"AI-dataset matches: {ai_matches}/{len(joined)} = {ai_rate:.4f}")
    print(f"primary human-AI matches reproduced for context: "
          f"{human_ai_matches}/{len(joined)} = {human_ai_matches / len(joined):.4f}")
    require(human_ai_matches == 162,
            f"reproduced human-AI matches = {human_ai_matches}, expected 162")

    human_matrix = matrix(joined, "human_label", "dataset_label")
    ai_matrix = matrix(joined, "label", "dataset_label")
    dataset_counts = [int((joined["dataset_label"] == i).sum()) for i in range(4)]

    rows = [
        {
            "comparison": "human_vs_dataset",
            "n": len(joined),
            "matches": human_matches,
            "agreement_rate": human_rate,
            "wilson_95_low": human_ci[0],
            "wilson_95_high": human_ci[1],
        },
        {
            "comparison": "ai_vs_dataset",
            "n": len(joined),
            "matches": ai_matches,
            "agreement_rate": ai_rate,
            "wilson_95_low": ai_ci[0],
            "wilson_95_high": ai_ci[1],
        },
    ]
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8")

    summary = {
        "script": "src/21_original_label_comparison.py",
        "inputs": {
            "raw": "data/raw/test-00000-of-00001.parquet",
            "manifest": "data/derived/evaluation_manifest.csv",
            "human": "data/derived/evaluation_200_labelled.xlsx",
            "ai": "results/ai_classification/evaluation_gemini/ai_classifications.csv",
        },
        "checks": {
            "n": len(joined),
            "unique_ids": int(joined["item_id"].nunique()),
            "unique_positions": int(positions.nunique()),
            "text_mismatches": text_mismatches,
            "dataset_label_counts": dict(zip(NAMES.values(), dataset_counts)),
        },
        "human_vs_dataset": {
            "matches": human_matches,
            "agreement_rate": human_rate,
            "wilson_95": list(human_ci),
            "confusion_human_by_dataset": human_matrix,
        },
        "ai_vs_dataset": {
            "matches": ai_matches,
            "agreement_rate": ai_rate,
            "wilson_95": list(ai_ci),
            "confusion_ai_by_dataset": ai_matrix,
        },
        "primary_human_vs_ai_context": {
            "matches": human_ai_matches,
            "agreement_rate": human_ai_matches / len(joined),
        },
        "note": (
            "Original dataset labels are another reference of unknown reliability, "
            "not unquestionable ground truth. These are secondary comparisons and "
            "do not change the primary human-AI result."
        ),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    lines = [
        "# Original-label comparison (secondary)",
        "",
        "- Script: `src/21_original_label_comparison.py`",
        "- Inputs: `data/raw/test-00000-of-00001.parquet`, "
        "`data/derived/evaluation_manifest.csv`, "
        "`data/derived/evaluation_200_labelled.xlsx`, and "
        "`results/ai_classification/evaluation_gemini/ai_classifications.csv`.",
        f"- Items: {len(joined)}; unique IDs: {joined['item_id'].nunique()}; "
        f"unique source positions: {positions.nunique()}.",
        f"- Text alignment mismatches between the raw texts retrieved through the "
        f"manifest and the frozen workbook: {text_mismatches}.",
        "",
        "## Agreement with the original dataset label",
        "",
        "| Comparison | Matches | Items | Agreement | Wilson 95% |",
        "| --- | --- | --- | --- | --- |",
        f"| Human vs dataset | {human_matches} | {len(joined)} | "
        f"{100 * human_rate:.2f}% | {100 * human_ci[0]:.2f}% to "
        f"{100 * human_ci[1]:.2f}% |",
        f"| AI vs dataset | {ai_matches} | {len(joined)} | "
        f"{100 * ai_rate:.2f}% | {100 * ai_ci[0]:.2f}% to "
        f"{100 * ai_ci[1]:.2f}% |",
        "",
        f"For context only, the frozen human-AI comparison reproduces "
        f"{human_ai_matches}/{len(joined)} = {100 * human_ai_matches / len(joined):.2f}% "
        "exact agreement. This secondary comparison does not change that result.",
        "",
        "## Confusion matrices",
        "",
        "Rows are the classification being compared; columns are the original "
        "dataset label.",
        "",
        "### Human labels by dataset label",
        "",
        *matrix_table(human_matrix, "Human", "Dataset"),
        "",
        "### AI labels by dataset label",
        "",
        *matrix_table(ai_matrix, "AI", "Dataset"),
        "",
        "## Interpretation limits",
        "",
        "The original AG News labels are another reference of unknown reliability. "
        "No original annotation guidelines are available to this project, and label "
        "correctness has not been verified. The dataset labels are therefore not "
        "treated as unquestionable ground truth, and these comparisons are "
        "secondary rather than a replacement for the primary human-AI analysis.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"output: {OUT_CSV.relative_to(PROJECT)}")
    print(f"output: {OUT_JSON.relative_to(PROJECT)}")
    print(f"output: {OUT_MD.relative_to(PROJECT)}")
    print("CHECKS PASSED")


if __name__ == "__main__":
    main()
