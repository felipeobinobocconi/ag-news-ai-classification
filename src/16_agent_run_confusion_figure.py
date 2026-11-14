"""Agent run, step 4: confusion-matrix figure.

Builds a clearly labelled two-panel figure from the saved confusion matrix:
left panel = counts, right panel = row-normalised percentages. Rows are the
human (manual) label; columns are the AI label.

Outputs (results/agent_run/):
  confusion_matrix.png
  confusion_matrix.pdf
  confusion_matrix_caption.md
  16_run_log.txt

Run: uv run src/16_agent_run_confusion_figure.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Fixed seed although this script has no stochastic step (AGENTS.md rule 5).
SEED = 42
np.random.seed(SEED)

PROJECT = Path(__file__).resolve().parents[1]
OUTDIR = PROJECT / "results" / "agent_run"
COUNTS_CSV = OUTDIR / "confusion_matrix_counts.csv"
PCT_CSV = OUTDIR / "confusion_matrix_row_pct.csv"
PNG = OUTDIR / "confusion_matrix.png"
PDF = OUTDIR / "confusion_matrix.pdf"
CAPTION = OUTDIR / "confusion_matrix_caption.md"
RUN_LOG = OUTDIR / "16_run_log.txt"

CATEGORY = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
AI_NAMES = [f"ai_{i}" for i in range(4)]


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str = "") -> None:
        print(message)
        self.lines.append(str(message))

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


log = Log()


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for p in (COUNTS_CSV, PCT_CSV):
        if not p.exists():
            print(f"STOP: missing {p}; run src/14_agent_run_agreement.py first")
            sys.exit(1)

    log("AGENT RUN STEP 16 — confusion-matrix figure")
    log(f"run_utc: {datetime.now(timezone.utc).isoformat()}")
    log(f"random seed fixed at {SEED} (no stochastic step)")

    counts_df = pd.read_csv(COUNTS_CSV, encoding="utf-8").sort_values("human_label")
    pct_df = pd.read_csv(PCT_CSV, encoding="utf-8").sort_values("human_label")
    if list(counts_df["human_label"]) != [0, 1, 2, 3]:
        print("STOP: counts table does not contain human labels 0-3 in order")
        sys.exit(1)
    if list(pct_df["human_label"]) != [0, 1, 2, 3]:
        print("STOP: percentage table does not contain human labels 0-3 in order")
        sys.exit(1)

    counts = counts_df[AI_NAMES].to_numpy(dtype=int)
    pct = pct_df[AI_NAMES].to_numpy(dtype=float)
    n_total = int(counts.sum())
    row_totals = counts.sum(axis=1)
    if n_total != 200:
        print(f"STOP: matrix sums to {n_total}, expected 200")
        sys.exit(1)
    if not np.allclose(row_totals[:, None] * np.nan_to_num(pct) / 100.0,
                       counts, atol=1e-9):
        print("STOP: count and percentage tables are inconsistent")
        sys.exit(1)

    tick_labels = [f"{i} — {CATEGORY[i]}" for i in range(4)]
    xlabel = "AI label (gemini-3.5-flash-lite)"
    ylabel = "Human label (manual reference)"

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.9), constrained_layout=True)

    def draw(ax, data, title, colorbar_label, value_fmt, threshold):
        vmax = float(np.nanmax(data)) if np.nanmax(data) > 0 else 1.0
        im = ax.imshow(data, cmap="Blues", vmin=0.0, vmax=vmax, aspect="equal")
        ax.set_xticks(range(4), tick_labels, rotation=20, ha="right")
        ax.set_yticks(range(4), tick_labels)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=12, fontweight="bold")
        for i in range(4):
            for j in range(4):
                value = data[i, j]
                colour = "white" if value > threshold * vmax else "black"
                ax.text(j, i, value_fmt(value), ha="center", va="center",
                        fontsize=12, color=colour)
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(colorbar_label)
        ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 4, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.2)
        ax.tick_params(which="minor", length=0)

    draw(axes[0], counts, "(a) Counts", "Number of texts",
         lambda v: f"{int(v)}", 0.55)
    draw(axes[1], pct, "(b) Row percentages", "Row percentage (%)",
         lambda v: f"{v:.1f}%", 0.50)

    fig.suptitle(
        f"Confusion matrix: human vs AI topic labels (n = {n_total})",
        fontsize=14, fontweight="bold",
    )
    fig.text(
        0.5, -0.015,
        "Rows are the human (manual) label; columns are the AI label. "
        "Row percentages sum to 100% within each human category.",
        ha="center", va="top", fontsize=9.5, style="italic",
    )

    fig.savefig(PNG, dpi=300, bbox_inches="tight")
    fig.savefig(PDF, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log(f"figure written: {PNG.relative_to(PROJECT)} "
        f"({PNG.stat().st_size} bytes); {PDF.relative_to(PROJECT)}")
    log(f"panel values: total n={n_total}; row totals={row_totals.tolist()}")

    caption = f"""# Figure caption — confusion matrix

**Figure 1.** Confusion matrix of AI topic labels against the human (manual)
reference for the evaluation sample (n = {n_total}). Rows are the human label;
columns are the AI label (`gemini-3.5-flash-lite`). Panel (a) shows counts and
panel (b) shows row-normalised percentages within each human category. The
diagonal contains exact agreements; off-diagonal cells are disagreements.
Uncertain human annotations are included, as in the primary analysis.

- Source data: `results/agent_run/confusion_matrix_counts.csv` and
  `results/agent_run/confusion_matrix_row_pct.csv`
- Produced by: `src/16_agent_run_confusion_figure.py` (from tables generated by
  `src/14_agent_run_agreement.py`)
- Agreement is exact label match, not accuracy: the human labels are an
  independent reference of unknown correctness, not ground truth.
- Category codes: 0 = World, 1 = Sports, 2 = Business, 3 = Sci/Tech.
"""
    CAPTION.write_text(caption, encoding="utf-8")
    log(f"caption written: {CAPTION.relative_to(PROJECT)}")
    log.save(RUN_LOG)


if __name__ == "__main__":
    main()
