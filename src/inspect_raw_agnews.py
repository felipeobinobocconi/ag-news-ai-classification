"""Read-only inspection of data/raw/test-00000-of-00001.parquet (AG News).

Reads data/raw/ (read-only by AGENTS.md rule 1) and writes a summary
of computed statistics to results/. No filters, merges or drops are
applied; all row counts are reported on the full dataset.

Run: uv run --with pyarrow --with pandas src/inspect_raw_agnews.py
"""

import hashlib
import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/test-00000-of-00001.parquet")
OUT = Path("results/inspect_raw_agnews_summary.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def is_blank(text: str) -> bool:
    return pd.isna(text) or str(text).strip() == ""


def main() -> None:
    lines: list[str] = []
    hash_before_bits = sha256(RAW)

    df = pd.read_parquet(RAW)

    lines.append(f"file: {RAW}")
    lines.append(f"shape (rows, cols): {df.shape}")
    lines.append("columns and dtypes:")
    for col, dtype in df.dtypes.items():
        lines.append(f"  {col}: {dtype}")

    lines.append("")
    lines.append("missing values per column (pandas isna):")
    for col in df.columns:
        lines.append(f"  {col}: {int(df[col].isna().sum())}")

    text_col = "text" if "text" in df.columns else None
    if text_col is not None:
        n_blank = int(df[text_col].map(is_blank).sum())
        lines.append(f"blank texts (empty or whitespace-only): {n_blank}")
    else:
        lines.append("no 'text' column found")

    label_col = "label" if "label" in df.columns else None
    if label_col is not None:
        lines.append("distinct label values (sorted):")
        lines.append(f"  {sorted(int(x) for x in df[label_col].unique())}")
        lines.append(f"rows per label (value_counts, no reshuffling):")
        vc = df[label_col].value_counts().sort_index()
        for lab, n in vc.items():
            lines.append(f"  label={int(lab)}: {int(n)} rows")

    if text_col is not None:
        n_dup_text = int(df[text_col].duplicated().sum())
        n_dup_rows_full = int(df.duplicated().sum())
        lines.append(f"exact duplicate texts (copies beyond first occurrence): {n_dup_text}")
        lines.append(f"fully duplicated rows (all columns identical): {n_dup_rows_full}")
        lines.append("NOTE: duplicates were counted but NOT removed (AGENTS.md rule 1/2).")
        lines.append("total rows after inspection: same as start, no rows dropped")

    hash_after_bits = sha256(RAW)
    lines.append("")
    lines.append(f"sha256 before read: {hash_before_bits}")
    lines.append(f"sha256 after read:  {hash_after_bits}")
    lines.append(f"raw file modified during inspection: {hash_before_bits != hash_after_bits}")

    lines.append("")
    lines.append("mode of computation: pandas/pyarrow parquet read; all counts computed from the file.")
    lines.append("assumption: columns identified by name ('text', 'label'); no type casting applied to counts.")

    report = "\n".join(lines)
    OUT.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nsummary written to: {OUT}")


if __name__ == "__main__":
    main()
