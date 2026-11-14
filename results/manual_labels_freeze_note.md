# Manual Labels Freeze Note

- Labelled workbook (frozen manual reference): `data\derived\evaluation_200_labelled.xlsx`
- Workbook SHA-256: `D71C12E8FBD7E070698413FCB341F162665CB0101A5539A454D25CB49203948A`
- Frozen on: 2026-11-12
- Frozen codebook version: **v1.0** (see `results/codebook_freeze_note.md`;
  codebook SHA-256 `9EB79D7BD0EDBDA2E9D856B68F0A6A72E97061F463652C58BD04056FC6148A7E` verified against the freeze note at
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
