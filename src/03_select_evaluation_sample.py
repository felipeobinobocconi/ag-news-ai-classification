"""Select the 200-text evaluation sample (plan.md step 2).

Reads ONLY the text column of the raw AG News test Parquet, preserves original
zero-based source-row positions, excludes all 20 preparation positions listed
in preparation_manifest.csv, and samples 200 rows from the remaining pool
uniformly at random without replacement using
DataFrame.sample(n=200, random_state=42). Original dataset labels are never
read. The damaged preparation_20.csv is not used as an input.

Outputs (must not already exist):
  data/derived/evaluation_200.xlsx        item_id, text, human_label,
                                          human_confidence, uncertainty_reason
                                          (annotation fields blank; wrapped
                                          text, readable widths, frozen header)
  data/derived/evaluation_manifest.csv    item_id, source_row_position
  results/evaluation_sampling_summary.md  sampling provenance and checks

Run: uv run --with openpyxl src/03_select_evaluation_sample.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

RAW = Path("data/raw/test-00000-of-00001.parquet")
PREP_MANIFEST = Path("data/derived/preparation_manifest.csv")
OUT_XLSX = Path("data/derived/evaluation_200.xlsx")
OUT_MANIFEST = Path("data/derived/evaluation_manifest.csv")
OUT_SUMMARY = Path("results/evaluation_sampling_summary.md")
SEED = 42
N = 200

ANNOTATION_FIELDS = ["human_label", "human_confidence", "uncertainty_reason"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def main() -> None:
    existing = [p for p in (OUT_XLSX, OUT_MANIFEST, OUT_SUMMARY) if p.exists()]
    if existing:
        print("STOP: target files already exist; not overwriting:")
        for p in existing:
            print(f"  {p}")
        sys.exit(1)

    raw_hash = sha256(RAW)

    # Preparation manifest: positions to exclude (damaged CSV is not an input).
    prep = pd.read_csv(PREP_MANIFEST, encoding="utf-8-sig")
    prep["source_row_position"] = prep["source_row_position"].astype(int)
    excluded = set(prep["source_row_position"])
    print(f"rows read from preparation manifest: {len(prep)}")

    # Raw source: read ONLY the text column; labels never read.
    df = pd.read_parquet(RAW, columns=["text"])
    n_source = len(df)
    print(f"rows read from source (text column only): {n_source}")
    print("original zero-based positions preserved before exclusion")

    # Pool: exclude the 20 preparation rows (reason: plan.md requires
    # preparation and evaluation texts to be separate).
    pool = df[~df.index.isin(excluded)].copy()
    n_excluded = n_source - len(pool)
    print(f"rows excluded: {n_excluded} (preparation sample positions; "
          "plan.md step 2 keeps preparation and evaluation texts separate)")
    print(f"pool size after exclusion: {len(pool)}")

    if n_excluded != len(prep) or excluded.intersection(range(n_source)) != excluded:
        fail("preparation exclusion mismatch")
    if len(pool) != n_source - len(prep):
        fail("pool size does not match source minus preparation rows")

    sampled = pool.sample(n=N, random_state=SEED)
    print(f"rows sampled: {len(sampled)} (uniform, without replacement, "
          f"seed {SEED}, from the {len(pool)}-row pool, labels not inspected)")
    sampled = sampled.sort_index().rename_axis("source_row_position").reset_index()
    sampled.insert(0, "item_id", [f"eval_{i + 1:03d}" for i in range(len(sampled))])
    for field in ANNOTATION_FIELDS:
        sampled[field] = None  # blank cells, not empty strings

    # --- Write workbook with wrapped text, readable widths, frozen header ---
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        sampled[["item_id", "text", *ANNOTATION_FIELDS]].to_excel(
            writer, sheet_name="evaluation_200", index=False
        )
        ws = writer.sheets["evaluation_200"]
        ws.freeze_panes = "A2"
        widths = {"A": 12, "B": 90, "C": 16, "D": 16, "E": 40}
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)

    manifest_out = sampled[["item_id", "source_row_position"]]
    manifest_out.to_csv(OUT_MANIFEST, index=False, encoding="utf-8-sig")

    # --- Verification: re-read saved outputs ---
    back = pd.read_excel(OUT_XLSX, sheet_name="evaluation_200", dtype=str,
                         keep_default_na=False)
    man_back = pd.read_csv(OUT_MANIFEST, encoding="utf-8-sig")
    man_back["source_row_position"] = man_back["source_row_position"].astype(int)
    source_text = df["text"].reset_index(drop=True)

    checks = []
    checks.append(("workbook has exactly 200 rows", len(back) == N))
    checks.append(("manifest has exactly 200 rows", len(man_back) == N))
    checks.append(("200 unique item IDs",
                   back["item_id"].is_unique and man_back["item_id"].is_unique))
    checks.append(("item IDs are eval_001..eval_200",
                   list(back["item_id"]) == [f"eval_{i + 1:03d}" for i in range(N)]
                   and list(man_back["item_id"]) == [f"eval_{i + 1:03d}" for i in range(N)]))
    checks.append(("200 distinct source positions",
                   man_back["source_row_position"].nunique() == N))
    checks.append(("all positions are valid zero-based indices in range",
                   bool(man_back["source_row_position"].between(0, n_source - 1).all())))
    checks.append(("workbook and manifest item_id sets identical",
                   set(back["item_id"]) == set(man_back["item_id"])))
    checks.append(("manifest positions identical to workbook order",
                   list(man_back["source_row_position"])
                   == [int(p) for p in back["item_id"].map(
                       dict(zip(back["item_id"], man_back["source_row_position"])))]))
    texts_match = all(
        str(source_text.iloc[int(pos)]) == str(text)
        for pos, text in zip(man_back["source_row_position"], back["text"])
    )
    checks.append(("all 200 texts exactly match their raw source rows", texts_match))
    checks.append(("all annotation fields blank",
                   all((back[f] == "").all() for f in ANNOTATION_FIELDS)))
    checks.append(("zero overlap with preparation positions",
                   set(man_back["source_row_position"]).isdisjoint(excluded)))
    checks.append(("pool arithmetic: 7600 - 20 = 7580 >= 200 sampled",
                   n_source - len(prep) == 7580 and 7580 >= N))
    checks.append(("no original label column in either output",
                   "label" not in back.columns and "label" not in man_back.columns))

    all_pass = True
    for name, ok in checks:
        print(f"CHECK {'PASS' if ok else 'FAIL'}: {name}")
        all_pass = all_pass and ok
    if not all_pass:
        fail("one or more verification checks failed")
    print("all checks passed")

    summary = f"""# Evaluation Sampling Summary

- Script: `src/03_select_evaluation_sample.py`
- Run date: 2026-11-12
- Source: `{RAW}`
- Source SHA-256: `{raw_hash}` (recorded at sampling time)
- Exclusion input: `{PREP_MANIFEST}` (20 preparation positions; the damaged
  `preparation_20.csv` was not used as an input)
- Sampling method: original zero-based positions preserved; the 20 preparation
  positions excluded (reason: plan.md step 2 keeps preparation and evaluation
  texts separate); `DataFrame.sample(n={N}, random_state={SEED})` on the
  remaining pool of {n_source - len(prep)} rows; uniform, without replacement;
  no stratification; original dataset labels never read.
- Seed: {SEED} (fixed)
- pandas version: {pd.__version__}
- Row counts: source {n_source}; excluded {n_excluded}; pool
  {n_source - n_excluded}; sampled {len(sampled)}.
- Outputs:
  - `{OUT_XLSX}` (item_id, text, human_label, human_confidence,
    uncertainty_reason; annotation fields blank; wrapped text, readable
    column widths, frozen header row)
  - `{OUT_MANIFEST}` (item_id, source_row_position)
- Item IDs: eval_001..eval_{N:03d}, assigned in ascending source-row order
  (same convention as the preparation sample; documented).
- Codebook status: FROZEN v1.0 (see `results/codebook_freeze_note.md`).
- Verification: all checks passed (200 unique IDs/positions; exact text match
  to source rows; blank annotation fields; zero overlap with preparation; no
  label column in outputs).
- Original dataset labels and any AI classification remain hidden until both
  independent classifications are complete (plan.md steps 5 and 8).
"""
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(summary, encoding="utf-8")
    print("files written:")
    print(f"  {OUT_XLSX}")
    print(f"  {OUT_MANIFEST}")
    print(f"  {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
