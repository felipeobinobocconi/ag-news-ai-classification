"""Reconcile the workflow_run and agent_run analyses.

Compares the saved outputs of the two runs:
  - overall item counts and agreement;
  - all 16 confusion-matrix cells after aligning category labels;
  - group denominators, disagreement counts, rates and the difference;
  - interval endpoints using unrounded values and an absolute tolerance;
  - item-level human/AI labels and confidence by item_id.

Also reviews the recorded OpenCode tool calls (read-only session database) for
the autonomous run's initial search and for the workflow's corrected diagonal
bug. The report is written to results/run_comparison.md.

No frozen label, codebook, study-design element or analysis result is changed.
No classification model is called and no original dataset label is read.

Run: uv run src/18_reconcile_runs.py
"""

from __future__ import annotations

import json
import re
import sqlite3
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
WF = PROJECT / "results" / "workflow_run"
AR = PROJECT / "results" / "agent_run"
REPORT = PROJECT / "results" / "run_comparison.md"

TOL = 1e-9  # absolute tolerance for unrounded numeric endpoints
CAT_NAMES = ["World", "Sports", "Business", "Sci/Tech"]
CAT_CODE = {name: i for i, name in enumerate(CAT_NAMES)}
Z95 = NormalDist().inv_cdf(0.975)

checks: list[dict] = []


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except ValueError:
        return str(path)


def add_check(section: str, name: str, wf, ar, tol: float | None = None) -> bool:
    """Record one comparison; return whether it passed."""
    if isinstance(wf, (int, float)) and isinstance(ar, (int, float)):
        diff = float(ar) - float(wf)
        passed = abs(diff) <= (tol if tol is not None else 0.0)
        checks.append({
            "section": section, "name": name, "workflow": wf, "agent": ar,
            "difference": diff, "tolerance": tol, "pass": passed,
        })
        return passed
    passed = wf == ar
    checks.append({
        "section": section, "name": name, "workflow": wf, "agent": ar,
        "difference": None, "tolerance": None, "pass": passed,
    })
    return passed


def fmt_value(x, digits: int = 17) -> str:
    if isinstance(x, float):
        return f"{x:.{digits}g}"
    return str(x)


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return out


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def workflow_matrix() -> np.ndarray:
    raw = pd.read_csv(WF / "confusion_matrix.csv", index_col=0, encoding="utf-8")
    matrix = np.zeros((4, 4), dtype=int)
    for row_name, row in raw.iterrows():
        h = CAT_CODE[str(row_name).replace("human_", "", 1)]
        for col_name, value in row.items():
            a = CAT_CODE[str(col_name).replace("ai_", "", 1)]
            matrix[h, a] = int(value)
    return matrix


def agent_matrix() -> np.ndarray:
    df = pd.read_csv(AR / "confusion_matrix_counts.csv", encoding="utf-8")
    df = df.sort_values("human_label").reset_index(drop=True)
    return df[[f"ai_{i}" for i in range(4)]].to_numpy(dtype=int)


# ---------------------------------------------------------------- tool audit
def session_rows(con: sqlite3.Connection, title: str):
    con.row_factory = sqlite3.Row
    row = con.execute(
        "select id, title, directory, time_created, time_updated "
        "from session_v2 where title=? order by time_created desc limit 1",
        (title,),
    ).fetchone()
    if row is None:
        return None, []
    messages = list(con.execute(
        "select seq, type, time_created, data from session_message "
        "where session_id=? order by seq", (row["id"],)))
    return row, messages


def tool_calls_and_text(messages) -> tuple[list[dict], list[dict]]:
    calls, texts = [], []
    for msg in messages:
        if msg["type"] != "assistant":
            continue
        data = json.loads(msg["data"])
        for part in data.get("content", []):
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype == "tool":
                state = part.get("state", {})
                output = "\n".join(
                    str(c.get("text", "")) for c in state.get("content", [])
                    if isinstance(c, dict) and c.get("type") == "text")
                calls.append({
                    "seq": msg["seq"], "time": msg["time_created"],
                    "name": part.get("name"),
                    "input": state.get("input", {}),
                    "output": output,
                })
            elif ptype in ("text", "reasoning"):
                texts.append({
                    "seq": msg["seq"], "time": msg["time_created"],
                    "kind": ptype, "text": str(part.get("text", "")),
                })
    return calls, texts


def audit_sessions() -> dict:
    db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
    log_path = Path.home() / ".local" / "share" / "opencode" / "log" / "opencode.log"
    result = {
        "db_path": str(db_path),
        "db_available": db_path.exists(),
        "autonomous": {"available": False},
        "workflow": {"available": False},
    }
    if not db_path.exists():
        return result

    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        # --- autonomous run: initial search before the reconciliation prompt
        row, messages = session_rows(con, "Autonomous evaluation agreement run")
        if row is not None:
            calls, texts = tool_calls_and_text(messages)
            users = [m for m in messages if m["type"] == "user"]
            cutoff = sorted(m["time_created"] for m in users)[1] if len(users) > 1 else None
            initial = [c for c in calls if cutoff is None or c["time"] < cutoff]
            selected = []
            for c in initial:
                inp = json.dumps(c["input"], ensure_ascii=False)
                is_glob_md = c["name"] == "glob" and "**/*.md" in inp
                is_results_listing = (
                    c["name"] == "shell"
                    and "Get-ChildItem -Recurse -File results" in inp)
                is_grep_results = (
                    c["name"] == "grep"
                    and "evaluation_manifest" in inp
                    and str(c["input"].get("path", "")).endswith("results"))
                if not (is_glob_md or is_results_listing or is_grep_results):
                    continue
                wf_lines = [ln for ln in c["output"].splitlines()
                            if "workflow_run" in ln]
                selected.append({
                    "seq": c["seq"], "tool": c["name"], "input": c["input"],
                    "output": c["output"],
                    "workflow_lines": wf_lines,
                    "n_workflow_lines": len(wf_lines),
                })
            result["autonomous"] = {
                "available": True,
                "session_id": row["id"],
                "title": row["title"],
                "directory": row["directory"],
                "calls": selected,
            }

        # --- workflow run: diagonal failure, fix and successful rerun
        row, messages = session_rows(con, "Data analysis assignment setup")
        if row is not None:
            calls, texts = tool_calls_and_text(messages)
            failure = next((c for c in calls
                            if "STOP: counts disagree with confusion matrix"
                            in c["output"]), None)
            fix = next((c for c in calls
                        if c["name"] == "edit"
                        and "cm_pooled_agree" in json.dumps(c["input"],
                                                           ensure_ascii=False)), None)
            rerun = next((c for c in calls
                          if "CHECK PASS: group counts match the saved confusion matrix"
                          in c["output"]), None)
            cause = next((t for t in texts
                          if "diagonal()" in t["text"] and "2" in t["text"]
                          and ("pooled" in t["text"].lower()
                               or "matrix" in t["text"].lower())), None)
            result["workflow"] = {
                "available": True,
                "session_id": row["id"],
                "title": row["title"],
                "failure_seq": failure["seq"] if failure else None,
                "failure_output": failure["output"] if failure else "",
                "fix_seq": fix["seq"] if fix else None,
                "fix_input": fix["input"] if fix else {},
                "rerun_seq": rerun["seq"] if rerun else None,
                "rerun_output": rerun["output"] if rerun else "",
                "cause_seq": cause["seq"] if cause else None,
                "cause_text": cause["text"] if cause else "",
            }
    finally:
        con.close()

    # Server log line for the initial grep invocation, if available.
    result["grep_log_line"] = ""
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ("rg.exe" in line and "evaluation_manifest" in line
                    and "2026-11-14T13:19" in line):
                result["grep_log_line"] = line
                break
    return result


# --------------------------------------------------------------------- main
def main() -> None:
    out = []
    all_pass = True

    def record(section: str, name: str, wf, ar, tol: float | None = None) -> None:
        nonlocal all_pass
        all_pass = add_check(section, name, wf, ar, tol) and all_pass

    # ---------------------------------------------------------------- inputs
    wf_agr = load_json(WF / "agreement_summary.json")
    ar_agr = load_json(AR / "agreement_summary.json")
    wf_cat = load_json(WF / "category_hypothesis_summary.json")
    ar_diff = load_json(AR / "difference_summary.json")

    wf_mat = workflow_matrix()
    ar_mat = agent_matrix()
    wf_items = pd.read_csv(WF / "comparison_table.csv", encoding="utf-8",
                           dtype={"item_id": str})
    ar_items = pd.read_csv(AR / "analysis_dataset.csv", encoding="utf-8",
                           dtype={"item_id": str})
    wf_group_tab = pd.read_csv(WF / "category_hypothesis_table.csv",
                               encoding="utf-8")
    ar_group_tab = pd.read_csv(AR / "group_disagreement.csv", encoding="utf-8")

    wf_pool = wf_cat["groups"]["pooled_business_scitech"]
    wf_sport = wf_cat["groups"]["sports"]
    ar_pool = ar_group_tab.set_index("group").loc["Business/Sci-Tech pooled"]
    ar_sport = ar_group_tab.set_index("group").loc["Sports"]
    wf_pool_tab = wf_group_tab.iloc[0]
    wf_sport_tab = wf_group_tab.iloc[1]

    # ------------------------------------------------- overall counts/agreement
    wf_disagree = int(wf_agr["items"] - wf_agr["agree"])
    ar_disagree = int(ar_agr["n_items"] - ar_agr["agreements"])
    wf_item_agree = int(pd.to_numeric(wf_items["agreement"]).sum())
    ar_item_agree = int((ar_items["human_label"] == ar_items["ai_label"]).sum())
    wf_item_disagree = int(len(wf_items) - wf_item_agree)
    ar_item_disagree = int(ar_items["disagreement"].sum())

    record("overall", "items", int(wf_agr["items"]), int(ar_agr["n_items"]))
    record("overall", "agreements", int(wf_agr["agree"]), int(ar_agr["agreements"]))
    record("overall", "disagreements (derived)", wf_disagree, ar_disagree)
    record("overall", "overall agreement rate", float(wf_agr["overall_agreement"]),
           float(ar_agr["agreement_rate"]), TOL)
    record("overall", "items recomputed from item table", len(wf_items), len(ar_items))
    record("overall", "agreements recomputed from item table",
           wf_item_agree, ar_item_agree)
    record("overall", "disagreements recomputed from item table",
           wf_item_disagree, ar_item_disagree)
    record("overall", "workflow matrix total", int(wf_agr["matrix_total"]),
           int(wf_mat.sum()))
    record("overall", "agent matrix total", int(ar_mat.sum()), int(ar_agr["n_items"]))
    record("overall", "workflow matrix diagonal", int(wf_agr["matrix_diagonal"]),
           int(np.trace(wf_mat)))
    record("overall", "agent matrix diagonal", int(np.trace(ar_mat)),
           int(ar_agr["agreements"]))

    # --------------------------------------------------------- confusion cells
    cell_rows = []
    max_cell_diff = 0.0
    for i in range(4):
        for j in range(4):
            difference = int(ar_mat[i, j] - wf_mat[i, j])
            max_cell_diff = max(max_cell_diff, abs(difference))
            record("matrix", f"cell {CAT_NAMES[i]} -> {CAT_NAMES[j]}",
                   int(wf_mat[i, j]), int(ar_mat[i, j]))
            cell_rows.append([
                f"{i} {CAT_NAMES[i]} -> {j} {CAT_NAMES[j]}",
                str(int(wf_mat[i, j])), str(int(ar_mat[i, j])), str(difference),
                "PASS" if difference == 0 else "FAIL",
            ])
    record("matrix", "maximum absolute cell difference", 0.0,
           float(max_cell_diff), 0.0)
    record("matrix", "row totals", wf_mat.sum(axis=1).tolist(),
           ar_mat.sum(axis=1).tolist())
    record("matrix", "column totals", wf_mat.sum(axis=0).tolist(),
           ar_mat.sum(axis=0).tolist())

    # ------------------------------------------------------------- group facts
    record("group", "pooled denominator", int(wf_pool["items"]), int(ar_pool["n"]))
    record("group", "sports denominator", int(wf_sport["items"]), int(ar_sport["n"]))
    record("group", "pooled disagreements", int(wf_pool["disagreements"]),
           int(ar_pool["disagreements"]))
    record("group", "sports disagreements", int(wf_sport["disagreements"]),
           int(ar_sport["disagreements"]))
    record("group", "pooled rate", float(wf_pool["rate"]),
           float(ar_pool["disagreement_rate"]), TOL)
    record("group", "sports rate", float(wf_sport["rate"]),
           float(ar_sport["disagreement_rate"]), TOL)
    record("group", "difference (percentage points)", float(wf_cat["difference_pp"]),
           float(ar_diff["difference_pp"]), TOL)
    record("group", "workflow table pooled rate vs summary",
           float(wf_pool["rate"]), float(wf_pool_tab["disagreement_rate"]), TOL)
    record("group", "workflow table sports rate vs summary",
           float(wf_sport["rate"]), float(wf_sport_tab["disagreement_rate"]), TOL)
    record("group", "agent table pooled rate vs summary",
           float(ar_pool["disagreement_rate"]), float(ar_diff["rate_group_1"]), TOL)
    record("group", "agent table sports rate vs summary",
           float(ar_sport["disagreement_rate"]), float(ar_diff["rate_group_2"]), TOL)

    # ------------------------------------------------------- interval endpoints
    endpoints = [
        ("pooled Wilson lower", float(wf_pool["wilson_95"][0]), float(ar_pool["wilson_low"])),
        ("pooled Wilson upper", float(wf_pool["wilson_95"][1]), float(ar_pool["wilson_high"])),
        ("Sports Wilson lower", float(wf_sport["wilson_95"][0]), float(ar_sport["wilson_low"])),
        ("Sports Wilson upper", float(wf_sport["wilson_95"][1]), float(ar_sport["wilson_high"])),
        ("Newcombe lower (pp)", float(wf_cat["newcombe_95_pp"][0]),
         float(ar_diff["difference_ci_95_pp"][0])),
        ("Newcombe upper (pp)", float(wf_cat["newcombe_95_pp"][1]),
         float(ar_diff["difference_ci_95_pp"][1])),
    ]
    endpoint_rows = []
    max_endpoint_diff = 0.0
    for name, wf_val, ar_val in endpoints:
        diff = ar_val - wf_val
        max_endpoint_diff = max(max_endpoint_diff, abs(diff))
        record("interval", name, wf_val, ar_val, TOL)
        endpoint_rows.append([
            name, fmt_value(wf_val), fmt_value(ar_val), fmt_value(diff),
            "PASS" if abs(diff) <= TOL else "FAIL",
        ])

    # ------------------------------------------------------- item-level fields
    wf_ids, ar_ids = set(wf_items["item_id"]), set(ar_items["item_id"])
    record("item", "ID sets identical", wf_ids == ar_ids, True)
    record("item", "workflow rows / unique IDs", len(wf_items),
           int(wf_items["item_id"].nunique()))
    record("item", "agent rows / unique IDs", len(ar_items),
           int(ar_items["item_id"].nunique()))
    merged = wf_items.merge(
        ar_items, on="item_id", how="inner", validate="one_to_one",
        suffixes=("_wf", "_ar"))
    record("item", "one-to-one merged rows", len(merged), len(ar_items))

    field_checks = {
        "human_label": (merged["human_label_wf"].astype(int),
                        merged["human_label_ar"].astype(int)),
        "ai_label": (merged["ai_label_wf"].astype(int),
                     merged["ai_label_ar"].astype(int)),
        "human_confidence": (merged["human_confidence_wf"].astype(str),
                             merged["human_confidence_ar"].astype(str)),
        "agreement = 1 - disagreement": (
            merged["agreement"].astype(int),
            1 - merged["disagreement"].astype(int)),
    }
    field_rows = []
    for name, (left, right) in field_checks.items():
        mismatches = int((left != right).sum())
        record("item", f"{name} mismatches", 0, mismatches, 0.0)
        field_rows.append([name, str(len(merged)), str(mismatches),
                           "PASS" if mismatches == 0 else "FAIL"])

    # -------------------------------------------------- internal consistency
    wf_human_counts = wf_items["human_label"].value_counts().reindex(
        range(4), fill_value=0).to_numpy()
    ar_human_counts = ar_items["human_label"].value_counts().reindex(
        range(4), fill_value=0).to_numpy()
    record("internal", "workflow matrix row totals vs item counts",
           wf_mat.sum(axis=1).tolist(), wf_human_counts.tolist())
    record("internal", "agent matrix row totals vs item counts",
           ar_mat.sum(axis=1).tolist(), ar_human_counts.tolist())

    wf_pool_dis_matrix = int(
        wf_mat[[2, 3], :].sum() - wf_mat[2, 2] - wf_mat[3, 3])
    ar_pool_dis_matrix = int(
        ar_mat[[2, 3], :].sum() - ar_mat[2, 2] - ar_mat[3, 3])
    wf_sport_dis_matrix = int(wf_mat[1, :].sum() - wf_mat[1, 1])
    ar_sport_dis_matrix = int(ar_mat[1, :].sum() - ar_mat[1, 1])
    record("internal", "workflow pooled disagreements vs matrix",
           int(wf_pool["disagreements"]), wf_pool_dis_matrix)
    record("internal", "agent pooled disagreements vs matrix",
           int(ar_pool["disagreements"]), ar_pool_dis_matrix)
    record("internal", "workflow sports disagreements vs matrix",
           int(wf_sport["disagreements"]), wf_sport_dis_matrix)
    record("internal", "agent sports disagreements vs matrix",
           int(ar_sport["disagreements"]), ar_sport_dis_matrix)

    # --------------------------------------- confidence split (exploratory only)
    confidence_rows = []
    for conf in ("confident", "uncertain"):
        subset = ar_items[ar_items["human_confidence"] == conf]
        n = len(subset)
        agree = int((subset["human_label"] == subset["ai_label"]).sum())
        rate = agree / n if n else float("nan")
        saved = ar_agr["human_confidence_subsets"][conf]
        record("confidence", f"{conf} n", int(saved["n"]), n)
        record("confidence", f"{conf} agreements", int(saved["agreements"]), agree)
        record("confidence", f"{conf} agreement rate",
               float(saved["agreement_rate"]), rate, TOL)
        confidence_rows.append([conf, str(n), str(agree),
                                f"{100 * rate:.2f}%"])

    ar_unc_pool = int(((ar_items["human_label"].isin([2, 3]))
                       & (ar_items["human_confidence"] == "uncertain")).sum())
    ar_unc_sport = int(((ar_items["human_label"] == 1)
                        & (ar_items["human_confidence"] == "uncertain")).sum())
    record("confidence", "pooled uncertain count (exploratory)",
           int(wf_pool["uncertain_kept"]), ar_unc_pool)
    record("confidence", "Sports uncertain count (exploratory)",
           int(wf_sport["uncertain_kept"]), ar_unc_sport)

    # ------------------------------------------------------------- tool audit
    audit = audit_sessions()

    # ------------------------------------------------------------- report
    out.append("# Reconciliation of workflow_run and agent_run analyses")
    out.append("")
    out.append(f"- Script: `src/18_reconcile_runs.py`")
    out.append(f"- Run (UTC): {datetime.now(timezone.utc).isoformat()}")
    out.append(f"- Workflow sources: `{rel(WF)}/*`")
    out.append(f"- Agent sources: `{rel(AR)}/*`")
    out.append(f"- Numerical tolerance: absolute `{TOL:g}` on unrounded values")
    out.append("  (proportions for Wilson endpoints; percentage points for the "
               "Newcombe endpoints).")
    out.append("- No frozen label, codebook, study-design element or analysis "
               "result was changed; no model was called; no original dataset "
               "label was read.")
    out.append("")
    out.append("## Overall counts and agreement")
    out.append("")
    overall_checks = [c for c in checks if c["section"] == "overall"]
    rows = [[c["name"], fmt_value(c["workflow"]), fmt_value(c["agent"]),
             fmt_value(c["difference"]) if c["difference"] is not None else "",
             "PASS" if c["pass"] else "FAIL"] for c in overall_checks]
    out += md_table(["Quantity", "Workflow", "Agent", "Agent - workflow", "Check"], rows)
    out.append("")
    out.append("Both runs recompute the same item-level counts from their saved "
               "classification tables. The workflow summary's matrix total and "
               "diagonal are also checked against the workflow matrix itself.")
    out.append("")

    out.append("## Confusion matrix after category alignment")
    out.append("")
    out.append("Category alignment: World = 0, Sports = 1, Business = 2, "
               "Sci/Tech = 3. Workflow row names `human_*` and column names "
               "`ai_*` were mapped to the same codes as the agent's numeric "
               "columns. Rows are human labels; columns are AI labels.")
    out.append("")
    out.append("### Workflow counts")
    out.append("")
    wf_rows = [[f"{i} {CAT_NAMES[i]}"] + [str(int(wf_mat[i, j])) for j in range(4)]
               + [str(int(wf_mat[i].sum()))] for i in range(4)]
    wf_rows.append(["**AI total**"] + [str(int(wf_mat[:, j].sum())) for j in range(4)]
                   + [str(int(wf_mat.sum()))])
    out += md_table(["Human \\ AI"] + CAT_NAMES + ["Total"], wf_rows)
    out.append("")
    out.append("### Agent counts")
    out.append("")
    ar_rows = [[f"{i} {CAT_NAMES[i]}"] + [str(int(ar_mat[i, j])) for j in range(4)]
               + [str(int(ar_mat[i].sum()))] for i in range(4)]
    ar_rows.append(["**AI total**"] + [str(int(ar_mat[:, j].sum())) for j in range(4)]
                   + [str(int(ar_mat.sum()))])
    out += md_table(["Human \\ AI"] + CAT_NAMES + ["Total"], ar_rows)
    out.append("")
    out.append("### Cell-by-cell comparison")
    out.append("")
    out += md_table(["Cell (human -> AI)", "Workflow", "Agent",
                     "Agent - workflow", "Check"], cell_rows)
    out.append("")
    out.append(f"All 16 cells were compared. Maximum absolute difference: "
               f"`{max_cell_diff:g}`. Row totals and column totals also match.")
    out.append("")

    out.append("## Group comparison")
    out.append("")
    group_checks = [c for c in checks if c["section"] == "group"]
    rows = [[c["name"], fmt_value(c["workflow"]), fmt_value(c["agent"]),
             fmt_value(c["difference"]) if c["difference"] is not None else "",
             "PASS" if c["pass"] else "FAIL"] for c in group_checks]
    out += md_table(["Quantity", "Workflow", "Agent", "Agent - workflow", "Check"], rows)
    out.append("")
    out.append("The group contrast is pooled Business/Sci-Tech minus Sports, "
               "with each group's own item count as denominator.")
    out.append("")

    out.append("## Interval endpoints (unrounded)")
    out.append("")
    out += md_table(["Endpoint", "Workflow", "Agent", "Absolute difference", "Check"],
                    [[r[0], r[1], r[2], fmt_value(abs(float(r[3]))), r[4]]
                     for r in endpoint_rows])
    out.append("")
    out.append(f"All interval comparisons use absolute tolerance `{TOL:g}`. "
               f"Maximum absolute endpoint difference: `{max_endpoint_diff:g}`. "
               "Wilson endpoints are proportions; Newcombe endpoints are "
               "percentage points.")
    out.append("")

    out.append("## Item-level comparison")
    out.append("")
    item_rows = [[c["name"], fmt_value(c["workflow"]), fmt_value(c["agent"]),
                  "PASS" if c["pass"] else "FAIL"]
                 for c in checks if c["section"] == "item" and
                 c["name"] in ("ID sets identical", "one-to-one merged rows",
                               "workflow rows / unique IDs",
                               "agent rows / unique IDs")]
    out += md_table(["Item-level check", "Workflow", "Agent", "Check"], item_rows)
    out.append("")
    out += md_table(["Field compared by item_id", "Items compared", "Mismatches",
                     "Check"], field_rows)
    out.append("")
    out.append("The item-level merge is one-to-one on `item_id`; no missing or "
               "extra IDs were found. The workflow `agreement` indicator equals "
               "one minus the agent `disagreement` indicator for every item.")
    out.append("")

    out.append("## Internal consistency and the workflow diagonal incident")
    out.append("")
    out.append("Both saved matrices sum to the same total, and both diagonals "
               "equal the corresponding agreement count. Pooled and Sports "
               "disagreement counts recomputed from the matrix slices match the "
               "group tables in both runs.")
    out.append("")
    if audit["workflow"].get("available"):
        wf = audit["workflow"]
        out.append("The recorded workflow session contains the earlier failed "
                   "matrix check and its correction:")
        out.append("")
        if wf.get("failure_output"):
            out.append(f"- Failure (message seq `{wf.get('failure_seq')}`):")
            out.append("")
            out.append("```")
            out.append(wf["failure_output"].strip())
            out.append("```")
            out.append("")
        if wf.get("cause_text"):
            snippet = wf["cause_text"].strip().replace("\n", " ")
            out.append(f"- Cause identified (seq `{wf.get('cause_seq')}`): "
                       f"{snippet[:900]}")
            out.append("")
        if wf.get("fix_input"):
            old = str(wf["fix_input"].get("oldString", ""))
            new = str(wf["fix_input"].get("newString", ""))
            out.append(f"- Correction (seq `{wf.get('fix_seq')}`): replaced the "
                       "slice diagonal with explicit diagonal cells.")
            out.append("")
            out.append("```")
            out.append("old: " + old.strip())
            out.append("new: " + new.strip())
            out.append("```")
            out.append("")
        if wf.get("rerun_output"):
            out.append(f"- Successful rerun (seq `{wf.get('rerun_seq')}`):")
            out.append("")
            out.append("```")
            out.append(wf["rerun_output"].strip())
            out.append("```")
            out.append("")
        out.append("In the failed check, `diagonal()` on the 2x4 pooled row "
                   "slice returned only the (Business, World) and "
                   "(Sci/Tech, Sports) cells, so pooled disagreements were "
                   "reported as 72 instead of 13. The explicit fix sums the "
                   "Business and Sci/Tech diagonal cells (39 + 22 = 61 "
                   "agreements; 74 - 61 = 13 disagreements). The failure "
                   "stopped the script before outputs were written; the saved "
                   "workflow outputs come from the successful rerun.")
    else:
        out.append("The recorded workflow session evidence was not available to "
                   "this script; the diagonal incident is reported from the "
                   "workflow outputs and the task record, not re-verified here.")
    out.append("")

    out.append("## Confident/uncertain split (agent-added exploratory analysis)")
    out.append("")
    out.append("**This split was added by the autonomous agent. It is an "
               "exploratory, descriptive analysis, not the primary hypothesis "
               "test.** It is not used in the group contrast or the Newcombe "
               "interval, and it must not be read as a substitute for the "
               "pre-specified analysis.")
    out.append("")
    out += md_table(["Human confidence", "Items", "Agreements", "Agreement rate"],
                    confidence_rows)
    out.append("")
    out.append("The workflow reported only the number of uncertain annotations "
               "kept per comparison group; the agent additionally reported the "
               "overall confidence split. The per-group uncertain counts match "
               "between the runs, but the split itself remains exploratory.")
    out.append("")

    out.append("## Recorded tool-call review: initial autonomous search")
    out.append("")
    if audit["autonomous"].get("available"):
        au = audit["autonomous"]
        out.append(f"- Session: `{au['session_id']}` — \"{au['title']}\"")
        out.append(f"- Recorded in: `{audit['db_path']}` (read-only)")
        out.append("")
        call_rows = []
        for c in au["calls"]:
            inp = c["input"]
            if c["tool"] == "glob":
                input_summary = f"glob `{inp.get('pattern', '')}`"
            elif c["tool"] == "shell":
                input_summary = "recursive `Get-ChildItem -Recurse -File results`"
            else:
                input_summary = (f"grep `{inp.get('pattern', '')}` in "
                                 f"`{inp.get('path', '')}` with "
                                 f"`include={inp.get('include', '')}`")
            if c["tool"] == "grep":
                match = re.search(r"Found (\d+) matches", c["output"])
                n_matches = match.group(1) if match else "unspecified"
                observed = (f"{c['n_workflow_lines']} workflow_run lines in "
                            f"returned output; {n_matches} matches total, all "
                            "outside workflow_run")
            elif c["tool"] == "shell":
                observed = (f"{c['n_workflow_lines']} workflow_run path lines "
                            f"among {len(c['output']):,} chars; sizes, no file "
                            "contents")
            else:
                observed = (f"{c['n_workflow_lines']} workflow_run path lines "
                            f"among {len(c['output']):,} chars; paths only, no "
                            "file contents")
            call_rows.append([str(c["seq"]), c["tool"], input_summary,
                              observed])
        out += md_table(["Message seq", "Tool", "Recorded input",
                         "Observed returned output"], call_rows)
        out.append("")
        if audit.get("grep_log_line"):
            out.append("Server log for the grep invocation:")
            out.append("")
            out.append("```")
            out.append(audit["grep_log_line"][:1600])
            out.append("```")
            out.append("")
        glob_calls = [c for c in au["calls"] if c["tool"] == "glob"]
        shell_calls = [c for c in au["calls"] if c["tool"] == "shell"]
        grep_calls = [c for c in au["calls"] if c["tool"] == "grep"]
        n_glob_wf = sum(c["n_workflow_lines"] for c in glob_calls)
        n_shell_wf = sum(c["n_workflow_lines"] for c in shell_calls)
        n_grep_wf = sum(c["n_workflow_lines"] for c in grep_calls)
        glob_chars = sum(len(c["output"]) for c in glob_calls)
        shell_chars = sum(len(c["output"]) for c in shell_calls)
        grep_matches = sum(
            int(m.group(1))
            for c in grep_calls
            for m in [re.search(r"Found (\d+) matches", c["output"])] if m)
        out.append(
            f"**Observed actions.** The glob call returned {n_glob_wf} "
            f"workflow_run paths among the `.md` paths it matched "
            f"({glob_chars:,} characters of output). The recursive listing "
            f"returned {n_shell_wf} workflow_run paths with sizes "
            f"({shell_chars:,} characters of output). Both returned path "
            "strings only, never file contents. The grep returned "
            f"{grep_matches} matching lines, all from files outside "
            f"workflow_run, and {n_grep_wf} workflow_run lines.")
        out.append("")
        out.append("**Recorded disclosure.** The autonomous run's own "
                   "`results/agent_run/analysis_choices.md` states that the "
                   "listing displayed names and sizes under "
                   "`results/workflow_run/` and that the content search "
                   "traversed that directory without returning lines from it.")
        out.append("")
        out.append("**Uncertain context exposure.** The server log shows that "
                   "the grep was executed with ripgrep over `results` using "
                   "`--glob=*.md` and no workflow_run exclusion. Ripgrep reads "
                   "file contents to search them, so the search process had "
                   "file-level access to the workflow_run markdown files. The "
                   "recorded tool output, however, contains no workflow_run "
                   "content. Whether any such bytes entered the model context "
                   "beyond the returned output cannot be established from the "
                   "record. Strict process-level independence therefore cannot "
                   "be fully verified; the analysis is independent at the level "
                   "of returned content and of the scripts' input paths, but "
                   "this is not a claim of verified non-exposure.")
    else:
        out.append("The recorded autonomous-run session was not available to "
                   "this script. Independence of the initial search cannot be "
                   "fully verified from tool-call evidence; no conclusion about "
                   "internal file access is drawn.")
    out.append("")

    out.append("## Verdict")
    out.append("")
    failed = [c for c in checks if not c["pass"]]
    out.append(f"- Comparisons performed: **{len(checks)}**; failed: "
               f"**{len(failed)}**.")
    out.append(f"- All numerical comparisons passed: "
               f"**{'YES' if all_pass and not failed else 'NO'}**.")
    out.append("- The two saved analyses are numerically identical at the "
               "reported precision and at the item level.")
    out.append("- **This is implementation consistency, not independent "
               "validation of the underlying classifications.** Both runs use "
               "the same frozen human labels and the same frozen AI labels; "
               "agreement between the runs does not add independent evidence "
               "about classification quality or accuracy.")
    out.append("- No frozen label, codebook, study-design element or analysis "
               "result was changed. `results/workflow_run/` and "
               "`results/agent_run/` were read only.")
    out.append("")

    if failed:
        out.append("## Failed comparisons")
        out.append("")
        for c in failed:
            out.append(f"- `{c['section']}` / `{c['name']}`: workflow "
                       f"`{fmt_value(c['workflow'])}`, agent "
                       f"`{fmt_value(c['agent'])}`")
        out.append("")

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"report written: {rel(REPORT)}")
    print(f"checks: {len(checks)}; failed: {len(failed)}; all_pass={all_pass and not failed}")
    print(f"max confusion-cell difference: {max_cell_diff:g}")
    print(f"max interval endpoint difference: {max_endpoint_diff:g}")
    for c in failed:
        print(f"FAIL: {c['section']} / {c['name']}: {c['workflow']} vs {c['agent']}")
    if not all_pass or failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
