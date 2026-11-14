"""Agent run, step 5: independent verification of the saved outputs.

Rebuilds the joined dataset from the three authorised inputs, recomputes every
headline number from scratch, and compares the results with the saved files.
Also cross-checks the Wilson intervals against statsmodels'
`proportion_confint(method="wilson")` (no continuity correction) and checks
that the figure and reports exist and are readable.

Outputs (results/agent_run/):
  verification_report.md
  verification_summary.json
  17_run_log.txt

Run: uv run --with openpyxl src/17_agent_run_verify_outputs.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

# Fixed seed although this script has no stochastic step (AGENTS.md rule 5).
SEED = 42
np.random.seed(SEED)

PROJECT = Path(__file__).resolve().parents[1]
WORKBOOK = PROJECT / "data" / "derived" / "evaluation_200_labelled.xlsx"
AI_CSV = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "ai_classifications.csv"
MANIFEST = PROJECT / "data" / "derived" / "evaluation_manifest.csv"
MANUAL_FREEZE = PROJECT / "results" / "manual_labels_freeze_note.md"
AI_FREEZE = PROJECT / "results" / "ai_classification" / "evaluation_gemini" / "classification_freeze_note.md"

OUTDIR = PROJECT / "results" / "agent_run"
DATASET = OUTDIR / "analysis_dataset.csv"
COUNTS_CSV = OUTDIR / "confusion_matrix_counts.csv"
PCT_CSV = OUTDIR / "confusion_matrix_row_pct.csv"
AGREEMENT_JSON = OUTDIR / "agreement_summary.json"
GROUP_CSV = OUTDIR / "group_disagreement.csv"
CATEGORY_CSV = OUTDIR / "category_disagreement.csv"
DIFF_JSON = OUTDIR / "difference_summary.json"
PNG = OUTDIR / "confusion_matrix.png"
PDF = OUTDIR / "confusion_matrix.pdf"
AGREEMENT_REPORT = OUTDIR / "agreement_report.md"
HYPOTHESIS_REPORT = OUTDIR / "category_hypothesis_report.md"
INPUT_REPORT = OUTDIR / "input_verification.md"
CAPTION = OUTDIR / "confusion_matrix_caption.md"
REPORT = OUTDIR / "verification_report.md"
SUMMARY_JSON = OUTDIR / "verification_summary.json"
RUN_LOG = OUTDIR / "17_run_log.txt"

CATEGORY = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
Z95 = NormalDist().inv_cdf(0.975)
TOL = 1e-12


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str = "") -> None:
        print(message)
        self.lines.append(str(message))

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


log = Log()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def labeled_hash(path: Path, label: str) -> str | None:
    """Return the SHA-256 introduced by `label` in a freeze note, else None."""
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        rf"{re.escape(label)}\s*:?\s*`([0-9A-Fa-f]{{64}})`", text, flags=re.S)
    return matches[0].upper() if len(matches) == 1 else None


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


def newcombe(k1: int, n1: int, k2: int, n2: int,
             z: float = Z95) -> tuple[float, float]:
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    return (float(d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)),
            float(d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)))


def close(a: float, b: float, tol: float = TOL) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    log("AGENT RUN STEP 17 — independent verification")
    log(f"run_utc: {datetime.now(timezone.utc).isoformat()}")
    log(f"random seed fixed at {SEED} (no stochastic step)")

    checks: list[tuple[str, bool]] = []

    # --------------------------------------------------------------- hashes
    e_wb = labeled_hash(MANUAL_FREEZE, "Workbook SHA-256")
    e_ai = labeled_hash(AI_FREEZE, "SHA-256")
    checks.append(("workbook hash still matches freeze note",
                   e_wb is not None and sha256(WORKBOOK) == e_wb))
    checks.append(("AI CSV hash still matches freeze note",
                   e_ai is not None and sha256(AI_CSV) == e_ai))

    # ----------------------------------------------------- rebuild the join
    log("rebuilding the analysis dataset from the three authorised inputs")
    labelled = pd.read_excel(WORKBOOK, sheet_name=0, dtype=str, keep_default_na=False)
    ai = pd.read_csv(AI_CSV, encoding="utf-8-sig")
    manifest = pd.read_csv(MANIFEST, encoding="utf-8-sig")

    for frame in (labelled, ai, manifest):
        frame["item_id"] = frame["item_id"].astype(str).str.strip()

    human = pd.DataFrame({
        "item_id": labelled["item_id"],
        "human_label": pd.to_numeric(labelled["human_label"], errors="raise").astype(int),
        "human_confidence": labelled["human_confidence"].str.strip().str.lower(),
    })
    machine = pd.DataFrame({
        "item_id": ai["item_id"],
        "ai_label": pd.to_numeric(ai["label"], errors="raise").astype(int),
    })
    rebuilt = human.merge(machine, on="item_id", how="inner",
                          validate="one_to_one").sort_values("item_id")
    rebuilt["human_category"] = rebuilt["human_label"].map(CATEGORY)
    rebuilt["ai_category"] = rebuilt["ai_label"].map(CATEGORY)
    rebuilt["disagreement"] = (
        rebuilt["human_label"] != rebuilt["ai_label"]).astype(int)
    rebuilt["human_group"] = np.where(
        rebuilt["human_label"] == 1, "Sports",
        np.where(rebuilt["human_label"].isin([2, 3]),
                 "Business/Sci-Tech pooled", "World (not in comparison)"))
    rebuilt = rebuilt[["item_id", "human_label", "human_category",
                       "human_confidence", "ai_label", "ai_category",
                       "human_group", "disagreement"]].reset_index(drop=True)
    log(f"rebuilt rows: {len(rebuilt)}; saved dataset rows: "
        f"{len(pd.read_csv(DATASET)) if DATASET.exists() else 'missing'}")

    saved = pd.read_csv(DATASET, encoding="utf-8").sort_values(
        "item_id").reset_index(drop=True)
    checks.append(("rebuilt dataset equals saved analysis dataset",
                   saved.equals(rebuilt)))
    checks.append(("analysis dataset has 200 unique rows",
                   len(saved) == 200 and saved["item_id"].is_unique))
    checks.append(("analysis dataset contains no news-text column",
                   "text" not in saved.columns))
    checks.append(("all manifest IDs used exactly once",
                   sorted(manifest["item_id"]) == sorted(saved["item_id"])))

    # ------------------------------------------------------------- agreement
    n = len(rebuilt)
    n_agree = int((rebuilt["human_label"] == rebuilt["ai_label"]).sum())
    n_disagree = n - n_agree
    p_agree = n_agree / n
    a_lo, a_hi = wilson(n_agree, n)

    with open(AGREEMENT_JSON, encoding="utf-8") as fh:
        agree_saved = json.load(fh)

    checks.append(("saved agreement count matches recomputation",
                   agree_saved["n_items"] == n
                   and agree_saved["agreements"] == n_agree
                   and agree_saved["disagreements"] == n_disagree))
    checks.append(("saved agreement rate matches recomputation",
                   close(agree_saved["agreement_rate"], p_agree)))
    checks.append(("saved agreement Wilson interval matches recomputation",
                   close(agree_saved["agreement_wilson_95"][0], a_lo)
                   and close(agree_saved["agreement_wilson_95"][1], a_hi)))

    matrix = np.zeros((4, 4), dtype=int)
    for h in range(4):
        for a in range(4):
            matrix[h, a] = int(((rebuilt["human_label"] == h)
                                & (rebuilt["ai_label"] == a)).sum())
    counts_saved = pd.read_csv(COUNTS_CSV, encoding="utf-8").sort_values(
        "human_label").reset_index(drop=True)
    counts_matrix = counts_saved[[f"ai_{i}" for i in range(4)]].to_numpy(dtype=int)
    checks.append(("confusion-matrix counts match recomputation",
                   np.array_equal(counts_matrix, matrix)))
    checks.append(("confusion-matrix counts sum to 200",
                   int(matrix.sum()) == 200))
    checks.append(("confusion-matrix row totals match human-label counts",
                   np.array_equal(
                       matrix.sum(axis=1),
                       rebuilt["human_label"].value_counts().reindex(
                           range(4), fill_value=0).to_numpy())))

    row_totals = matrix.sum(axis=1)
    expected_pct = np.where(row_totals[:, None] > 0,
                            matrix / row_totals[:, None] * 100.0, np.nan)
    pct_saved = pd.read_csv(PCT_CSV, encoding="utf-8").sort_values(
        "human_label").reset_index(drop=True)
    checks.append(("row-percentage table matches recomputation",
                   np.allclose(pct_saved[[f"ai_{i}" for i in range(4)]].to_numpy(
                       dtype=float), expected_pct, atol=1e-9, equal_nan=True)))

    # ---------------------------------------------------------- group contrast
    pooled = rebuilt[rebuilt["human_label"].isin([2, 3])]
    sports = rebuilt[rebuilt["human_label"] == 1]
    k1, n1 = int(pooled["disagreement"].sum()), len(pooled)
    k2, n2 = int(sports["disagreement"].sum()), len(sports)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    diff = p1 - p2
    ci_low, ci_high = newcombe(k1, n1, k2, n2)

    with open(DIFF_JSON, encoding="utf-8") as fh:
        diff_saved = json.load(fh)
    group_saved = pd.read_csv(GROUP_CSV, encoding="utf-8").set_index("group")

    checks.append(("saved group denominators match recomputation",
                   diff_saved["n_group_1"] == n1
                   and diff_saved["n_group_2"] == n2))
    checks.append(("saved group disagreement counts match recomputation",
                   diff_saved["disagreements_group_1"] == k1
                   and diff_saved["disagreements_group_2"] == k2
                   and int(group_saved.loc["Business/Sci-Tech pooled", "n"]) == n1
                   and int(group_saved.loc["Sports", "n"]) == n2))
    checks.append(("saved group rates match recomputation",
                   close(diff_saved["rate_group_1"], p1)
                   and close(diff_saved["rate_group_2"], p2)
                   and close(group_saved.loc["Business/Sci-Tech pooled",
                                             "disagreement_rate"], p1)
                   and close(group_saved.loc["Sports", "disagreement_rate"], p2)))
    checks.append(("saved Wilson intervals match recomputation",
                   close(group_saved.loc["Business/Sci-Tech pooled",
                                         "wilson_low"], l1)
                   and close(group_saved.loc["Business/Sci-Tech pooled",
                                             "wilson_high"], u1)
                   and close(group_saved.loc["Sports", "wilson_low"], l2)
                   and close(group_saved.loc["Sports", "wilson_high"], u2)))
    checks.append(("saved difference matches recomputation",
                   close(diff_saved["difference"], diff)
                   and close(diff_saved["difference_pp"], 100.0 * diff)))
    checks.append(("saved Newcombe interval matches recomputation",
                   close(diff_saved["difference_ci_95"][0], ci_low)
                   and close(diff_saved["difference_ci_95"][1], ci_high)))

    # ------------------------------------ cross-check Wilson via statsmodels
    sm_l1, sm_u1 = proportion_confint(k1, n1, alpha=0.05, method="wilson")
    sm_l2, sm_u2 = proportion_confint(k2, n2, alpha=0.05, method="wilson")
    sm_al, sm_au = proportion_confint(n_agree, n, alpha=0.05, method="wilson")
    checks.append(("Wilson intervals match statsmodels (group 1)",
                   close(sm_l1, l1, 1e-10) and close(sm_u1, u1, 1e-10)))
    checks.append(("Wilson intervals match statsmodels (group 2)",
                   close(sm_l2, l2, 1e-10) and close(sm_u2, u2, 1e-10)))
    checks.append(("Wilson interval matches statsmodels (overall agreement)",
                   close(sm_al, a_lo, 1e-10) and close(sm_au, a_hi, 1e-10)))

    alt_low = diff - np.sqrt((p1 - sm_l1) ** 2 + (sm_u2 - p2) ** 2)
    alt_high = diff + np.sqrt((sm_u1 - p1) ** 2 + (p2 - sm_l2) ** 2)
    checks.append(("Newcombe interval matches statsmodels-based rebuild",
                   close(alt_low, ci_low, 1e-10)
                   and close(alt_high, ci_high, 1e-10)))

    # ----------------------------------------------------- categories / files
    cat_saved = pd.read_csv(CATEGORY_CSV, encoding="utf-8").set_index("human_label")
    cat_ok = True
    for lab in range(4):
        subset = rebuilt[rebuilt["human_label"] == lab]
        k, m = int(subset["disagreement"].sum()), len(subset)
        cat_ok = cat_ok and int(cat_saved.loc[lab, "n"]) == m
        cat_ok = cat_ok and int(cat_saved.loc[lab, "disagreements"]) == k
        if m > 0:
            cat_ok = cat_ok and close(cat_saved.loc[lab, "disagreement_rate"],
                                      k / m)
    checks.append(("per-category descriptive rates match recomputation", cat_ok))

    required_files = [DATASET, COUNTS_CSV, PCT_CSV, AGREEMENT_JSON, GROUP_CSV,
                      CATEGORY_CSV, DIFF_JSON, PNG, PDF, AGREEMENT_REPORT,
                      HYPOTHESIS_REPORT, INPUT_REPORT, CAPTION]
    checks.append(("all expected output files exist",
                   all(p.exists() for p in required_files)))
    checks.append(("figure PNG is a readable image larger than 10 KB",
                   PNG.exists() and PNG.stat().st_size > 10_000
                   and min(mpimg.imread(PNG).shape[:2]) > 500))
    checks.append(("figure PDF is larger than 10 KB",
                   PDF.exists() and PDF.stat().st_size > 10_000))
    checks.append(("reports are non-empty",
                   all(p.exists() and p.stat().st_size > 0
                       for p in (AGREEMENT_REPORT, HYPOTHESIS_REPORT,
                                 INPUT_REPORT, CAPTION))))

    # ------------------------------------------------------------- summary
    all_pass = all(ok for _, ok in checks)
    log("")
    for name, ok in checks:
        log(f"CHECK {'PASS' if ok else 'FAIL'}: {name}")
    log("")
    log(f"recomputed: n={n}; agreements={n_agree}; "
        f"agreement={p_agree:.6f} (Wilson {a_lo:.6f}-{a_hi:.6f})")
    log(f"recomputed: pooled {k1}/{n1}={p1:.6f}; sports {k2}/{n2}={p2:.6f}; "
        f"difference={100 * diff:+.4f} pp; Newcombe "
        f"[{100 * ci_low:+.4f}, {100 * ci_high:+.4f}] pp")
    log(f"all checks passed: {'YES' if all_pass else 'NO'}")

    summary = {
        "script": "src/17_agent_run_verify_outputs.py",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "all_checks_passed": all_pass,
        "n_checks": len(checks),
        "checks_failed": [name for name, ok in checks if not ok],
        "recomputed": {
            "n_items": n,
            "agreements": n_agree,
            "disagreements": n_disagree,
            "agreement_rate": p_agree,
            "agreement_wilson_95": [a_lo, a_hi],
            "confusion_matrix_counts": matrix.tolist(),
            "pooled_n": n1,
            "pooled_disagreements": k1,
            "pooled_rate": p1,
            "pooled_wilson_95": [l1, u1],
            "sports_n": n2,
            "sports_disagreements": k2,
            "sports_rate": p2,
            "sports_wilson_95": [l2, u2],
            "difference": diff,
            "difference_pp": 100.0 * diff,
            "difference_ci_95": [ci_low, ci_high],
            "difference_ci_95_pp": [100.0 * ci_low, 100.0 * ci_high],
        },
        "statsmodels_cross_check": {
            "pooled_wilson_95": [float(sm_l1), float(sm_u1)],
            "sports_wilson_95": [float(sm_l2), float(sm_u2)],
            "overall_wilson_95": [float(sm_al), float(sm_au)],
            "newcombe_rebuilt": [float(alt_low), float(alt_high)],
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Verification report — agent run",
        "",
        "- Script: `src/17_agent_run_verify_outputs.py`",
        f"- Run (UTC): {summary['run_utc']}",
        "- Method: rebuild the joined dataset from the three authorised inputs,",
        "  recompute all headline quantities from scratch, and compare with the",
        "  saved files. Wilson intervals are additionally cross-checked against",
        "  `statsmodels.stats.proportion.proportion_confint(method=\"wilson\")`",
        "  (no continuity correction).",
        "",
        "## Headline quantities recomputed",
        "",
        f"- Items: {n}",
        f"- Exact agreements: {n_agree}; disagreements: {n_disagree}",
        f"- Overall agreement: {100 * p_agree:.2f}% "
        f"(95% Wilson {100 * a_lo:.2f}% to {100 * a_hi:.2f}%)",
        f"- Pooled Business/Sci-Tech: {k1}/{n1} = {100 * p1:.2f}% "
        f"(95% Wilson {100 * l1:.2f}% to {100 * u1:.2f}%)",
        f"- Sports: {k2}/{n2} = {100 * p2:.2f}% "
        f"(95% Wilson {100 * l2:.2f}% to {100 * u2:.2f}%)",
        f"- Difference (pooled minus Sports): {100 * diff:+.2f} pp "
        f"(95% Newcombe {100 * ci_low:+.2f} to {100 * ci_high:+.2f} pp)",
        "",
        "## Checks",
        "",
    ]
    lines += [f"- [{'x' if ok else ' '}] {name}" for name, ok in checks]
    lines += [
        "",
        f"All checks passed: **{'YES' if all_pass else 'NO'}**.",
        "",
        "## Scope and limits",
        "",
        "- Verification covers data handling, arithmetic and file integrity only.",
        "- The human labels were not judged for correctness; agreement is exact",
        "  label match, not accuracy.",
        "- No original dataset label, news text, classification model, `.env`",
        "  file, `results/workflow_run/` file or earlier analysis script was used.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    log(f"files written: {REPORT.relative_to(PROJECT)}; "
        f"{SUMMARY_JSON.relative_to(PROJECT)}; {RUN_LOG.relative_to(PROJECT)}")
    log.save(RUN_LOG)

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
