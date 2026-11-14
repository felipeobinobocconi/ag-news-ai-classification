# Archive — pre-correction documents, 2026-11-14

These files are the versions of the project documents **before** the final
documentation corrections made on 2026-11-14. They are kept unchanged as a
record. The live versions are in the project root and in `results/`.

## Why these versions were superseded

1. **Reproduction instructions.** The earlier `README.md` listed commands that
   hit the scripts' existing-output guards. The live version now gives an exact
   procedure for a separate copy, names only the generated outputs that must be
   moved aside there, and separates verification commands from regeneration
   commands.
2. **Model/API wording.** The earlier documents wrote the model as
   `gemini-3.5-flash-lite` (v1beta), which could read as a model version. The
   live documents use "gemini-3.5-flash-lite, accessed through the Gemini API
   v1beta" and keep the recorded model-version metadata separate.

No numerical result, frozen input, label, codebook, study-design element or
analysis script was changed by these corrections.

## Archived files

| Archived file | Live path | SHA-256 of the archived copy |
| --- | --- | --- |
| `final_report.md` | `final_report.md` | `170DC14F1D1E44377018644B968FD162CA19B921DAD0C00F7DCD3CD1F72B93AB` |
| `README.md` | `README.md` | `0460C04C33D267F327A3620304F2D3C4B10C1126D221FF5F25C9BA3F687643B5` |
| `results/final_delivery_checklist.md` | `results/final_delivery_checklist.md` | `B02E11A191B782036609287C557BB409AD07D8FA4325490544CD642C9A4E867B` |

The hashes identify the archived copies. They were computed with
`Get-FileHash -Algorithm SHA256` before the live files were edited.
