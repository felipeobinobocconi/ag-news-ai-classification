"""Record which OpenCode model produced each saved analysis run.

This is a provenance record, not an analysis. It reads the local OpenCode
session store in read-only mode, extracts the model identifiers attached to the
assistant messages that mention the analysis scripts, and writes them to a
result file so the report can cite a saved artefact.

The OpenCode session store is machine-local and is not part of the project
inputs. No prompt, response text or credential is copied into the output; only
model identifiers, agent name, CLI version, session title and message counts are
recorded.

Inputs (read-only):
  ~/.local/share/opencode/opencode.db   local OpenCode session store

Outputs:
  results/agent_run/analysis_model_metadata.json
  results/agent_run/analysis_model_metadata.md

Run:
  uv run python src/23_record_analysis_model_metadata.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SEED = 42

PROJECT = Path(__file__).resolve().parents[1]
DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
OUT_JSON = PROJECT / "results" / "agent_run" / "analysis_model_metadata.json"
OUT_MD = PROJECT / "results" / "agent_run" / "analysis_model_metadata.md"

RUNS = (
    {
        "run": "workflow_run",
        "title": "Data analysis assignment setup",
        "scripts": ("11_agreement_overall", "12_category_hypothesis"),
    },
    {
        "run": "agent_run",
        "title": "Autonomous evaluation agreement run",
        "scripts": (
            "13_agent_run_verify_inputs",
            "14_agent_run_agreement",
            "15_agent_run_category_comparison",
            "16_agent_run_confusion_figure",
            "17_agent_run_verify_outputs",
            "18_reconcile_runs",
            "20_consolidate_review",
            "21_original_label_comparison",
            "22_final_verification",
        ),
    },
)


def fail(message: str) -> None:
    print(f"CHECK FAILED: {message}")
    sys.exit(1)


def iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


def model_label(model: dict | None) -> str:
    if not isinstance(model, dict):
        return "unrecorded"
    return f"{model.get('providerID')}/{model.get('id')}"


def main() -> None:
    print(f"random seed fixed at {SEED} (no stochastic step in this script)")
    if not DB.exists():
        fail(f"OpenCode session store not found at {DB}; "
             "cannot record model provenance on this machine")

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    records = []
    for spec in RUNS:
        row = con.execute(
            "select id, title, directory, agent, model, version, time_created "
            "from session_v2 where title = ?",
            (spec["title"],),
        ).fetchone()
        if row is None:
            fail(f"session not found: {spec['title']}")
        if Path(row[2]).resolve() != PROJECT:
            fail(f"session {spec['title']} belongs to a different directory: "
                 f"{row[2]}")

        session_id, title, _directory, agent, session_model, version, created = row
        session_model = json.loads(session_model) if session_model else None

        messages = con.execute(
            "select type, data from session_message where session_id = ?",
            (session_id,),
        ).fetchall()

        assistant_models: Counter[str] = Counter()
        variants: Counter[str] = Counter()
        per_script: dict[str, Counter[str]] = {
            script: Counter() for script in spec["scripts"]
        }
        for message_type, data in messages:
            if message_type != "assistant":
                continue
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            model = payload.get("model")
            label = model_label(model)
            assistant_models[label] += 1
            if isinstance(model, dict) and model.get("variant"):
                variants[str(model["variant"])] += 1
            for script in spec["scripts"]:
                if script in data:
                    per_script[script][label] += 1

        records.append({
            "run": spec["run"],
            "session_title": title,
            "session_id": session_id,
            "agent": agent,
            "cli_version": version,
            "session_start_utc": iso_utc(created),
            "session_model": model_label(session_model),
            "session_model_variant": (
                ", ".join(sorted(variants)) if variants else "not recorded"
            ),
            "assistant_messages_by_model": dict(assistant_models),
            "scripts": {
                script: dict(counts) for script, counts in per_script.items()
            },
        })
    con.close()

    payload = {
        "script": "src/23_record_analysis_model_metadata.py",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Local OpenCode session store, read in read-only mode. "
                  "No prompt or response text was copied into this file.",
        "note": "The OpenCode agent is the analysis assistant. It is not the "
                "classifier; the AI labels were produced separately by the "
                "Gemini API model recorded in the classification freeze note.",
        "runs": records,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Analysis model metadata",
        "",
        f"- Script: `src/23_record_analysis_model_metadata.py`",
        f"- Recorded (UTC): {payload['run_utc']}",
        f"- Source: {payload['source']}",
        "",
        "| Run | Session | Agent | CLI | Session model | Variant |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| `{record['run']}` | {record['session_title']} | "
            f"`{record['agent']}` | `{record['cli_version']}` | "
            f"`{record['session_model']}` | `{record['session_model_variant']}` |"
        )
    lines += [
        "",
        "Per-script model attribution counts each assistant message whose recorded",
        "content mentions the script name. A session can therefore list more than",
        "one model if the model was switched mid-session.",
        "",
    ]
    for record in records:
        lines.append(f"## {record['run']}")
        lines.append("")
        lines.append(f"- Session ID: `{record['session_id']}`")
        lines.append(f"- Started (UTC): {record['session_start_utc']}")
        lines.append("- Assistant messages by model: "
                     f"{record['assistant_messages_by_model']}")
        for script, counts in record["scripts"].items():
            lines.append(f"- `{script}`: {counts}")
        lines.append("")
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(PROJECT)}")
    print(f"wrote {OUT_MD.relative_to(PROJECT)}")
    for record in records:
        print(f"  {record['run']}: {record['session_model']} "
              f"(CLI {record['cli_version']})")


if __name__ == "__main__":
    main()
