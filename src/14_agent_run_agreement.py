"""Agent run, step 2: overall agreement and 4x4 confusion matrix.

Reads the verified analysis dataset produced by
src/13_agent_run_verify_inputs.py and computes:
  - overall exact agreement (human vs AI) with a 95% Wilson score interval
    without continuity correction (descriptive uncertainty);
  - the 4x4 confusion matrix (rows = human label, columns = AI label), counts
    and row percentages;
  - descriptive per-human-category agreement and an uncertain-annotation
    subset (secondary only; uncertain items stay in the primary analysis).

Outputs (results/agent_run/):
  confusion_matrix_counts.csv
  confusion_matrix_row_pct.csv
  agreement_summary.json
  agreement_report.md
  14_run_log.txt

Run: uv run src/14_agent_run_agreement.py
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
COUNTS_CSV = OUTDIR / "confusion_matrix_counts.csv"
PCT_CSV = OUTDIR / "confusion_matrix_row_pct.csv"
SUMMARY_JSON = OUTDIR / "agreement_summary.json"
REPORT = OUTDIR / "agreement_report.md"
RUN_LOG = OUTDIR / "14_run_log.txt"

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


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{100.0 * x:.{digits}f}%"


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not DATASET.exists():
        print(f"STOP: missing {DATASET}; run src/13_agent_run_verify_inputs.py first")
        sys.exit(1)

    log("AGENT RUN STEP 14 — overall agreement and confusion matrix")
    log(f"run_utc: {datetime.now(timezone.utc).isoformat()}")
    log(f"random seed fixed at {SEED} (no stochastic step)")
    log(f"input: {DATASET.relative_to(PROJECT)}")

    df = pd.read_csv(DATASET, encoding="utf-8")
    log(f"row count on read: {len(df)}")
    log("no filter, merge or drop applied in this script")

    required = {"item_id", "human_label", "ai_label", "human_confidence",
                "disagreement", "human_category", "ai_category"}
    if not required.issubset(df.columns):
        print(f"STOP: dataset lacks required columns: {sorted(required - set(df.columns))}")
        sys.exit(1)
    if len(df) != 200 or not df["item_id"].is_unique:
        print("STOP: expected 200 unique item_id rows in the analysis dataset")
        sys.exit(1)
    if not df["human_label"].isin([0, 1, 2, 3]).all():
        print("STOP: invalid human_label value")
        sys.exit(1)
    if not df["ai_label"].isin([0, 1, 2, 3]).all():
        print("STOP: invalid ai_label value")
        sys.exit(1)
    if ((df["human_label"] != df["ai_label"]).astype(int)
            != df["disagreement"]).any():
        print("STOP: disagreement column inconsistent with the two labels")
        sys.exit(1)

    n = len(df)
    n_agree = int((df["human_label"] == df["ai_label"]).sum())
    n_disagree = n - n_agree
    p_agree = n_agree / n
    agree_lo, agree_hi = wilson(n_agree, n)
    log(f"agreements: {n_agree}/{n}; disagreements: {n_disagree}/{n}; "
        f"agreement rate: {p_agree:.6f}")

    # ------------------------------------------------------ confusion matrix
    rows = list(range(4))
    names = [CATEGORY[i] for i in rows]
    matrix = np.zeros((4, 4), dtype=int)
    for h in rows:
        for a in rows:
            matrix[h, a] = int(((df["human_label"] == h) & (df["ai_label"] == a)).sum())

    row_totals = matrix.sum(axis=1)
    col_totals = matrix.sum(axis=0)
    if int(matrix.sum()) != n:
        print("STOP: confusion matrix does not sum to the dataset size")
        sys.exit(1)
    if not np.array_equal(row_totals, df["human_label"].value_counts().reindex(rows, fill_value=0).to_numpy()):
        print("STOP: matrix row totals do not match human-label counts")
        sys.exit(1)

    counts_df = pd.DataFrame(matrix, index=rows, columns=[f"ai_{i}" for i in rows])
    counts_df.insert(0, "human_category", names)
    counts_df["total_human"] = row_totals
    counts_df["disagreements"] = row_totals - np.diag(matrix)
    counts_df.index.name = "human_label"
    counts_out = counts_df.reset_index()
    counts_out.to_csv(COUNTS_CSV, index=False, encoding="utf-8")

    with np.errstate(divide="ignore", invalid="ignore"):
        pct = np.where(row_totals[:, None] > 0,
                       matrix / row_totals[:, None] * 100.0,
                       np.nan)
    pct_df = pd.DataFrame(pct, index=rows, columns=[f"ai_{i}" for i in rows])
    pct_df.insert(0, "human_category", names)
    pct_df["total_human"] = row_totals
    pct_df.index.name = "human_label"
    pct_out = pct_df.reset_index()
    pct_out.to_csv(PCT_CSV, index=False, encoding="utf-8")

    log("confusion matrix (rows = human, columns = AI):")
    header = "human \\ AI  " + "  ".join(f"{CATEGORY[i]:>8}" for i in rows) + "   total"
    log("  " + header)
    for i in rows:
        log("  " + f"{CATEGORY[i]:>10}  " +
            "  ".join(f"{matrix[i, j]:>8d}" for j in range(4)) +
            f"   {row_totals[i]:>5d}")
    log("  " + f"{'AI total':>10}  " +
        "  ".join(f"{col_totals[j]:>8d}" for j in range(4)) + f"   {n:>5d}")

    # -------------------------------------------------- per-category descriptives
    per_category = {}
    for i in rows:
        subset = df[df["human_label"] == i]
        k = int((subset["human_label"] == subset["ai_label"]).sum())
        m = len(subset)
        lo, hi = wilson(k, m) if m > 0 else (float("nan"), float("nan"))
        per_category[str(i)] = {
            "category": CATEGORY[i],
            "n_human": m,
            "agreements": k,
            "disagreements": m - k,
            "agreement_rate": (k / m) if m > 0 else None,
            "agreement_wilson_95": [lo, hi] if m > 0 else None,
        }
        log(f"  human {i} ({CATEGORY[i]}): n={m}; agreements={k}; "
            f"rate={k / m:.6f}" if m > 0 else f"  human {i}: n=0")

    # ------------------------------------------------------ uncertainty subset
    subsets = {}
    for conf in ("confident", "uncertain"):
        subset = df[df["human_confidence"] == conf]
        k = int((subset["human_label"] == subset["ai_label"]).sum())
        m = len(subset)
        lo, hi = wilson(k, m) if m > 0 else (float("nan"), float("nan"))
        subsets[conf] = {
            "n": m,
            "agreements": k,
            "disagreements": m - k,
            "agreement_rate": (k / m) if m > 0 else None,
            "agreement_wilson_95": [lo, hi] if m > 0 else None,
        }
        log(f"  human_confidence={conf}: n={m}; agreements={k}; "
            f"disagreement rate={(m - k) / m:.6f}" if m > 0 else
            f"  human_confidence={conf}: n=0")

    summary = {
        "script": "src/14_agent_run_agreement.py",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(DATASET.relative_to(PROJECT)),
        "n_items": n,
        "agreements": n_agree,
        "disagreements": n_disagree,
        "agreement_rate": p_agree,
        "agreement_wilson_95": [agree_lo, agree_hi],
        "confidence_level": 0.95,
        "wilson_continuity_correction": False,
        "z_95": Z95,
        "confusion_matrix_rows": "human_label",
        "confusion_matrix_columns": "ai_label",
        "category_order": {str(i): CATEGORY[i] for i in rows},
        "confusion_matrix_counts": matrix.tolist(),
        "confusion_matrix_row_totals": row_totals.tolist(),
        "confusion_matrix_col_totals": col_totals.tolist(),
        "per_human_category": per_category,
        "human_confidence_subsets": subsets,
        "primary_analysis_includes_uncertain": True,
        "note": "Uncertain human annotations remain in the primary analysis; "
                "the confident/uncertain split is descriptive and secondary.",
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------- report
    lines = [
        "# Overall agreement and confusion matrix — agent run",
        "",
        "- Script: `src/14_agent_run_agreement.py`",
        f"- Run (UTC): {summary['run_utc']}",
        f"- Input: `{summary['input']}` (produced by `src/13_agent_run_verify_inputs.py`)",
        f"- Items: {n}",
        "- Primary analysis keeps all items, including uncertain human annotations.",
        "",
        "## Overall agreement",
        "",
        f"- Agreements: {n_agree} of {n}",
        f"- Disagreements: {n_disagree} of {n}",
        f"- Exact agreement: {fmt_pct(p_agree, 2)} "
        f"(95% Wilson interval {fmt_pct(agree_lo, 2)} to {fmt_pct(agree_hi, 2)}; "
        "no continuity correction)",
        "",
        "Agreement here means exact label match between the human reference and",
        "the AI output. It is not accuracy: the human labels are an independent",
        "reference of unknown correctness, not ground truth.",
        "",
        "## Confusion matrix (counts)",
        "",
        "Rows are the human label; columns are the AI label.",
        "",
        "| Human \\ AI | " + " | ".join(names) + " | Total | Disagreements |",
        "| ---------- | " + " | ".join("---" for _ in rows) + " | --- | --- |",
    ]
    for i in rows:
        lines.append(
            f"| {i} — {CATEGORY[i]} | " +
            " | ".join(str(int(matrix[i, j])) for j in range(4)) +
            f" | {int(row_totals[i])} | {int(row_totals[i] - matrix[i, i])} |"
        )
    lines.append(
        "| **AI total** | " + " | ".join(str(int(col_totals[j])) for j in range(4)) +
        f" | **{n}** | **{n_disagree}** |"
    )

    lines += [
        "",
        "Cell values are counts. The full machine-readable matrix, including",
        "row-normalised percentages, is in `results/agent_run/confusion_matrix_counts.csv`",
        "and `results/agent_run/confusion_matrix_row_pct.csv`.",
        "",
        "## Row-normalised confusion matrix (row percentages)",
        "",
        "| Human \\ AI | " + " | ".join(names) + " | Row total |",
        "| ---------- | " + " | ".join("---" for _ in rows) + " | --- |",
    ]
    for i in rows:
        lines.append(
            f"| {i} — {CATEGORY[i]} | " +
            " | ".join(f"{pct[i, j]:.1f}%" for j in range(4)) +
            f" | {int(row_totals[i])} |"
        )

    lines += [
        "",
        "## Descriptive agreement by human category",
        "",
        "| Human category | n | Agreements | Disagreements | Agreement rate |",
        "| -------------- | - | ---------- | ------------- | -------------- |",
    ]
    for i in rows:
        c = per_category[str(i)]
        lines.append(
            f"| {i} — {c['category']} | {c['n_human']} | {c['agreements']} | "
            f"{c['disagreements']} | {fmt_pct(c['agreement_rate'], 1)} |"
        )

    lines += [
        "",
        "## Uncertainty subset (secondary, descriptive)",
        "",
        "| Human confidence | n | Agreements | Disagreements | Agreement rate |",
        "| ---------------- | - | ---------- | ------------- | -------------- |",
    ]
    for conf in ("confident", "uncertain"):
        s = subsets[conf]
        lines.append(
            f"| {conf} | {s['n']} | {s['agreements']} | {s['disagreements']} | "
            f"{fmt_pct(s['agreement_rate'], 1)} |"
        )
    lines += [
        "",
        "The uncertain subset is shown only to make its influence visible. It does",
        "not replace the primary analysis, which includes all items as required by",
        "the frozen codebook (Part B) and the analysis plan.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    log("")
    log(f"files written: {COUNTS_CSV.relative_to(PROJECT)}; "
        f"{PCT_CSV.relative_to(PROJECT)}; {SUMMARY_JSON.relative_to(PROJECT)}; "
        f"{REPORT.relative_to(PROJECT)}; {RUN_LOG.relative_to(PROJECT)}")
    log.save(RUN_LOG)


if __name__ == "__main__":
    main()
