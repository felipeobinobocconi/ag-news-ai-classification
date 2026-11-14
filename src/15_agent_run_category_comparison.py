"""Agent run, step 3: compare disagreement rates, pooled Business/Sci-Tech vs Sports.

Primary comparison (plan.md step 7):
  denominator = number of texts in each human-labelled group;
  disagreement = AI label differs from the human label;
  contrast = pooled Business/Sci-Tech rate minus Sports rate (percentage points);
  95% Newcombe interval for the difference, built from Wilson score intervals
  without continuity correction (Newcombe 1998, method 10).

No hypothesis test or p-value is computed. Uncertain human annotations remain
in the primary analysis. Outputs are descriptive for this sample.

Outputs (results/agent_run/):
  group_disagreement.csv
  category_disagreement.csv
  difference_summary.json
  category_hypothesis_report.md
  15_run_log.txt

Run: uv run src/15_agent_run_category_comparison.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

# Fixed seed although this script has no stochastic step (AGENTS.md rule 5).
SEED = 42
np.random.seed(SEED)

PROJECT = Path(__file__).resolve().parents[1]
OUTDIR = PROJECT / "results" / "agent_run"
DATASET = OUTDIR / "analysis_dataset.csv"
GROUP_CSV = OUTDIR / "group_disagreement.csv"
CATEGORY_CSV = OUTDIR / "category_disagreement.csv"
SUMMARY_JSON = OUTDIR / "difference_summary.json"
REPORT = OUTDIR / "category_hypothesis_report.md"
RUN_LOG = OUTDIR / "15_run_log.txt"

CATEGORY = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
Z95 = NormalDist().inv_cdf(0.975)


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str = "") -> None:
        print(message)
        self.lines.append(str(message))

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


log = Log()


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval without continuity correction."""
    if n <= 0:
        raise ValueError("n must be positive")
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


def newcombe_interval(k1: int, n1: int, k2: int, n2: int,
                      z: float = Z95) -> tuple[float, float]:
    """Newcombe (1998) method 10 interval for p1 - p2.

    Hybrid score interval built from Wilson intervals without continuity
    correction. k is the number of disagreements, n the group denominator.
    """
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p1 - p2
    lower = d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return float(lower), float(upper)


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{100.0 * x:.{digits}f}%"


def fmt_pp(x: float, digits: int = 1) -> str:
    return f"{100.0 * x:+.{digits}f} pp"


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not DATASET.exists():
        print(f"STOP: missing {DATASET}; run src/13_agent_run_verify_inputs.py first")
        sys.exit(1)

    log("AGENT RUN STEP 15 — category disagreement comparison")
    log(f"run_utc: {datetime.now(timezone.utc).isoformat()}")
    log(f"random seed fixed at {SEED} (no stochastic step)")
    log(f"input: {DATASET.relative_to(PROJECT)}")

    df = pd.read_csv(DATASET, encoding="utf-8")
    log(f"row count on read: {len(df)}")
    if len(df) != 200 or not df["item_id"].is_unique:
        print("STOP: expected 200 unique item_id rows")
        sys.exit(1)
    if not df["human_label"].isin([0, 1, 2, 3]).all():
        print("STOP: invalid human_label value")
        sys.exit(1)
    if not df["ai_label"].isin([0, 1, 2, 3]).all():
        print("STOP: invalid ai_label value")
        sys.exit(1)

    # Group definitions use the HUMAN label only, as specified in plan.md.
    pooled_mask = df["human_label"].isin([2, 3])
    sports_mask = df["human_label"] == 1
    comparison_mask = pooled_mask | sports_mask

    log("")
    log("STEP 1 — group construction from human labels")
    log(f"  rows before group restriction: {len(df)}")
    log(f"  excluded World (human_label=0): {int((~comparison_mask).sum())} "
        "(outside the pre-specified comparison)")
    dfc = df[comparison_mask].copy()
    log(f"  rows after group restriction: {len(dfc)} "
        "(all rows retained for Business/Sci-Tech/Sports)")

    pooled = dfc[dfc["human_label"].isin([2, 3])]
    sports = dfc[dfc["human_label"] == 1]
    if len(pooled) + len(sports) != len(dfc):
        print("STOP: groups overlap or do not exhaust the comparison subset")
        sys.exit(1)
    if len(pooled) == 0 or len(sports) == 0:
        print("STOP: empty comparison group")
        sys.exit(1)

    k1, n1 = int(pooled["disagreement"].sum()), len(pooled)
    k2, n2 = int(sports["disagreement"].sum()), len(sports)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    diff = p1 - p2
    ci_low, ci_high = newcombe_interval(k1, n1, k2, n2)

    log("")
    log("STEP 2 — disagreement rates and difference")
    log(f"  pooled Business/Sci-Tech: {k1}/{n1} disagreements = {p1:.6f} "
        f"(Wilson 95% {l1:.6f} to {u1:.6f})")
    log(f"  Sports: {k2}/{n2} disagreements = {p2:.6f} "
        f"(Wilson 95% {l2:.6f} to {u2:.6f})")
    log(f"  difference (pooled - Sports): {diff:+.6f} = {100 * diff:+.2f} pp")
    log(f"  Newcombe 95% interval: {ci_low:+.6f} to {ci_high:+.6f} "
        f"({100 * ci_low:+.2f} to {100 * ci_high:+.2f} pp)")
    log("  no continuity correction; no p-value computed")

    group_rows = [
        {
            "group": "Business/Sci-Tech pooled",
            "human_labels": "2, 3",
            "n": n1,
            "disagreements": k1,
            "agreements": n1 - k1,
            "disagreement_rate": p1,
            "disagreement_rate_pct": 100.0 * p1,
            "wilson_low": l1,
            "wilson_high": u1,
            "wilson_low_pct": 100.0 * l1,
            "wilson_high_pct": 100.0 * u1,
        },
        {
            "group": "Sports",
            "human_labels": "1",
            "n": n2,
            "disagreements": k2,
            "agreements": n2 - k2,
            "disagreement_rate": p2,
            "disagreement_rate_pct": 100.0 * p2,
            "wilson_low": l2,
            "wilson_high": u2,
            "wilson_low_pct": 100.0 * l2,
            "wilson_high_pct": 100.0 * u2,
        },
    ]
    group_df = pd.DataFrame(group_rows)
    group_df.to_csv(GROUP_CSV, index=False, encoding="utf-8")

    # Descriptive per-category rates, including World for completeness.
    cat_rows = []
    for lab in range(4):
        subset = df[df["human_label"] == lab]
        k, m = int(subset["disagreement"].sum()), len(subset)
        lo, hi = wilson(k, m) if m > 0 else (float("nan"), float("nan"))
        cat_rows.append({
            "human_label": lab,
            "human_category": CATEGORY[lab],
            "in_primary_comparison": lab in (1, 2, 3),
            "n": m,
            "disagreements": k,
            "disagreement_rate": (k / m) if m > 0 else None,
            "disagreement_rate_pct": (100.0 * k / m) if m > 0 else None,
            "wilson_low": lo if m > 0 else None,
            "wilson_high": hi if m > 0 else None,
            "wilson_low_pct": (100.0 * lo) if m > 0 else None,
            "wilson_high_pct": (100.0 * hi) if m > 0 else None,
        })
    cat_df = pd.DataFrame(cat_rows)
    cat_df.to_csv(CATEGORY_CSV, index=False, encoding="utf-8")

    ci_excludes_zero = ci_low > 0 or ci_high < 0
    direction = ("higher for pooled Business/Sci-Tech" if diff > 0
                 else "lower for pooled Business/Sci-Tech" if diff < 0
                 else "no observed difference")

    summary = {
        "script": "src/15_agent_run_category_comparison.py",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(DATASET.relative_to(PROJECT)),
        "contrast": "pooled Business/Sci-Tech disagreement rate minus Sports "
                    "disagreement rate",
        "group_1": "human_label in {2, 3} (Business, Sci/Tech)",
        "group_2": "human_label == 1 (Sports)",
        "n_group_1": n1,
        "n_group_2": n2,
        "disagreements_group_1": k1,
        "disagreements_group_2": k2,
        "rate_group_1": p1,
        "rate_group_2": p2,
        "wilson_group_1_95": [l1, u1],
        "wilson_group_2_95": [l2, u2],
        "difference": diff,
        "difference_pp": 100.0 * diff,
        "difference_ci_95": [ci_low, ci_high],
        "difference_ci_95_pp": [100.0 * ci_low, 100.0 * ci_high],
        "ci_method": "Newcombe (1998) method 10, hybrid score interval",
        "component_intervals": "Wilson score intervals, no continuity correction",
        "z_95": Z95,
        "confidence_level": 0.95,
        "p_value_computed": False,
        "ci_excludes_zero": bool(ci_excludes_zero),
        "observed_direction": direction,
        "primary_analysis_includes_uncertain": True,
        "uncertain_count_in_comparison": int(
            dfc["human_confidence"].eq("uncertain").sum()),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------- report
    if ci_low > 0:
        ci_statement = (
            "The entire 95% interval lies above zero: in this sample, the "
            "observed direction (higher disagreement in the pooled "
            "Business/Sci-Tech group) is not compatible with a zero or negative "
            "difference at the 5% level under this interval method."
        )
    elif ci_high < 0:
        ci_statement = (
            "The entire 95% interval lies below zero: in this sample, the "
            "observed direction (lower disagreement in the pooled "
            "Business/Sci-Tech group) is not compatible with a zero or positive "
            "difference at the 5% level under this interval method."
        )
    else:
        ci_statement = (
            "The 95% interval includes zero, so the data are compatible with "
            "both a higher and a lower pooled Business/Sci-Tech disagreement "
            "rate; the observed direction is not statistically resolved by this "
            "sample."
        )

    if diff > 0:
        observed_statement = (
            "The observed pooled Business/Sci-Tech disagreement rate was higher "
            "than the Sports rate."
        )
    elif diff < 0:
        observed_statement = (
            "The observed pooled Business/Sci-Tech disagreement rate was lower "
            "than the Sports rate."
        )
    else:
        observed_statement = "The two observed rates were equal."

    disproof_met = p1 <= p2
    disproof_statement = (
        "The plan's disproof condition (pooled rate equal to or lower than the "
        "Sports rate), applied to the observed point estimates, "
        + ("is met: the point estimate does not support the hypothesis."
           if disproof_met else
           "is not met: the point estimate is in the hypothesised direction.")
    )

    lines = [
        "# Category disagreement comparison — agent run",
        "",
        "- Script: `src/15_agent_run_category_comparison.py`",
        f"- Run (UTC): {summary['run_utc']}",
        f"- Input: `{summary['input']}` (produced by `src/13_agent_run_verify_inputs.py`)",
        "- Contrast: pooled human-labelled Business/Sci-Tech disagreement rate "
        "minus human-labelled Sports disagreement rate.",
        "- Denominator for each group: the group's number of texts.",
        "- Uncertain human annotations remain in the primary analysis.",
        "",
        "## Group construction",
        "",
        f"- Starting rows: {len(df)}",
        f"- Excluded from this comparison: {int((~comparison_mask).sum())} "
        "World-labelled texts (outside the pre-specified contrast).",
        f"- Comparison rows: {len(dfc)}; all retained rows belong to exactly "
        "one comparison group.",
        "",
        "## Disagreement rates",
        "",
        "| Human-labelled group | Labels | n | Disagreements | Disagreement rate "
        "| 95% Wilson interval |",
        "| -------------------- | ------ | - | ------------- | ----------------- "
        "| ------------------- |",
        f"| Business/Sci-Tech pooled | 2, 3 | {n1} | {k1} | {fmt_pct(p1, 1)} | "
        f"{fmt_pct(l1, 1)} to {fmt_pct(u1, 1)} |",
        f"| Sports | 1 | {n2} | {k2} | {fmt_pct(p2, 1)} | "
        f"{fmt_pct(l2, 1)} to {fmt_pct(u2, 1)} |",
        "",
        "Wilson intervals use the score method without continuity correction.",
        "",
        "## Difference and 95% Newcombe interval",
        "",
        f"- Observed difference (pooled minus Sports): **{fmt_pp(diff, 2)}**",
        f"- 95% Newcombe interval: **{fmt_pp(ci_low, 2)} to {fmt_pp(ci_high, 2)}**",
        f"- Method: Newcombe (1998) method 10, combining the two Wilson score "
        f"intervals (z = {Z95:.6f}); no continuity correction.",
        "- No p-value or hypothesis test is reported; the interval is the "
        "inferential summary.",
        "",
        "## Interpretation",
        "",
        f"- **Observed direction.** {observed_statement}",
        f"- **Statistical uncertainty.** {ci_statement}",
        f"- **Pre-specified disproof rule.** {disproof_statement}",
        "- **Agreement is not accuracy.** These rates measure exact label match "
        "between the AI and one human reference. The human labels are an "
        "independent reference of unknown correctness, not ground truth, and no "
        "original dataset labels were consulted.",
        "- **Scope.** This is one sample of 200 texts under one frozen codebook "
        "and one classifier configuration. The analysis is associational; it "
        "does not identify a causal effect of topic on disagreement, and it does "
        "not generalise beyond this sample and setup without further evidence.",
        "",
        "## Descriptive per-category rates",
        "",
        "| Human category | In comparison | n | Disagreements | Disagreement rate "
        "| 95% Wilson interval |",
        "| -------------- | ------------- | - | ------------- | ----------------- "
        "| ------------------- |",
    ]
    for row in cat_rows:
        if row["n"] == 0:
            continue
        in_comp = "yes" if row["in_primary_comparison"] else "no (descriptive)"
        lines.append(
            f"| {row['human_label']} — {row['human_category']} | {in_comp} | "
            f"{row['n']} | {row['disagreements']} | "
            f"{fmt_pct(row['disagreement_rate'], 1)} | "
            f"{fmt_pct(row['wilson_low'], 1)} to {fmt_pct(row['wilson_high'], 1)} |"
        )
    lines += [
        "",
        "The per-category rows are descriptive and are not used to test separate",
        "hypotheses; splitting the data reduces the precision of each estimate.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    log("")
    log(f"files written: {GROUP_CSV.relative_to(PROJECT)}; "
        f"{CATEGORY_CSV.relative_to(PROJECT)}; {SUMMARY_JSON.relative_to(PROJECT)}; "
        f"{REPORT.relative_to(PROJECT)}; {RUN_LOG.relative_to(PROJECT)}")
    log.save(RUN_LOG)


if __name__ == "__main__":
    main()
