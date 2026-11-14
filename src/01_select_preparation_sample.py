"""Select the 20-text preparation sample (plan.md step 1).

Reads ONLY the text column from the raw AG News test Parquet, assigns each
source row its original zero-based position, and selects 20 rows uniformly at
random without replacement using DataFrame.sample(n=20, random_state=42).
Original labels are never read. Original texts are preserved exactly.

Outputs (must not already exist):
  data/derived/preparation_20.csv          item_id, text, human_label,
                                           human_confidence, uncertainty_reason
                                           (annotation fields left empty;
                                           UTF-8 with BOM, CSV-quoted for Excel)
  data/derived/preparation_manifest.csv    item_id, source_row_position
  results/preparation_sampling_summary.md  sampling provenance

Run: uv run src/01_select_preparation_sample.py
"""

import csv
import hashlib
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/test-00000-of-00001.parquet")
OUT_SAMPLE = Path("data/derived/preparation_20.csv")
OUT_MANIFEST = Path("data/derived/preparation_manifest.csv")
OUT_SUMMARY = Path("results/preparation_sampling_summary.md")
SEED = 42
N = 20

ANNOTATION_FIELDS = ["human_label", "human_confidence", "uncertainty_reason"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def main() -> None:
    # Overwrite guard: stop if any target file already exists.
    existing = [p for p in (OUT_SAMPLE, OUT_MANIFEST, OUT_SUMMARY) if p.exists()]
    if existing:
        print("STOP: target files already exist; not overwriting:")
        for p in existing:
            print(f"  {p}")
        sys.exit(1)

    raw_hash = sha256(RAW)
    # Read ONLY the text column; original labels are not touched.
    df = pd.read_parquet(RAW, columns=["text"])
    n_source = len(df)
    print(f"rows read from source (text column only): {n_source}")
    print("no filter, merge or drop applied to the source; a 20-row random "
          f"sample (authorized preparation sample, seed {SEED}) is drawn next")

    # Original zero-based position before sampling.
    df = df.reset_index(drop=True)
    df["source_row_position"] = range(len(df))

    sampled = df.sample(n=N, random_state=SEED)
    # Deterministic item_id assignment in ascending source order.
    sampled = sampled.sort_values("source_row_position").reset_index(drop=True)
    print(f"rows sampled: {len(sampled)} (uniform, without replacement, "
          f"seed {SEED}, labels not inspected)")

    sampled.insert(0, "item_id", [f"prep_{i + 1:03d}" for i in range(len(sampled))])
    for field in ANNOTATION_FIELDS:
        sampled[field] = ""

    sample_out = sampled[["item_id", "text", *ANNOTATION_FIELDS]]
    manifest_out = sampled[["item_id", "source_row_position"]]

    OUT_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    sample_out.to_csv(
        OUT_SAMPLE,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
    )
    manifest_out.to_csv(
        OUT_MANIFEST,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
    )

    # --- Verification checks (print check results only; never texts/labels) ---
    sample_back = pd.read_csv(OUT_SAMPLE, encoding="utf-8-sig", dtype=str)
    manifest_back = pd.read_csv(OUT_MANIFEST, encoding="utf-8-sig")

    checks = []

    checks.append(("sample has exactly 20 rows", len(sample_back) == N))
    checks.append(("20 distinct source rows",
                   manifest_back["source_row_position"].nunique() == N))
    checks.append(("20 unique item IDs",
                   sample_back["item_id"].nunique() == N
                   and manifest_back["item_id"].nunique() == N))
    checks.append(("item IDs are prep_001..prep_020",
                   list(sample_back["item_id"]) == [f"prep_{i + 1:03d}" for i in range(N)]))

    # Texts must match their source rows exactly.
    texts_match = True
    for pos, text in zip(manifest_back["source_row_position"], sample_back["text"]):
        if str(df.loc[int(pos), "text"]) != str(text):
            texts_match = False
            break
    checks.append(("all 20 texts match their source rows exactly", texts_match))
    checks.append(("manifest positions match the sampled rows",
                   set(manifest_back["source_row_position"])
                   == set(sampled["source_row_position"])))

    # Annotation fields must be blank.
    checks.append(("all annotation fields blank",
                   all((sample_back[f].isna() | (sample_back[f] == "")).all()
                       for f in ANNOTATION_FIELDS)))

    # No original label column anywhere in the outputs.
    checks.append(("no original label column in either output CSV",
                   "label" not in sample_back.columns
                   and "label" not in manifest_back.columns))

    all_pass = True
    for name, ok in checks:
        print(f"CHECK {'PASS' if ok else 'FAIL'}: {name}")
        all_pass = all_pass and ok
    if not all_pass:
        fail("one or more verification checks failed")
    print("all checks passed")

    manifest_lines = ", ".join(str(int(p)) for p in manifest_back["source_row_position"])
    summary = f"""# Preparation Sampling Summary

- Script: `src/01_select_preparation_sample.py`
- Run date: 2026-11-12
- Source: `{RAW}`
- Source SHA-256: `{raw_hash}` (recorded at sampling time)
- Sampling method: `pandas.DataFrame.sample(n={N}, random_state={SEED})` on the
  text column only; uniform, without replacement; no stratification, no
  filtering by topic, no inspection of original labels.
- Seed: {SEED} (fixed)
- pandas version: {pd.__version__}
- Source rows read: {n_source} (text column only)
- Rows sampled: {len(sampled)}; distinct source rows: {N}; unique item IDs: {N}
- Original row count preserved: no rows dropped from the source file; the
  sample is a selection, not a reduction of the source.
- Outputs:
  - `{OUT_SAMPLE}` (item_id, text, human_label, human_confidence, uncertainty_reason; annotation fields empty)
  - `{OUT_MANIFEST}` (item_id, source_row_position)
- Item IDs: prep_001..prep_{N:03d}, assigned in ascending source-row order
  (analysis choice, documented here).
- Sampled source positions (for excluding these rows from the future
  evaluation sample): [{manifest_lines}]
- Verification: all checks passed (20 distinct rows, 20 unique IDs, exact text
  match to source rows, blank annotation fields, no label column in outputs).
"""
    OUT_SUMMARY.write_text(summary, encoding="utf-8")
    print("files written:")
    print(f"  {OUT_SAMPLE}")
    print(f"  {OUT_MANIFEST}")
    print(f"  {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
