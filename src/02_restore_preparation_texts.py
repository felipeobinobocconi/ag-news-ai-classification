"""Restore truncated texts in the manual preparation workbook.

Authorized recovery (option 1, after data/derived/preparation_20.csv was
found corrupted by a semicolon-delimited, unquoted re-save): texts are
restored from the raw Parquet via preparation_manifest.csv.

Reads ONLY the text column of the raw Parquet. Validates source-row positions
and matches rows strictly by item_id. Preserves human_label, human_confidence
and uncertainty_reason exactly as entered in the workbook. Neither input file
is modified; classifications are not changed.

Inputs (read-only):
  data/raw/test-00000-of-00001.parquet          (text column only)
  data/derived/preparation_manifest.csv         (item_id -> source_row_position)
  data/derived/preparation_20_labelled.xlsx     (human annotations)

Outputs (must not already exist):
  data/derived/preparation_20_labelled_restored.xlsx
  results/preparation_text_restore_verification.md

Run: uv run --with openpyxl src/02_restore_preparation_texts.py
"""

import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/test-00000-of-00001.parquet")
MANIFEST = Path("data/derived/preparation_manifest.csv")
XLSX_IN = Path("data/derived/preparation_20_labelled.xlsx")
XLSX_OUT = Path("data/derived/preparation_20_labelled_restored.xlsx")
REPORT = Path("results/preparation_text_restore_verification.md")

ID_COL = "item_id"
TEXT_COL = "text"
ANNOTATION_COLS = ["human_label", "human_confidence", "uncertainty_reason"]
N = 20


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def read_xlsx(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=0, dtype=str, keep_default_na=False)


def main() -> None:
    if XLSX_OUT.exists() or REPORT.exists():
        print("STOP: target files already exist; not overwriting:")
        for p in (XLSX_OUT, REPORT):
            if p.exists():
                print(f"  {p}")
        sys.exit(1)

    # --- Manifest: item_id -> source_row_position ---
    manifest = pd.read_csv(MANIFEST, encoding="utf-8-sig")
    manifest["source_row_position"] = manifest["source_row_position"].astype(int)
    n_manifest = len(manifest)
    print(f"rows read from manifest: {n_manifest}")
    print("no filter, merge or drop applied; strict match by item_id follows")

    # --- Raw source: read ONLY the text column ---
    source_text = pd.read_parquet(RAW, columns=["text"])
    n_source = len(source_text)
    print(f"rows available in source (text column only): {n_source}")
    print("labels were never read from the source")

    # --- Labelled workbook ---
    xlsx_df = read_xlsx(XLSX_IN)
    print(f"rows read from workbook: {len(xlsx_df)}")

    # --- Validation and strict matching ---
    checks = []
    checks.append(("manifest has exactly 20 rows", n_manifest == N))
    checks.append(("manifest item_ids unique", manifest[ID_COL].is_unique))
    positions = manifest["source_row_position"]
    checks.append(("all source positions are valid zero-based indices in range",
                   bool((positions >= 0).all() and (positions < n_source).all())))
    checks.append(("manifest source positions unique", positions.is_unique))
    checks.append(("workbook has exactly 20 rows", len(xlsx_df) == N))
    checks.append(("workbook item_ids unique", xlsx_df[ID_COL].is_unique))
    manifest_ids = set(manifest[ID_COL])
    xlsx_ids = set(xlsx_df[ID_COL])
    checks.append(("identical item_id sets in manifest and workbook",
                   manifest_ids == xlsx_ids))
    if manifest_ids != xlsx_ids:
        fail(f"item_id sets differ; only in manifest: {sorted(manifest_ids - xlsx_ids)}; "
             f"only in workbook: {sorted(xlsx_ids - manifest_ids)}")

    # --- Original texts from the raw source via the manifest ---
    original_text = {item_id: str(source_text.iloc[int(pos)]["text"])
                     for item_id, pos in zip(manifest[ID_COL], positions)}
    xlsx_text = dict(zip(xlsx_df[ID_COL], xlsx_df[TEXT_COL]))
    changed_ids = sorted(i for i in sorted(manifest_ids)
                         if xlsx_text[i] != original_text[i])
    print(f"items with text differing between workbook and raw source: {len(changed_ids)}")

    restored = xlsx_df.copy()
    restored[TEXT_COL] = restored[ID_COL].map(original_text)

    # --- Write restored workbook (annotations as entered; blanks stay blank) ---
    restored.to_excel(
        XLSX_OUT,
        sheet_name="preparation_20",
        index=False,
        engine="openpyxl",
        na_rep="",
    )

    # --- Verify the restored workbook by re-reading it ---
    back = read_xlsx(XLSX_OUT)
    back_text = dict(zip(back[ID_COL], back[TEXT_COL]))
    checks.append(("restored workbook has exactly 20 rows", len(back) == N))
    checks.append(("20 unique item IDs", back[ID_COL].is_unique))
    checks.append(("item_id set unchanged after restore", set(back[ID_COL]) == manifest_ids))
    checks.append(("all 20 texts exactly match the raw source texts",
                   all(back_text[i] == original_text[i] for i in sorted(manifest_ids))))
    checks.append(("human annotations unchanged for every item",
                   all(
                       [dict(zip(back[ID_COL], back[c]))[i]
                        == dict(zip(xlsx_df[ID_COL], xlsx_df[c]))[i]
                        for c in ANNOTATION_COLS for i in sorted(manifest_ids)])))
    checks.append(("changed items' annotation values identical before/after",
                   all(
                       [dict(zip(back[ID_COL], back[c]))[i]
                        == dict(zip(xlsx_df[ID_COL], xlsx_df[c]))[i]
                        for c in ANNOTATION_COLS for i in changed_ids])))

    all_pass = True
    for name, ok in checks:
        print(f"CHECK {'PASS' if ok else 'FAIL'}: {name}")
        all_pass = all_pass and ok
    if not all_pass:
        fail("one or more verification checks failed")
    print("all checks passed")

    changed_list = ", ".join(changed_ids) if changed_ids else "none"
    unchanged = len(manifest_ids) - len(changed_ids)
    report = f"""# Text Restoration Verification — preparation workbook

- Script: `src/02_restore_preparation_texts.py`
- Run date: 2026-11-12
- **Deviation from the original authorization (documented):** texts were
  restored from the raw Parquet via `preparation_manifest.csv` instead of
  from `preparation_20.csv`, because the CSV was found corrupted after
  creation (re-saved as semicolon-delimited, unquoted data at 12:23:34 on
  2026-11-12, after the labelled workbook was saved). This recovery path was
  authorized by the user. The corrupted CSV was not modified.
- Inputs (read-only, not modified):
  - `{RAW}` (text column only; original dataset labels never read)
  - `{MANIFEST}` (item_id -> source_row_position; unchanged since creation)
  - `{XLSX_IN}` (human annotations; some texts truncated at semicolons during Excel import)
- Output: `{XLSX_OUT}` (texts restored from the raw source; annotations preserved as entered)
- Matching: strictly by `item_id`; source positions validated as unique,
  zero-based indices within range before any change.
- Items whose text differed between workbook and raw source (text restored):
  **{changed_list}** ({len(changed_ids)} of {len(manifest_ids)}; {unchanged} items already matched exactly)
- Annotation columns preserved verbatim: human_label, human_confidence,
  uncertainty_reason (compared before and after for every item).
- News texts and annotation values are not displayed in this report, by
  design.

## Checks (all must pass)

""" + "\n".join(f"- [x] {name}" for name, _ in checks) + """

## Integrity notes

- No original dataset labels were read at any point.
- No classification model was called; no evaluation texts were selected.
- The codebook status is unchanged (DRAFT).
- Script 01 was not rerun; the damaged CSV was left as found.
"""
    REPORT.write_text(report, encoding="utf-8")
    print("files written:")
    print(f"  {XLSX_OUT}")
    print(f"  {REPORT}")


if __name__ == "__main__":
    main()
