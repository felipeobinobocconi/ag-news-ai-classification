"""Category-hypothesis comparison (plan.md step 7).

Defines groups exclusively by human_label:
  - pooled Business/Sci-Tech: human_label in {2, 3}
  - Sports: human_label == 1

Reports totals, disagreements and disagreement rates, the difference in
percentage points, and a 95% Newcombe interval for the difference of two
independent proportions (Wilson score intervals, Newcombe 1998 method 10).

Uncertain human annotations are kept (primary analysis). Counts are verified
against the saved confusion matrix. No labels are changed, no model is called,
no original dataset labels are read, and no individual disagreements are
reviewed. Only one interval is computed as requested; no additional tests.

Outputs: results/workflow_run/ (never overwritten)

Run: uv run src/12_category_hypothesis.py
"""

import json
import math
from pathlib import Path

import pandas as pd

PROJECT = Path.cwd()
OUT_DIR = PROJECT / "results" / "workflow_run"
TABLE = OUT_DIR / "comparison_table.csv"
MATRIX = OUT_DIR / "confusion_matrix.csv"

Z = 1.959963984540054  # 95%


def wilson_interval(x: int, n: int, z: float = Z):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        raise ValueError("empty group")
    p = x / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return p, max(0.0, centre - half), min(1.0, centre + half)


def newcombe_interval(x1: int, n1: int, x2: int, n2: int, z: float = Z):
    """Newcombe (1998) method 10 interval for p1 - p2 using Wilson intervals."""
    p1, l1, u1 = wilson_interval(x1, n1, z)
    p2, l2, u2 = wilson_interval(x2, n2, z)
    diff = p1 - p2
    lower = diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return diff, lower, upper, (p1, l1, u1), (p2, l2, u2)


def main() -> None:
    for name in ("category_hypothesis_table.csv", "category_hypothesis_summary.json",
                 "category_hypothesis_report.md"):
        if (OUT_DIR / name).exists():
            raise SystemExit(f"STOP: output already exists, refusing to overwrite: {OUT_DIR / name}")

    df = pd.read_csv(TABLE)
    if not {"item_id", "human_label", "ai_label", "human_confidence", "agreement"} <= set(df.columns):
        raise SystemExit("STOP: comparison table missing expected columns")
    print(f"LOAD: {len(df)} rows from comparison_table.csv")

    df["disagree"] = 1 - df["agreement"]
    pooled = df[df["human_label"].isin([2, 3])]
    sports = df[df["human_label"] == 1]
    print(f"GROUPS: pooled Business/Sci-Tech = {len(pooled)} items; Sports = {len(sports)} items")
    print(f"KEPT: uncertain human annotations -> pooled {int((pooled['human_confidence']=='uncertain').sum())}, "
          f"Sports {int((sports['human_confidence']=='uncertain').sum())}")

    def stats(g):
        n = len(g)
        d = int(g["disagree"].sum())
        return n, d, d / n

    n1, d1, r1 = stats(pooled)
    n2, d2, r2 = stats(sports)

    diff, lower, upper, w1, w2 = newcombe_interval(d1, n1, d2, n2)
    diff_pp = diff * 100
    lower_pp = lower * 100
    upper_pp = upper * 100

    # --- Verify counts against the saved confusion matrix ---
    cm = pd.read_csv(MATRIX, index_col=0)
    cm.columns = [c.replace("ai_", "") for c in cm.columns]
    pooled_rows = ["human_Business", "human_Sci/Tech"]
    cm_pooled_total = int(cm.loc[pooled_rows].values.sum())
    cm_pooled_agree = int(cm.loc["human_Business", "Business"] + cm.loc["human_Sci/Tech", "Sci/Tech"])
    cm_pooled_dis = cm_pooled_total - cm_pooled_agree
    cm_sports_total = int(cm.loc["human_Sports"].sum())
    cm_sports_dis = int(cm.loc["human_Sports"].sum() - cm.loc["human_Sports", "Sports"])
    if (n1, d1, n2, d2) != (cm_pooled_total, cm_pooled_dis, cm_sports_total, cm_sports_dis):
        raise SystemExit(
            f"STOP: counts disagree with confusion matrix: computed {(n1, d1, n2, d2)}, "
            f"matrix {(cm_pooled_total, cm_pooled_dis, cm_sports_total, cm_sports_dis)}")
    print("CHECK PASS: group counts match the saved confusion matrix "
          f"(pooled {n1}/{d1}, Sports {n2}/{d2})")

    table = pd.DataFrame([
        {"group": "Business/Sci-Tech (pooled, human_label 2 or 3)",
         "items": n1, "disagreements": d1, "disagreement_rate": r1,
         "rate_pct": r1 * 100,
         "wilson_95_lo_pct": w1[1] * 100, "wilson_95_hi_pct": w1[2] * 100},
        {"group": "Sports (human_label 1)",
         "items": n2, "disagreements": d2, "disagreement_rate": r2,
         "rate_pct": r2 * 100,
         "wilson_95_lo_pct": w2[1] * 100, "wilson_95_hi_pct": w2[2] * 100},
    ])
    table.to_csv(OUT_DIR / "category_hypothesis_table.csv", index=False)

    summary = {
        "script": "src/12_category_hypothesis.py",
        "input": "results/workflow_run/comparison_table.csv",
        "groups": {
            "pooled_business_scitech": {"items": n1, "disagreements": d1, "rate": r1,
                                        "wilson_95": [w1[1], w1[2]],
                                        "uncertain_kept": int((pooled['human_confidence'] == 'uncertain').sum())},
            "sports": {"items": n2, "disagreements": d2, "rate": r2,
                       "wilson_95": [w2[1], w2[2]],
                       "uncertain_kept": int((sports['human_confidence'] == 'uncertain').sum())},
        },
        "difference_pp": diff_pp,
        "newcombe_95_pp": [lower_pp, upper_pp],
        "method": "Newcombe (1998) method 10 interval for p1 - p2 using Wilson score intervals; 95%; z=1.959964",
        "assumptions": [
            "The two groups are independent (disjoint, independently classified items).",
            "Within each group, disagreement indicators are treated as binomial draws.",
            "Wilson/Newcombe intervals are approximate and may be asymmetric.",
            "No continuity correction; no multiple-comparison adjustment.",
            "Uncertain human annotations are included in the primary analysis.",
        ],
        "note": "Agreement with one human reference, not accuracy against ground truth. No causal claim; no generalization beyond this sample and setup.",
    }
    (OUT_DIR / "category_hypothesis_summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                              encoding="utf-8")

    report = [
        "# Category-hypothesis comparison (plan.md step 7)",
        "",
        "- Script: `src/12_category_hypothesis.py`",
        "- Input: `results/workflow_run/comparison_table.csv`",
        "- Groups defined exclusively by `human_label`; uncertain annotations kept.",
        "",
        "## Group rates",
        "",
        "| Group | Items | Disagreements | Rate | Wilson 95% |",
        "| --- | --- | --- | --- | --- |",
        f"| Business/Sci-Tech (2 or 3) | {n1} | {d1} | {r1:.4f} ({r1*100:.2f}%) | "
        f"{w1[1]*100:.2f}% – {w1[2]*100:.2f}% |",
        f"| Sports (1) | {n2} | {d2} | {r2:.4f} ({r2*100:.2f}%) | "
        f"{w2[1]*100:.2f}% – {w2[2]*100:.2f}% |",
        "",
        f"**Difference (pooled minus Sports): {diff_pp:.2f} percentage points.**",
        f"**95% Newcombe interval: [{lower_pp:.2f}, {upper_pp:.2f}] percentage points.**",
        "",
        "## Method and assumptions",
        "",
        "95% Newcombe (1998) method-10 interval for the difference of two",
        "independent proportions, built from Wilson score intervals (z = 1.959964).",
        "Assumptions: the groups are independent (disjoint items); within-group",
        "disagreement indicators are treated as binomial draws; the interval is",
        "approximate and may be asymmetric; no continuity correction and no",
        "multiple-comparison adjustment. Uncertain human annotations are kept.",
        "",
        "## Interpretation",
        "",
        f"Observed direction: the pooled Business/Sci-Tech disagreement rate is",
        f"{diff_pp:.2f} pp higher than the Sports rate in this sample. The 95%",
        f"interval [{lower_pp:.2f}, {upper_pp:.2f}] pp "
        + ("excludes 0, which is consistent with a positive difference in this sample; "
           "the interval still reflects substantial sampling uncertainty."
           if lower > 0 else
           "includes 0, so the data do not establish the direction of the difference; "
           "sampling uncertainty is substantial.")
        + "",
        "",
        "This describes agreement with one human reference in this sample and setup;",
        "it is not accuracy against unquestionable ground truth, not a causal claim,",
        "and does not generalize beyond this sample.",
    ]
    (OUT_DIR / "category_hypothesis_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"\nTABLE:\n{table[['group','items','disagreements','rate_pct']].to_string(index=False)}")
    print(f"DIFFERENCE: {diff_pp:.2f} pp; 95% Newcombe: [{lower_pp:.2f}, {upper_pp:.2f}] pp")
    print(f"OUTPUTS: {OUT_DIR}")
    print("VERDICT: STEP 7 COMPLETE")


if __name__ == "__main__":
    main()
