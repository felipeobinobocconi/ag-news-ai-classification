# Analysis model metadata

- Script: `src/23_record_analysis_model_metadata.py`
- Recorded (UTC): 2026-11-17T14:35:00.338077+00:00
- Source: Local OpenCode session store, read in read-only mode. No prompt or response text was copied into this file.

| Run | Session | Agent | CLI | Session model | Variant |
| --- | --- | --- | --- | --- | --- |
| `workflow_run` | Data analysis assignment setup | `build` | `2.2.5` | `opencode/deepseek-v4.1-flash-free` | `default` |
| `agent_run` | Autonomous evaluation agreement run | `build` | `2.2.5` | `opencode/deepseek-v4.1-flash-free` | `default` |

Per-script model attribution counts each assistant message whose recorded
content mentions the script name. A session can therefore list more than
one model if the model was switched mid-session.

## workflow_run

- Session ID: `ses_e54d9108dffeng0evfFnR5vdWc`
- Started (UTC): 2026-11-05T10:00:18.054000+00:00
- Assistant messages by model: {'opencode/glm-5.3-flash-free': 107, 'opencode/deepseek-v4.1-flash-free': 45}
- `11_agreement_overall`: {'opencode/deepseek-v4.1-flash-free': 7}
- `12_category_hypothesis`: {'opencode/deepseek-v4.1-flash-free': 7}

## agent_run

- Session ID: `ses_e25ca40cfffeBwMwykmm0E7pxD`
- Started (UTC): 2026-11-14T13:18:37.905000+00:00
- Assistant messages by model: {'opencode/deepseek-v4.1-flash-free': 257}
- `13_agent_run_verify_inputs`: {'opencode/deepseek-v4.1-flash-free': 40}
- `14_agent_run_agreement`: {'opencode/deepseek-v4.1-flash-free': 39}
- `15_agent_run_category_comparison`: {'opencode/deepseek-v4.1-flash-free': 29}
- `16_agent_run_confusion_figure`: {'opencode/deepseek-v4.1-flash-free': 27}
- `17_agent_run_verify_outputs`: {'opencode/deepseek-v4.1-flash-free': 42}
- `18_reconcile_runs`: {'opencode/deepseek-v4.1-flash-free': 48}
- `20_consolidate_review`: {'opencode/deepseek-v4.1-flash-free': 28}
- `21_original_label_comparison`: {'opencode/deepseek-v4.1-flash-free': 31}
- `22_final_verification`: {'opencode/deepseek-v4.1-flash-free': 49}
