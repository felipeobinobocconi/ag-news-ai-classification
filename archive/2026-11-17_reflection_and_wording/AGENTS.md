# Agent Rules

1. **Never modify anything in `data/raw/`.** Treat it as read-only; only read from it.
2. **After every filter, merge or drop, print the number of rows and the reason.** Every step that changes the number of observations must log the new row count and why rows were removed or joined.
3. **Every number in a write-up must come from a file in `results/`; name the script that made it.** No hand-typed or remembered numbers in any text output.
4. **Follow `plan.md`. Ask before changing it, and list every analysis choice you make.** Deviations, defaults, and judgment calls must be stated explicitly.
5. **Fix random seeds, and log the prompt, output and model name of every model call.** Set the seed at the top of any script using randomness; record every LLM/model invocation verbatim.
6. **No causal claims unless the design supports them.** If the identification is not causal, describe associations only. Say "I am not sure" when uncertain.
7. **Run Python scripts using `uv run`.** All Python execution goes through uv.
8. **When a task explicitly prohibits file creation or modification, do not write scripts, reports or logs.** Explain any conflict with standing instructions before proceeding.
9. **Write all project analyses, reports and documentation in English. Preserve original source texts.**
10. **Consult `data/README.md` before working with project data. When an authorized change affects the documented schema, provenance, or data properties, update the relevant documentation and report the change.**
