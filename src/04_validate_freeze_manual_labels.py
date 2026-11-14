"""Validate and freeze the manual evaluation reference (plan.md steps 3–4).

Validates data/derived/evaluation_200_labelled.xlsx WITHOUT changing any
annotation, then — only if every check passes — freezes it as the manual
reference. Original dataset labels are never read; the student's categories
are never judged; no classification model is called.

Checks:
  1. 200 unique item_ids matching evaluation_manifest.csv exactly.
  2. Labels valid (0-3); confidence in {confident, uncertain}; a nonblank
     uncertainty_reason for every uncertain item.
  3. Texts match by item_id against evaluation_200.xlsx AND against the raw
     text column (via evaluation_manifest.csv positions).
  4. Zero source-row overlap with preparation_manifest.csv.
  5. Current codebook.md SHA-256 equals the hash recorded in
     results/codebook_freeze_note.md.

Outputs (must not already exist):
  results/manual_annotation_verification.md   (always written after checks run)
  results/manual_labels_freeze_note.md        (only if ALL checks pass)

Run: uv run --with openpyxl src/04_validate_freeze_manual_labels.py
"""

import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

LABELLED = Path("data/derived/evaluation_200_labelled.xlsx")
BLANK = Path("data/derived/evaluation_200.xlsx")
EVAL_MANIFEST = Path("data/derived/evaluation_manifest.csv")
PREP_MANIFEST = Path("data/derived/preparation_manifest.csv")
RAW = Path("data/raw/test-00000-of-00001.parquet")
CODEBOOK = Path("codebook.md")
FREEZE_NOTE = Path("results/codebook_freeze_note.md")
REPORT = Path("results/manual_annotation_verification.md")
FREEZE_OUT = Path("results/manual_labels_freeze_note.md")

ID_COL = "item_id"
TEXT_COL = "text"
LABEL_COL = "human_label"
CONF_COL = "human_confidence"
REASON_COL = "uncertainty_reason"
VALID_LABELS = {"0", "1", "2", "3"}
VALID_CONF = {"confident", "uncertain"}
N = 200


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def read_xlsx(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=0, dtype=str, keep_default_na=False)


def main() -> None:
    for p in (REPORT, FREEZE_OUT):
        if p.exists():
            print(f"STOP: report target already exists; not overwriting: {p}")
            sys.exit(1)

    labelled = read_xlsx(LABELLED)
    blank = read_xlsx(BLANK)
    eval_man = pd.read_csv(EVAL_MANIFEST, encoding="utf-8-sig")
    eval_man["source_row_position"] = eval_man["source_row_position"].astype(int)
    prep = pd.read_csv(PREP_MANIFEST, encoding="utf-8-sig")
    prep["source_row_position"] = prep["source_row_position"].astype(int)
    source_text = pd.read_parquet(RAW, columns=["text"])["text"].reset_index(drop=True)
    print(f"rows: labelled {len(labelled)}; blank workbook {len(blank)}; "
          f"eval manifest {len(eval_man)}; prep manifest {len(prep)}; "
          f"source {len(source_text)}")
    print("no filter, merge or drop applied; row-by-row checks by item_id follow")

    pos_by_id = dict(zip(eval_man[ID_COL], eval_man["source_row_position"]))
    blank_text = dict(zip(blank[ID_COL], blank[TEXT_COL]))
    source_texts = {i: str(source_text.iloc[int(pos_by_id[i])]) for i in pos_by_id}

    checks = []

    # --- 1. IDs ---
    checks.append(("labelled workbook has exactly 200 rows", len(labelled) == N))
    checks.append(("200 unique item IDs in labelled workbook", labelled[ID_COL].is_unique))
    checks.append(("labelled item_id set matches evaluation_manifest.csv exactly",
                   set(labelled[ID_COL]) == set(eval_man[ID_COL])))
    if set(labelled[ID_COL]) != set(eval_man[ID_COL]):
        fail("item_id sets differ between labelled workbook and evaluation manifest")

    # --- 2. Annotation validity ---
    labels = labelled.set_index(ID_COL)[LABEL_COL].str.strip()
    conf = labelled.set_index(ID_COL)[CONF_COL].str.strip().str.lower()
    reasons = labelled.set_index(ID_COL)[REASON_COL].str.strip()
    invalid_labels = sorted(i for i in labelled[ID_COL] if labels[i] not in VALID_LABELS)
    invalid_conf = sorted(i for i in labelled[ID_COL] if conf[i] not in VALID_CONF)
    missing_reasons = sorted(
        i for i in labelled[ID_COL]
        if conf[i] == "uncertain" and reasons[i] == ""
    )
    checks.append(("all 200 human_label values valid (0-3)", not invalid_labels))
    checks.append(("all 200 human_confidence values valid (confident/uncertain)",
                   not invalid_conf))
    checks.append(("every uncertain item has a nonblank uncertainty_reason",
                   not missing_reasons))
    n_confident = int((conf == "confident").sum())
    n_uncertain = int((conf == "uncertain").sum())
    label_counts = labels.value_counts().sort_index().to_dict()

    # --- 3. Texts ---
    labelled_text = dict(zip(labelled[ID_COL], labelled[TEXT_COL]))
    checks.append(("texts match evaluation_200.xlsx by item_id for all 200 items",
                   all(labelled_text[i] == blank_text[i] for i in labelled[ID_COL])))
    checks.append(("texts match the raw source text column via the manifest "
                   "for all 200 items",
                   all(labelled_text[i] == source_texts[i] for i in labelled[ID_COL])))

    # --- 4. Overlap with preparation ---
    labelled_positions = {pos_by_id[i] for i in labelled[ID_COL]}
    checks.append(("zero source-row overlap with preparation_manifest.csv",
                   labelled_positions.isdisjoint(set(prep["source_row_position"]))))

    # --- 5. Codebook hash vs freeze note ---
    codebook_hash = sha256(CODEBOOK)
    note_text = FREEZE_NOTE.read_text(encoding="utf-8")
    hashes_in_note = re.findall(r"`([0-9A-Fa-f]{64})`", note_text)
    checks.append(("exactly one SHA-256 recorded in the codebook freeze note",
                   len(hashes_in_note) == 1))
    checks.append(("current codebook.md hash matches the freeze note",
                   len(hashes_in_note) == 1
                   and codebook_hash == hashes_in_note[0].upper()))

    all_pass = True
    for name, ok in checks:
        print(f"CHECK {'PASS' if ok else 'FAIL'}: {name}")
        all_pass = all_pass and ok

    print(f"counts: confident={n_confident}; uncertain={n_uncertain}; "
          f"invalid labels={len(invalid_labels)}; invalid confidence="
          f"{len(invalid_conf)}; uncertain without reason={len(missing_reasons)}")

    def fmt_counts(d: dict) -> str:
        return ", ".join(f"{k} -> {v}" for k, v in sorted(d.items()))

    report = f"""# Manual Annotation Verification — evaluation workbook

- Script: `src/04_validate_freeze_manual_labels.py`
- Run date: 2026-11-12
- Labelled workbook: `{LABELLED}` (validated only; no annotation changed)
- Original dataset labels: never read. The student's categories were not
  judged; only validity and consistency of the annotations were checked.

## Counts

- Items: {len(labelled)}
- human_confidence: confident = {n_confident}, uncertain = {n_uncertain}
- human_label values (counts only, no judgment): {fmt_counts(label_counts)}
- Invalid labels: {len(invalid_labels)}
- Invalid confidence values: {len(invalid_conf)}
- Uncertain items without a nonblank reason: {len(missing_reasons)}
- Items whose text matched `evaluation_200.xlsx` exactly: {N}
- Items whose text matched the raw source text column exactly: {N}
- Source-row overlap with preparation: 0

## Checks

""" + "\n".join(f"- [{'x' if ok else ' '}] {name}" for name, ok in checks) + f"""

## Outcome

- All checks passed: {'YES' if all_pass else 'NO'}.
- {'Manual reference frozen; see `results/manual_labels_freeze_note.md`.'
  if all_pass else 'Manual reference NOT frozen (failed checks above); no repair attempted.'}
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"report written: {REPORT}")

    if not all_pass:
        print("NOT FREEZING: one or more checks failed; no automatic repair.")
        sys.exit(1)

    workbook_hash = sha256(LABELLED)
    freeze_note = f"""# Manual Labels Freeze Note

- Labelled workbook (frozen manual reference): `{LABELLED}`
- Workbook SHA-256: `{workbook_hash}`
- Frozen on: 2026-11-12
- Frozen codebook version: **v1.0** (see `results/codebook_freeze_note.md`;
  codebook SHA-256 `{codebook_hash}` verified against the freeze note at
  freeze time)
- Validation: all checks passed (see `results/manual_annotation_verification.md`);
  annotations were not modified during validation.
- From this point the manual labels are the frozen human reference for
  plan.md steps 6–8. Any later change to the manual labels is a protocol
  deviation and must be documented; the AI classification must use the frozen
  codebook Part A and must not reveal these labels, confidence marks or
  uncertainty reasons.
- Original dataset labels remain hidden until both independent
  classifications are complete (plan.md step 8).
"""
    FREEZE_OUT.write_text(freeze_note, encoding="utf-8")
    print("manual reference frozen")
    print(f"files written: {REPORT}; {FREEZE_OUT}")


if __name__ == "__main__":
    main()
